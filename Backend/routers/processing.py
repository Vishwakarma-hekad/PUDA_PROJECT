from fastapi.responses import HTMLResponse
from fastapi import APIRouter,Request, Depends, Query, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from Backend.models.models import Users, DWGApplication
from sqlalchemy import select
from starlette.templating import Jinja2Templates
from Backend.models.database import get_db, SessionLocal
from .authentication import get_current_user
from typing import Optional
from Backend.services import redis_progress


router=APIRouter(prefix="/processing",tags=["processing"])
templates= Jinja2Templates(directory="FrontEnd/templates")

@router.get("/", response_class=HTMLResponse)
async def processing(
    request: Request,
    ref_id: Optional[str] = Query(None),
    current_user: Users = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):

    if ref_id:

        result = await db.execute(
            select(DWGApplication).where(
                DWGApplication.ref_id == ref_id,
                DWGApplication.user_id == current_user.id
            )
        )

    else:

        result = await db.execute(
            select(DWGApplication)
            .where(
                DWGApplication.user_id == current_user.id
            )
            .order_by(
                DWGApplication.created_at.desc()
            )
            .limit(1)
        )

    application = result.scalar_one_or_none()

    if application is None:

        raise HTTPException(
            status_code=404,
            detail="Application not found"
        )


    return templates.TemplateResponse(
        request=request,
        name="processing.html",
        context={
            "user": current_user.username,
            "application": application
        }
    )

@router.get("/status/{ref_id}")
async def track_filestatus(ref_id:str,db:AsyncSession=Depends(get_db),
                           current_user:Users=Depends(get_current_user)):

    progress= redis_progress.get_progress(ref_id)

    if progress:
        status = {
            "status": progress["status"],
            "step": progress["step"],
            "step_no": progress["step_no"],
            "progress":progress["progress"] ,
            "estimated_time": "",
            "executed_time": ""
        }
        return status

    result= await db.execute(select(DWGApplication).where(DWGApplication.user_id==current_user.id,
                                                          DWGApplication.ref_id == ref_id))

    appln= result.scalar_one_or_none()

    if appln:

        if appln.report_status=="completed":
            status={
                "status": "completed",
                "step": "completed",
                "step_no": 7,
                "progress": 100,
                "estimated_time":"",
                "executed_time": appln.total_time
            }
        elif appln.report_status=="submitted":
            status={
                "status": "submitted",
                "step": "submitted",
                "step_no": 1,
                "progress": 18,
                "estimated_time":"",
                "executed_time": appln.total_time
            }

        else:

            status = {
                "status": "failed",
                "step": "",
                "step_no": 1,
                "progress":0,
                "estimated_time": "",
                "executed_time": appln.total_time
            }

        return status

    return {"msg":"application Not Found"}

# from typing import Optional
#
# from fastapi import APIRouter, Request, Depends, Query, HTTPException
# from fastapi.responses import HTMLResponse
# from sqlalchemy.ext.asyncio import AsyncSession
# from sqlalchemy import select
# from starlette.templating import Jinja2Templates
#
# from models.models import Users, DWGApplication
# from models.database import get_db
# from app import get_current_user
# from services import redis_progress
#
#
# router = APIRouter(
#     prefix="/processing",
#     tags=["processing"]
# )
#
# templates = Jinja2Templates(
#     directory="../FrontEnd/templates"
# )
#
#
# # ---------------------------------------------------------
# # Processing Page
# # ---------------------------------------------------------
#
# @router.get("/", response_class=HTMLResponse)
# async def processing(
#     request: Request,
#     ref_id: Optional[str] = Query(default=None),
#     current_user: Users = Depends(get_current_user),
#     db: AsyncSession = Depends(get_db)
# ):
#
#     # If ref_id is provided, get that application
#     if ref_id:
#
#         result = await db.execute(
#             select(DWGApplication).where(
#                 DWGApplication.ref_id == ref_id,
#                 DWGApplication.user_id == current_user.id
#             )
#         )
#
#     # Otherwise get latest application of current user
#     else:
#
#         result = await db.execute(
#             select(DWGApplication)
#             .where(
#                 DWGApplication.user_id == current_user.id
#             )
#             .order_by(
#                 DWGApplication.created_at.desc()
#             )
#             .limit(1)
#         )
#
#     application = result.scalar_one_or_none()
#
#     if application is None:
#
#         raise HTTPException(
#             status_code=404,
#             detail="Application not found"
#         )
#
#     return templates.TemplateResponse(
#         request=request,
#         name="processing.html",
#         context={
#             "user": current_user.username,
#             "application": application
#         }
#     )
#
#
# # ---------------------------------------------------------
# # Processing Status API
# # ---------------------------------------------------------
#
# @router.get("/status/{ref_id}")
# async def track_file_status(
#     ref_id: str,
#     db: AsyncSession = Depends(get_db),
#     current_user: Users = Depends(get_current_user)
# ):
#
#     # -----------------------------------------------------
#     # First check Redis
#     # -----------------------------------------------------
#
#     progress = redis_progress.get_progress(ref_id)
#
#     if progress:
#
#         return {
#             "status": progress.get("status", "processing"),
#             "step": progress.get("step", ""),
#             "step_no": progress.get("step_no", 1),
#             "progress": progress.get("progress", 0),
#             "estimated_time": progress.get(
#                 "estimated_time",
#                 ""
#             ),
#             "executed_time": progress.get(
#                 "executed_time",
#                 ""
#             )
#         }
#
#     # -----------------------------------------------------
#     # Redis does not contain progress
#     # Check database
#     # -----------------------------------------------------
#
#     result = await db.execute(
#         select(DWGApplication).where(
#             DWGApplication.user_id == current_user.id,
#             DWGApplication.ref_id == ref_id
#         )
#     )
#
#     application = result.scalar_one_or_none()
#
#     if application is None:
#
#         raise HTTPException(
#             status_code=404,
#             detail="Application not found"
#         )
#
#     # -----------------------------------------------------
#     # Completed
#     # -----------------------------------------------------
#
#     if application.report_status == "completed":
#
#         return {
#             "status": "completed",
#             "step": "Completed",
#             "step_no": 7,
#             "progress": 100,
#             "estimated_time": "",
#             "executed_time": application.total_time or ""
#         }
#
#     # -----------------------------------------------------
#     # Submitted / Waiting
#     # -----------------------------------------------------
#
#     elif application.report_status == "submitted":
#
#         return {
#             "status": "submitted",
#             "step": "Drawing Submitted",
#             "step_no": 1,
#             "progress": 10,
#             "estimated_time": "",
#             "executed_time": application.total_time or ""
#         }
#
#     # -----------------------------------------------------
#     # Processing
#     # -----------------------------------------------------
#
#     elif application.report_status in [
#         "processing",
#         "in_progress"
#     ]:
#
#         return {
#             "status": "processing",
#             "step": "Processing",
#             "step_no": 2,
#             "progress": 20,
#             "estimated_time": "",
#             "executed_time": application.total_time or ""
#         }
#
#     # -----------------------------------------------------
#     # Failed
#     # -----------------------------------------------------
#
#     elif application.report_status == "failed":
#
#         return {
#             "status": "failed",
#             "step": "Processing Failed",
#             "step_no": 1,
#             "progress": 0,
#             "estimated_time": "",
#             "executed_time": application.total_time or ""
#         }
#
#     # -----------------------------------------------------
#     # Unknown state
#     # -----------------------------------------------------
#
#     return {
#         "status": application.report_status or "waiting",
#         "step": "",
#         "step_no": 1,
#         "progress": 0,
#         "estimated_time": "",
#         "executed_time": application.total_time or ""
#     }