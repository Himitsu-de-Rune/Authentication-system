import uuid
from fastapi import Depends, HTTPException, Security
from fastapi.security.api_key import APIKeyHeader
from sqlalchemy import text
from sqlalchemy.orm import Session
from passlib.context import CryptContext

from app.database import get_db
from app.models.models import User, Session as UserSession


pwd = CryptContext(schemes=['pbkdf2_sha256'], deprecated='auto')

api_key_header = APIKeyHeader(name='X-Session-Token', auto_error=False)


def hash_password(password: str):
    return pwd.hash(password)


def verify_password(password: str, hash_value: str):
    return pwd.verify(password, hash_value)


def create_session(db: Session, user_id: int):
    token = str(uuid.uuid4())
    sess = UserSession(user_id=user_id, token=token)
    db.add(sess)
    db.commit()
    return token


def get_current_user(token: str = Security(api_key_header), db: Session = Depends(get_db)):
    if not token:
        raise HTTPException(401, 'No session token')

    sess = db.execute(
        text('SELECT * FROM sessions WHERE token = :t'),
        {'t': token}
    ).fetchone()

    if not sess:
        raise HTTPException(401, 'Invalid session token')

    user = db.query(User).filter_by(id=sess.user_id).first()

    if not user or not user.is_active:
        raise HTTPException(401, 'Inactive user')

    return user
