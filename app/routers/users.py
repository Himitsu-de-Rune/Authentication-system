from fastapi import APIRouter, Depends

from app.database import get_db
from app.auth import get_current_user
from app.models.models import Session, User
from app.schemas.auth import StatusResponse
from app.schemas.users import UserOut, UserUpdate


router = APIRouter(prefix='/user', tags=['Users'])


@router.get('/me', response_model=UserOut)
def me(user: User = Depends(get_current_user)):
    return UserOut(
        id=user.id,
        email=user.email,
        first_name=user.first_name,
        last_name=user.last_name,
        is_active=user.is_active,
        role=user.role.name if user.role else None
    )


@router.put('/update', response_model=StatusResponse)
def update_user(data: UserUpdate, user=Depends(get_current_user), db: Session = Depends(get_db)):
    if data.first_name:
        user.first_name = data.first_name
    if data.last_name:
        user.last_name = data.last_name
    db.commit()
    return StatusResponse(status='updated')


@router.delete('/delete', response_model=StatusResponse)
def delete_user(user=Depends(get_current_user), db: Session = Depends(get_db)):
    user.is_active = False
    db.commit()
    return StatusResponse(status='disabled')