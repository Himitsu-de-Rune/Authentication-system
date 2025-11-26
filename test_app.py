import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from main import app
from database import Base, get_db
from models import User, Role
from auth import hash_password


# ------------------------ Test database ------------------------

SQLALCHEMY_DATABASE_URL = 'sqlite:///./test.db'

engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={'check_same_thread': False}
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()

app.dependency_overrides[get_db] = override_get_db

@pytest.fixture(scope='session', autouse=True)
def setup_db():
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)

@pytest.fixture
def client():
    with TestClient(app) as c:
        yield c


# ------------------------ Fixtures ------------------------

@pytest.fixture
def admin_token(client):
    db = next(override_get_db())
    admin_role = db.query(Role).filter_by(name='admin').first()
    if not admin_role:
        admin_role = Role(name='admin')
        db.add(admin_role)
        db.commit()

    admin = db.query(User).filter_by(email='admin@example.com').first()
    if not admin:
        admin = User(
            first_name='Admin',
            last_name='Root',
            email='admin@example.com',
            password_hash=hash_password('admin123'),
            role_id=admin_role.id
        )
        db.add(admin)
        db.commit()

    response = client.post('/login', json={'email': 'admin@example.com', 'password': 'admin123'})
    return response.json()['token']

@pytest.fixture
def user_token(client):
    db = next(override_get_db())
    user_role = db.query(Role).filter_by(name='user').first()
    if not user_role:
        user_role = Role(name='user')
        db.add(user_role)
        db.commit()

    user = db.query(User).filter_by(email='user@example.com').first()
    if not user:
        user = User(
            first_name='Test',
            last_name='User',
            email='user@example.com',
            password_hash=hash_password('12345'),
            role_id=user_role.id
        )
        db.add(user)
        db.commit()

    response = client.post('/login', json={'email': 'user@example.com', 'password': '12345'})
    return response.json()['token']


# ----------------------- Helpers -----------------------

def auth_headers(token):
    return {'X-Session-Token': token}


# ------------------------ Tests ------------------------

def test_register_user(client):
    response = client.post('/register', json={
        'first_name': 'Temp',
        'last_name': 'User2',
        'email': 'temp@example.com',
        'password': 'abc123'
    })
    assert response.status_code == 200
    assert response.json()['status'] == 'ok'

def test_login_user(client, user_token):
    assert user_token is not None

def test_login_admin(client, admin_token):
    assert admin_token is not None

def test_admin_create_role(client, admin_token):
    response = client.post('/admin/role', params={'name': 'manager'}, headers=auth_headers(admin_token))
    assert response.status_code == 200
    assert response.json()['status'] == 'role created'

def test_admin_create_permission(client, admin_token):
    db = next(override_get_db())
    role = db.query(Role).filter_by(name='user').first()
    response = client.post(
        '/admin/permission',
        json={'role_id': role.id, 'resource': 'items', 'action': 'read'},
        headers=auth_headers(admin_token)
    )
    assert response.status_code == 200
    assert response.json()['status'] == 'permission added'

def test_user_can_read_items(client, user_token):
    response = client.get('/items/', headers=auth_headers(user_token))
    assert response.status_code == 200
    assert isinstance(response.json(), list)

def test_user_forbidden_without_permission(client, user_token):
    response = client.post('/items/', headers=auth_headers(user_token))
    assert response.status_code == 403

def test_admin_list_users(client, admin_token):
    response = client.get('/admin/users', headers=auth_headers(admin_token))
    assert response.status_code == 200
    assert isinstance(response.json(), list)

def test_change_user_role(client, admin_token):
    db = next(override_get_db())
    user = db.query(User).filter_by(email='user@example.com').first()
    role = db.query(Role).filter_by(name='manager').first()
    response = client.put(
        '/admin/user/role',
        json={'user_id': user.id, 'role_id': role.id},
        headers=auth_headers(admin_token)
    )
    assert response.status_code == 200
    assert response.json()['status'] == 'role updated'

def test_user_me_endpoint(client, user_token):
    response = client.get('/user/me', headers=auth_headers(user_token))
    assert response.status_code == 200
    data = response.json()
    assert data['email'] == 'user@example.com'
    assert data['active'] is True

def test_update_user(client, user_token):
    response = client.put('/user/update', json={'first_name': 'Updated'}, headers=auth_headers(user_token))
    assert response.status_code == 200
    assert response.json()['status'] == 'updated'

def test_logout_user(client, user_token):
    response = client.post('/logout', headers=auth_headers(user_token))
    assert response.status_code == 200
    assert response.json()['status'] == 'logged out'

def test_soft_delete_user(client, user_token):
    response = client.post('/login', json={'email': 'user@example.com', 'password': '12345'})
    token = response.json()['token']

    response = client.delete('/user/delete', headers=auth_headers(token))
    assert response.status_code == 200
    assert response.json()['status'] == 'disabled'

    response2 = client.post('/login', json={'email': 'user@example.com', 'password': '12345'})
    assert response2.status_code == 401

def test_unauthorized_access(client):
    response = client.get('/user/me')
    assert response.status_code == 401
    response = client.get('/items/')
    assert response.status_code == 401
