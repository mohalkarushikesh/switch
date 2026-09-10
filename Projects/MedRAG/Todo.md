2. MedRAG with LlamaIndex: Clinical Guideline RAG from Ingestion to Deployment
🔗 https://www.krishnaik.in/project/medrag-clinical-guideline-qa-with-retrieval-augmented-generation 📚 33 lectures

Build a production-ready clinical-guideline question-answering system with LlamaIndex powering document ingestion, indexing, retrieval, and grounded generation. Students use LlamaParse and PubMedReader to create LlamaIndex documents, then chunk and embed them into a Qdrant-backed VectorStoreIndex queried through an OpenAI-powered LlamaIndex query engine. The project completes the system with evaluations, FastAPI and Streamlit interfaces, Docker CI/CD deployment, and API-boundary input and output guardrails.

What You Will Learn

Design a reusable, domain-agnostic RAG core with a MedRAG-specific project plugin.
Build clinical-document ingestion, indexing, vector retrieval, and grounded answer generation workflows.
Create shared evaluation modules to measure retrieval and generation quality.
Expose one RAG service through CLI, FastAPI, and Streamlit interfaces.
Containerize and deploy the application through CI/CD while implementing input and output safety guardrails.
What You'll Build

A clinical-guideline ingestion and indexing pipeline backed by a vector database.
A modular MedRAG retrieval and answer-generation service with source-grounded responses.
CLI, FastAPI, and Streamlit interfaces powered by the same reusable RAG service.
An evaluation harness with shared metrics and diagnostic workflows.
A Dockerized CI/CD deployment with API-boundary input and output guardrails.