import uuid
from unittest.mock import AsyncMock

import pytest

from app.schemas.user import CreateUserRequest
from app.services.admin_service import AdminService
from tests.conftest import make_user


@pytest.fixture
def mock_repo():
    return AsyncMock()


@pytest.fixture
def service(mock_repo):
    return AdminService(mock_repo)


@pytest.mark.asyncio
async def test_create_user_success(service, mock_repo):
    mock_repo.get_by_username_or_email.return_value = None
    created_user = make_user(username="bob", email="bob@example.com")
    mock_repo.create.return_value = created_user

    result = await service.create_user(
        CreateUserRequest(username="bob", email="bob@example.com")
    )

    assert result.username == "bob"
    assert result.email == "bob@example.com"
    assert result.password  # generated password is returned
    assert result.id == created_user.id
    mock_repo.create.assert_awaited_once()


@pytest.mark.asyncio
async def test_create_user_duplicate(service, mock_repo):
    mock_repo.get_by_username_or_email.return_value = make_user()

    with pytest.raises(Exception) as exc_info:
        await service.create_user(
            CreateUserRequest(username="alice", email="alice@example.com")
        )
    assert exc_info.value.status_code == 409


@pytest.mark.asyncio
async def test_list_users(service, mock_repo):
    users = [
        make_user(username="alice", email="alice@example.com"),
        make_user(username="bob", email="bob@example.com"),
    ]
    mock_repo.get_all.return_value = users
    mock_repo.count.return_value = 2

    result = await service.list_users()

    assert result.total == 2
    assert len(result.items) == 2
    assert result.items[0].username == "alice"
    assert result.items[1].username == "bob"
    mock_repo.get_all.assert_awaited_once_with(order_by="created_at")


@pytest.mark.asyncio
async def test_list_users_empty(service, mock_repo):
    mock_repo.get_all.return_value = []
    mock_repo.count.return_value = 0

    result = await service.list_users()

    assert result.total == 0
    assert result.items == []


@pytest.mark.asyncio
async def test_delete_user_success(service, mock_repo):
    user = make_user()
    mock_repo.get_by_id.return_value = user

    result = await service.delete_user(str(user.id))

    assert result.message == "User deleted"
    assert result.id == user.id
    mock_repo.delete.assert_awaited_once_with(user)


@pytest.mark.asyncio
async def test_delete_user_not_found(service, mock_repo):
    mock_repo.get_by_id.return_value = None

    with pytest.raises(Exception) as exc_info:
        await service.delete_user(str(uuid.uuid4()))
    assert exc_info.value.status_code == 404


@pytest.mark.asyncio
async def test_delete_admin_forbidden(service, mock_repo):
    admin_user = make_user(role="admin")
    mock_repo.get_by_id.return_value = admin_user

    with pytest.raises(Exception) as exc_info:
        await service.delete_user(str(admin_user.id))
    assert exc_info.value.status_code == 403
    mock_repo.delete.assert_not_awaited()
