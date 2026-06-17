def test_register_success(client):
    res = client.post('/api/auth/register', json={
        'email': 'new@test.com', 'password': 'password123',
    })
    assert res.status_code == 201
    assert res.get_json()['email'] == 'new@test.com'


def test_register_duplicate_email(client):
    client.post('/api/auth/register', json={'email': 'dup@test.com', 'password': 'password123'})
    res = client.post('/api/auth/register', json={'email': 'dup@test.com', 'password': 'password123'})
    assert res.status_code == 409


def test_register_short_password(client):
    res = client.post('/api/auth/register', json={'email': 'x@test.com', 'password': '123'})
    assert res.status_code == 422


def test_register_invalid_email(client):
    res = client.post('/api/auth/register', json={'email': 'not-an-email', 'password': 'password123'})
    assert res.status_code == 422


def test_login_success(client):
    client.post('/api/auth/register', json={'email': 'login@test.com', 'password': 'password123'})
    res = client.post('/api/auth/login', json={'email': 'login@test.com', 'password': 'password123'})
    assert res.status_code == 200
    assert 'email' in res.get_json()


def test_login_wrong_password(client):
    client.post('/api/auth/register', json={'email': 'wp@test.com', 'password': 'password123'})
    res = client.post('/api/auth/login', json={'email': 'wp@test.com', 'password': 'wrongpass'})
    assert res.status_code == 401


def test_login_unknown_email(client):
    res = client.post('/api/auth/login', json={'email': 'ghost@test.com', 'password': 'password123'})
    assert res.status_code == 401


def test_me_authenticated(auth_client):
    res = auth_client.get('/api/auth/me')
    assert res.status_code == 200
    data = res.get_json()
    assert data['email'] == 'user@test.com'


def test_me_unauthenticated(client):
    res = client.get('/api/auth/me')
    assert res.status_code == 401


def test_logout(auth_client):
    res = auth_client.post('/api/auth/logout')
    assert res.status_code == 200


def test_change_password(auth_client):
    res = auth_client.put('/api/auth/password', json={
        'current_password': 'password123',
        'new_password': 'newpassword456',
    })
    assert res.status_code == 200


def test_change_password_wrong_current(auth_client):
    res = auth_client.put('/api/auth/password', json={
        'current_password': 'wrongpass',
        'new_password': 'newpassword456',
    })
    assert res.status_code == 400


def test_update_profile_currency(auth_client):
    res = auth_client.put('/api/auth/profile', json={'default_currency': 'USD'})
    assert res.status_code == 200
    assert res.get_json()['default_currency'] == 'USD'
