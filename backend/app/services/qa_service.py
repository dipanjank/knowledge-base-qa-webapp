import asyncio
import uuid

from langchain_aws import ChatBedrockConverse
from langchain_core.documents import Document as LCDocument
from langchain_core.prompts import PromptTemplate
from langchain_postgres import PGVector
from sqlalchemy.orm import sessionmaker

from app.models.conversation import Conversation, Message
from app.repositories.conversation_repository import ConversationRepository
from app.schemas.qa import (
    AskResponse,
    ConversationDetailResponse,
    ConversationListResponse,
    ConversationSummary,
    MessageResponse,
    SourceInfo,
)
from app.services.chat_history import PostgresChatMessageHistory

_STUFF_PROMPT_TEMPLATE = """\
You are a helpful assistant that answers questions based on the provided context documents.
Use ONLY the information from the context below to answer the question.
If the context does not contain enough information, say so clearly.

If there is prior conversation history, use it to understand follow-up questions, but always
ground your answer in the document context.

Chat History:
{chat_history}

Context:
---
{context}
---

Question: {question}

Provide a clear, concise answer with references to the source documents.
ALWAYS end your response with a "SOURCES:" line listing the source filenames you used, \
comma-separated. If you used no sources, write "SOURCES: none"."""

STUFF_PROMPT = PromptTemplate(
    template=_STUFF_PROMPT_TEMPLATE,
    input_variables=["context", "question", "chat_history"],
)


def _format_docs(docs: list[LCDocument]) -> str:
    parts = []
    for doc in docs:
        source = doc.metadata.get("filename", "unknown")
        parts.append(f"{doc.page_content}\n[Source: {source}]")
    return "\n---\n".join(parts)


def _parse_sources(text: str) -> tuple[str, set[str]]:
    """Split answer text from the SOURCES: line and return (answer, source_names)."""
    lines = text.strip().rsplit("\n", 5)
    for i, line in enumerate(lines):
        if line.strip().upper().startswith("SOURCES:"):
            sources_str = line.strip().split(":", 1)[1].strip()
            answer = "\n".join(lines[:i]).strip()
            if sources_str.lower() == "none":
                return answer, set()
            return answer, {s.strip() for s in sources_str.split(",") if s.strip()}
    return text.strip(), set()


class QAService:
    """RAG question-answering service with multi-turn conversation support."""

    def __init__(
        self,
        conversation_repo: ConversationRepository,
        vector_store: PGVector,
        llm: ChatBedrockConverse,
        sync_session_factory: sessionmaker,
    ):
        self._conversation_repo = conversation_repo
        self._vector_store = vector_store
        self._llm = llm
        self._sync_session_factory = sync_session_factory
        self._chain = STUFF_PROMPT | llm

    async def ask(self, user_id: uuid.UUID, question: str, conversation_id: uuid.UUID | None) -> AskResponse:
        conversation = await self._resolve_conversation(user_id, question, conversation_id)

        docs = await asyncio.to_thread(self._retrieve, str(user_id), question)

        history = PostgresChatMessageHistory(
            conversation_id=str(conversation.id),
            session_factory=self._sync_session_factory,
        )
        chat_history_text = "\n".join(
            f"{'Human' if m.type == 'human' else 'Assistant'}: {m.content}"
            for m in history.messages
        )

        context = _format_docs(docs)
        result = await asyncio.to_thread(
            self._chain.invoke,
            {"context": context, "question": question, "chat_history": chat_history_text},
        )

        raw_text = result.content if hasattr(result, "content") else str(result)
        answer, source_names = _parse_sources(raw_text)

        sources = [
            SourceInfo(
                document_id=d.metadata["document_id"],
                filename=d.metadata["filename"],
                excerpt=d.page_content[:200],
            )
            for d in docs
            if d.metadata.get("filename") in source_names
        ]
        if not sources and docs:
            sources = [
                SourceInfo(
                    document_id=d.metadata["document_id"],
                    filename=d.metadata["filename"],
                    excerpt=d.page_content[:200],
                )
                for d in docs
            ]

        human_msg = Message(conversation_id=conversation.id, role="human", content=question)
        ai_msg = Message(
            conversation_id=conversation.id,
            role="ai",
            content=answer,
            sources=[s.model_dump() for s in sources],
        )
        await self._conversation_repo.add_message(human_msg)
        await self._conversation_repo.add_message(ai_msg)
        await self._conversation_repo.update_timestamp(conversation)
        await self._conversation_repo.session.commit()

        return AskResponse(answer=answer, sources=sources, conversation_id=conversation.id)

    async def list_conversations(self, user_id: uuid.UUID) -> ConversationListResponse:
        conversations = await self._conversation_repo.get_recent_by_user(user_id, limit=10)
        total = await self._conversation_repo.count_by_user(user_id)
        return ConversationListResponse(
            items=[
                ConversationSummary(
                    id=c.id, title=c.title, created_at=c.created_at, updated_at=c.updated_at
                )
                for c in conversations
            ],
            total=total,
        )

    async def get_conversation(
        self, user_id: uuid.UUID, conversation_id: uuid.UUID
    ) -> ConversationDetailResponse | None:
        conversation = await self._conversation_repo.get_by_id_and_user(conversation_id, user_id)
        if not conversation:
            return None
        messages = await self._conversation_repo.get_messages(conversation_id)
        return ConversationDetailResponse(
            id=conversation.id,
            title=conversation.title,
            messages=[
                MessageResponse(
                    id=m.id,
                    role=m.role,
                    content=m.content,
                    sources=[SourceInfo(**s) for s in m.sources] if m.sources else None,
                    created_at=m.created_at,
                )
                for m in messages
            ],
        )

    async def _resolve_conversation(
        self, user_id: uuid.UUID, question: str, conversation_id: uuid.UUID | None
    ) -> Conversation:
        if conversation_id:
            conversation = await self._conversation_repo.get_by_id_and_user(conversation_id, user_id)
            if not conversation:
                raise ValueError("Conversation not found")
            return conversation
        conversation = Conversation(user_id=user_id, title=question[:200])
        return await self._conversation_repo.create(conversation)

    def _retrieve(self, user_id: str, question: str):
        retriever = self._vector_store.as_retriever(
            search_kwargs={"k": 5, "filter": {"user_id": user_id}}
        )
        return retriever.invoke(question)
