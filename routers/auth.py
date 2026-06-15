from fastapi import APIRouter

router = APIRouter()

@router.post("/login")
def login():
    """User login endpoint"""
    return {"message": "Login endpoint"}

@router.post("/register")
def register():
    """User registration endpoint"""
    return {"message": "Register endpoint"}
