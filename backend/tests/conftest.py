import os
import pytest
from cryptography.fernet import Fernet

# Set env vars before importing app modules
os.environ.setdefault('ENCRYPTION_KEY', Fernet.generate_key().decode())
os.environ.setdefault('WEBHOOK_SECRET', 'test-secret')

from app import create_app
from app.extensions import db as _db


@pytest.fixture(scope='session')
def app():
    application = create_app('testing')
    with application.app_context():
        _db.create_all()
        yield application
        _db.drop_all()


@pytest.fixture(scope='function')
def db(app):
    ctx = app.app_context()
    ctx.push()
    yield _db
    _db.session.rollback()
    for table in reversed(_db.metadata.sorted_tables):
        _db.session.execute(table.delete())
    _db.session.commit()
    ctx.pop()


@pytest.fixture(scope='function')
def client(app, db):
    return app.test_client()


@pytest.fixture(scope='function')
def auth_client(client, db):
    client.post('/api/auth/register', json={
        'email': 'user@test.com',
        'password': 'password123',
    })
    client.post('/api/auth/login', json={
        'email': 'user@test.com',
        'password': 'password123',
    })
    return client
