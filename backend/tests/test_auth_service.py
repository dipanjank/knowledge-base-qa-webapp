from unittest.mock import AsyncMock

import pytest

from app.schemas.auth import LoginRequest
from app.services.auth_service import AuthService
from app.utils.auth import create_refresh_token
from tests.conftest import make_user


@pytest.fixture
def mock_repo():
    return AsyncMock()


@pytest.fixture
def service(mock_repo):
    return AuthService(mock_repo)


@pytest.mark.asyncio
async def test_login_success(service, mock_repo):
    user = make_user(password="correct")
    mock_repo.get_one.return_value = user

    token_response, refresh_token = await service.login(
        LoginRequest(username="alice", password="correct")
    )

    assert token_response.access_token
    assert token_response.token_type == "bearer"
    assert token_response.expires_in > 0
    assert refresh_token
    mock_repo.get_one.assert_awaited_once_with(username="alice")


@pytest.mark.asyncio
async def test_login_user_not_found(service, mock_repo):
    mock_repo.get_one.return_value = None

    with pytest.raises(Exception) as exc_info:
        await service.login(LoginRequest(username="nobody", password="pass"))
    assert exc_info.value.status_code == 401


@pytest.mark.asyncio
async def test_login_wrong_password(service, mock_repo):
    user = make_user(password="correct")
    mock_repo.get_one.return_value = user

    with pytest.raises(Exception) as exc_info:
        await service.login(LoginRequest(username="alice", password="wrong"))
    assert exc_info.value.status_code == 401


@pytest.mark.asyncio
async def test_refresh_success(service, mock_repo):
    user = make_user()
    mock_repo.get_by_id.return_value = user
    token = create_refresh_token(str(user.id))

    token_response, new_refresh = await service.refresh(token)

    assert token_response.access_token
    assert new_refresh
    mock_repo.get_by_id.assert_awaited_once()


@pytest.mark.asyncio
async def test_refresh_invalid_token(service):
    with pytest.raises(Exception) as exc_info:
        await service.refresh("invalid.token.here")
    assert exc_info.value.status_code == 401


@pytest.mark.asyncio
async def test_refresh_wrong_token_type(service):
    from app.utils.auth import create_access_token

    token = create_access_token("some-id", "user")

    with pytest.raises(Exception) as exc_info:
        await service.refresh(token)
    assert exc_info.value.status_code == 401


@pytest.mark.asyncio
async def test_refresh_user_not_found(service, mock_repo):
    user = make_user()
    mock_repo.get_by_id.return_value = None
    token = create_refresh_token(str(user.id))

    with pytest.raises(Exception) as exc_info:
        await service.refresh(token)
    assert exc_info.value.status_code == 401
