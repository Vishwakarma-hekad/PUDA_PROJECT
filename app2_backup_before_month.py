import math
from fastapi import FastAPI,Form,File, UploadFile, Request, HTTPException,Depends,BackgroundTasks,Query
from fastapi.concurrency import run_in_threadpool
from typing import Optional
from starlette.templating import Jinja2Templates
from digit_base import LayerMaster
import os
from starlette.responses import JSONResponse, FileResponse, HTMLResponse, RedirectResponse
from starlette import status
from config import settings
import uuid
import tempfile
from logging_config import get_server_logger, get_request_logger, close_request_logger, set_request_logger
import shutil
import json
import traceback
from process_file_new import processPlanBasedOnType
import sys
from timeit import default_timer as timer
from DB_API import send_building_data
from datetime import datetime
from DWG2DXF import convertDWGUtil_orig
from concurrent.futures import ThreadPoolExecutor
import asyncio
from pathlib import Path
from sqlalchemy.ext.asyncio import AsyncSession
from models.database import get_db, SessionLocal
from auth import hash_password,create_access_token, verify_password
from sqlalchemy import select, func, or_
from models.schemas import UserRegister,UserResponse,UserLogin
from models.models import Users,DWGApplication,UserSettings
from fastapi.security import OAuth2PasswordBearer
from fastapi.staticfiles import StaticFiles
from routers.authentication import get_current_user
oauth2_scheme= OAuth2PasswordBearer(tokenUrl="login",auto_error=False)
file_processor_pool = ThreadPoolExecutor(max_workers=4)

server_logger=get_server_logger()

app=FastAPI(title="BPConnectAPI")
app.mount("/static",StaticFiles(directory="../FrontEnd/static"),name="static")
templates= Jinja2Templates(directory="../FrontEnd/templates")

os.makedirs(settings.DWG_DIR,exist_ok=True)
os.makedirs(settings.DXF_DIR,exist_ok=True)
os.makedirs(settings.JSON_SUMMARY_DIR, exist_ok=True)

PORT_BP_MAP = {
    8000: "BP1",
    8001: "BP2",
    8002: "BP3",
    8003: "BP4",
    8004: "BP5",
    8005: "BP6",
    8006: "BP7",
    8007: "BP8",
    8008: "BP9",
    8009: "BP10",
}

Status_Dict={}

# async def get_current_user(token: str=Depends(oauth2_scheme),
#                            db:AsyncSession= Depends(get_db)):
#
#     try:
#             payload= jwt.decode(token,SECREATE_KEY,algorithms=[ALGORITHM])
#
#             user_id= int(payload.get("sub"))
#
#             if user_id is None:
#
#                 raise HTTPException(status_code=401,detail="Invalid Token")
#
#     except JWTError:
#
#         raise HTTPException(status_code=401,detail="Invalid Token")
#
#     result= await db.execute(select(Users).where(Users.id == user_id))
#
#     user= result.scalar_one_or_none()
#
#     if user is None:
#
#         raise HTTPException(status_code=401,detail="User not Found")
#
#     return user



@app.get("/",response_class=HTMLResponse)
async def home(request:Request):

    return templates.TemplateResponse(request,"login.html",{"request":request})

@app.get("/dashboard",response_class=HTMLResponse)
async def dashboard(request:Request,
                    current_user:Users=Depends(get_current_user),
                    db:AsyncSession=Depends(get_db),
                    page:int= Query(1,ge=1)):
    per_page=10
    total=await db.scalar(select(func.count()).select_from(DWGApplication))

    total_pages= math.ceil(total/per_page) if total else 1

    processing = await db.scalar(select(func.count()).where(DWGApplication.report_status=="processing"))

    completed = await db.scalar(select(func.count()).where(DWGApplication.report_status=="completed"))

    failed = await db.scalar(select(func.count()).where(DWGApplication.report_status== "failed"))

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

@app.get("/upload",response_class=HTMLResponse)
async def upload(request:Request,current_user:Users=Depends(get_current_user)):

    return templates.TemplateResponse(request,"upload.html",{'user':current_user.username})

@app.post("/upload", response_class=HTMLResponse)
async def upload_file(request:Request,
        background_task: BackgroundTasks,
        authenticated: bool = Depends(oauth2_scheme),
        layout: str = Form("N/A"),
        ulb :Optional[str] = Form(None),
        subtype:str = Form("N/A"),
        purposecode: str = Form("N/A"),
        user_name: str = Form("N/A"),
        location: str = Form("N/A"),
        sub_location: str = Form("N/A"),
        total_plotArea: str = Form("N/A"),
        is_underground_drain: str = Form("N/A"),
        deslugging_years: str = Form("N/A"),
        number_occupants: str = Form("N/A"),
        roadwiden_concession_setback: str = Form("N/A"),
        roadwiden_concession_additionalfloors: str = Form("N/A"),
        nala_concession_setback: str = Form("N/A"),
        nala_concession_additionalfloors: str = Form("N/A"),
        additional_mortgage_nala: str = Form("N/A"),
        utilize_tdr: str = Form("N/A"),
        tdr_no_floors: str = Form("N/A"),
        apply_for: str = Form("N/A"),
        authority: str = Form("N/A"),
        dwgfile: UploadFile = File(None),
        type_of_development: str = Form("N/A"),
        block_details: str = Form("[]"),
        use: str = Form("N/A"),
        subuse: str = Form("N/A"),
        applicationFormId: str = Form("N/A"),
        generate_svg: str = Form("false"),
        isGatedCommunity: bool = Form(False),
        runOnlyCombinedUtil: bool = Form(False),
        typeofplan:str= Form("PlanScrutiny"),
        db:AsyncSession=Depends(get_db),
        current_user:Users=Depends(get_current_user)):


    ref_id = hex(uuid.uuid4().time)[2:-1] + datetime.now().strftime("%d")
    file_name=dwgfile.filename if dwgfile else ""
    server_logger.info(f"Request getting APP ID:{applicationFormId} REF ID:{ref_id} FileName:{file_name}")
    request_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    portName=PORT_BP_MAP.get(request.url.port,str(request.url.port))

    if not (user_name or dwgfile):

        msg = "Bad Request. username or dwgfile required parameters are missing."
        server_logger.error(msg)
        return JSONResponse(content=create_response(applicationFormId,ref_id,file_name
                            ,"Failed",msg),
                            status_code=status.HTTP_400_BAD_REQUEST)

    temp_filename= os.path.join(tempfile.gettempdir(),f"{ref_id}.dwg")
    try:

        if not dwgfile.filename.lower().endswith(".dwg"):

            msg = "File Extension not supported yet. Valid drawing extensions should be 'dwg'"
            server_logger(msg)
            return JSONResponse(content=create_response(applicationFormId,ref_id,file_name,"FAILED",msg),
                                status_code=status.HTTP_400_BAD_REQUEST)

        error_msg = ""
        if (layout not in LayerMaster.PLAN_CATEGORY_LIST):
            invalidLayout = True
            error_msg += ", Layout (Given): " + layout + " allowed values: " + str(
                LayerMaster.PLAN_CATEGORY_LIST.value.keys()).replace('dict_keys', '') + " "
        else:
            invalidLayout = False

        if (subtype not in LayerMaster.BUILDING_CATEGORY):
            invalidSubtype = True
            error_msg += ", Subtype (Given): " + subtype + " allowed values: " + str(
                LayerMaster.BUILDING_CATEGORY.value).replace('dict_keys', '') + " "
        else:
            invalidSubtype = False

        if (purposecode not in LayerMaster.PURPOSE_CODE_DESC_MAP.keys()):
            invalidPurposeCode = True
            error_msg += ", PurposeCode (Given): " + purposecode + " allowed values: " + str(
                LayerMaster.PURPOSE_CODE_DESC_MAP.value.keys()).replace('dict_keys', '') + ""
        else:
            invalidPurposeCode = False

        if (invalidPurposeCode or invalidLayout or invalidSubtype):
            msg = "One or more parameters have invalid Options." + error_msg
            server_logger.error(msg)
            return JSONResponse(content=create_response(applicationFormId,ref_id,file_name, "Failed", msg),
                                status_code=status.HTTP_400_BAD_REQUEST)

        file_basename = os.path.splitext(dwgfile.filename)[0].replace(" ", "_")
        file_name = f"{ref_id}-{file_basename}.dwg"

        saved_dwg_path = os.path.join(settings.DWG_DIR, file_name)

        def save_file(dwgfile,saved_dwg_path):
            # Save DWG file directly (streaming, memory-safe)
            with open(saved_dwg_path, "wb") as buffer:
                shutil.copyfileobj(dwgfile.file, buffer)

        await run_in_threadpool(save_file, dwgfile, saved_dwg_path)

        requestParams = dict()
        requestParams["ReportGeneratedDateTime"]="-"
        requestParams['additional_mortgage_nala'] = additional_mortgage_nala
        requestParams['applicationFormId'] = applicationFormId
        requestParams['apply_for'] = apply_for
        requestParams['authority'] = authority
        requestParams['block_details'] = "[]"
        requestParams['deslugging_years'] = deslugging_years
        requestParams['drawing_filename']=file_name
        requestParams['generate_svg'] = generate_svg
        requestParams['isGatedCommunity'] =  "True" if isGatedCommunity else "False"
        requestParams['is_underground_drain'] = is_underground_drain
        requestParams['layout'] = layout
        requestParams['location'] = location
        requestParams['nala_concession_additionalfloors'] = nala_concession_additionalfloors
        requestParams['nala_concession_setback'] = nala_concession_setback
        requestParams['number_occupants'] = number_occupants
        requestParams['purposecode'] = purposecode
        requestParams['purposedesc'] = "N/A"
        requestParams['referenceId'] = ref_id
        requestParams['roadwiden_concession_additionalfloors'] = roadwiden_concession_additionalfloors
        requestParams['roadwiden_concession_setback'] = roadwiden_concession_setback
        requestParams['runOnlyCombinedUtil'] = "True" if runOnlyCombinedUtil else "False"
        requestParams['sub_location'] = sub_location
        requestParams['subtype'] = subtype
        requestParams['subuse'] = subuse
        requestParams['tdr_no_floors'] = tdr_no_floors
        requestParams['total_plotArea'] = total_plotArea
        requestParams['type_of_development'] = type_of_development
        requestParams['typeofplan'] = typeofplan
        requestParams['ulb'] = typeofplan
        requestParams['use'] = use
        requestParams['username'] = user_name
        requestParams['utilize_tdr'] = utilize_tdr

        # converted_status = await convertDWGUtil_orig(settings.DWG_DIR, file_name, settings.DXF_DIR)

        loop = asyncio.get_event_loop()
        converted_status = await loop.run_in_executor(
            file_processor_pool,
            lambda: asyncio.run(convertDWGUtil_orig(settings.DWG_DIR, file_name, settings.DXF_DIR))
        )
        if converted_status.get("Status") != "Success":
            responseTimestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            msg = "DWG to DXF conversion failed."
            server_logger.error(msg)
            return JSONResponse(
                content=create_response(ref_id, file_name, request_time, "FAILED", responseTimestamp, msg),
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)

        dxf_filename = converted_status.get("FileName")

        startTimer = timer()

        background_task.add_task(process_file,request_time, startTimer,applicationFormId,ref_id,portName,settings.DWG_DIR,
                                  settings.DXF_DIR,dxf_filename,requestParams)

        msg= "File received and processing started."

        server_logger.info(msg)

        server_logger.info(f"Request User Input Form Details Sent:\n{requestParams}")

        new_file=DWGApplication(
            user_id=current_user.id,
            ref_id=ref_id,
            applicant_no=applicationFormId,
            applicant_name=current_user.username,
            file_name=file_name,
            status="submitted"
        )

        db.add(new_file)
        await db.commit()
        await db.refresh(new_file)


        return JSONResponse(content=create_response(applicationFormId,ref_id,file_name, "Submitted", msg),
                            status_code=status.HTTP_200_OK)

    except Exception as e:

        msg= "Fatal error processing the request "
        server_logger.error(msg)
        server_logger.exception(f"Unexpected error while processing file RefId={ref_id}:\n {e} ")
        return JSONResponse(content=create_response(applicationFormId,ref_id,file_name , "Failed", msg),
                            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)

    finally:

        if os.path.exists(temp_filename):

            try:
                os.remove(temp_filename)
                server_logger.info(f"Deleted temporary file: {temp_filename}")

            except Exception as Cleanup_error:
                server_logger.warning(f"Could not delete temp file: {Cleanup_error}")



@app.get("/applications",response_class=HTMLResponse)
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

@app.get("/reports",response_class=HTMLResponse)
async def reports(request:Request,
                  current_user:Users=Depends(get_current_user),
                  db:AsyncSession=Depends(get_db),
                  search:Optional[str]=Query(None),
                  page: int=Query(1,ge=1)):

    per_page= 10

    query= select(DWGApplication).where(func.lower(DWGApplication.status)=="completed")

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

@app.get("/processing",response_class=HTMLResponse)
async def processing(request:Request,
                     ref_id:Optional[str] =Query(None),
                     current_user:Users=Depends(get_current_user),
                     db:AsyncSession=Depends(get_db)):

    if ref_id:

        result = await db.execute(select(DWGApplication).where(DWGApplication.ref_id== ref_id))

    else:

        result = await db.execute(
            select(DWGApplication)
            .order_by(DWGApplication.created_at.desc())
            .limit(1)
        )

    application = result.scalar_one_or_none()

    if application is None:

        raise HTTPException(status_code=404, detail="Application not found")

    return templates.TemplateResponse(request,"processing.html",{'user':current_user.username,"application":application})

@app.get("/profile",response_class=HTMLResponse)
async def profile(request:Request,current_user:Users=Depends(get_current_user)):

    return templates.TemplateResponse(request,"profile.html",{'user':current_user})
@app.post("/profile/update")
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

@app.post("/profile/password")
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

@app.get("/settings",response_class=HTMLResponse)
async def settingsx(request:Request,
                    current_user:Users=Depends(get_current_user),
                    db:AsyncSession=Depends(get_db)
                    ):

    result= await db.execute(select(UserSettings).where(UserSettings.user_id==current_user.id))

    settings= result.scalar_one_or_none()

    return templates.TemplateResponse(request,"settings.html",{'user':current_user,
                                                               "settings":settings})

# @app.post("/settings/update")
# async def update_settings(
#         dark_mode:bool=Form(False),
#         email_notification:bool=Form(False),
#         sms_notification:bool=Form(False),
#         db:AsyncSession=Depends(get_db),
#         current_user:Users=Depends(get_current_user)
# ):
#     result= await db.execute(select(UserSettings).where(UserSettings.id==current_user.id))
#
#     settings= result.scalar_one_or_none()
#
#     if settings is None:
#
#         settings=UserSettings(user_id=current_user.id)
#
#
#     settings.dark_mode= dark_mode
#     settings.email_notification= email_notification
#     settings.sms_notification= sms_notification
#
#     db.add(settings)
#
#     await db.commit()
#
#     return RedirectResponse(url="/settings", status_code=303)

@app.post("/settings/delete_account")
async def delete_account(
        db:AsyncSession= Depends(get_db),
        current_user: Users= Depends(get_current_user),
):
    await db.delete(current_user)
    await db.commit()

    response= RedirectResponse(url="/login",status_code=303)

    response.delete_cookie("access_token")

    return response

@app.get("/register", response_class=HTMLResponse)
async def register_page(request: Request,):

    return templates.TemplateResponse(
        request=request,
        name="register.html",
    )


@app.post("/register",response_class=HTMLResponse)
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



@app.post("/login")
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

    response= RedirectResponse("/dashboard",status_code=status.HTTP_303_SEE_OTHER)

    response.set_cookie(
        key="access_token",
        value=token,
        httponly=True,
        samesite="lax"
    )
    return response

@app.get("/logout")
async def logout(request:Request,
                 db:AsyncSession=Depends(get_db),
                 current_user: Users=Depends(get_current_user)):
    current_user.is_active=False
    await db.commit()

    response= RedirectResponse("/",status_code=status.HTTP_303_SEE_OTHER)

    response.delete_cookie(key="access_token")

    return response

@app.post("/api/register",response_model=UserResponse)
async def register(user:UserRegister,
             db:AsyncSession=Depends(get_db)):

    result= await db.execute(select(Users).where(Users.username==user.username))
    existing_username=result.scalar_one_or_none()

    if existing_username:

        raise HTTPException(status_code=400,detail="username already exists")

    result= await db.execute(select(Users).where(Users.email==user.email))
    existing_email= result.scalar_one_or_none()

    if existing_email:

        raise HTTPException(status_code=400, detail="email already exists")

    hashed_password= hash_password(user.password)

    new_user=Users(username=user.username,
                   email=user.email,
                   password=hashed_password,
                   phone=user.phone)

    db.add(new_user)
    await db.commit()
    await db.refresh(new_user)

    return new_user

@app.post("/api/login")
async def login(user:UserLogin,
                db:AsyncSession = Depends(get_db)):

    result= await db.execute(select(Users).where(Users.email==user.email))

    db_user= result.scalar_one_or_none()

    if db_user is None:

        raise HTTPException(status_code=401,detail="Invalid email or password")

    if not verify_password(user.password,db_user.password):

        raise HTTPException(status_code=401, detail="Invalid email or password")

    token= create_access_token(
        {
            "sub":str(db_user.id),
            "email": db_user.email,
            "role":"user"
        }
    )

    return {
        "access_token":token,
        "token_type":"bearer"
    }

async def process_file(request_time, startTimer, applicationFormID, reference_id, portName, Dwg_Dir, Dxf_Dir,file_name,request_params):
    req_logger = get_request_logger(reference_id)

    req_logger.info(f"=== Request Started: {reference_id} ===")
    req_logger.info(f"File: {file_name}, AppID: {applicationFormID}")
    req_time_stamp = datetime.strptime(request_time, "%Y-%m-%d %H:%M:%S")
    status_dict = {
        "ReferenceId": reference_id,
        "Status": "Started",
        "StepName": "Initializing",
        "Progress": 0,
        "Executed_Time":0,
        "Estimated_Remaining_Time":0

    }

    db= SessionLocal()

    result= await db.execute(select(DWGApplication).where(DWGApplication.ref_id==reference_id))

    application = result.scalar_one_or_none()

    if application is None:
        return

    application.status = "processing"

    await db.commit()

    results = {
        "ReferenceId": reference_id,
        "applicationFormId": applicationFormID,
        "serverName": portName,
        "code": "Failed",
        "error_msg": "",
        "csvReport": file_name.replace(".dxf", ".csv"),
        "jsonReport": file_name.replace(".dxf", ".json"),
        "layout": request_params.get("layout", ""),
        "reportExtract": []
    }

    try:
        req_logger.info(f"{file_name} File Processing started...")

        def _run_in_thread():
            set_request_logger(req_logger)  # ← must be inside thread
            try:
                return processPlanBasedOnType(
                    reference_id, Dwg_Dir, Dxf_Dir,
                    file_name, request_params, status_dict, req_time_stamp
                )
            finally:
                set_request_logger(None)  # ← clean up after done

        loop = asyncio.get_event_loop()
        response = await loop.run_in_executor(file_processor_pool, _run_in_thread)

        # loop = asyncio.get_event_loop()
        # response = await loop.run_in_executor(file_processor_pool,processPlanBasedOnType,reference_id, Dwg_Dir, Dxf_Dir,
        #                                  file_name, request_params,status_dict,req_time_stamp)
        # print('====res', response)
        if (response.get('responseCode', -1) == 0):
            results['code'] = 'Completed'

            application.status = "completed"

            await db.commit()

            results['reportExtract'] =response.get("dwgExtract",[])

        else:
            errorList = response.get('errors', 'N/A')
            req_logger.error(errorList)
            endTimer = timer()
            if isinstance(errorList,list):
                errorStr="|".join(errorList)
            else:
                errorStr = errorList.replace("\n","|")

            results['code'] = 'Failed'

            timetakenstr = str(round(endTimer - startTimer, 2)) + " sec "

            results['timetaken'] = timetakenstr

            results['error_msg'] = errorStr[:errorStr.find('exception')]

            application.status = "failed"

            await db.commit()

            req_logger.warning(f"Failed to saved JSON File")

    except:

        req_logger.error('Exception occured in processPlanBasedOnType ')
        ex_type, ex_value, ex_traceback = sys.exc_info()

        # Extract unformatter stack traces as tuples
        trace_back = traceback.extract_tb(ex_traceback)

        # Format stacktrace
        stack_trace = list()

        for trace in trace_back:
            errorDict = dict()
            fileName = trace[0]
            fileName = fileName.strip()
            stripFileName = fileName[fileName.rindex("\\") + 1:-3]
            errorDict['File'] = stripFileName
            errorDict['Line'] = trace[1]
            errorDict['Func.Name'] = trace[2]
            errorDict['Statement'] = trace[3]
            stack_trace.append(errorDict)
            # stack_trace.append("File : %s , Line : %d, Func.Name : %s, Statement : %s" % (stripFileName, trace[1], trace[2], trace[3]))

        req_logger.exception("Exception type : %s " % ex_type.__name__)
        req_logger.error("Exception message : %s" % ex_value)
        req_logger.error("Stack trace : %s" % stack_trace)

        respDict = dict()
        respDict['ReferenceId'] = reference_id
        respDict['requestTimeStamp'] = request_time
        respDict['responseTimestamp'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")  # "%d/%m/%Y %H:%M:%S")
        respDict['code'] = "FAILED"
        respDict['error_msg'] = "Fatal error processing the request."
        return JSONResponse(respDict, status_code=400)

    finally:
        now = datetime.now()
        results["requestTimeStamp"] = req_time_stamp.strftime("%Y-%m-%d %H:%M:%S")
        results["responseTimestamp"] = now.strftime("%Y-%m-%d %H:%M:%S")
        results["svgfile"] = "N/A"
        results["timetaken"] = f"{(now - req_time_stamp).total_seconds():.2f} sec"

        try:

            # Save JSON
            json_path = os.path.join(settings.JSON_SUMMARY_DIR, file_name.replace(".dxf", ".json"))

            with open(json_path, "w", encoding="utf-8") as f:
                json.dump(results, f, indent=4)

            req_logger.info("JSON saved at %s", json_path)

            response = await run_in_threadpool(send_building_data,
                payload=results,
                api_key=settings.DBAPI_KEY,
                username=settings.DBAPI_USERNAME,
                password=settings.DBAPI_PASSWORD)
            req_logger.info("DB API RES: %s", response)

        except Exception as e:

            # status_dict["Status"] = "Failed"
            # status_dict["StepName"] = "Database saving failed"
            # update_status(ref_id, status_dict)
            req_logger.exception("DB API failed: %s", e)

        finally:

            req_logger.info(f"=== Request Finished: {reference_id} | Time: {results['timetaken']} ===")

            close_request_logger(reference_id)

def create_response(application_id,reference_id,file_name,status,message):

    respDict = dict()
    respDict['ApplicationFormId'] = application_id
    respDict['ref_id'] = reference_id
    respDict['input'] = file_name
    respDict['status'] = status
    respDict['Detail'] = message

    return respDict
#
# @app.post("/api/drawingrequest/create",response_class=JSONResponse)
# async def upload_file(request:Request,
#         background_task: BackgroundTasks,
#         authenticated: bool = Depends(oauth2_scheme),
#         layout: str = Form("N/A"),
#         ulb :Optional[str] = Form(None),
#         subtype:str = Form("N/A"),
#         purposecode: str = Form("N/A"),
#         user_name: str = Form("N/A"),
#         location: str = Form("N/A"),
#         sub_location: str = Form("N/A"),
#         total_plotArea: str = Form("N/A"),
#         is_underground_drain: str = Form("N/A"),
#         deslugging_years: str = Form("N/A"),
#         number_occupants: str = Form("N/A"),
#         roadwiden_concession_setback: str = Form("N/A"),
#         roadwiden_concession_additionalfloors: str = Form("N/A"),
#         nala_concession_setback: str = Form("N/A"),
#         nala_concession_additionalfloors: str = Form("N/A"),
#         additional_mortgage_nala: str = Form("N/A"),
#         utilize_tdr: str = Form("N/A"),
#         tdr_no_floors: str = Form("N/A"),
#         apply_for: str = Form("N/A"),
#         authority: str = Form("N/A"),
#         dwgfile: UploadFile = File(None),
#         type_of_development: str = Form("N/A"),
#         block_details: str = Form("[]"),
#         use: str = Form("N/A"),
#         subuse: str = Form("N/A"),
#         applicationFormId: str = Form("N/A"),
#         generate_svg: str = Form("false"),
#         isGatedCommunity: bool = Form(False),
#         runOnlyCombinedUtil: bool = Form(False),
#         typeofplan:str= Form("PlanScrutiny"),
#         db:AsyncSession=Depends(get_db),
#         current_user:Users=Depends(get_current_user)):
#
#
#     ref_id = hex(uuid.uuid4().time)[2:-1] + datetime.now().strftime("%d")
#     file_name=dwgfile.filename if dwgfile else ""
#     server_logger.info(f"Request getting APP ID:{applicationFormId} REF ID:{ref_id} FileName:{file_name}")
#     request_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
#     portName=PORT_BP_MAP.get(request.url.port,str(request.url.port))
#
#     if not (user_name or dwgfile):
#
#         msg = "Bad Request. username or dwgfile required parameters are missing."
#         server_logger.error(msg)
#         return JSONResponse(content=create_response(applicationFormId,ref_id,file_name
#                             ,"Failed",msg),
#                             status_code=status.HTTP_400_BAD_REQUEST)
#
#     temp_filename= os.path.join(tempfile.gettempdir(),f"{ref_id}.dwg")
#     try:
#
#         if not dwgfile.filename.lower().endswith(".dwg"):
#
#             msg = "File Extension not supported yet. Valid drawing extensions should be 'dwg'"
#             server_logger(msg)
#             return JSONResponse(content=create_response(applicationFormId,ref_id,file_name,"FAILED",msg),
#                                 status_code=status.HTTP_400_BAD_REQUEST)
#
#         error_msg = ""
#         if (layout not in LayerMaster.PLAN_CATEGORY_LIST):
#             print("invalid layout",layout)
#             invalidLayout = True
#             error_msg += ", Layout (Given): " + layout + " allowed values: " + str(
#                 LayerMaster.PLAN_CATEGORY_LIST.keys()).replace('dict_keys', '') + " "
#         else:
#             invalidLayout = False
#
#         if (subtype not in LayerMaster.BUILDING_CATEGORY):
#             print("invalid subtype",subtype)
#             invalidSubtype = True
#             error_msg += ", Subtype (Given): " + subtype + " allowed values: " + str(
#                 LayerMaster.BUILDING_CATEGORY).replace('dict_keys', '') + " "
#         else:
#             invalidSubtype = False
#
#         if (purposecode not in LayerMaster.PURPOSE_CODE_DESC_MAP.keys()):
#
#             invalidPurposeCode = True
#             error_msg += ", PurposeCode (Given): " + purposecode + " allowed values: " + str(
#                 LayerMaster.PURPOSE_CODE_DESC_MAP.keys()).replace('dict_keys', '') + ""
#         else:
#             invalidPurposeCode = False
#         print(invalidPurposeCode , invalidLayout , invalidSubtype)
#         if (invalidPurposeCode or invalidLayout or invalidSubtype):
#             msg = "One or more parameters have invalid Options." + error_msg
#             server_logger.error(msg)
#             return JSONResponse(content=create_response(applicationFormId,ref_id,file_name, "Failed", msg),
#                                 status_code=status.HTTP_400_BAD_REQUEST)
#
#         file_basename = os.path.splitext(dwgfile.filename)[0].replace(" ", "_")
#         file_name = f"{ref_id}-{file_basename}.dwg"
#
#         saved_dwg_path = os.path.join(settings.DWG_DIR, file_name)
#
#         def save_file(dwgfile,saved_dwg_path):
#             # Save DWG file directly (streaming, memory-safe)
#             with open(saved_dwg_path, "wb") as buffer:
#                 shutil.copyfileobj(dwgfile.file, buffer)
#
#         await run_in_threadpool(save_file, dwgfile, saved_dwg_path)
#
#         requestParams = dict()
#         requestParams["ReportGeneratedDateTime"]="-"
#         requestParams['additional_mortgage_nala'] = additional_mortgage_nala
#         requestParams['applicationFormId'] = applicationFormId
#         requestParams['apply_for'] = apply_for
#         requestParams['authority'] = authority
#         requestParams['block_details'] = "[]"
#         requestParams['deslugging_years'] = deslugging_years
#         requestParams['drawing_filename']=file_name
#         requestParams['generate_svg'] = generate_svg
#         requestParams['isGatedCommunity'] =  "True" if isGatedCommunity else "False"
#         requestParams['is_underground_drain'] = is_underground_drain
#         requestParams['layout'] = layout
#         requestParams['location'] = location
#         requestParams['nala_concession_additionalfloors'] = nala_concession_additionalfloors
#         requestParams['nala_concession_setback'] = nala_concession_setback
#         requestParams['number_occupants'] = number_occupants
#         requestParams['purposecode'] = purposecode
#         requestParams['purposedesc'] = "N/A"
#         requestParams['referenceId'] = ref_id
#         requestParams['roadwiden_concession_additionalfloors'] = roadwiden_concession_additionalfloors
#         requestParams['roadwiden_concession_setback'] = roadwiden_concession_setback
#         requestParams['runOnlyCombinedUtil'] = "True" if runOnlyCombinedUtil else "False"
#         requestParams['sub_location'] = sub_location
#         requestParams['subtype'] = subtype
#         requestParams['subuse'] = subuse
#         requestParams['tdr_no_floors'] = tdr_no_floors
#         requestParams['total_plotArea'] = total_plotArea
#         requestParams['type_of_development'] = type_of_development
#         requestParams['typeofplan'] = typeofplan
#         requestParams['ulb'] = typeofplan
#         requestParams['use'] = use
#         requestParams['username'] = user_name
#         requestParams['utilize_tdr'] = utilize_tdr
#
#         # converted_status = await convertDWGUtil_orig(settings.DWG_DIR, file_name, settings.DXF_DIR)
#
#         loop = asyncio.get_event_loop()
#         converted_status = await loop.run_in_executor(
#             file_processor_pool,
#             lambda: asyncio.run(convertDWGUtil_orig(settings.DWG_DIR, file_name, settings.DXF_DIR))
#         )
#         if converted_status.get("Status") != "Success":
#             responseTimestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
#             msg = "DWG to DXF conversion failed."
#             server_logger.error(msg)
#             return JSONResponse(
#                 content=create_response(ref_id, file_name, request_time, "FAILED", responseTimestamp, msg),
#                 status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)
#
#         dxf_filename = converted_status.get("FileName")
#
#         startTimer = timer()
#
#         background_task.add_task(process_file,request_time, startTimer,applicationFormId,ref_id,portName,settings.DWG_DIR,
#                                   settings.DXF_DIR,dxf_filename,requestParams)
#
#         msg= "File received and processing started."
#
#         server_logger.info(msg)
#
#         server_logger.info(f"Request User Input Form Details Sent:\n{requestParams}")
#
#         new_file=DWGApplication(
#             user_id=current_user.id,
#             ref_id=ref_id,
#             applicant_no=applicationFormId,
#             applicant_name=current_user.username,
#             file_name=file_name,
#             status="submitted"
#         )
#
#         db.add(new_file)
#         await db.commit()
#         await db.refresh(new_file)
#
#
#         return JSONResponse(content=create_response(applicationFormId,ref_id,file_name, "Submitted", msg),
#                             status_code=status.HTTP_200_OK)
#
#     except Exception as e:
#
#         msg= "Fatal error processing the request "
#         server_logger.error(msg)
#         server_logger.exception(f"Unexpected error while processing file RefId={ref_id}:\n {e} ")
#         return JSONResponse(content=create_response(applicationFormId,ref_id,file_name , "Failed", msg),
#                             status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)
#
#     finally:
#
#         if os.path.exists(temp_filename):
#
#             try:
#                 os.remove(temp_filename)
#                 server_logger.info(f"Deleted temporary file: {temp_filename}")
#
#             except Exception as Cleanup_error:
#                 server_logger.warning(f"Could not delete temp file: {Cleanup_error}")


# @app.get("/download/{ref_id}")
# async def get_json_file(ref_id: str):
#     find_file = None
#     for filename in os.listdir(settings.JSON_SUMMARY_DIR):
#         file_ref_id=filename.lower().split("-")[0]
#         if filename.lower().startswith(ref_id.lower()) and ref_id==file_ref_id:
#             find_file = filename
#             break
#
#     if find_file is None:
#
#         server_logger.error(f"File Not Found Of That Ref ID '{ref_id}' ")
#         raise HTTPException(status_code=404, detail="File Not Found")
#
#     file_path = os.path.join(settings.JSON_SUMMARY_DIR, find_file)
#     server_logger.info(f"DownLoaded That File: {file_path}")
#     return FileResponse(
#         file_path,
#         media_type="application/json",
#         filename=find_file,
#     )

@app.get("/download/{ref_id}")
async def get_json_file(ref_id: str):
    matches = list(Path(settings.JSON_SUMMARY_DIR).glob(f"{ref_id}-*"))

    if not matches:
        server_logger.error(f"File Not Found Of That Ref ID '{ref_id}' ")
        raise HTTPException(status_code=404, detail="File Not Found")

    file_path = matches[0]
    server_logger.info(f"DownLoaded That File: {file_path}")
    return FileResponse(
        path=file_path,
        media_type="application/json",
        filename=file_path.name
    )