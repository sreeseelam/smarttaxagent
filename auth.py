# auth.py
from fastapi import APIRouter, HTTPException, Request, Depends
from fastapi.responses import JSONResponse
from pydantic import BaseModel
import secrets

router = APIRouter()

# Dummy users and roles
users_db = {
    "IndividualUser": {
        "username": "IndividualUser",
        "password": "IndividualUser",
        "role": "IndividualUser"
    },
    "TaxSpecialist": {
        "username": "TaxSpecialist",
        "password": "TaxSpecialist",
        "role": "TaxSpecialist"
    }
}

class LoginRequest(BaseModel):
    username: str
    password: str

@router.post("/login")
async def login(data: LoginRequest):
    print("🔐 LOGIN ATTEMPT:", data.username, data.password)  # Add this
    user = users_db.get(data.username)
    if user and secrets.compare_digest(data.password, user["password"]):
        return {"username": user["username"], "role": user["role"]}
    raise HTTPException(status_code=401, detail="Invalid credentials")

@router.get("/whoami")
async def whoami(request: Request):
    auth = request.headers.get("Authorization")
    if not auth or not auth.startswith("Basic "):
        raise HTTPException(status_code=401, detail="Not authenticated")

    import base64
    try:
        auth_decoded = base64.b64decode(auth.split(" ")[1]).decode()
        username, password = auth_decoded.split(":")
        user = users_db.get(username)
        if user and secrets.compare_digest(password, user["password"]):
            return {"username": user["username"], "role": user["role"]}
    except:
        pass

    raise HTTPException(status_code=401, detail="Invalid credentials")

def get_current_user(request: Request):
    auth = request.headers.get("Authorization")
    if not auth or not auth.startswith("Basic "):
        raise HTTPException(status_code=401, detail="Not authenticated")

    import base64
    try:
        auth_decoded = base64.b64decode(auth.split(" ")[1]).decode()
        username, password = auth_decoded.split(":")
        user = users_db.get(username)
        if user and secrets.compare_digest(password, user["password"]):
            return user
    except:
        pass

    raise HTTPException(status_code=401, detail="Invalid credentials")