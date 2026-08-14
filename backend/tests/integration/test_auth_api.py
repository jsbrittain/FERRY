from app.auth.local import hash_password
from app.core.config import settings
from app.models.user import User, UserRole

LOGIN_TEST_EMAIL = "logintest@ferry.local"
LOGIN_TEST_PASSWORD = "login-test-pw"


def test_login_success(anon_client, db_session):
    hashed = hash_password(LOGIN_TEST_PASSWORD)
    user = User(
        email=LOGIN_TEST_EMAIL,
        display_name="Login Test",
        password_hash=hashed,
        role=UserRole.ADMIN,
    )
    db_session.add(user)
    db_session.commit()

    response = anon_client.post(
        "/api/auth/login",
        json={
            "email": LOGIN_TEST_EMAIL,
            "password": LOGIN_TEST_PASSWORD,
        },
    )
    assert response.status_code == 200
    data = response.json()
    assert data["email"] == LOGIN_TEST_EMAIL
    assert "session_id" in response.cookies


def test_login_invalid_password(anon_client, db_session):
    hashed = hash_password(LOGIN_TEST_PASSWORD)
    user = User(
        email=LOGIN_TEST_EMAIL,
        display_name="Login Test",
        password_hash=hashed,
        role=UserRole.ADMIN,
    )
    db_session.add(user)
    db_session.commit()

    response = anon_client.post(
        "/api/auth/login",
        json={
            "email": LOGIN_TEST_EMAIL,
            "password": "wrong-password",
        },
    )
    assert response.status_code == 401
    assert "session_id" not in response.cookies


def test_login_nonexistent_user(client):
    response = client.post(
        "/api/auth/login",
        json={
            "email": "nobody@example.com",
            "password": "anything",
        },
    )
    assert response.status_code == 401


def test_get_me_authenticated(client):
    response = client.get("/api/me")
    assert response.status_code == 200
    data = response.json()
    assert data["email"] == settings.admin_email
    assert data["display_name"] == "Administrator"
    assert data["role"] == "admin"


def test_get_me_anonymous_rejected(anon_client):
    response = anon_client.get("/api/me")
    assert response.status_code == 401


def test_logout(client):
    response = client.post("/api/auth/logout")
    assert response.status_code == 204

    # Session should be invalidated
    me_response = client.get("/api/me")
    assert me_response.status_code == 401


def test_login_rate_limiting(anon_client, db_session):
    hashed = hash_password("rate-test-pw")
    user = User(
        email="ratelimit@test.local",
        display_name="Rate Limit Test",
        password_hash=hashed,
        role=UserRole.ADMIN,
    )
    db_session.add(user)
    db_session.commit()

    # Exhaust the rate limit
    for i in range(settings.rate_limit_max_attempts):
        response = anon_client.post(
            "/api/auth/login",
            json={"email": "ratelimit@test.local", "password": "wrong"},
        )
        assert response.status_code == 401

    # Next attempt should be rate-limited
    response = anon_client.post(
        "/api/auth/login",
        json={"email": "ratelimit@test.local", "password": "wrong"},
    )
    assert response.status_code == 429


def test_session_rotation(anon_client, db_session):
    hashed = hash_password("rotation-pw")
    user = User(
        email="rotation@test.local",
        display_name="Rotation Test",
        password_hash=hashed,
        role=UserRole.ADMIN,
    )
    db_session.add(user)
    db_session.commit()

    # First login
    r1 = anon_client.post(
        "/api/auth/login",
        json={"email": "rotation@test.local", "password": "rotation-pw"},
    )
    assert r1.status_code == 200
    session1 = r1.cookies.get("session_id")

    # Second login — should invalidate the first session
    r2 = anon_client.post(
        "/api/auth/login",
        json={"email": "rotation@test.local", "password": "rotation-pw"},
    )
    assert r2.status_code == 200
    session2 = r2.cookies.get("session_id")
    assert session2 != session1

    # First session should no longer be valid
    anon_client.cookies.set("session_id", session1 or "")
    me = anon_client.get("/api/me")
    assert me.status_code == 401


def test_secure_cookie_not_set_in_dev(anon_client, db_session):
    """In development, secure=False by default."""
    from app.core.config import settings

    assert settings.secure_cookie is False
    hashed = hash_password("secure-test-pw")
    user = User(
        email="securecookie@test.local",
        display_name="Secure Cookie Test",
        password_hash=hashed,
        role=UserRole.ADMIN,
    )
    db_session.add(user)
    db_session.commit()

    response = anon_client.post(
        "/api/auth/login",
        json={"email": "securecookie@test.local", "password": "secure-test-pw"},
    )
    assert response.status_code == 200
    cookie = response.cookies.get("session_id")
    assert cookie is not None
