from fastapi import APIRouter, Request,Depends, Query
from fastapi.responses import HTMLResponse
from typing import Optional
from sqlalchemy import select, func, or_
from sqlalchemy.ext.asyncio import AsyncSession
from Backend.models.models import Users, DWGApplication
from .authentication import get_current_user
from Backend.models.database import get_db, SessionLocal
import math
from fastapi.templating import Jinja2Templates

router=APIRouter(prefix="/reports", tags=["reports"])
templates= Jinja2Templates(directory="FrontEnd/templates")

@router.get("/",response_class=HTMLResponse)
async def reports(request:Request,
                  current_user:Users=Depends(get_current_user),
                  db:AsyncSession=Depends(get_db),
                  search:Optional[str]=Query(None),
                  page: int=Query(1,ge=1)):

    per_page= 10

    query= select(DWGApplication).where(func.lower(DWGApplication.report_status)=="completed",DWGApplication.user_id == current_user.id)

    if search:

        query= query.where(or_(DWGApplication.ref_id.ilike(f"%{search}%"),
                               DWGApplication.applicant_name.ilike(f"%{search}%"),
                               DWGApplication.applicant_no.ilike(f"%{search}%")))

    count_query= query.with_only_columns(func.count(DWGApplication.application_id)).order_by(None)

    total_records= await db.scalar(count_query)

    total_pages= math.ceil(total_records/per_page) if total_records else 1

    query= (query.order_by(DWGApplication.created_at.desc()).offset((page-1)*per_page).limit(per_page))

    result= await db.execute(query)

    reports= result.scalars().all()


    return templates.TemplateResponse(request,"reports.html",
                                      {'user':current_user.username,"reports":reports,
                                       "search":search,"page":page,"total_pages":total_pages,
                                       "total_records":total_records})