from shapely.geometry import Polygon,Point
from ezdxf.entities.mtext import plain_mtext
import math
import re
import ezdxf
class AccessoriesList:

    def __init__(self,msp):

        self.msp=msp
        self.acc_use_textquery=self.msp.query("TEXT MTEXT[layer=='_AccessoryUse']")
        self.acc_use_polyquery=self.msp.query("LWPOLYLINE[layer=='_AccessoryUse']")
        self.floor_textquery=self.msp.query("TEXT MTEXT[layer=='_Floor']")
        self.floor_polyquery=self.msp.query("LWPOLYLINE[layer=='_Floor']")

    def get_height(self,inputText: str, startDelimeter: None, endDelimeter= "h"):

        height_value = 0.0

        if (inputText is None or len(inputText) == 0):

            return height_value
        else:
            # any digit patterns
            numeric_const_pattern = '[-+]? (?: (?: \d* \. \d+ ) | (?: \d+ \.? ) )(?: [Ee] [+-]? \d+ ) ?'
            rx = re.compile(numeric_const_pattern, re.VERBOSE)

            # check if u can find the start and end delimeters
            if (startDelimeter is not None and len(startDelimeter) > 0):
                start_idx = inputText.find(startDelimeter)
            else:
                start_idx = 0

            end_idx = inputText.find(endDelimeter)

            sub_text = inputText[start_idx:end_idx]

            height_tmp = rx.findall(sub_text)

            if (len(height_tmp) > 0):
                # return the index[0] value
                return height_tmp[0]
            else:

                print(f"Unable to extract height value from :: {inputText} - Returning default value {height_value}")
                return height_value

    def label_check_polygon(self,poly_queries,text_queries):

        closed_polygons=[poly for poly in poly_queries if poly.closed and len(poly.get_points("xy"))>3]
        final_dct=dict()
        for poly in closed_polygons:
            polygon_id=poly.dxf.handle
            polygon_points=Polygon(poly.get_points("xy"))
            contain_label=None

            for text in text_queries:

                text_label= text.dxf.text if text.dxftype()=="TEXT" else text.plain_text()

                filtered_label= self.clean_text_mtext_label(text_label)
                label_point= Point([text.dxf.insert[0],text.dxf.insert[1]])

                if polygon_points.contains(label_point):
                    contain_label= filtered_label
                    final_dct[polygon_id]=(contain_label,polygon_points)
                    break

            if contain_label is None:

                print(f"Missing Label For #REF ({polygon_id}) Polygon")

        return final_dct

    def checkString4AlphaDigits(self, nameOfFloor: str):

            nameOfFloor = nameOfFloor.upper()

            word2RemoveList = ['|', 'TYPICAL', 'FLOOR', 'PLAN']

            pIndex = nameOfFloor.find("|")

            if pIndex > -1:
                nameOfFloor = nameOfFloor[pIndex:].upper()

            for word2Remove in word2RemoveList:
                nameOfFloor = nameOfFloor.replace(word2Remove, "")

            nameOfFloor_Check = re.sub(r'|\s|\t|\,|\-|\*|', '', nameOfFloor)

            isAlpha = nameOfFloor_Check.isalpha()  # check if string is only alpha a-z
            isAlphaNum = nameOfFloor_Check.isalnum()  # check if string has digits and alpha
            isDigits = nameOfFloor_Check.isnumeric()  # only digits
            # print("check str",nameOfFloor_Check )
            # print ("  Alpha, isAlphaNum, has Digits ", isAlpha, isAlphaNum, isDigits)

            if (isDigits and isAlphaNum and not (isAlpha)):
                return "DIGITS"
            elif ((isAlpha and isAlphaNum) and not (isDigits)):
                return "ONLYTEXT"
            elif (isAlphaNum and not (isDigits and isAlpha)):
                return "ALPHANUM"
            else:
                # print("unknown, default to ALPHA ")
                return "ONLYTEXT"

    def determineFloorNumbers(self, nameOfFloor: str):
        from num2words import num2words

        retVal = []

        # check if string has any digits otherwise just split the string

        word2RemoveList = ['|', 'TYPICAL', 'FLOOR', 'PLAN']

        # print("The original string is : " + nameOfFloor)

        if "|" in nameOfFloor:
            nameOfFloor = nameOfFloor[nameOfFloor.find("|"):].upper()

        # clean
        for word2Remove in word2RemoveList:
            nameOfFloor = nameOfFloor.replace(word2Remove, "")

        # translate
        if ("&" in nameOfFloor):
            nameOfFloor = nameOfFloor.replace("&", ',')

        typeOfString = self.checkString4AlphaDigits(nameOfFloor)  # ALPHA, DIGITS, ALPHANUM

        # print("determined type of string as : " + typeOfString)

        if ("DIGITS" in typeOfString):  # nameOfFloor is not None and hasDigits):

            # Convert String ranges to list
            # Using sum() + list comprehension + enumerate() + split()

            # print("The original string is : " + nameOfFloor)
            # remove spaces and alphabhets
            nameOfFloor = re.sub(r'[a-z]|[A-Z]|\s|\t|\|', '', nameOfFloor)

            # print("After removing spaces/alphabhets string is now : " + nameOfFloor)

            # extract the number ranges
            nameOfFloor = re.sub("[^0123456789\,\-]", "", nameOfFloor)

            if (nameOfFloor[0] == "-"):
                nameOfFloor = nameOfFloor[1:]
            # print("The number range from string is : " + nameOfFloor)

            # printing original string
            # print("The string is :" + nameOfFloor)
            if (nameOfFloor[0] == ","):
                nameOfFloor = nameOfFloor[1:]
            # print("The final string is :" + nameOfFloor)
            # Convert String ranges to list
            # Using sum() + list comprehension + enumerate() + split()
            res = sum(
                ((list(range(*[int(b) + c for c, b in enumerate(a.split('-'))])) if ('-' in a or ' ' in a) else [a]) for
                 a
                 in re.split(',|\s', nameOfFloor)), [])
            # if '-' in a else [int(a)]) for a in nameOfFloor.split(',')), [])

            # printing result
            # print("List after conversion from string : " + str(res))

            # convert them to ordinal words 1 First 2 secound 4 fourth etc ...
            wordResults = []
            for numberOfFlr in res:
                wordResults.append(num2words(numberOfFlr, to='ordinal').upper())

            retVal = wordResults

        elif ("ALPHANUM" in typeOfString):
            nameOfFloor = re.sub(r'|\s|\t|\|', '', nameOfFloor)
            # print ("after cleanup:" + nameOfFloor.strip())

            if (nameOfFloor[0] == "-"):
                nameOfFloor = nameOfFloor[1:]
            # print("The mixed word and number range is : " + nameOfFloor)

            wordResults = []

            for tok in nameOfFloor.split(","):
                if (tok.isnumeric()):
                    asword = num2words(tok, to='ordinal').upper()
                    wordResults.append(asword)
                else:
                    wordResults.append(tok)
            retVal = wordResults

        elif ("ONLYTEXT" in typeOfString):  # (not hasDigits and (","  in nameOfFloor or "-"  in nameOfFloor) ) :
            """ some have a words itself """
            words2Remove = ['FLOOR', 'PLAN', 'TYPICAL']

            # print("The original string is : " + nameOfFloor)
            for toRemove in words2Remove:
                nameOfFloor = nameOfFloor.replace(toRemove, "")

            # remove spaces
            nameOfFloor = re.sub(r'|\s|\t|\|', '', nameOfFloor)
            if ("&" in nameOfFloor):
                nameOfFloor = nameOfFloor.replace("&", ',')
            # print("After removing spaces string is now : " + nameOfFloor)

            if (nameOfFloor[0] == "-"):
                nameOfFloor = nameOfFloor[1:]
            # print("The word-number range is : " + nameOfFloor)

            # printing original string
            # print("The string is :" + nameOfFloor)
            if (nameOfFloor[0] == ","):
                nameOfFloor = nameOfFloor[1:]
                # print("The final string is :" + nameOfFloor)

            wordResults = []
            for nameStr in nameOfFloor.split(","):
                wordResults.append(nameStr)

            retVal = wordResults

        return retVal

    def clean_text_mtext_label(self,text_label: str):

        text = plain_mtext(text_label)
        text = text.strip().replace("\n", " ")
        return text

    def get_lengthAndWidth(self, polygon):
        if polygon.is_empty or polygon.area == 0:
            return 0.0, 0.0

        rect = polygon.minimum_rotated_rectangle
        if not hasattr(rect, "exterior"):  # Point or LineString fallback
            return 0.0, 0.0

        coords = list(rect.exterior.coords)
        edge1 = math.hypot(coords[1][0] - coords[0][0],
                           coords[1][1] - coords[0][1])
        edge2 = math.hypot(coords[2][0] - coords[1][0],
                           coords[2][1] - coords[1][1])
        return round(max(edge1, edge2), 2), round(min(edge1, edge2), 2)

    def get_acc_list_details(self):

        listOfAccessory= []

        Accessory_data = self.label_check_polygon(self.acc_use_polyquery,self.acc_use_textquery)

        Floor_data= self.label_check_polygon(self.floor_polyquery,self.floor_textquery)

        for acc_id,acc_values in Accessory_data.items():
            acc_dict= dict()
            fl_name=None
            lenght, width = self.get_lengthAndWidth(acc_values[1])
            for flr_id,flr_values in Floor_data.items():

                if flr_values[1].contains(acc_values[1]):
                    # print(f"{acc_values[0]} in {flr_values[0]}")
                    if "typical" in flr_values[0].lower():
                        fl_name=flr_values[0]
                        break

            acc_dict['ACCESSORY_NAME'] = acc_values[0]
            acc_dict['ACCESSORY_WIDTH'] = str(round(width,2))
            if "parapet wall" in acc_values[0].lower():
                acc_dict['ACCESSORY_AREA'] = self.get_height(acc_values[0],None,'h')
            elif "entrance" or "ent" in acc_values[0].lower():
                acc_dict['ACCESSORY_AREA'] = self.get_height(acc_values[0], None, 'h')
            else:
                acc_dict['ACCESSORY_AREA'] = str(round(acc_values[1].area,2))

            # print(fl_name)
            if fl_name is not None:

                floornumbers=self.determineFloorNumbers(fl_name)
                # print("typical floors",floornumbers)
                if floornumbers:
                    for _ in range(len(floornumbers)):
                        listOfAccessory.append(acc_dict.copy())

            else:

                listOfAccessory.append(acc_dict)

        return listOfAccessory

# if __name__=="__main__":
#     import os
#     try:
#
#         folder="G:\MyProjects\BPConnectProject\PUDAAPI\DXF_files"
#         filename="6c1ea258f41d925-40x90PUDA.dxf"
#
#         dxf_path= os.path.join(folder,filename)
#
#         dxf_file= ezdxf.readfile(dxf_path)
#
#         modelspace= dxf_file.modelspace()
#
#         acc_list_details_obj=AccessoryListDetails(modelspace)
#
#         get_details=acc_list_details_obj.get_acc_list_details()
#
#         print(f"Response:\n {get_details}")
#
#     except FileNotFoundError as e:
#
#         print(f"File Does Not Exists:{e}")