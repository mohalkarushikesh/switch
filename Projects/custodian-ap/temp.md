Open Router: 
Cloud service
, Routes to external model providers
, Managed by OpenRouter


Lite LLM: 
Self-hosted gateway
Routes to OpenAI, Azure, Gemini, Ollama,
vLLM, OpenRouter, Anthropic, etc.

-vLLM is an open-source high-performance LLM serving engine designed to run and serve Large Language Models efficiently in production.

Key Features:
- Fast Inference: Optimized for high request throughput and low latency.
- PagedAttention: Efficient memory management for serving large models.
- OpenAI-Compatible API: Can expose local models through OpenAI-style endpoints.
- Multi-GPU Support: Scales across multiple GPUs for large deployments.

- One-line summary:
vLLM is the "high-performance runtime/server" that hosts and serves LLMs efficiently.

#### Dockerfile : Defines HOW to build a single container image (Application, Frontend, Backend, etc.)

ex:
``` 
FROM node:20
COPY . .
RUN npm install
CMD ["npm", "start"]
``` 

#### Docker Compose: Defines WHICH containers run together and HOW they communicate
ex: 
```
services:
frontend:
build: .
 
backend:
build: ./api
 
postgres:
image: postgres
```

- docker.yml → Defines how to **build and run a single Docker container**.
- docker-compose.yml → Defines and **manages multiple application services** (app, frontend, backend, etc.) together.
- docker-compose-infra.yml → Defines **supporting infrastructure services** like databases, Redis, Prometheus, Grafana, Kafka, etc. separately from the application.