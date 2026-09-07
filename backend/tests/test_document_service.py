import uuid
from unittest.mock import AsyncMock, MagicMock

import pytest
from fastapi import UploadFile

from app.services.document_service import DocumentService
from tests.conftest import make_document, make_rag_job


@pytest.fixture
def mock_doc_repo():
    return AsyncMock()


@pytest.fixture
def mock_rag_job_repo():
    return AsyncMock()


@pytest.fixture
def mock_s3():
    return MagicMock()


@pytest.fixture
def mock_sqs():
    return MagicMock()


@pytest.fixture
def service(mock_doc_repo, mock_rag_job_repo, mock_s3, mock_sqs):
    return DocumentService(mock_doc_repo, mock_rag_job_repo, mock_s3, mock_sqs)


def make_upload_file(filename: str = "test.txt", content: bytes = b"hello") -> UploadFile:
    import io

    file = UploadFile(filename=filename, file=io.BytesIO(content), size=len(content))
    return file


@pytest.mark.asyncio
async def test_upload_documents_success(service, mock_doc_repo, mock_rag_job_repo, mock_s3, mock_sqs):
    user_id = uuid.uuid4()
    mock_rag_job_repo.get_active_job.return_value = None

    job = make_rag_job(user_id=user_id)
    mock_rag_job_repo.create.return_value = job

    async def create_doc(doc):
        doc.id = uuid.uuid4()
        return doc

    mock_doc_repo.create.side_effect = create_doc
    mock_doc_repo.session = AsyncMock()

    result = await service.upload_documents([make_upload_file("a.txt")], user_id)

    assert result.job_id == job.id
    assert len(result.documents) == 1
    assert result.documents[0].filename == "a.txt"
    mock_s3.upload_file.assert_called_once()
    mock_sqs.send_message.assert_called_once()


@pytest.mark.asyncio
async def test_upload_documents_rejects_active_job(service, mock_rag_job_repo):
    user_id = uuid.uuid4()
    mock_rag_job_repo.get_active_job.return_value = make_rag_job(user_id=user_id, status="processing")

    with pytest.raises(Exception) as exc_info:
        await service.upload_documents([make_upload_file()], user_id)
    assert exc_info.value.status_code == 409


@pytest.mark.asyncio
async def test_upload_documents_rejects_too_many_files(service, mock_rag_job_repo):
    user_id = uuid.uuid4()
    files = [make_upload_file(f"file{i}.txt") for i in range(6)]

    with pytest.raises(Exception) as exc_info:
        await service.upload_documents(files, user_id)
    assert exc_info.value.status_code == 400


@pytest.mark.asyncio
async def test_upload_documents_rejects_unsupported_type(service, mock_rag_job_repo):
    user_id = uuid.uuid4()
    mock_rag_job_repo.get_active_job.return_value = None

    with pytest.raises(Exception) as exc_info:
        await service.upload_documents([make_upload_file("test.pdf")], user_id)
    assert exc_info.value.status_code == 400


@pytest.mark.asyncio
async def test_list_documents(service, mock_doc_repo):
    user_id = uuid.uuid4()
    docs = [make_document(user_id=user_id, filename="a.txt"), make_document(user_id=user_id, filename="b.txt")]
    mock_doc_repo.get_by_user.return_value = docs
    mock_doc_repo.count_by_user.return_value = 2

    result = await service.list_documents(user_id)

    assert result.total == 2
    assert len(result.items) == 2
    assert result.items[0].filename == "a.txt"


@pytest.mark.asyncio
async def test_list_documents_empty(service, mock_doc_repo):
    user_id = uuid.uuid4()
    mock_doc_repo.get_by_user.return_value = []
    mock_doc_repo.count_by_user.return_value = 0

    result = await service.list_documents(user_id)

    assert result.total == 0
    assert result.items == []


@pytest.mark.asyncio
async def test_delete_document_success(service, mock_doc_repo):
    user_id = uuid.uuid4()
    doc = make_document(user_id=user_id)
    mock_doc_repo.get_by_id_and_user.return_value = doc

    result = await service.delete_document(doc.id, user_id)

    assert result.message == "Document deleted"
    assert result.id == doc.id
    mock_doc_repo.soft_delete.assert_awaited_once_with(doc)


@pytest.mark.asyncio
async def test_delete_document_not_found(service, mock_doc_repo):
    mock_doc_repo.get_by_id_and_user.return_value = None

    with pytest.raises(Exception) as exc_info:
        await service.delete_document(uuid.uuid4(), uuid.uuid4())
    assert exc_info.value.status_code == 404
