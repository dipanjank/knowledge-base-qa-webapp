import pytest

from app.repositories.user_repository import UserRepository
from tests.conftest import make_user


@pytest.fixture
def repo(async_session):
    return UserRepository(async_session)


@pytest.mark.asyncio
async def test_create_and_get_by_id(repo):
    user = make_user()
    created = await repo.create(user)
    assert created.id == user.id

    fetched = await repo.get_by_id(user.id)
    assert fetched is not None
    assert fetched.username == "alice"


@pytest.mark.asyncio
async def test_get_by_id_not_found(repo):
    import uuid

    result = await repo.get_by_id(uuid.uuid4())
    assert result is None


@pytest.mark.asyncio
async def test_get_one(repo):
    await repo.create(make_user())
    found = await repo.get_one(username="alice")
    assert found is not None
    assert found.email == "alice@example.com"


@pytest.mark.asyncio
async def test_get_one_no_match(repo):
    result = await repo.get_one(username="nonexistent")
    assert result is None


@pytest.mark.asyncio
async def test_get_all(repo):
    await repo.create(make_user(username="alice", email="alice@example.com"))
    await repo.create(make_user(username="bob", email="bob@example.com"))
    users = await repo.get_all()
    assert len(users) == 2


@pytest.mark.asyncio
async def test_get_all_order_by(repo):
    await repo.create(make_user(username="bob", email="bob@example.com"))
    await repo.create(make_user(username="alice", email="alice@example.com"))
    users = await repo.get_all(order_by="username")
    assert users[0].username == "alice"
    assert users[1].username == "bob"


@pytest.mark.asyncio
async def test_count(repo):
    assert await repo.count() == 0
    await repo.create(make_user())
    assert await repo.count() == 1


@pytest.mark.asyncio
async def test_delete(repo):
    user = await repo.create(make_user())
    await repo.delete(user)
    assert await repo.get_by_id(user.id) is None


@pytest.mark.asyncio
async def test_get_by_username_or_email_matches_username(repo):
    await repo.create(make_user(username="alice", email="alice@example.com"))
    found = await repo.get_by_username_or_email("alice", "other@example.com")
    assert found is not None
    assert found.username == "alice"


@pytest.mark.asyncio
async def test_get_by_username_or_email_matches_email(repo):
    await repo.create(make_user(username="alice", email="alice@example.com"))
    found = await repo.get_by_username_or_email("other", "alice@example.com")
    assert found is not None
    assert found.email == "alice@example.com"


@pytest.mark.asyncio
async def test_get_by_username_or_email_no_match(repo):
    result = await repo.get_by_username_or_email("nobody", "nobody@example.com")
    assert result is None
