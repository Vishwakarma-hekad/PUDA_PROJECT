from fastapi import APIRouter

router=APIRouter(prefix="/test")

@router.get("/")
def get_test():

    return {"msg":"testing server"}

@router.get("/api")
def get_api():
    return {"msg":"api end point"}