import os
import subprocess
from Backend.config import settings
def getDWGVersion(source_dir, input_file):
    filepath = os.path.abspath(os.path.join(source_dir, input_file))

    with open(filepath, 'rb') as f:
        header = f.read(6).decode('utf-8')

    version_map = {
        "AC1015": "ACAD2000",
        "AC1018": "ACAD2004",
        "AC1021": "ACAD2007",
        "AC1024": "ACAD2010",
        "AC1027": "ACAD2013",
        "AC1032": "ACAD2018",
        "AC1036": "ACAD2021"
    }

    return version_map.get(header, "ACAD2018")  # Default fallback


async def convertDWGUtil_orig(SOURCE_DIR, inputFile, DXFFILE_DIR):

    # ---------------------------------------------------------
    # Prepare output filename
    # ---------------------------------------------------------

    outputFile = os.path.splitext(inputFile)[0] + ".dxf"

    if len(outputFile) > 255:
        outputFile = outputFile[:255]

    # ---------------------------------------------------------
    # Get DWG version
    # ---------------------------------------------------------

    acadVersion = getDWGVersion(
        SOURCE_DIR,
        inputFile
    )

    print(
        "Input and output files are "
        + inputFile
        + " , "
        + outputFile
        + " drawing version "
        + acadVersion
    )

    # ---------------------------------------------------------
    # ODA File Converter
    # ---------------------------------------------------------

    odafc_exec_path = settings.ODAFC_EXE_PATH

    print(
        "ODA File Converter path:",
        odafc_exec_path
    )

    # ---------------------------------------------------------
    # Check ODA executable
    # ---------------------------------------------------------

    if not os.path.isfile(odafc_exec_path):

        raise FileNotFoundError(
            f"ODA File Converter not found at: "
            f"{odafc_exec_path}"
        )

    # ---------------------------------------------------------
    # Check source directory
    # ---------------------------------------------------------

    if not os.path.isdir(SOURCE_DIR):

        raise FileNotFoundError(
            f"Source directory not found: "
            f"{SOURCE_DIR}"
        )

    # ---------------------------------------------------------
    # Check DXF output directory
    # ---------------------------------------------------------

    if not os.path.isdir(DXFFILE_DIR):

        os.makedirs(
            DXFFILE_DIR,
            exist_ok=True
        )

    # ---------------------------------------------------------
    # Run ODA File Converter
    #
    # Linux Docker compatible
    # ---------------------------------------------------------

    try:

        runStatus = subprocess.run(
            [
                odafc_exec_path,
                SOURCE_DIR,
                DXFFILE_DIR,
                acadVersion,
                "DXF",
                "0",
                "1",
                inputFile
            ],
            capture_output=True,
            text=True
        )

    except Exception as exc:

        print(
            "ODA File Converter execution failed:",
            str(exc)
        )

        return {
            "Status": "Failed",
            "Code": -1,
            "Version": acadVersion,
            "FileName": outputFile
        }

    # ---------------------------------------------------------
    # Print ODA output
    # ---------------------------------------------------------

    print(
        "ODA return code:",
        runStatus.returncode
    )

    print(
        "ODA stdout:",
        runStatus.stdout
    )

    print(
        "ODA stderr:",
        runStatus.stderr
    )

    # ---------------------------------------------------------
    # Normalize directory path
    #
    # Your old code was Windows-specific:
    #
    # app\\base\\..\\..\\
    #
    # This is not required in Linux Docker.
    # ---------------------------------------------------------

    DXFFILE_DIR = os.path.abspath(
        DXFFILE_DIR
    )

    # ---------------------------------------------------------
    # ODA execution failed
    # ---------------------------------------------------------

    if runStatus.returncode != 0:

        print(
            "ODA conversion failed. "
            "Return code:",
            runStatus.returncode
        )

        status = "Failed"
        fileName = None

    else:

        # -----------------------------------------------------
        # Check ODA error file
        # -----------------------------------------------------

        err_file = os.path.join(
            DXFFILE_DIR,
            outputFile + ".err"
        )

        errored = os.path.isfile(
            err_file
        )

        print(
            "ODA conversion status:",
            runStatus.returncode,
            "Error file exists:",
            errored
        )

        # -----------------------------------------------------
        # ODA generated error
        #
        # We are NOT using QCAD here because your QCAD path
        # was Windows-specific.
        # -----------------------------------------------------

        if errored:

            print(
                "ODA conversion generated an error file:"
            )

            print(
                "Error file:",
                err_file
            )

            try:

                with open(
                    err_file,
                    "r",
                    errors="ignore"
                ) as error_file:

                    print(
                        "ODA error:",
                        error_file.read()
                    )

            except Exception as exc:

                print(
                    "Unable to read ODA error file:",
                    str(exc)
                )

            status = "Failed"
            fileName = None

        else:

            # -------------------------------------------------
            # Check generated DXF file
            # -------------------------------------------------

            output_dxf = os.path.join(
                DXFFILE_DIR,
                outputFile
            )

            print(
                "Expected DXF file:",
                output_dxf
            )

            if os.path.isfile(output_dxf):

                print(
                    "ODA conversion successful."
                )

                status = "Success"
                fileName = "FileName " + outputFile

            else:

                print(
                    "ODA returned success, "
                    "but DXF file was not found."
                )

                status = "Failed"
                fileName = None

    # ---------------------------------------------------------
    # Return response
    # ---------------------------------------------------------

    dataDict = {
        "Status": status,
        "Code": runStatus.returncode,
        "Version": acadVersion,
        "FileName": outputFile
    }

    print(
        "Conversion result:",
        dataDict
    )

    return dataDict

# async def convertDWGUtil_orig(SOURCE_DIR, inputFile, DXFFILE_DIR):
#     # print('Convert DWG 2 DXF Util -orig params source_dir, input file and dxffile_dir ', SOURCE_DIR, ' ; ', inputFile,
#     #       ' ; ', DXFFILE_DIR)
#     outputFile = os.path.splitext(inputFile)[0] + ".dxf"  # "Open_Layout_4"
#     if (len(outputFile) > 255):
#         outputFile = outputFile[0:255]
#
#     acadVersion =getDWGVersion(SOURCE_DIR, inputFile)  # = "ACAD2018"
#
#     print(" input and output files are " + inputFile + " , " + outputFile + " drawing version " + acadVersion)
#     # odafc_exec_path = "C:\\Program Files\\ODA\\ODA Drawings Explorer 21.6.0\\OdaFileConverter.exe"
#     # odafc_exec_path = r"C:\Users\Viswa\AppData\Local\Programs\Python\Python38\ODAFileConverter.exe"
#     # odafc_exec_path = r"C:\Program Files\ODA\ODAFileConverter 26.4.0\ODAFileConverter.exe"
#     odafc_exec_path = settings.ODAFC_EXE_PATH
#     # Setup to hide window
#     startupinfo = subprocess.STARTUPINFO()
#     startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
#
#     runStatus = subprocess.run(args=[odafc_exec_path, SOURCE_DIR, DXFFILE_DIR, acadVersion, "DXF", "0", "1", inputFile],
#                                startupinfo=startupinfo,
#                                creationflags=subprocess.CREATE_NO_WINDOW
#                                )
#     DXFFILE_DIR = DXFFILE_DIR.replace("app\\base\\..\\..\\", "")
#     print('runstatus ', str(runStatus))
#     if (runStatus.returncode != 0):
#         status = "Failed"
#     else:
#         # print()
#         err_file = DXFFILE_DIR + outputFile + ".err"
#         err_file = err_file.replace("app\\base\\..\\..\\", "")
#         errored = os.path.isfile(err_file)
#         print("ODA convertion status " + str(runStatus) + " Error file exists " + str(errored))
#         if (errored):
#             # try qcad
#             print('Error File exists in ODA - try ing with QCAD conversion ')
#             try:
#
#                 inputF = DXFFILE_DIR + outputFile
#                 os.remove(err_file)
#                 if (os.path.isfile(inputF)):
#                     os.remove(inputF)
#
#                 if (os.path.isfile("C:\\adsbpas\\apps\\qcad-3.25.2-pro-win64\\dwg2dwg.bat")):
#                     qcad_exec_path = "C:\\adsbpas\\apps\\qcad-3.25.2-pro-win64\\dwg2dwg.bat"
#                 else:
#                     qcad_exec_path = "C:\\adsbpas\\apps\\qcad-3.25.2-pro-win64\\dwg2dwg.bat"
#
#                 clean_srcdir = SOURCE_DIR.replace("app\\base\\..\\..\\", "")
#
#                 # os.path.isfile(SOURCE_DIR+inputFile)
#                 runStatus = subprocess.run(
#                     args=[qcad_exec_path, "-f", "-o", DXFFILE_DIR + outputFile, clean_srcdir + inputFile])
#
#                 if (os.path.isfile(DXFFILE_DIR + outputFile)):
#                     # print("qcad conversion worked ")
#                     status = "Success"
#                     fileName = "FileName " + outputFile  # "output/Open_Layout_4.dxf"
#                 else:
#                     # print("qcad conversion failed ")
#                     status = "Failed"
#                     fileName = None
#
#             except Exception as excp:
#                 print("problem removing errored files ", str(excp))
#
#         else:
#             # print("oda conversion worked ")
#             status = "Success"
#             fileName = "FileName " + outputFile  # "output/Open_Layout_4.dxf"
#
#     dataDict = dict()
#     dataDict['Status'] = status
#     dataDict['Code'] = runStatus.returncode
#     dataDict['Version'] = acadVersion
#     dataDict['FileName'] = outputFile
#
#     return dataDict

# # Example usage
# if __name__ == "__main__":
#     source_directory = r"C:\Users\Viswa\OneDrive\Desktop\error_dwg_files"
#     output_directory = r"C:\Users\Viswa\OneDrive\Desktop\dxf_files"
#     dwg_filename = "TOWERF (1).dwg"
#
#     os.makedirs(output_directory, exist_ok=True)
#
#     result = convertDWGUtil_orig(source_directory, dwg_filename, output_directory)
#     print(result)