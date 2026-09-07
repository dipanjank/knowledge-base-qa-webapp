import uuid
from unittest.mock import AsyncMock

import pytest

from app.models.rag_job import RagJobDocument
from app.services.rag_job_service import RagJobService
from tests.conftest import make_rag_job


@pytest.fixture
def mock_repo():
    return AsyncMock()


@pytest.fixture
def service(mock_repo):
    return RagJobService(mock_repo)


@pytest.mark.asyncio
async def test_get_active_job_found(service, mock_repo):
    user_id = uuid.uuid4()
    job = make_rag_job(user_id=user_id, status="processing")
    mock_repo.get_active_job.return_value = job

    job_doc = RagJobDocument(rag_job_id=job.id, document_id=uuid.uuid4(), status="processing")
    mock_repo.get_job_documents.return_value = [(job_doc, "test.txt")]

    result = await service.get_active_job(user_id)

    assert result is not None
    assert result.id == job.id
    assert result.status == "processing"
    assert len(result.documents) == 1
    assert result.documents[0].filename == "test.txt"


@pytest.mark.asyncio
async def test_get_active_job_none(service, mock_repo):
    mock_repo.get_active_job.return_value = None

    result = await service.get_active_job(uuid.uuid4())
    assert result is None


@pytest.mark.asyncio
async def test_list_jobs(service, mock_repo):
    user_id = uuid.uuid4()
    job1 = make_rag_job(user_id=user_id, status="success")
    job2 = make_rag_job(user_id=user_id, status="pending")
    mock_repo.get_user_jobs.return_value = [job1, job2]
    mock_repo.count_user_jobs.return_value = 2
    mock_repo.get_job_documents.return_value = []

    result = await service.list_jobs(user_id)

    assert result.total == 2
    assert len(result.items) == 2
    assert result.items[0].status == "success"
    assert result.items[1].status == "pending"


@pytest.mark.asyncio
async def test_list_jobs_empty(service, mock_repo):
    user_id = uuid.uuid4()
    mock_repo.get_user_jobs.return_value = []
    mock_repo.count_user_jobs.return_value = 0

    result = await service.list_jobs(user_id)

    assert result.total == 0
    assert result.items == []


@pytest.mark.asyncio
async def test_list_jobs_includes_documents(service, mock_repo):
    user_id = uuid.uuid4()
    job = make_rag_job(user_id=user_id, status="success", total_documents=2)
    mock_repo.get_user_jobs.return_value = [job]
    mock_repo.count_user_jobs.return_value = 1

    doc1 = RagJobDocument(rag_job_id=job.id, document_id=uuid.uuid4(), status="ready")
    doc2 = RagJobDocument(rag_job_id=job.id, document_id=uuid.uuid4(), status="failed", error_message="bad file")
    mock_repo.get_job_documents.return_value = [(doc1, "a.txt"), (doc2, "b.txt")]

    result = await service.list_jobs(user_id)

    assert len(result.items[0].documents) == 2
    assert result.items[0].documents[0].filename == "a.txt"
    assert result.items[0].documents[0].status == "ready"
    assert result.items[0].documents[1].error_message == "bad file"
