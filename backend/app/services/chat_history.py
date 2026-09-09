import uuid

from langchain_core.chat_history import BaseChatMessageHistory
from langchain_core.messages import AIMessage, BaseMessage, HumanMessage
from sqlalchemy.orm import sessionmaker

from app.models.conversation import Message


class PostgresChatMessageHistory(BaseChatMessageHistory):
    """LangChain chat history backed by the conversations/messages tables."""

    def __init__(self, conversation_id: str, session_factory: sessionmaker):
        self.conversation_id = uuid.UUID(conversation_id)
        self._session_factory = session_factory

    @property
    def messages(self) -> list[BaseMessage]:
        with self._session_factory() as session:
            rows = (
                session.query(Message)
                .filter(Message.conversation_id == self.conversation_id)
                .order_by(Message.created_at)
                .all()
            )
        result = []
        for row in rows:
            if row.role == "human":
                result.append(HumanMessage(content=row.content))
            else:
                result.append(AIMessage(content=row.content))
        return result

    def add_message(self, message: BaseMessage) -> None:
        role = "human" if isinstance(message, HumanMessage) else "ai"
        with self._session_factory() as session:
            session.add(
                Message(
                    conversation_id=self.conversation_id,
                    role=role,
                    content=message.content,
                )
            )
            session.commit()

    def clear(self) -> None:
        with self._session_factory() as session:
            session.query(Message).filter(Message.conversation_id == self.conversation_id).delete()
            session.commit()
