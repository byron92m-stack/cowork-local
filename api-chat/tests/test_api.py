import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from server import app
from db import Base, get_session
from auth import create_access_token, SECRET_KEY, ALGORITHM
from jose import jwt
from datetime import datetime, timedelta, timezone

TEST_DB_URL = "sqlite+aiosqlite:///./test_chat.db"

engine = create_async_engine(TEST_DB_URL, echo=False)
TestSessionFactory = async_sessionmaker(engine, expire_on_commit=False)


@pytest_asyncio.fixture(autouse=True)
async def setup_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


async def override_get_session():
    async with TestSessionFactory() as session:
        yield session


app.dependency_overrides[get_session] = override_get_session


@pytest_asyncio.fixture
async def client():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


@pytest_asyncio.fixture
async def registered_user(client: AsyncClient):
    resp = await client.post(
        "/auth/register",
        json={"username": "testuser", "password": "testpass123"},
    )
    assert resp.status_code == 201
    return resp.json()


@pytest_asyncio.fixture
async def token(client: AsyncClient) -> str:
    await client.post(
        "/auth/register",
        json={"username": "testuser", "password": "testpass123"},
    )
    resp = await client.post(
        "/auth/login",
        json={"username": "testuser", "password": "testpass123"},
    )
    assert resp.status_code == 200
    return resp.json()["access_token"]


@pytest_asyncio.fixture
async def auth_headers(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


class TestAuth:
    async def test_register_user(self, client: AsyncClient):
        resp = await client.post(
            "/auth/register",
            json={"username": "alice", "password": "secret123"},
        )
        assert resp.status_code == 201
        data = resp.json()
        assert data["username"] == "alice"
        assert "id" in data
        assert "created_at" in data

    async def test_register_duplicate_user(self, client: AsyncClient, registered_user):
        resp = await client.post(
            "/auth/register",
            json={"username": "testuser", "password": "otherpass"},
        )
        assert resp.status_code == 409
        assert "already taken" in resp.json()["detail"].lower()

    async def test_register_invalid_short_username(self, client: AsyncClient):
        resp = await client.post(
            "/auth/register",
            json={"username": "ab", "password": "validpass123"},
        )
        assert resp.status_code == 422

    async def test_register_invalid_short_password(self, client: AsyncClient):
        resp = await client.post(
            "/auth/register",
            json={"username": "validuser", "password": "ab"},
        )
        assert resp.status_code == 422

    async def test_login_user(self, client: AsyncClient, registered_user):
        resp = await client.post(
            "/auth/login",
            json={"username": "testuser", "password": "testpass123"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"

    async def test_login_wrong_password(self, client: AsyncClient, registered_user):
        resp = await client.post(
            "/auth/login",
            json={"username": "testuser", "password": "wrongpass"},
        )
        assert resp.status_code == 401
        assert "invalid" in resp.json()["detail"].lower()

    async def test_login_nonexistent_user(self, client: AsyncClient):
        resp = await client.post(
            "/auth/login",
            json={"username": "nobody", "password": "somepass"},
        )
        assert resp.status_code == 401

    async def test_get_me_authenticated(self, client: AsyncClient, auth_headers):
        resp = await client.get("/auth/me", headers=auth_headers)
        assert resp.status_code == 200
        assert resp.json()["username"] == "testuser"

    async def test_get_me_unauthenticated(self, client: AsyncClient):
        resp = await client.get("/auth/me")
        assert resp.status_code == 401

    async def test_get_me_invalid_token(self, client: AsyncClient):
        resp = await client.get(
            "/auth/me", headers={"Authorization": "Bearer invalidtoken"}
        )
        assert resp.status_code == 401

    async def test_get_me_expired_token(self, client: AsyncClient):
        expired_token = create_access_token(
            data={"sub": "testuser"},
            expires_delta=timedelta(seconds=-1),
        )
        resp = await client.get(
            "/auth/me", headers={"Authorization": f"Bearer {expired_token}"}
        )
        assert resp.status_code == 401

    async def test_get_me_wrong_subject_token(self, client: AsyncClient):
        payload = {"sub": "nonexistent", "exp": datetime.now(timezone.utc) + timedelta(hours=1)}
        bad_token = jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)
        resp = await client.get(
            "/auth/me", headers={"Authorization": f"Bearer {bad_token}"}
        )
        assert resp.status_code == 401


class TestChat:
    async def test_chat_without_auth(self, client: AsyncClient):
        resp = await client.post("/chat", json={"content": "Hello"})
        assert resp.status_code == 401

    async def test_chat_with_auth(self, client: AsyncClient, auth_headers):
        resp = await client.post(
            "/chat", json={"content": "Hello"}, headers=auth_headers
        )
        assert resp.status_code == 200
        data = resp.json()
        assert "reply" in data
        assert "message" in data
        assert data["message"]["role"] == "user"
        assert data["message"]["content"] == "Hello"

    async def test_chat_greeting_response(self, client: AsyncClient, auth_headers):
        resp = await client.post(
            "/chat", json={"content": "Hi there!"}, headers=auth_headers
        )
        data = resp.json()
        assert "hello" in data["reply"].lower()

    async def test_chat_question_response(self, client: AsyncClient, auth_headers):
        resp = await client.post(
            "/chat", json={"content": "What is AI?"}, headers=auth_headers
        )
        data = resp.json()
        assert "question" in data["reply"].lower() or "think" in data["reply"].lower()

    async def test_chat_bye_response(self, client: AsyncClient, auth_headers):
        resp = await client.post(
            "/chat", json={"content": "Goodbye!"}, headers=auth_headers
        )
        data = resp.json()
        assert "goodbye" in data["reply"].lower()

    async def test_chat_fallback_response(self, client: AsyncClient, auth_headers):
        resp = await client.post(
            "/chat", json={"content": "xylophone"}, headers=auth_headers
        )
        data = resp.json()
        assert "you said" in data["reply"].lower()

    async def test_chat_multiple_messages(self, client: AsyncClient, auth_headers):
        for msg in ["Hello", "How are you?", "Goodbye"]:
            resp = await client.post(
                "/chat", json={"content": msg}, headers=auth_headers
            )
            assert resp.status_code == 200

    async def test_chat_empty_message(self, client: AsyncClient, auth_headers):
        resp = await client.post(
            "/chat", json={"content": ""}, headers=auth_headers
        )
        assert resp.status_code == 422

    async def test_chat_whitespace_message(self, client: AsyncClient, auth_headers):
        resp = await client.post(
            "/chat", json={"content": "   "}, headers=auth_headers
        )
        assert resp.status_code == 200

    async def test_chat_very_long_message(self, client: AsyncClient, auth_headers):
        long_content = "A" * 4096
        resp = await client.post(
            "/chat", json={"content": long_content}, headers=auth_headers
        )
        assert resp.status_code == 200

    async def test_chat_too_long_message(self, client: AsyncClient, auth_headers):
        long_content = "A" * 4097
        resp = await client.post(
            "/chat", json={"content": long_content}, headers=auth_headers
        )
        assert resp.status_code == 422

    async def test_chat_special_characters(self, client: AsyncClient, auth_headers):
        resp = await client.post(
            "/chat", json={"content": "Hello! @#$% ^&*()"}, headers=auth_headers
        )
        assert resp.status_code == 200

    async def test_chat_unicode(self, client: AsyncClient, auth_headers):
        resp = await client.post(
            "/chat", json={"content": "你好世界"}, headers=auth_headers
        )
        assert resp.status_code == 200
        data = resp.json()
        assert "you said" in data["reply"].lower()

    async def test_chat_stores_both_messages(self, client: AsyncClient, auth_headers):
        await client.post("/chat", json={"content": "Hello"}, headers=auth_headers)
        hist = await client.get("/chat/history", headers=auth_headers)
        assert hist.status_code == 200
        messages = hist.json()
        assert len(messages) >= 2
        assert messages[1]["role"] == "user"
        assert messages[0]["role"] == "assistant"

    async def test_chat_history_empty(self, client: AsyncClient, auth_headers):
        resp = await client.get("/chat/history", headers=auth_headers)
        assert resp.status_code == 200
        assert resp.json() == []

    async def test_chat_history_without_auth(self, client: AsyncClient):
        resp = await client.get("/chat/history")
        assert resp.status_code == 401

    async def test_chat_history_multiple_messages(
        self, client: AsyncClient, auth_headers
    ):
        for i in range(5):
            await client.post(
                "/chat", json={"content": f"Message {i}"}, headers=auth_headers
            )
        resp = await client.get("/chat/history", headers=auth_headers)
        assert resp.status_code == 200
        messages = resp.json()
        assert len(messages) == 10

    async def test_chat_history_limit(self, client: AsyncClient, auth_headers):
        for i in range(10):
            await client.post(
                "/chat", json={"content": f"Msg {i}"}, headers=auth_headers
            )
        resp = await client.get(
            "/chat/history", headers=auth_headers, params={"limit": 4}
        )
        assert resp.status_code == 200
        assert len(resp.json()) == 4

    async def test_chat_history_offset(self, client: AsyncClient, auth_headers):
        for i in range(10):
            await client.post(
                "/chat", json={"content": f"Msg {i}"}, headers=auth_headers
            )
        resp = await client.get(
            "/chat/history", headers=auth_headers, params={"offset": 18}
        )
        assert resp.status_code == 200
        assert len(resp.json()) == 2

    async def test_different_users_isolated_history(
        self, client: AsyncClient, auth_headers
    ):
        await client.post(
            "/chat", json={"content": "User1 msg"}, headers=auth_headers
        )
        await client.post(
            "/auth/register",
            json={"username": "user2", "password": "pass1234"},
        )
        resp2 = await client.post(
            "/auth/login",
            json={"username": "user2", "password": "pass1234"},
        )
        token2 = resp2.json()["access_token"]
        headers2 = {"Authorization": f"Bearer {token2}"}
        await client.post(
            "/chat", json={"content": "User2 msg"}, headers=headers2
        )
        hist1 = await client.get("/chat/history", headers=auth_headers)
        hist2 = await client.get("/chat/history", headers=headers2)
        assert len(hist1.json()) == 2
        assert len(hist2.json()) == 2
        assert hist1.json()[1]["content"] == "User1 msg"
        assert hist2.json()[1]["content"] == "User2 msg"


class TestHealth:
    async def test_health_endpoint(self, client: AsyncClient):
        resp = await client.get("/health")
        assert resp.status_code == 200
        assert resp.json() == {"status": "ok"}
