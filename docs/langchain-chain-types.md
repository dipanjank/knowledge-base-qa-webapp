# LangChain Question Answering Chain Types

LangChain offers four main QA chain types — **stuff**, **map_reduce**, **refine**, and **map_rerank** — each with different strategies for processing retrieved documents before the LLM generates an answer.

## 1. stuff

All retrieved documents are concatenated into a single context string and passed to the LLM in one prompt.

- **Pros**: Simple to implement; good for small document sets.
- **Cons**: Can hit context limits with large document sets.

```python
from langchain.chains.question_answering import load_qa_chain
from langchain.llms import OpenAI

chain = load_qa_chain(OpenAI(temperature=0), chain_type="stuff")
result = chain.run(input_documents=docs, question=query)
```

## 2. map_reduce

Splits retrieved documents into chunks, runs the LLM on each chunk to produce a summary, then combines these summaries into a final answer.

- **Pros**: Scales better for large document sets; reduces token usage per call.
- **Cons**: Requires multiple LLM calls; may lose nuance if summaries are too brief.

## 3. refine

Iteratively refines the answer by feeding the LLM the question plus the most relevant documents, updating the answer after each step.

- **Pros**: Produces more coherent, context-aware answers.
- **Cons**: More complex; requires more sequential LLM calls.

## 4. map_rerank

Similar to map_reduce but adds a reranking step — after initial chunk processing, re-ranks results based on relevance before final aggregation.

- **Pros**: Improves relevance of the final answer.
- **Cons**: More computationally intensive due to the reranking step.

## Choosing the Right Chain Type

| Scenario | Recommended Chain |
|---|---|
| Small datasets | `stuff` |
| Large datasets | `map_reduce` or `map_rerank` |
| Iterative refinement needed | `refine` |

## With Sources

LangChain also offers `load_qa_with_sources_chain` for the same chain types, returning citations alongside the answer.
