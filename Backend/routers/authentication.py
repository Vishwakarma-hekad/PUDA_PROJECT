from fastapi import APIRouter, Depends,Form, Request, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy.ext.asyncio import AsyncSession
from Backend.models.models import Users,DWGApplication,UserSettings
from Backend.models.database import get_db, SessionLocal
from sqlalchemy import select
from starlette import status
from starlette.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from passlib.context import CryptContext
from datetime import datetime, timedelta
import jwt

ACCESS_TOKEN_EXPIRE_MINUTES= 60
SECREATE_KEY="PUDA_JWT_EXPIRY_TOKEN"
ALGORITHM= "HS256"

pwd_context=CryptContext(schemes=["bcrypt"],deprecated="auto")

oauth2_scheme= OAuth2PasswordBearer(tokenUrl="/login",auto_error=False)

router=APIRouter(tags=["authentication"])

router.mount("/static",StaticFiles(directory="FrontEnd/static"),name="static")

templates= Jinja2Templates(directory="FrontEnd/templates")


def hash_password(password:str):

    return pwd_context.hash(password)


def verify_password(password,hashed_password):

    return pwd_context.verify(password,hashed_password)

def create_access_token(data:dict):

    to_encode= data.copy()

    expire = datetime.utcnow()+ timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)

    to_encode.update({"exp":expire})

    return jwt.encode(to_encode,SECREATE_KEY)



async def get_current_user(
    request: Request,
    token: str = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db),
):
    # If Authorization header is missing, use cookie
    if not token:
        token = request.cookies.get("access_token")

    if not token:
        return None

    try:
        payload = jwt.decode(
            token,
            SECREATE_KEY,
            algorithms=[ALGORITHM]
        )

        user_id = int(payload["sub"])

    except JWTError:
        return None

    result = await db.execute(
        select(Users).where(Users.id == user_id)
    )

    user = result.scalar_one_or_none()

    if user is None:
        return None

    return user


@router.get("/login",response_class=HTMLResponse)
async def home(request:Request):

    return templates.TemplateResponse(request,"login.html")

@router.get("/register", response_class=HTMLResponse)
async def register_page(request: Request,):

    return templates.TemplateResponse(
        request=request,
        name="register.html",
    )

@router.post("/register",response_class=HTMLResponse)
async def register(db:AsyncSession=Depends(get_db),
                   fullname:str=Form(...),
                   username:str=Form(...),
                   email:str=Form(...),
                   phone:str=Form(...),
                   password:str=Form(...)):

    results= await db.execute(select(Users).where(Users.username==username))

    username_existing= results.scalar_one_or_none()

    if username_existing:

        raise HTTPException(status_code=400,detail="username already exists")

    result = await db.execute(select(Users).where(Users.email == email))
    existing_email = result.scalar_one_or_none()

    if existing_email:
        raise HTTPException(status_code=400, detail="email already exists")

    hashed_password = hash_password(password)

    new_user = Users(username=username,
                     email=email,
                     password=hashed_password,
                     phone=phone)

    db.add(new_user)
    await db.commit()
    await db.refresh(new_user)

    return RedirectResponse("/login")

@router.post("/login")
async def login(
        email: str = Form(...),
        password: str = Form(...),
        db:AsyncSession=Depends(get_db)
):

    result= await db.execute(select(Users).where(Users.email==email))

    exists_email=result.scalar_one_or_none()

    if exists_email is None:

        raise HTTPException(status_code=401,detail="Invalid email or password")

    if not verify_password(password,exists_email.password):

        raise HTTPException(status_code=401, detail="Invalid email or password")

    exists_email.is_active = True
    await db.commit()

    token=create_access_token({
        "sub":str(exists_email.id),
        "email":exists_email.email,
        "role":"user"
    })

    response= RedirectResponse("/",status_code=status.HTTP_303_SEE_OTHER)

    response.set_cookie(
        key="access_token",
        value=token,
        httponly=True,
        samesite="lax"
    )
    return response

@router.get("/logout")
async def logout(request:Request,
                 db:AsyncSession=Depends(get_db),
                 current_user: Users=Depends(get_current_user)):
    current_user.is_active=False
    await db.commit()

    response= RedirectResponse("/login",status_code=status.HTTP_303_SEE_OTHER)

    response.delete_cookie(key="access_token")

    return response