from typing import List
from fastapi import APIRouter, Depends, HTTPException

from app.database import get_db
from app.auth import get_current_user
from app.models.models import Permission, Role, Session, User
from app.schemas.auth import StatusResponse
from app.schemas.permissions import PermissionCreate, PermissionOut
from app.schemas.roles import ChangeUserRole, RoleCreate
from app.schemas.users import UserOut


router = APIRouter(prefix='/admin', tags=['Admin'])


def admin_required(user=Depends(get_current_user)):
    if user.role.name != 'admin':
        raise HTTPException(403, 'Admin only')
    return user


@router.post('/role', response_model=StatusResponse)
def create_role(data: RoleCreate, db: Session = Depends(get_db), user=Depends(admin_required)):
    existing = db.query(Role).filter_by(name=data.name).first()
    if existing:
        return StatusResponse(status='role already exist')
    role = Role(name=data.name)
    db.add(role)
    db.commit()
    return StatusResponse(status='role created')


@router.post('/permission', response_model=PermissionOut)
def create_permission(data: PermissionCreate, db: Session = Depends(get_db), user=Depends(admin_required)):
    perm = Permission(
        role_id=data.role_id,
        resource=data.resource,
        action=data.action,
    )
    db.add(perm)
    db.commit()
    return perm


@router.put('/user/role', response_model=StatusResponse)
def change_user_role(data: ChangeUserRole, db: Session = Depends(get_db), user=Depends(admin_required)):
    requested_user = db.query(User).filter_by(id=data.user_id).first()
    if not requested_user:
        raise HTTPException(404, 'User not found')
    role = db.query(Role).filter_by(id=data.role_id).first()
    if not role:
        raise HTTPException(404, 'Role not found')
    requested_user.role_id = data.role_id
    db.commit()
    return StatusResponse(status='role updated')


@router.get('/users', response_model=List[UserOut])
def list_users(db: Session = Depends(get_db), user=Depends(admin_required)):
    users = db.query(User).all()
    return [
        UserOut(
            id=u.id,
            first_name=u.first_name,
            last_name=u.last_name,
            email=u.email,
            is_active=u.is_active,
            role=u.role.name if u.role else None
        )
        for u in users
    ]