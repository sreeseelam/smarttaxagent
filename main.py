from fastapi import FastAPI, Request, Depends, HTTPException, status
from fastapi.responses import HTMLResponse, FileResponse, RedirectResponse
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
import secrets
import os
from smarttaxagent_api import router as smarttaxagent_router

app = FastAPI()
app.include_router(smarttaxagent_router)

# Allow frontend JS to call /whoami without CORS issues
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Static files setup
app.mount("/static", StaticFiles(directory="static"), name="static")

# Basic HTTP authentication
security = HTTPBasic()

# Hardcoded users and roles
users_db = {
    "IndividualUser": {
        "username": "IndividualUser",
        "password": "IndividualUser",
        "role": "Individual"
    },
    "TaxSpecialist": {
        "username": "TaxSpecialist",
        "password": "TaxSpecialist",
        "role": "Specialist"
    }
}

def get_current_user(credentials: HTTPBasicCredentials = Depends(security)):
    user = users_db.get(credentials.username)
    if user and secrets.compare_digest(credentials.password, user["password"]):
        return user
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid authentication",
        headers={"WWW-Authenticate": "Basic"},
    )

BASE_DIR = os.path.dirname(__file__)
STATIC_HTML_DIR = os.path.join(BASE_DIR, "static")

@app.get("/", response_class=HTMLResponse)
async def login_page():
    return FileResponse(os.path.join(STATIC_HTML_DIR, "login.html"))

@app.get("/whoami")
async def whoami(credentials: HTTPBasicCredentials = Depends(security)):
    user = get_current_user(credentials)
    return {"username": user["username"], "role": user["role"]}

@app.get("/home", response_class=HTMLResponse)
@app.get("/user-guide", response_class=HTMLResponse)
@app.get("/example", response_class=HTMLResponse)
async def shared_layout():
    return FileResponse(os.path.join(STATIC_HTML_DIR, "layout.html"))