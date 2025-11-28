from fastapi import Depends, FastAPI, HTTPException, Header
from fastapi.openapi.utils import get_openapi
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.models.models import Base, User, Role
from app.database import engine, get_db
from app.auth import create_session, get_current_user, hash_password, verify_password
from app.routers.items import router as items_router
from app.routers.auth import router as auth_router
from app.routers.users import router as users_router
from app.routers.admin import router as admin_router


app = FastAPI()

def custom_openapi():
    if app.openapi_schema:
        return app.openapi_schema
    openapi_schema = get_openapi(
        title=app.title,
        version=app.version,
        routes=app.routes,
    )
    app.openapi_schema = openapi_schema
    return app.openapi_schema

app.openapi = custom_openapi

Base.metadata.create_all(bind=engine)

with Session(engine) as db:
    if not db.query(Role).filter_by(name='admin').first():
        admin_role = Role(name='admin')
        db.add(admin_role)
        db.commit()

    if not db.query(User).filter_by(email='admin@example.com').first():
        admin = User(
            first_name='Admin',
            last_name='Root',
            email='admin@example.com',
            password_hash=hash_password('admin123'),
            role_id=admin_role.id,
        )
        db.add(admin)
        db.commit()

app.include_router(items_router)

app.include_router(auth_router)

app.include_router(users_router)

app.include_router(admin_router)