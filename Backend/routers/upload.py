from fastapi import Request, Depends, BackgroundTasks, Form, APIRouter, UploadFile, File
from fastapi.responses import HTMLResponse, JSONResponse
from starlette.templating import Jinja2Templates
from .authentication import get_current_user
from models.models import Users, DWGApplication
from logging_config import get_server_logger, get_request_logger, close_request_logger, set_request_logger
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from models.database import get_db, SessionLocal
from fastapi.security import OAuth2PasswordBearer
from datetime import datetime
import uuid
import os
import shutil
from starlette import status
import tempfile
from digit_base import LayerMaster
from fastapi.concurrency import run_in_threadpool
from concurrent.futures import ThreadPoolExecutor
from config import settings
from tasks.drawing_task import process_drawing
from services.redis_progress import set_progress

file_processor_pool = ThreadPoolExecutor(max_workers=4)

server_logger=get_server_logger()

templates=Jinja2Templates(directory="../FrontEnd/templates")
router= APIRouter(tags=["upload"])

oauth2_scheme= OAuth2PasswordBearer(tokenUrl="login",auto_error=False)

@router.get("/upload",response_class=HTMLResponse)
async def upload(request:Request,current_user:Users=Depends(get_current_user)):

    return templates.TemplateResponse(request,"upload.html",{'user':current_user.username})


def create_response(application_id,reference_id,file_name,status,message):

    respDict = dict()
    respDict['ApplicationFormId'] = application_id
    respDict['ref_id'] = reference_id
    respDict['input'] = file_name
    respDict['status'] = status
    respDict['Detail'] = message

    return respDict

@router.post("/upload", response_class=HTMLResponse)
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
    portName=request.url.port

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

        # loop = asyncio.get_event_loop()
        # converted_status = await loop.run_in_executor(
        #     file_processor_pool,
        #     lambda: asyncio.run(convertDWGUtil_orig(settings.DWG_DIR, file_name, settings.DXF_DIR))
        # )
        # if converted_status.get("Status") != "Success":
        #     responseTimestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        #     msg = "DWG to DXF conversion failed."
        #     server_logger.error(msg)
        #     return JSONResponse(
        #         content=create_response(ref_id, file_name, request_time, "FAILED", responseTimestamp, msg),
        #         status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)

        # dxf_filename = converted_status.get("FileName")

        # startTimer = timer()

        # background_task.add_task(process_file,request_time, startTimer,applicationFormId,ref_id,portName,settings.DWG_DIR,
        #                           settings.DXF_DIR,dxf_filename,requestParams)

        process_drawing.delay(
            file_name=file_name,
            request_time=request_time,
            applicationFormId=applicationFormId,
            ref_id=ref_id,
            portName=portName,
            requestParams=requestParams
        )

        msg= "File received and processing started."

        server_logger.info(msg)

        server_logger.info(f"Request User Input Form Details Sent:\n{requestParams}")

        new_file = DWGApplication(
            user_id=current_user.id,
            applicant_name=current_user.username,
            ref_id=ref_id,
            file_name=f"{file_basename}.dwg",
            report_status="submitted"
        )

        db.add(new_file)
        await db.commit()
        await db.refresh(new_file)

        set_progress(ref_id, "Drawing Submitted", 1, 7, "submitted")

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