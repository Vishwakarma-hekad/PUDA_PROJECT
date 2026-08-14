from fastapi.responses import HTMLResponse,RedirectResponse
from fastapi import APIRouter,Request, Depends,HTTPException, Form
from sqlalchemy.ext.asyncio import AsyncSession
from Backend.models.models import Users, DWGApplication
from starlette.templating import Jinja2Templates
from Backend.models.database import get_db, SessionLocal
from .authentication import get_current_user,verify_password, hash_password

router=APIRouter(prefix="/profile",tags=["profile"])
templates= Jinja2Templates(directory="FrontEnd/templates")


@router.get("/",response_class=HTMLResponse)
async def profile(request:Request,current_user:Users=Depends(get_current_user)):

    return templates.TemplateResponse(request,"profile.html",{'user':current_user})
@router.post("/profile/update")
async def update_profile(
        username: str= Form(...),
        email: str= Form(...),
        phone: str= Form(...),
        current_user: Users= Depends(get_current_user),
        db:AsyncSession=Depends(get_db)
):
    current_user.username= username
    current_user.email= email
    current_user.phone= phone

    db.add(current_user)
    await db.commit()
    await db.refresh(current_user)

    return RedirectResponse(url="/profile",status_code=303)

@router.post("/profile/password")
async def update_password(
        old_password: str= Form(...),
        new_password: str= Form(...),
        confirm_password: str= Form(...),
        current_user:Users=Depends(get_current_user),
        db:AsyncSession=Depends(get_db)
):
    if not verify_password(old_password,current_user.password):

        raise HTTPException(status_code=400, detail="old password is incorrect.")

    if new_password!=confirm_password:

        raise HTTPException(status_code=400, detail="Password do not match")

    current_user.password= hash_password(new_password)

    db.add(current_user)

    await db.commit()

    return RedirectResponse(url="/profile",status_code=303)