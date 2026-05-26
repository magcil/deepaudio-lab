# routers/auth.py

from fastapi import APIRouter, Depends, status, Form
from sqlalchemy.orm import Session
from db.session import get_db
from schemas.token_response import TokenResponse
from services.auth_service import authenticate_user, delete_user, get_current_user, register_user, require_admin
from schemas.signup_request import SignupRequest
from schemas.user_info import UserInfo


router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/signup", status_code=status.HTTP_201_CREATED)
def signup(data: SignupRequest, db: Session = Depends(get_db)) -> dict:
    return register_user(db, data)


@router.post("/login", status_code=status.HTTP_200_OK)
def login(username: str = Form(...), password: str = Form(...)):
    access_token = authenticate_user(username, password)
    return TokenResponse(access_token=access_token)


@router.get("/me", status_code=status.HTTP_200_OK)
def me(user: UserInfo = Depends(get_current_user)) -> UserInfo:
    return user


@router.delete("/users/{username}", status_code=status.HTTP_204_NO_CONTENT)
def remove_user(username: str, db: Session = Depends(get_db), _: UserInfo = Depends(require_admin)):
    delete_user(db, username)
    
