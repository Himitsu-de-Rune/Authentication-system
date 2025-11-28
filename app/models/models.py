from sqlalchemy import Column, Integer, String, Boolean, ForeignKey
from sqlalchemy.orm import relationship

from app.database import Base


class User(Base):
    __tablename__ = 'users'

    id = Column(Integer, primary_key=True, index=True)
    first_name = Column(String)
    last_name = Column(String)
    email = Column(String, unique=True, index=True)
    password_hash = Column(String)
    is_active = Column(Boolean, default=True)

    role_id = Column(Integer, ForeignKey('roles.id'))
    role = relationship('Role')

    sessions = relationship('Session', back_populates='user')


class Session(Base):
    __tablename__ = 'sessions'

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'))
    token = Column(String, unique=True, index=True)

    user = relationship('User', back_populates='sessions')


class Role(Base):
    __tablename__ = 'roles'

    id = Column(Integer, primary_key=True)
    name = Column(String, unique=True)

    permissions = relationship('Permission', back_populates='role')


class Permission(Base):
    __tablename__ = 'permissions'

    id = Column(Integer, primary_key=True)
    role_id = Column(Integer, ForeignKey('roles.id'))
    resource = Column(String)
    action = Column(String)

    role = relationship('Role', back_populates='permissions')
