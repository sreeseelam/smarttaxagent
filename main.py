from fastapi import FastAPI, Request, Depends, HTTPException, status
from fastapi.responses import HTMLResponse, FileResponse
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
import secrets
import os

from auth import get_current_user
from smarttaxagent_api import router as smarttaxagent_router

app = FastAPI()

# CORS for frontend JS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Static public assets
app.mount("/static", StaticFiles(directory="static"), name="static")

# Base directories
BASE_DIR = os.path.dirname(__file__)
STATIC_HTML_DIR = os.path.join(BASE_DIR, "static")
PROTECTED_HTML_DIR = os.path.join(BASE_DIR, "static/protected")

# Public login page
@app.get("/", response_class=HTMLResponse)
async def login_page():
    return FileResponse(os.path.join(STATIC_HTML_DIR, "login.html"))

# Expose whoami for frontend role/username
@app.get("/whoami")
def whoami(user: dict = Depends(get_current_user)):
    return {"username": user["username"], "role": user["role"]}

# ✅ Protected HTML pages
@app.get("/home", response_class=HTMLResponse)
def home(user: dict = Depends(get_current_user)):
    return FileResponse(os.path.join(PROTECTED_HTML_DIR, "layout.html"))

@app.get("/user-guide", response_class=HTMLResponse)
def user_guide(user: dict = Depends(get_current_user)):
    return FileResponse(os.path.join(PROTECTED_HTML_DIR, "layout.html"))

@app.get("/example", response_class=HTMLResponse)
def example(user: dict = Depends(get_current_user)):
    return FileResponse(os.path.join(PROTECTED_HTML_DIR, "layout.html"))

# ✅ Secure all smarttax APIs
app.include_router(smarttaxagent_router, dependencies=[Depends(get_current_user)])