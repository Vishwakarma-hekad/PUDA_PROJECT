from pydantic import BaseModel,EmailStr

class UserRegister(BaseModel):

    username: str

    email: EmailStr

    password: str

    phone: str

class UserResponse(BaseModel):

    id: int
    username: str
    email: EmailStr
    phone:str

    class Config:

        from_attributes= True

class UserLogin(BaseModel):

    email: EmailStr
    password: str

class DWGApplication(BaseModel):

    ref_id:str

    applicant_no:str

    applicant_name:str

    file_name:str

    status:str

    is_active:bool