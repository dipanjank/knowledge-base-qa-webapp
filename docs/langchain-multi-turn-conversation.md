# LangChain Multi-Turn Conversation Memory Patterns

LangChain supports four main memory patterns for managing multi-turn conversation context, each trading off between recall fidelity, token efficiency, and architectural flexibility.

## 1. ConversationBufferMemory

Stores every message verbatim and injects the complete history into prompts on each call.

- **Pros**: Simple, transparent, perfect recall with accurate message retention.
- **Cons**: Token costs compound quickly as conversations grow; unsuitable for long sessions.
- **Best for**: Short sessions under ~20 turns.

```python
from langchain.memory import ConversationBufferMemory

memory = ConversationBufferMemory(return_messages=True, memory_key="history")
```

## 2. ConversationSummaryMemory

Uses an LLM to compress older conversation turns into a running summary while keeping recent context intact.

- **Pros**: Reduces token usage significantly through compression; handles longer sessions.
- **Cons**: May lose fine-grained detail; burns tokens to generate summaries, making overhead questionable for brief chats.
- **Best for**: Very long sessions (50+ turns).

```python
from langchain.memory import ConversationSummaryMemory

memory = ConversationSummaryMemory(llm=llm)
```

## 3. ConversationSummaryBufferMemory

Hybrid approach — keeps recent messages verbatim while summarizing anything exceeding a token limit threshold.

- **Pros**: Good balance between precision and efficiency; caps memory size to prevent runaway token growth.
- **Cons**: Slightly more complex configuration.
- **Best for**: Most production applications.

```python
from langchain.memory import ConversationSummaryBufferMemory

memory = ConversationSummaryBufferMemory(llm=llm, max_token_limit=2000)
```

## 4. RunnableWithMessageHistory

Modern LCEL pattern that separates history management from chain logic via a `get_session_history` callable keyed by session ID.

- **Pros**: Clean architecture; trivial storage backend swaps (Redis, MongoDB); works with any LLM provider.
- **Cons**: Requires LCEL familiarity.
- **Best for**: New projects using LCEL.

```python
from langchain_core.runnables.history import RunnableWithMessageHistory
from langchain_community.chat_message_histories import ChatMessageHistory

store = {}

def get_session_history(session_id: str):
    if session_id not in store:
        store[session_id] = ChatMessageHistory()
    return store[session_id]

chain_with_history = RunnableWithMessageHistory(
    chain,
    get_session_history,
)
```

## Choosing the Right Pattern

| Scenario | Recommended Pattern |
|---|---|
| Short sessions (<20 turns) | `ConversationBufferMemory` |
| Long sessions (50+ turns) | `ConversationSummaryMemory` |
| Production default | `ConversationSummaryBufferMemory` |
| New LCEL projects | `RunnableWithMessageHistory` |
