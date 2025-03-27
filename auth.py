# auth.py
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBasic, HTTPBasicCredentials
import secrets

security = HTTPBasic()

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

def get_current_user(credentials: HTTPBasicCredentials = Depends(security)):
    user = users_db.get(credentials.username)
    if user and secrets.compare_digest(credentials.password, user["password"]):
        return user
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid authentication",
        headers={"WWW-Authenticate": "Basic"},
    )