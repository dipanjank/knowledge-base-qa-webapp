import uuid

import pytest

from app.repositories.document_repository import DocumentRepository
from tests.conftest import make_document, make_user


@pytest.fixture
def repo(async_session):
    return DocumentRepository(async_session)


@pytest.mark.asyncio
async def test_get_by_user(repo, async_session):
    user = make_user()
    async_session.add(user)
    await async_session.flush()

    doc1 = make_document(user_id=user.id, filename="a.txt")
    doc2 = make_document(user_id=user.id, filename="b.txt")
    await repo.create(doc1)
    await repo.create(doc2)

    docs = await repo.get_by_user(user.id)
    assert len(docs) == 2


@pytest.mark.asyncio
async def test_get_by_user_excludes_deleted(repo, async_session):
    user = make_user()
    async_session.add(user)
    await async_session.flush()

    doc = make_document(user_id=user.id)
    await repo.create(doc)
    await repo.soft_delete(doc)

    docs = await repo.get_by_user(user.id)
    assert len(docs) == 0


@pytest.mark.asyncio
async def test_get_by_user_excludes_other_users(repo, async_session):
    user1 = make_user(username="alice", email="alice@example.com")
    user2 = make_user(username="bob", email="bob@example.com")
    async_session.add(user1)
    async_session.add(user2)
    await async_session.flush()

    await repo.create(make_document(user_id=user1.id, filename="a.txt"))
    await repo.create(make_document(user_id=user2.id, filename="b.txt"))

    docs = await repo.get_by_user(user1.id)
    assert len(docs) == 1
    assert docs[0].filename == "a.txt"


@pytest.mark.asyncio
async def test_count_by_user(repo, async_session):
    user = make_user()
    async_session.add(user)
    await async_session.flush()

    assert await repo.count_by_user(user.id) == 0
    await repo.create(make_document(user_id=user.id))
    assert await repo.count_by_user(user.id) == 1


@pytest.mark.asyncio
async def test_count_by_user_excludes_deleted(repo, async_session):
    user = make_user()
    async_session.add(user)
    await async_session.flush()

    doc = make_document(user_id=user.id)
    await repo.create(doc)
    await repo.soft_delete(doc)

    assert await repo.count_by_user(user.id) == 0


@pytest.mark.asyncio
async def test_get_by_id_and_user(repo, async_session):
    user = make_user()
    async_session.add(user)
    await async_session.flush()

    doc = make_document(user_id=user.id)
    await repo.create(doc)

    found = await repo.get_by_id_and_user(doc.id, user.id)
    assert found is not None
    assert found.id == doc.id


@pytest.mark.asyncio
async def test_get_by_id_and_user_wrong_user(repo, async_session):
    user = make_user()
    async_session.add(user)
    await async_session.flush()

    doc = make_document(user_id=user.id)
    await repo.create(doc)

    found = await repo.get_by_id_and_user(doc.id, uuid.uuid4())
    assert found is None


@pytest.mark.asyncio
async def test_get_by_id_and_user_deleted(repo, async_session):
    user = make_user()
    async_session.add(user)
    await async_session.flush()

    doc = make_document(user_id=user.id)
    await repo.create(doc)
    await repo.soft_delete(doc)

    found = await repo.get_by_id_and_user(doc.id, user.id)
    assert found is None


@pytest.mark.asyncio
async def test_soft_delete_sets_deleted_at(repo, async_session):
    user = make_user()
    async_session.add(user)
    await async_session.flush()

    doc = make_document(user_id=user.id)
    await repo.create(doc)
    assert doc.deleted_at is None

    await repo.soft_delete(doc)
    assert doc.deleted_at is not None
