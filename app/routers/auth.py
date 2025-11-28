from fastapi import APIRouter, Depends, HTTPException, Header
from pytest import Session
from sqlalchemy import text

from app.auth import create_session, get_current_user, hash_password, verify_password
from app.database import get_db
from app.models.models import User
from app.schemas.auth import LoginRequest, StatusResponse, TokenResponse
from app.schemas.users import UserCreate, UserOut


router = APIRouter()


@router.post('/register', response_model=UserOut)
def register(data: UserCreate, db: Session = Depends(get_db)):
    if db.query(User).filter_by(email=data.email).first():
        raise HTTPException(400, 'Email already exists')
    user = User(
        first_name=data.first_name,
        last_name=data.last_name,
        email=data.email,
        password_hash=hash_password(data.password),
        role_id=2
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@router.post('/login', response_model=TokenResponse)
def login(data: LoginRequest, db: Session = Depends(get_db)):
    user: User = db.query(User).filter_by(email=data.email).first()
    if not user or not user.is_active or not verify_password(data.password, user.password_hash):
        raise HTTPException(401, 'Invalid credentials')
    token = create_session(db, user.id)
    return TokenResponse(token=token)


@router.post('/logout', response_model=StatusResponse)
def logout(user=Depends(get_current_user), db: Session = Depends(get_db), token: str | None = Header(None, alias='X-Session-Token')):
    if not token:
        raise HTTPException(400, 'No session token')
    db.execute(
        text('DELETE FROM sessions WHERE token = :t'),
        {'t': token}
    )
    db.commit()
    return StatusResponse(status="logged out")