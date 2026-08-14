import time
from Backend.celery_worker import celery
from Backend.config import settings
from Backend.logging_config import get_server_logger, get_request_logger, close_request_logger, set_request_logger
from Backend.models.models import Users, DWGApplication
from Backend.models.database import get_db, SessionLocal
from datetime import datetime
from sqlalchemy import select
from Backend.process_file_new import processPlanBasedOnType
import asyncio
import json
from timeit import default_timer as timer
from concurrent.futures import ThreadPoolExecutor
import traceback
import sys
from fastapi.responses import JSONResponse
from Backend.DWG2DXF import convertDWGUtil_orig
from Backend.services.redis_progress import (set_progress,complete_progress,failed_progress,clear_progress)
import os

file_processor_pool = ThreadPoolExecutor(max_workers=4)

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

    application.report_status = "processing"

    await db.commit()

    start_time= datetime.now()

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

            application.report_status = "completed"
            application.view_report = response.get("dwgExtract",[])
            application.report_exec_time = datetime.now() - start_time

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

            application.report_status = "failed"

            application.report_error_msg = errorStr[:errorStr.find('exception')]

            application.report_exec_time = datetime.now() - start_time

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

            # response = await run_in_threadpool(send_building_data,
            #     payload=results,
            #     api_key=settings.DBAPI_KEY,
            #     username=settings.DBAPI_USERNAME,
            #     password=settings.DBAPI_PASSWORD)
            # req_logger.info("DB API RES: %s", response)

        except Exception as e:

            # status_dict["Status"] = "Failed"
            # status_dict["StepName"] = "Database saving failed"
            # update_status(ref_id, status_dict)
            req_logger.exception("DB API failed: %s", e)

        finally:

            req_logger.info(f"=== Request Finished: {reference_id} | Time: {results['timetaken']} ===")

            close_request_logger(reference_id)

# @celery.task(bind=True)
# async def process_drawing(file_name,
#         request_time,
#         applicationFormId,
#         ref_id,
#         portName,
#         dxf_filename,
#         requestParams
# ):
#
#     converted_status = await convertDWGUtil_orig(settings.DWG_DIR, file_name, settings.DXF_DIR)
#
#     if converted_status.get("Status") != "Success":
#         # responseTimestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
#         msg = "DWG to DXF conversion failed."
#         get_request_logger.error(msg)
#         # return JSONResponse(
#         #     content=create_response(ref_id, file_name, request_time, "FAILED", responseTimestamp, msg),
#         #     status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)
#
#
#     read_layers= await reading_layers()
#
#
#     extreport_data = await process_file(request_time=request_time,startTimer=0,applicationFormID=applicationFormId,
#             reference_id=ref_id,portName=portName,Dwg_Dir=settings.DWG_DIR,Dxf_Dir=settings.DXF_DIR,file_name=dxf_filename,
#             request_params=requestParams)
#
#     gen_report_data = await get_gen_report()

@celery.task(bind=True)
def process_drawing(
    self,
    file_name,
    request_time,
    applicationFormId,
    ref_id,
    portName,
    requestParams
):
    logger = get_request_logger(ref_id)

    try:

        set_progress(ref_id, "DWG Conversion", 2, 7,"processing")

        converted_status = asyncio.run(
            convertDWGUtil_orig(
                settings.DWG_DIR,
                file_name,
                settings.DXF_DIR
            )
        )

        if converted_status["Status"] != "Success":
            # Update DB to failed
            clear_progress(ref_id)
            return

        dxf_filename = converted_status["FileName"]

        time.sleep(10)

        set_progress(ref_id, "Reading Layers", 3, 7, "processing")

        time.sleep(10)

        set_progress(ref_id, "Extracting Report Data", 4, 7, "processing")

        asyncio.run(
            process_file(
                request_time=request_time,
                startTimer=0,
                applicationFormID=applicationFormId,
                reference_id=ref_id,
                portName=portName,
                Dwg_Dir=settings.DWG_DIR,
                Dxf_Dir=settings.DXF_DIR,
                file_name=dxf_filename,
                request_params=requestParams
            )
        )

        time.sleep(10)

        set_progress(ref_id, "Generating Report", 5, 7, "processing")

        time.sleep(10)

        set_progress(ref_id, "Extracting Data For PDF", 6, 7, "processing")

        time.sleep(10)
        set_progress(ref_id, "Generating PDF", 7, 7, "completed")

        time.sleep(10)

        clear_progress(ref_id)

    except Exception:
        logger.exception("Processing failed")
        clear_progress(ref_id)