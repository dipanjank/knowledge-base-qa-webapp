
import pytest

from app.models.rag_job import RagJobDocument
from app.repositories.document_repository import DocumentRepository
from app.repositories.rag_job_repository import RagJobRepository
from tests.conftest import make_document, make_rag_job, make_user


@pytest.fixture
def repo(async_session):
    return RagJobRepository(async_session)


@pytest.fixture
def doc_repo(async_session):
    return DocumentRepository(async_session)


@pytest.mark.asyncio
async def test_create_and_get_by_id(repo, async_session):
    user = make_user()
    async_session.add(user)
    await async_session.flush()

    job = make_rag_job(user_id=user.id, total_documents=2)
    created = await repo.create(job)

    fetched = await repo.get_by_id(created.id)
    assert fetched is not None
    assert fetched.total_documents == 2
    assert fetched.status == "pending"


@pytest.mark.asyncio
async def test_get_active_job(repo, async_session):
    user = make_user()
    async_session.add(user)
    await async_session.flush()

    job = make_rag_job(user_id=user.id, status="processing")
    await repo.create(job)

    active = await repo.get_active_job(user.id)
    assert active is not None
    assert active.id == job.id


@pytest.mark.asyncio
async def test_get_active_job_none_when_completed(repo, async_session):
    user = make_user()
    async_session.add(user)
    await async_session.flush()

    job = make_rag_job(user_id=user.id, status="success")
    await repo.create(job)

    active = await repo.get_active_job(user.id)
    assert active is None


@pytest.mark.asyncio
async def test_get_active_job_none_for_other_user(repo, async_session):
    user1 = make_user(username="alice", email="alice@example.com")
    user2 = make_user(username="bob", email="bob@example.com")
    async_session.add(user1)
    async_session.add(user2)
    await async_session.flush()

    await repo.create(make_rag_job(user_id=user1.id, status="pending"))

    active = await repo.get_active_job(user2.id)
    assert active is None


@pytest.mark.asyncio
async def test_get_user_jobs(repo, async_session):
    user = make_user()
    async_session.add(user)
    await async_session.flush()

    await repo.create(make_rag_job(user_id=user.id, status="success"))
    await repo.create(make_rag_job(user_id=user.id, status="pending"))

    jobs = await repo.get_user_jobs(user.id)
    assert len(jobs) == 2


@pytest.mark.asyncio
async def test_count_user_jobs(repo, async_session):
    user = make_user()
    async_session.add(user)
    await async_session.flush()

    assert await repo.count_user_jobs(user.id) == 0
    await repo.create(make_rag_job(user_id=user.id))
    assert await repo.count_user_jobs(user.id) == 1


@pytest.mark.asyncio
async def test_get_job_documents(repo, doc_repo, async_session):
    user = make_user()
    async_session.add(user)
    await async_session.flush()

    job = make_rag_job(user_id=user.id, total_documents=2)
    await repo.create(job)

    doc1 = make_document(user_id=user.id, filename="a.txt")
    doc2 = make_document(user_id=user.id, filename="b.txt")
    await doc_repo.create(doc1)
    await doc_repo.create(doc2)

    await repo.create_job_document(RagJobDocument(rag_job_id=job.id, document_id=doc1.id))
    await repo.create_job_document(RagJobDocument(rag_job_id=job.id, document_id=doc2.id))
    await async_session.commit()

    job_docs = await repo.get_job_documents(job.id)
    assert len(job_docs) == 2
    filenames = {filename for _, filename in job_docs}
    assert filenames == {"a.txt", "b.txt"}


@pytest.mark.asyncio
async def test_create_job_document(repo, doc_repo, async_session):
    user = make_user()
    async_session.add(user)
    await async_session.flush()

    job = make_rag_job(user_id=user.id)
    await repo.create(job)

    doc = make_document(user_id=user.id)
    await doc_repo.create(doc)

    job_doc = await repo.create_job_document(
        RagJobDocument(rag_job_id=job.id, document_id=doc.id)
    )
    assert job_doc.rag_job_id == job.id
    assert job_doc.document_id == doc.id
    assert job_doc.status == "pending"
