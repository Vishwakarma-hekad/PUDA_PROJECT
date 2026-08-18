import smtplib
from datetime import timezone
import bcrypt
from fastapi import APIRouter, Depends,Form, Request, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy.ext.asyncio import AsyncSession
from starlette.responses import JSONResponse
from Backend.models.models import Users, PasswordResetOtp
from Backend.models.database import get_db
from sqlalchemy import select
from starlette import status
from starlette.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from passlib.context import CryptContext
from datetime import datetime, timedelta
import jwt
from jwt.exceptions import ExpiredSignatureError
import secrets
from email.message import EmailMessage
from Backend.config import settings

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

    except ExpiredSignatureError:

        print("Access token expired")

        return None


    except jwt.InvalidTokenError:

        print("Invalid access token")

        return None

    except (KeyError, ValueError, TypeError):

        print("Invalid user information in token")
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

def generate_otp():

    return str(secrets.randbelow(900000)+100000)

def hash_otp(otp:str):

    return bcrypt.hashpw(otp.encode("utf-8"),bcrypt.gensalt()).decode("utf-8")

def verify_otp(otp:str,otp_hash:str):

    return bcrypt.checkpw(otp.encode("utf-8"),otp_hash.encode("utf-8"))

def send_otp_email(recipient_email:str,otp:str):

    message= EmailMessage()

    message["Subject"] = "PUDA Password Reset OTP"

    message["From"] = settings.MAIL_FROM

    message["To"] = recipient_email

    message.set_content(
        f"""
    Hello,

    We received a request to reset your PUDA account password.

    Your OTP is:

    {otp}

    This OTP is valid for 5 minutes.

    If you did not request a password reset, please ignore this email.

    Regards,
    PUDA Team
    """
    )

    with smtplib.SMTP(settings.MAIL_HOST,settings.MAIL_PORT) as server:

            server.starttls()
            server.login(settings.MAIL_USERNAME,
                         settings.MAIL_PASSWORD)

            server.send_message(message)

@router.get("/forgot-password")
async def forgot_password(request: Request):

    return templates.TemplateResponse(
        request=request,
        name="forgot_password.html"
    )


@router.post("/forgot-password")
async def forgot_password(
    request: Request,
    email: str = Form(...),
    db: AsyncSession = Depends(get_db)
):

    # -----------------------------------------
    # Clean email
    # -----------------------------------------
    email = email.strip().lower()

    # -----------------------------------------
    # Find user
    # -----------------------------------------
    result = await db.execute(
        select(Users).where(Users.email == email)
    )

    user = result.scalar_one_or_none()

    # -----------------------------------------
    # Email not registered
    # -----------------------------------------
    if user is None:

        return JSONResponse(
            status_code=404,
            content={
                "detail": "Email address is not registered."
            }
        )

    # -----------------------------------------
    # Generate OTP
    # -----------------------------------------
    otp = generate_otp()

    print("Generated OTP:", otp)

    # -----------------------------------------
    # Hash OTP before storing
    # -----------------------------------------
    otp_hash = hash_otp(otp)

    # -----------------------------------------
    # OTP expires after 5 minutes
    # -----------------------------------------
    expires_at = (
        datetime.now(timezone.utc)
        + timedelta(minutes=5)
    )

    # -----------------------------------------
    # Delete previous OTPs for this email
    # -----------------------------------------
    old_result = await db.execute(
        select(PasswordResetOtp).where(
            PasswordResetOtp.email == email
        )
    )

    old_otps = old_result.scalars().all()

    for old_otp in old_otps:
        await db.delete(old_otp)

    # -----------------------------------------
    # Create new OTP record
    # -----------------------------------------
    reset_otp = PasswordResetOtp(
        user_id=user.id,
        email=user.email,
        otp=otp_hash,
        expires_at=expires_at,
        is_verified=False
    )

    db.add(reset_otp)

    await db.commit()

    # -----------------------------------------
    # Send OTP email
    # -----------------------------------------
    try:

        send_otp_email(
            recipient_email=email,
            otp=otp
        )

        print("OTP Sent Successfully !!!")

    except Exception as exc:

        print("Email sending Failed:", exc)

        # Remove OTP record if email failed
        await db.delete(reset_otp)
        await db.commit()

        return JSONResponse(
            status_code=500,
            content={
                "detail": "Unable to send OTP email."
            }
        )

    # -----------------------------------------
    # Email sent successfully
    # -----------------------------------------
    response = JSONResponse(
        status_code=200,
        content={
            "message": "OTP sent successfully."
        }
    )

    # -----------------------------------------
    # Store email in cookie
    # -----------------------------------------
    response.set_cookie(
        key="password_reset_email",
        value=email,
        httponly=True,
        secure=False,       # True when using HTTPS in production
        samesite="lax",
        max_age=600
    )

    return response


@router.get(
    "/reset-password",
    response_class=HTMLResponse
)
async def reset_password_page(
    request: Request
):

    email = request.cookies.get(
        "password_reset_email"
    )

    verified = request.cookies.get(
        "password_reset_verified"
    )

    if not email or verified != "true":

        return RedirectResponse(
            url="/forgot-password",
            status_code=303
        )

    return templates.TemplateResponse(
        request=request,
        name="reset_password.html"
    )

@router.post("/reset-password")
async def reset_password(request:Request,
                         new_password:str= Form(...),
                         confirm_password:str= Form(...),
                         db:AsyncSession=Depends(get_db)):

    email= request.cookies.get("password_reset_email")

    verified= request.cookies.get("password_reset_verified")

    if not email or verified != "true":

        return JSONResponse(status_code=400, content={
            "detail":"Password Reset Session Expired."
        })

    if new_password != confirm_password:

        return JSONResponse(status_code=400,content={
            "detail":"Password do not match"
        })

    if len(new_password)<8:

        return JSONResponse(status_code=400, content={
            "detail":"Password must contain at least 8 characters."
        })

    result= await db.execute(select(Users).where(Users.email == email))

    user= result.scalar_one_or_none()

    if not user:

        return JSONResponse(status_code=400, content={
            "detail":"User Not Found"
        })
    hashed_password= hash_password(new_password)

    user.password= hashed_password

    await db.commit()

    otp_result= await db.execute(select(PasswordResetOtp).where(PasswordResetOtp.email==email))

    otp_records= otp_result.scalars().all()

    for otp_record in otp_records:

        await db.delete(otp_record)

    await db.commit()

    response= JSONResponse(status_code=200,content={"detail":"Password Reset Successfully."})

    response.delete_cookie(key="password_reset_email")

    response.delete_cookie(key="password_reset_verified")

    return response

@router.get("/verify-otp",response_class=HTMLResponse)
async def verify_otp_page(request:Request):

    email= request.cookies.get("password_reset_email")
    print(f"Verify Email: {email}")
    if not email:

        return RedirectResponse(url="/forgot-password",status_code=303)

    return templates.TemplateResponse(request=request,name="verify_otp.html")

@router.post("/verify-otp")
async def verify_otp_api(request:Request,otp:str=Form(...),
                         db:AsyncSession=Depends(get_db)):

    email= request.cookies.get("password_reset_email")
    if not email:

        return JSONResponse(
            status_code=400,
            content={
                "detail":
                "Password reset session expired."
            }
        )

    otp= otp.strip()

    if not otp.isdigit() or len(otp)!=6:

        return JSONResponse(
            status_code=400,
            content={
                "detail":
                "Please enter a valid 6-digit OTP."
            }
        )

    result= await db.execute(select(PasswordResetOtp).where(PasswordResetOtp.email==email,
                                                            PasswordResetOtp.is_verified == False).
                             order_by(PasswordResetOtp.created_at.desc()))

    reset_record= result.scalars().first()

    if not reset_record:

        return JSONResponse(
            status_code=400,
            content={
                "detail":
                "Invalid or expired OTP."
            }
        )

    now = datetime.now(timezone.utc)

    if reset_record.expires_at < now:

        return JSONResponse(
            status_code=400,
            content={
                "detail":
                "OTP has expired. Please request a new OTP."
            }
        )

    if not verify_otp(otp,reset_record.otp):

        await db.commit()

        return JSONResponse(
            status_code=400,
            content={
                "detail":
                    "Invalid OTP."
            }
        )

    reset_record.is_verified=True
    await db.commit()

    response = JSONResponse(
        status_code=200,
        content={
            "message":
                "OTP verified successfully."
        }
    )

    response.set_cookie(key="password_reset_verified",
                        value="true",
                        httponly=True,
                        secure=False,
                        samesite="lax",
                        max_age=600)

    return response