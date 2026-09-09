import uuid
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from langchain_core.documents import Document as LCDocument
from langchain_core.messages import AIMessage

from app.services.qa_service import QAService, _format_docs, _parse_sources
from tests.conftest import make_conversation, make_message


@pytest.fixture
def mock_conversation_repo():
    repo = AsyncMock()
    repo.session = AsyncMock()
    return repo


@pytest.fixture
def mock_vector_store():
    return MagicMock()


@pytest.fixture
def mock_llm():
    return MagicMock()


@pytest.fixture
def mock_sync_session_factory():
    return MagicMock()


@pytest.fixture
def service(mock_conversation_repo, mock_vector_store, mock_llm, mock_sync_session_factory):
    svc = QAService(mock_conversation_repo, mock_vector_store, mock_llm, mock_sync_session_factory)
    svc._chain = MagicMock()
    return svc


def _make_lc_docs():
    return [
        LCDocument(
            page_content="Revenue was $4.2B in Q3",
            metadata={"document_id": str(uuid.uuid4()), "user_id": str(uuid.uuid4()), "filename": "report.txt"},
        ),
        LCDocument(
            page_content="Expenses were $2.1B",
            metadata={"document_id": str(uuid.uuid4()), "user_id": str(uuid.uuid4()), "filename": "expenses.txt"},
        ),
    ]


# --- Unit tests for helper functions ---


def test_format_docs():
    docs = _make_lc_docs()
    result = _format_docs(docs)
    assert "Revenue was $4.2B" in result
    assert "[Source: report.txt]" in result
    assert "[Source: expenses.txt]" in result


def test_parse_sources_with_sources():
    text = "Revenue was $4.2B.\nSOURCES: report.txt, expenses.txt"
    answer, sources = _parse_sources(text)
    assert answer == "Revenue was $4.2B."
    assert sources == {"report.txt", "expenses.txt"}


def test_parse_sources_none():
    text = "I don't know.\nSOURCES: none"
    answer, sources = _parse_sources(text)
    assert answer == "I don't know."
    assert sources == set()


def test_parse_sources_missing():
    text = "An answer without sources section."
    answer, sources = _parse_sources(text)
    assert answer == "An answer without sources section."
    assert sources == set()


# --- Service tests ---


@pytest.mark.asyncio
async def test_ask_new_conversation(service, mock_conversation_repo, mock_vector_store):
    user_id = uuid.uuid4()
    question = "What was Q3 revenue?"
    convo = make_conversation(user_id=user_id, title=question[:200])
    mock_conversation_repo.create.return_value = convo

    docs = _make_lc_docs()
    mock_retriever = MagicMock()
    mock_retriever.invoke.return_value = docs
    mock_vector_store.as_retriever.return_value = mock_retriever

    service._chain.invoke.return_value = AIMessage(
        content="Revenue was $4.2B.\nSOURCES: report.txt"
    )

    with patch("app.services.qa_service.PostgresChatMessageHistory") as mock_history_cls:
        mock_history = MagicMock()
        mock_history.messages = []
        mock_history_cls.return_value = mock_history

        result = await service.ask(user_id, question, None)

    assert result.answer == "Revenue was $4.2B."
    assert result.conversation_id == convo.id
    assert len(result.sources) == 1
    assert result.sources[0].filename == "report.txt"
    mock_conversation_repo.create.assert_awaited_once()
    assert mock_conversation_repo.add_message.await_count == 2


@pytest.mark.asyncio
async def test_ask_existing_conversation(service, mock_conversation_repo, mock_vector_store):
    user_id = uuid.uuid4()
    convo = make_conversation(user_id=user_id)
    mock_conversation_repo.get_by_id_and_user.return_value = convo

    docs = _make_lc_docs()
    mock_retriever = MagicMock()
    mock_retriever.invoke.return_value = docs
    mock_vector_store.as_retriever.return_value = mock_retriever

    service._chain.invoke.return_value = AIMessage(
        content="Some answer.\nSOURCES: report.txt, expenses.txt"
    )

    with patch("app.services.qa_service.PostgresChatMessageHistory") as mock_history_cls:
        mock_history = MagicMock()
        mock_history.messages = []
        mock_history_cls.return_value = mock_history

        result = await service.ask(user_id, "Follow up question", convo.id)

    assert result.conversation_id == convo.id
    assert len(result.sources) == 2
    mock_conversation_repo.create.assert_not_awaited()


@pytest.mark.asyncio
async def test_ask_conversation_not_found(service, mock_conversation_repo):
    user_id = uuid.uuid4()
    mock_conversation_repo.get_by_id_and_user.return_value = None

    with pytest.raises(ValueError, match="Conversation not found"):
        await service.ask(user_id, "Question", uuid.uuid4())


@pytest.mark.asyncio
async def test_ask_fallback_sources_when_no_match(service, mock_conversation_repo, mock_vector_store):
    user_id = uuid.uuid4()
    convo = make_conversation(user_id=user_id)
    mock_conversation_repo.create.return_value = convo

    docs = _make_lc_docs()
    mock_retriever = MagicMock()
    mock_retriever.invoke.return_value = docs
    mock_vector_store.as_retriever.return_value = mock_retriever

    service._chain.invoke.return_value = AIMessage(
        content="Answer text.\nSOURCES: none"
    )

    with patch("app.services.qa_service.PostgresChatMessageHistory") as mock_history_cls:
        mock_history = MagicMock()
        mock_history.messages = []
        mock_history_cls.return_value = mock_history

        result = await service.ask(user_id, "Question", None)

    assert len(result.sources) == 2


@pytest.mark.asyncio
async def test_ask_saves_human_and_ai_messages(service, mock_conversation_repo, mock_vector_store):
    user_id = uuid.uuid4()
    convo = make_conversation(user_id=user_id)
    mock_conversation_repo.create.return_value = convo

    docs = _make_lc_docs()
    mock_retriever = MagicMock()
    mock_retriever.invoke.return_value = docs
    mock_vector_store.as_retriever.return_value = mock_retriever

    service._chain.invoke.return_value = AIMessage(
        content="Answer.\nSOURCES: report.txt"
    )

    with patch("app.services.qa_service.PostgresChatMessageHistory") as mock_history_cls:
        mock_history = MagicMock()
        mock_history.messages = []
        mock_history_cls.return_value = mock_history

        await service.ask(user_id, "My question", None)

    calls = mock_conversation_repo.add_message.call_args_list
    assert len(calls) == 2
    human_msg = calls[0][0][0]
    ai_msg = calls[1][0][0]
    assert human_msg.role == "human"
    assert human_msg.content == "My question"
    assert ai_msg.role == "ai"
    assert ai_msg.content == "Answer."
    assert ai_msg.sources is not None
    mock_conversation_repo.update_timestamp.assert_awaited_once()
    mock_conversation_repo.session.commit.assert_awaited_once()


@pytest.mark.asyncio
async def test_list_conversations(service, mock_conversation_repo):
    user_id = uuid.uuid4()
    convos = [make_conversation(user_id=user_id, title=f"Convo {i}") for i in range(3)]
    mock_conversation_repo.get_recent_by_user.return_value = convos
    mock_conversation_repo.count_by_user.return_value = 3

    result = await service.list_conversations(user_id)

    assert result.total == 3
    assert len(result.items) == 3
    assert result.items[0].title == "Convo 0"
    mock_conversation_repo.get_recent_by_user.assert_awaited_once_with(user_id, limit=10)


@pytest.mark.asyncio
async def test_list_conversations_empty(service, mock_conversation_repo):
    user_id = uuid.uuid4()
    mock_conversation_repo.get_recent_by_user.return_value = []
    mock_conversation_repo.count_by_user.return_value = 0

    result = await service.list_conversations(user_id)

    assert result.total == 0
    assert result.items == []


@pytest.mark.asyncio
async def test_get_conversation(service, mock_conversation_repo):
    user_id = uuid.uuid4()
    convo = make_conversation(user_id=user_id)
    mock_conversation_repo.get_by_id_and_user.return_value = convo

    msgs = [
        make_message(conversation_id=convo.id, role="human", content="Q"),
        make_message(
            conversation_id=convo.id,
            role="ai",
            content="A",
            sources=[{"document_id": "x", "filename": "f.txt", "excerpt": "e"}],
        ),
    ]
    mock_conversation_repo.get_messages.return_value = msgs

    result = await service.get_conversation(user_id, convo.id)

    assert result is not None
    assert result.id == convo.id
    assert len(result.messages) == 2
    assert result.messages[0].role == "human"
    assert result.messages[1].sources is not None
    assert result.messages[1].sources[0].filename == "f.txt"


@pytest.mark.asyncio
async def test_get_conversation_not_found(service, mock_conversation_repo):
    mock_conversation_repo.get_by_id_and_user.return_value = None

    result = await service.get_conversation(uuid.uuid4(), uuid.uuid4())
    assert result is None
