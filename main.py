from fastapi import FastAPI, Depends, HTTPException, Header
from fastapi.openapi.utils import get_openapi
from sqlalchemy.orm import Session
from sqlalchemy import text
from models import Base, User, Role, Permission
from database import engine, get_db
from auth import hash_password, verify_password, create_session, get_current_user
from mock_views import router as items_router


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


# ------------------------ User actions ------------------------

@app.get('/user/me')
def me(user=Depends(get_current_user)):
    return {
        'id': user.id,
        'email': user.email,
        'role_id': user.role_id,
        'active': user.is_active
    }

@app.post('/register')
def register(data: dict, db: Session = Depends(get_db)):
    if db.query(User).filter_by(email=data['email']).first():
        raise HTTPException(400, 'Email already exists')
    user = User(
        first_name=data['first_name'],
        last_name=data['last_name'],
        email=data['email'],
        password_hash=hash_password(data['password']),
        role_id=2
    )
    db.add(user)
    db.commit()
    return {'status': 'ok'}


@app.post('/login')
def login(data: dict, db: Session = Depends(get_db)):
    user: User = db.query(User).filter_by(email=data['email']).first()
    if not user or not user.is_active or not verify_password(data['password'], user.password_hash):
        raise HTTPException(401, 'Invalid credentials')
    token = create_session(db, user.id)
    return {'token': token}


@app.post('/logout')
def logout(user=Depends(get_current_user), db: Session = Depends(get_db), token: str | None = Header(None, alias='X-Session-Token')):
    if not token:
        raise HTTPException(400, 'No session token')
    db.execute(
        text('DELETE FROM sessions WHERE token = :t'),
        {'t': token}
    )
    db.commit()
    return {'status': 'logged out'}


@app.put('/user/update')
def update_user(data: dict, user=Depends(get_current_user), db: Session = Depends(get_db)):
    user.first_name = data.get('first_name', user.first_name)
    user.last_name = data.get('last_name', user.last_name)
    db.commit()
    return {'status': 'updated'}


@app.delete('/user/delete')
def delete_user(user=Depends(get_current_user), db: Session = Depends(get_db)):
    user.is_active = False
    db.commit()
    return {'status': 'disabled'}


# ------------------------ Admin: roles & permissions ------------------------

def admin_required(user=Depends(get_current_user)):
    if user.role.name != 'admin':
        raise HTTPException(403, 'Admin only')
    return user


@app.post('/admin/role')
def create_role(name: str, db: Session = Depends(get_db), user=Depends(admin_required)):
    role = Role(name=name)
    db.add(role)
    db.commit()
    return {'status': 'role created'}


@app.post('/admin/permission')
def create_permission(data: dict, db: Session = Depends(get_db), user=Depends(admin_required)):
    perm = Permission(
        role_id=data['role_id'],
        resource=data['resource'],
        action=data['action'],
    )
    db.add(perm)
    db.commit()
    return {'status': 'permission added'}

@app.put('/admin/user/role')
def change_user_role(data: dict, db: Session = Depends(get_db), user=Depends(admin_required)):
    requested_user = db.query(User).filter_by(id=data['user_id']).first()
    if not requested_user:
        raise HTTPException(404, 'User not found')
    role = db.query(Role).filter_by(id=data['role_id']).first()
    if not role:
        raise HTTPException(404, 'Role not found')
    requested_user.role_id = data['role_id']
    db.commit()

    return {'status': 'role updated', 'user_id': requested_user.id, 'new_role': role.name}

@app.get('/admin/users')
def list_users(db: Session = Depends(get_db), user=Depends(admin_required)):
    users = db.query(User).all()
    return [
        {
            'id': u.id,
            'first_name': u.first_name,
            'last_name': u.last_name,
            'email': u.email,
            'is_active': u.is_active,
            'role': u.role.name if u.role else None
        }
        for u in users
    ]
