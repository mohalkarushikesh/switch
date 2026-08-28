# Enterprise Advanced RAG in LangGraph

A production-grade Enterprise RAG system for Kubernetes IT operations, built with LangGraph, FastAPI, Qdrant, PostgreSQL, and Redis — covering hybrid search, reranking, HyDE, CRAG, Self-RAG, Text2SQL, caching, and guardrails.

> Course reference: [Enterprise Advanced RAG with Hybrid Search, ReRanking, HyDE, CRAG, Self-RAG…](https://www.krishnaik.in/project/) — 39 lectures
>
> _Note: the original course URL was truncated in the source material; replace the link above with the full URL._

## Overview

The project starts from a baseline RAG pipeline and incrementally layers on advanced retrieval and safety patterns until it becomes a Kubernetes SRE copilot:

1. Baseline RAG
2. Hybrid search (dense + sparse retrieval)
3. Reranking
4. HyDE (Hypothetical Document Embeddings)
5. CRAG (Corrective RAG)
6. Self-RAG
7. Text2SQL with human-in-the-loop approval
8. Evaluation
9. A 9-layer guardrails pipeline

## What You Will Learn

- Advanced RAG design: hybrid search, reranking, HyDE, CRAG, Self-RAG, and Text2SQL
- LangGraph orchestration for multi-step, stateful retrieval workflows
- Caching strategies, evaluation methodology, and guardrail design

## What You'll Build

A production-grade Kubernetes SRE copilot featuring:

- **FastAPI** service layer
- **LangGraph** orchestration of the RAG workflow
- **Qdrant** vector retrieval with hybrid search and reranking
- **PostgreSQL** Text2SQL with human approval before execution
- **Redis** caching
- **Streamlit** UI
- **Ragas** evaluations
- **Security layers** — a 9-layer guardrails pipeline

## Tech Stack

| Layer | Technology |
| --- | --- |
| Orchestration | LangGraph |
| API | FastAPI |
| Vector store | Qdrant |
| Relational store / Text2SQL | PostgreSQL |
| Cache | Redis |
| UI | Streamlit |
| Evaluation | Ragas |

## Getting Started

_Setup instructions to be added as the implementation lands._
