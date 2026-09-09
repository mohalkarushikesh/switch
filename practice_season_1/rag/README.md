# RAG concepts -- tiny runnable examples

Thirteen small, self-contained scripts that each demonstrate one Retrieval-
Augmented Generation concept. They run **fully offline** (only `numpy` required)
-- no models to download, no API keys, no network. That keeps the focus on the
*retrieval logic* rather than model plumbing, and it works behind a locked-down
corporate proxy where model hubs are blocked.

Everything shared lives in [common.py](common.py):

- a **toy embedder** (`embed`) -- a stand-in for a real sentence-transformer. It
  maps text onto a handful of hand-made "meaning groups" so synonyms
  (`slow` ~ `sluggish`) land near each other.
- a small **10-document corpus** (`CORPUS`).
- helpers: `tokenize`, `cosine`, `lexical_coverage`, `content_tokens`.

Each script has a comment marking exactly where a **real embedding model, LLM,
reranker, or search API** would plug in. Files that need longer or structured
text (chunking, parent-document, multi-hop) define their own small corpus inline.

## A learning path

Read them in this order -- it walks the RAG pipeline from baseline to advanced.

### Start here: the baseline
| File | Concept | One-line idea |
|------|---------|---------------|
| [00_naive_rag.py](00_naive_rag.py) | **Naive RAG** | The whole pipeline in one file: index -> retrieve -> augment the prompt -> generate. Everything below fixes a specific weakness of this baseline. |

### Indexing -- how you prepare documents
| File | Concept | One-line idea |
|------|---------|---------------|
| [06_chunking.py](06_chunking.py) | **Chunking** | How you split documents drives retrieval quality; fixed-size vs. sliding-window (overlap) vs. sentence-based, and why overlap rescues a boundary-spanning answer. |

### Pre-retrieval -- transforming the query
| File | Concept | One-line idea |
|------|---------|---------------|
| [07_query_transformations.py](07_query_transformations.py) | **Query transforms** | Rewrite the query before retrieval: multi-query / RAG-fusion (RRF), decomposition into sub-questions, and step-back to broader context. |
| [03_hyde.py](03_hyde.py) | **HyDE** | Ask an LLM to write a *hypothetical answer*, embed **that** instead of the raw query, and retrieve -- a fake answer looks like the real answer docs. |

### Retrieval -- finding candidates
| File | Concept | One-line idea |
|------|---------|---------------|
| [01_hybrid_retrieval.py](01_hybrid_retrieval.py) | **Dense + BM25 hybrid** | Run a lexical (BM25) and a semantic (dense) retriever, fuse their rankings with Reciprocal Rank Fusion for keyword precision *and* paraphrase recall. |

### Post-retrieval -- refining what came back
| File | Concept | One-line idea |
|------|---------|---------------|
| [02_reranking.py](02_reranking.py) | **Reranking** | A cheap bi-encoder fetches a shortlist; an expensive cross-encoder rereads each (query, doc) pair together and reorders for precision. |
| [08_mmr.py](08_mmr.py) | **MMR** | Maximal Marginal Relevance trades relevance against novelty so the top-k isn't full of near-duplicates. |
| [09_contextual_compression.py](09_contextual_compression.py) | **Contextual compression** | Filter out irrelevant docs, then keep only the relevant sentences inside the survivors, to cut tokens and distraction before generation. |
| [10_parent_document.py](10_parent_document.py) | **Small-to-big** | Embed & match on small child chunks (precise), but hand the larger parent document (or a sentence window) to the LLM (enough context). |

### Agentic / adaptive -- deciding and correcting
| File | Concept | One-line idea |
|------|---------|---------------|
| [04_crag.py](04_crag.py) | **CRAG** | Grade retrieved docs first; if good, refine them into useful strips; if bad, fall back to an external web search. |
| [05_self_rag.py](05_self_rag.py) | **Self-RAG** | The model emits reflection tokens (Retrieve?, ISREL, ISSUP, ISUSE) to decide *whether* to retrieve and to critique what it got. |
| [11_multi_hop.py](11_multi_hop.py) | **Multi-hop** | Chain facts across documents: retrieve, extract an intermediate entity, reformulate the query, retrieve again -- for questions one lookup can't answer. |

### Measuring -- is it any good?
| File | Concept | One-line idea |
|------|---------|---------------|
| [12_rag_evaluation.py](12_rag_evaluation.py) | **Evaluation** | Offline stand-ins for RAGAS-style metrics: context precision/recall (retrieval), faithfulness/groundedness (grounded vs. hallucinated), answer relevance (generation). |

## Run them

```bash
cd practice_season_1/rag
python 00_naive_rag.py
python 06_chunking.py
python 07_query_transformations.py
python 03_hyde.py
python 01_hybrid_retrieval.py
python 02_reranking.py
python 08_mmr.py
python 09_contextual_compression.py
python 10_parent_document.py
python 04_crag.py
python 05_self_rag.py
python 11_multi_hop.py
python 12_rag_evaluation.py
```

(The numeric prefixes are just filenames; the learning path above is the order
worth reading them in.)

## From toy to real

Swap the stand-ins for real components without changing the surrounding logic:

- `embed(text)` -> `SentenceTransformer(...).encode(text)` (or an embeddings API)
- the toy cross-encoder in `02` -> a real reranker (BERT cross-encoder / a rerank API)
- the fake LLMs in `00`/`03`/`04`/`05`/`07`/`11` -> real LLM calls
- `web_search` in `04` -> a real search API
- `CORPUS` + `embed_corpus()` -> a real vector database
- the heuristic metrics in `12` -> an LLM-judge-based evaluator (e.g. RAGAS)
