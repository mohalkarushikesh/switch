Good prep area — and your resume is loaded with RAG depth, so you should aim to answer these at a senior level, not just define terms. Here are the questions that come up most, grouped by theme, with a short pointer on what a strong answer covers.

**Fundamentals**

*What is RAG and why use it instead of just an LLM?* — Retrieval grounds the model in external/up-to-date knowledge, reduces hallucination, avoids retraining, and lets you cite sources. Contrast with fine-tuning: RAG for knowledge that changes, fine-tuning for behavior/style.

*Walk me through a RAG pipeline end to end.* — Ingestion → chunking → embedding → vector store → retrieval (query embed + similarity search) → optional rerank → prompt assembly → generation. Be ready to draw it.

*RAG vs fine-tuning vs prompt engineering — when do you pick each?* — Classic tradeoff question. Cost, freshness of data, and whether the gap is knowledge vs behavior.

**Chunking & embeddings**

*How do you decide chunk size and overlap?* — Tradeoff: small chunks = precise retrieval but lost context; large = more context but noisy and token-costly. Mention semantic chunking and overlap to preserve boundaries.

*How do you choose an embedding model?* — Domain fit, dimensionality vs cost, MTEB benchmark, max sequence length, open vs API. Note that query and document embeddings must come from the same model.

*What's the difference between dense and sparse retrieval?* — Dense (embeddings, semantic) vs sparse (BM25/TF-IDF, keyword/lexical). Hybrid combines both — you've built this, so lead with your experience.

**Retrieval quality**

*Your RAG system returns irrelevant chunks — how do you debug?* — Very common applied question. Separate retrieval failure from generation failure: check if the right chunk was even retrieved (recall) before blaming the LLM. Then look at chunking, embedding model, query phrasing, k value.

*What is reranking and why add it?* — First-stage retrieval optimizes recall cheaply; a cross-encoder reranker reorders top-k for precision. You've done this — mention the two-stage retrieve-then-rerank pattern.

*What are HyDE, query expansion, and query rewriting?* — HyDE generates a hypothetical answer, embeds *that* to retrieve (bridges the question-answer vocabulary gap). You list HyDE on your resume, so be ready to explain the intuition clearly.

*How do you handle multi-hop questions?* — Iterative/agentic retrieval, query decomposition, or graph-based approaches.

**Advanced / architecture**

*Explain CRAG and Self-RAG.* — Both on your resume. CRAG (Corrective RAG) grades retrieved docs and triggers correction (e.g. web search) when they're weak. Self-RAG trains the model to decide *when* to retrieve and to critique its own output with reflection tokens. Interviewers love when a candidate has actually implemented these.

*How do you prevent hallucination in RAG?* — Grounding/attribution, "answer only from context" prompting, confidence thresholds, guardrails, and returning "I don't know" when retrieval is weak. Tie to your nine-layer guardrails.

*How do you handle the context window / too many retrieved docs?* — Reranking, compression/summarization of chunks, context ordering (lost-in-the-middle problem — models attend less to the middle of long contexts).

**Evaluation** (often the differentiator)

*How do you evaluate a RAG system?* — Split retrieval metrics (precision@k, recall@k, MRR, NDCG) from generation metrics (faithfulness, answer relevance, groundedness). Mention frameworks like RAGAS. Your 0.76 precision@5 number is gold here — state it.

*What's "faithfulness" vs "answer relevance"?* — Faithfulness = is the answer supported by retrieved context; relevance = does it actually answer the question. Both matter independently.

**Production / MLOps**

*How do you reduce latency and cost in a RAG system?* — Caching (semantic caching — you built this), smaller/quantized models, async retrieval, limiting k, batching. You've done latency/cost optimization, so this is a strength.

*How do you keep the vector store fresh as documents change?* — Incremental indexing, upserts, TTL, re-embedding strategy.

*How do you secure a RAG system?* — Input/output guardrails, PII redaction (you did this in Custodian), access control on retrieval so users only see permitted docs, prompt-injection defense.

A tip: for almost every one of these, you can pivot to "in my Enterprise RAG project I actually implemented X…" — that's what separates you from candidates who've only read about RAG. Rehearse two or three of your project stories so they're ready.

Want me to run a mock interview where I ask these one at a time and give feedback on your answers, or go deep on any single topic (evaluation and CRAG/Self-RAG are the ones most likely to impress)?
