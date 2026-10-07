tech stack (short): Python · FastAPI · LangGraph · Gemini (chat + embeddings) · Claude Haiku (fast LLM) · fastembed/ONNX (dense BAAI/bge-small + BM25 sparse) · Qdrant hybrid store · RAGAS eval

reranker: YES cross-encoder — fastembed TextCrossEncoder `Xenova/ms-marco-MiniLM-L-6-v2` (local); fallbacks = Gemini-LLM reranker / lexical IDF scorer

---

data ingestion :   chunker, loader, `rag-ingest` CLI

load the settings .env 

start the fastapi app 

graph compiled 

/ask  -> received the question 

guardrails checked - 6 input: shape, piiredaction, secret request,sql injection, intent, scope / 3 output -  destructive_output, secret_egress, output_review  

cached lookup - exact/ semantic else fall back to llm 

router 		vector/sql/both/reject   (both = vector + sql, results merged) 

retrieval 	hybrid (dense + space search) - (bm25/gemini+bm25/dense+bm25(fastembed)) 
	
	re-ranker : retrieved docs -> rerank score -> sorted -> 

CRAG - 		when information quality is low -> rewrite the query -> fall back to retrieval

generated ans 

self rag - 	Allows the LLM to self-reflect and decide when to retrieve, evaluate, revise  

output guardrails has been checked 

finalize 

store ans cache 

return json response 

sql pauses for approval  - using langgrpah intruupt 

database rows are rendered into ans context and final response is produced 

caching: exact + semantic (embedding) lookup; blocked path short-circuits to error response 

observability: each node traced/logged (latency, tokens, verdicts) 

evaluation: hit@k, recall, mrr, ndcg, p@k, cases 



---

temp 

data ingestion : clean out noise and understanding their structure 

Intent - LLM classifier decides if the request violates platform policy

1. `destructive_output`
   - if the answer contains `kubectl delete`, `helm uninstall`, etc., it adds a change-control notice
2. `secret_egress`
   - redact secrets found in generated text
3. `output_review`
   - LLM reviews if the answer is grounded, safe, and not claiming unsupported facts
 
hit@k - Was the correct document found in the top K results?

MRR (Mean Reciprocal Rank): How early does the first relevant result appear?

NDCG@K (Normalized Discounted Cumulative Gain) : Are highly relevant documents ranked near the top?


Corrective RAG (CRAG): Evaluates retrieved documents and corrects retrieval by re-searching or refining context when information quality is low.

Self-RAG: Allows the LLM to self-reflect and decide when to retrieve, evaluate retrieved content, and revise its own response.

grounded - Achoring an AI response stictly from external facts rather than it's training memory 

RAGAS - faithfulness(hallucination detection) & context relevance 