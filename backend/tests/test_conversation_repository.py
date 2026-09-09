import uuid

import pytest

from app.repositories.conversation_repository import ConversationRepository
from tests.conftest import make_conversation, make_message, make_user


@pytest.fixture
def repo(async_session):
    return ConversationRepository(async_session)


@pytest.mark.asyncio
async def test_create_and_get_by_id(repo, async_session):
    user = make_user()
    async_session.add(user)
    await async_session.flush()

    convo = make_conversation(user_id=user.id)
    created = await repo.create(convo)

    fetched = await repo.get_by_id(created.id)
    assert fetched is not None
    assert fetched.title == "Test conversation"


@pytest.mark.asyncio
async def test_get_by_id_and_user(repo, async_session):
    user = make_user()
    async_session.add(user)
    await async_session.flush()

    convo = make_conversation(user_id=user.id)
    await repo.create(convo)

    found = await repo.get_by_id_and_user(convo.id, user.id)
    assert found is not None
    assert found.id == convo.id


@pytest.mark.asyncio
async def test_get_by_id_and_user_wrong_user(repo, async_session):
    user = make_user()
    async_session.add(user)
    await async_session.flush()

    convo = make_conversation(user_id=user.id)
    await repo.create(convo)

    found = await repo.get_by_id_and_user(convo.id, uuid.uuid4())
    assert found is None


@pytest.mark.asyncio
async def test_get_recent_by_user(repo, async_session):
    user = make_user()
    async_session.add(user)
    await async_session.flush()

    for i in range(12):
        await repo.create(make_conversation(user_id=user.id, title=f"Convo {i}"))

    recent = await repo.get_recent_by_user(user.id, limit=10)
    assert len(recent) == 10


@pytest.mark.asyncio
async def test_get_recent_by_user_excludes_other_users(repo, async_session):
    user1 = make_user(username="alice", email="alice@example.com")
    user2 = make_user(username="bob", email="bob@example.com")
    async_session.add(user1)
    async_session.add(user2)
    await async_session.flush()

    await repo.create(make_conversation(user_id=user1.id, title="Alice's convo"))
    await repo.create(make_conversation(user_id=user2.id, title="Bob's convo"))

    recent = await repo.get_recent_by_user(user1.id)
    assert len(recent) == 1
    assert recent[0].title == "Alice's convo"


@pytest.mark.asyncio
async def test_count_by_user(repo, async_session):
    user = make_user()
    async_session.add(user)
    await async_session.flush()

    assert await repo.count_by_user(user.id) == 0
    await repo.create(make_conversation(user_id=user.id))
    assert await repo.count_by_user(user.id) == 1


@pytest.mark.asyncio
async def test_get_messages(repo, async_session):
    user = make_user()
    async_session.add(user)
    await async_session.flush()

    convo = make_conversation(user_id=user.id)
    await repo.create(convo)

    msg1 = make_message(conversation_id=convo.id, role="human", content="Hello")
    msg2 = make_message(conversation_id=convo.id, role="ai", content="Hi there")
    await repo.add_message(msg1)
    await repo.add_message(msg2)
    await async_session.commit()

    messages = await repo.get_messages(convo.id)
    assert len(messages) == 2
    assert messages[0].role == "human"
    assert messages[1].role == "ai"


@pytest.mark.asyncio
async def test_get_messages_empty(repo, async_session):
    user = make_user()
    async_session.add(user)
    await async_session.flush()

    convo = make_conversation(user_id=user.id)
    await repo.create(convo)

    messages = await repo.get_messages(convo.id)
    assert messages == []


@pytest.mark.asyncio
async def test_add_message(repo, async_session):
    user = make_user()
    async_session.add(user)
    await async_session.flush()

    convo = make_conversation(user_id=user.id)
    await repo.create(convo)

    msg = make_message(conversation_id=convo.id, role="human", content="Test question")
    created = await repo.add_message(msg)

    assert created.conversation_id == convo.id
    assert created.content == "Test question"


@pytest.mark.asyncio
async def test_add_message_with_sources(repo, async_session):
    user = make_user()
    async_session.add(user)
    await async_session.flush()

    convo = make_conversation(user_id=user.id)
    await repo.create(convo)

    sources = [{"document_id": str(uuid.uuid4()), "filename": "test.txt", "excerpt": "some text"}]
    msg = make_message(conversation_id=convo.id, role="ai", content="Answer", sources=sources)
    await repo.add_message(msg)
    await async_session.commit()

    messages = await repo.get_messages(convo.id)
    assert len(messages) == 1
    assert messages[0].sources is not None
    assert messages[0].sources[0]["filename"] == "test.txt"
