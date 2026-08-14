from fastapi.responses import HTMLResponse
from fastapi import APIRouter,Request, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from Backend.models.models import Users, DWGApplication, UserSettings
from starlette.templating import Jinja2Templates
from Backend.models.database import get_db, SessionLocal
from .authentication import get_current_user
from sqlalchemy import select

router=APIRouter(prefix="/settings",tags=["settings"])
templates= Jinja2Templates(directory="FrontEnd/templates")

@router.get("/",response_class=HTMLResponse)
async def settingsx(request:Request,
                    current_user:Users=Depends(get_current_user),
                    db:AsyncSession=Depends(get_db)
                    ):

    result= await db.execute(select(UserSettings).where(UserSettings.user_id==current_user.id))

    settings= result.scalar_one_or_none()

    return templates.TemplateResponse(request,"settings.html",{'user':current_user,
                                                               "settings":settings})