from fastapi.responses import HTMLResponse
from fastapi import APIRouter,Request, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from models.models import Users, DWGApplication
import math
from sqlalchemy import select, func
from starlette.responses import RedirectResponse
from starlette.templating import Jinja2Templates
from models.database import get_db, SessionLocal

from .authentication import get_current_user

router=APIRouter(tags=["dashboard"])
templates= Jinja2Templates(directory="../FrontEnd/templates")

# async def get_current_user(
#     request: Request,
#     token: str = Depends(oauth2_scheme),
#     db: AsyncSession = Depends(get_db),
# ):
#     # If Authorization header is missing, use cookie
#     if not token:
#         token = request.cookies.get("access_token")
#
#     if not token:
#         raise HTTPException(status_code=401, detail="Not authenticated")
#
#     try:
#         payload = jwt.decode(
#             token,
#             SECREATE_KEY,
#             algorithms=[ALGORITHM]
#         )
#
#         user_id = int(payload["sub"])
#
#     except JWTError:
#         raise HTTPException(status_code=401, detail="Invalid token")
#
#     result = await db.execute(
#         select(Users).where(Users.id == user_id)
#     )
#
#     user = result.scalar_one_or_none()
#
#     if user is None:
#         raise HTTPException(status_code=401, detail="User not found")
#
#     return user

@router.get("/",response_class=HTMLResponse)
async def dashboard(request:Request,
                    current_user:Users=Depends(get_current_user),
                    db:AsyncSession=Depends(get_db),
                    page:int= Query(1,ge=1)):

    if current_user is None:

        return RedirectResponse(url="/login")

    per_page=10
    total=await db.scalar(select(func.count()).select_from(DWGApplication))

    total_pages= math.ceil(total/per_page) if total else 1

    processing = await db.scalar(select(func.count()).where(DWGApplication.scrutiny_status=="processing"))

    completed = await db.scalar(select(func.count()).where(DWGApplication.scrutiny_status=="completed"))

    failed = await db.scalar(select(func.count()).where(DWGApplication.scrutiny_status== "failed"))

    result = await db.execute(select(DWGApplication).order_by(DWGApplication.created_at.desc()).offset((page-1)*per_page).limit(per_page))
    recent_applications=result.scalars().all()

    # print("Applications Count:", len(recent_applications))
    #
    # for app in recent_applications:
    #     print(app.ref_id, app.applicant_name, app.status)

    return templates.TemplateResponse(request,"dashboard.html",{'username':current_user.username,
                                                                "page":page,"total_pages":total_pages,
                                                                "total":total,"processing":processing,
                                                                "completed":completed,"failed":failed,
                                                                "recent_applications":recent_applications})