from fastapi import Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import text

from app.auth import get_current_user
from app.database import get_db


def check_access(resource: str, action: str):
    def wrapper(user=Depends(get_current_user), db: Session = Depends(get_db)):
        role = user.role
        if not role:
            raise HTTPException(403, 'No role assigned')

        allowed = db.execute(
            text("""
                SELECT * FROM permissions
                WHERE role_id = :r AND resource = :res AND action = :act
            """),
            {'r': role.id, 'res': resource, 'act': action}
        ).fetchone()

        if not allowed:
            raise HTTPException(403, 'Forbidden')

        return user

    return wrapper
