data ingestion :   chunker, loader, `rag-ingest` CLI

load the settings .env 

start the fastapi app 

graph compiled 

/ask  -> received the question 

guardrails checked - 6 input: shape, piiredaction, secret request, ingestion, intent, scope / 3 output -  destructive_output, secret_egress, output_review  

cached lookup - exact/ semantic else fall back to llm 

router 		vector/sql/both/reject   (both = vector + sql, results merged) 

retrieval 	hybrid dense + space search (bm25/gemini+bm25/dense+bm25(fastembed)) 
	
	re-ranker : retrieved docs -> rerank score -> sorted -> 

CRAG - 		relevance check -> rewrite the query -> fall back to retrieval

generated ans 

self rag - 	validate the text, it has special reflective token

output guardrails has been checked 

finalize 

store ans cache 

return json response 

sql pauses for approval  - using langgrpah intruupt 

database rows are rendered into ans context and final response is produced 

caching: exact + semantic (embedding) lookup; blocked path short-circuits to error response 

observability: each node traced/logged (latency, tokens, verdicts) 


evaluation: hit@k, recall, mrr, ndcg, p@k, cases 