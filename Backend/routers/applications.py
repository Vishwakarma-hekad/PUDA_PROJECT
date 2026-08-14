from http.client import HTTPException

from celery.utils.text import indent
from fastapi import APIRouter,Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi import Request, Query, Depends
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from Backend.models.database import get_db, SessionLocal
from sqlalchemy import select, func, or_
from Backend.models.models import Users, DWGApplication
import math
from fastapi.templating import Jinja2Templates
from .authentication import get_current_user

router=APIRouter(prefix="/applications",tags=["applications"])
templates= Jinja2Templates(directory="FrontEnd/templates")

@router.get("/",response_class=HTMLResponse)
async def applications(request:Request,
                       search:Optional[str]=Query(None),
                       status:Optional[str]=Query(None),
                       db:AsyncSession=Depends(get_db),
                       page:int=Query(1,ge=1)):

    per_page = 10

    query=select(DWGApplication)

    if search:

        query= query.where(or_(
            DWGApplication.ref_id.ilike(f"%{search}%"),
            DWGApplication.applicant_name.ilike(f"%{search}%"),
            DWGApplication.file_name.ilike(f"%{search}%")
        ))

    if status:

        query= query.where(DWGApplication.status== status.lower())


    count_query= query.with_only_columns(func.count(DWGApplication.application_id)).order_by(None)

    total_records = await db.scalar(count_query)

    total_pages = math.ceil(total_records / per_page) if total_records else 1

    query=  (query.order_by(DWGApplication.created_at.desc()).offset((page-1)*per_page).limit(per_page))

    result= await db.execute(query)

    applications= result.scalars().all()

    return templates.TemplateResponse(request,"applications.html",{"applications":applications,
                                                                   "search":search,"status":status,
                                                                   "page":page,"total_pages":total_pages,
                                                                   "total_records":total_records})

# @router.get("/view-report/{ref_id}",response_class=HTMLResponse)
# async def get_report_data(request:Request,ref_id:str,
#                           db:AsyncSession=Depends(get_db),
#                           current_user:Users=Depends(get_current_user)):
#
#     result= await db.execute(select(DWGApplication).where(DWGApplication.ref_id == ref_id,
#                                                           DWGApplication.user_id == current_user.id))
#
#     report= result.scalar_one_or_none()
#
#     if report is None:
#
#         raise HTTPException(status_code= 404, detail= "Report Data Not Found")
#
#     return templates.TemplateResponse(
#     request=request,
#     name="pdf_report.html",
#     context={
#         "request": request,
#         "ref_id": ref_id
#     }
# )

@router.get("/json-report/{ref_id}")
async def view_report_json(
    ref_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: Users = Depends(get_current_user),
):

    result = await db.execute(
        select(DWGApplication).where(
            DWGApplication.ref_id == ref_id
        )
    )

    report = result.scalar_one_or_none()

    if report is None:
        raise HTTPException(404, "Report not found")

    return JSONResponse(content=report.view_report)

@router.get("/view-report/{ref_id}",response_class=HTMLResponse)
async def get_report_data(request:Request,ref_id:str,
                          db:AsyncSession=Depends(get_db),
                          current_user:Users=Depends(get_current_user)):

    result= await db.execute(select(DWGApplication).where(DWGApplication.ref_id == ref_id,
                                                          DWGApplication.user_id == current_user.id))

    report= result.scalar_one_or_none()

    if report is None:

        raise HTTPException(status_code= 404, detail= "Report Data Not Found")

    return templates.TemplateResponse(
    request=request,
    name="pdf_report.html",
    context={
        "request": request,
        "ref_id": ref_id
    }
)