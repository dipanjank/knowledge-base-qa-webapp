import uuid

import pytest
from langchain_core.messages import AIMessage, HumanMessage
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlmodel import SQLModel

from app.models.conversation import Conversation
from app.services.chat_history import PostgresChatMessageHistory


@pytest.fixture
def sync_session_factory():
    engine = create_engine("sqlite://", echo=False)
    SQLModel.metadata.create_all(engine)
    return sessionmaker(engine, expire_on_commit=False)


@pytest.fixture
def conversation_id(sync_session_factory):
    convo_id = uuid.uuid4()
    user_id = uuid.uuid4()
    with sync_session_factory() as session:
        session.add(Conversation(id=convo_id, user_id=user_id, title="Test"))
        session.commit()
    return convo_id


def test_messages_empty(sync_session_factory, conversation_id):
    history = PostgresChatMessageHistory(str(conversation_id), sync_session_factory)
    assert history.messages == []


def test_add_human_message(sync_session_factory, conversation_id):
    history = PostgresChatMessageHistory(str(conversation_id), sync_session_factory)
    history.add_message(HumanMessage(content="Hello"))

    messages = history.messages
    assert len(messages) == 1
    assert isinstance(messages[0], HumanMessage)
    assert messages[0].content == "Hello"


def test_add_ai_message(sync_session_factory, conversation_id):
    history = PostgresChatMessageHistory(str(conversation_id), sync_session_factory)
    history.add_message(AIMessage(content="Hi there"))

    messages = history.messages
    assert len(messages) == 1
    assert isinstance(messages[0], AIMessage)
    assert messages[0].content == "Hi there"


def test_multiple_messages_ordered(sync_session_factory, conversation_id):
    history = PostgresChatMessageHistory(str(conversation_id), sync_session_factory)
    history.add_message(HumanMessage(content="Q1"))
    history.add_message(AIMessage(content="A1"))
    history.add_message(HumanMessage(content="Q2"))
    history.add_message(AIMessage(content="A2"))

    messages = history.messages
    assert len(messages) == 4
    assert messages[0].content == "Q1"
    assert messages[1].content == "A1"
    assert messages[2].content == "Q2"
    assert messages[3].content == "A2"


def test_clear(sync_session_factory, conversation_id):
    history = PostgresChatMessageHistory(str(conversation_id), sync_session_factory)
    history.add_message(HumanMessage(content="Hello"))
    history.add_message(AIMessage(content="Hi"))

    history.clear()

    assert history.messages == []


def test_separate_conversations(sync_session_factory):
    convo1_id = uuid.uuid4()
    convo2_id = uuid.uuid4()
    user_id = uuid.uuid4()
    with sync_session_factory() as session:
        session.add(Conversation(id=convo1_id, user_id=user_id, title="Convo 1"))
        session.add(Conversation(id=convo2_id, user_id=user_id, title="Convo 2"))
        session.commit()

    history1 = PostgresChatMessageHistory(str(convo1_id), sync_session_factory)
    history2 = PostgresChatMessageHistory(str(convo2_id), sync_session_factory)

    history1.add_message(HumanMessage(content="From convo 1"))
    history2.add_message(HumanMessage(content="From convo 2"))

    assert len(history1.messages) == 1
    assert history1.messages[0].content == "From convo 1"
    assert len(history2.messages) == 1
    assert history2.messages[0].content == "From convo 2"
