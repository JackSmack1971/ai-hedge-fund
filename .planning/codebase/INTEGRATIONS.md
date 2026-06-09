# External Integrations

**Analysis Date:** 2026-06-09

## APIs & External Services

**Financial Data:**
- Financial Datasets API (`https://api.financialdatasets.ai`) - Retrieves historical prices, financial statements/metrics, search line items, insider transactions, company news, and market cap.
  - SDK/Client: `requests` HTTP client with full-jitter exponential backoff retry handler for 429 rate limit responses.
  - Auth: API key sent via header `X-API-KEY` populated from `FINANCIAL_DATASETS_API_KEY` environment variable.

**Language Models:**
- OpenAI API - Runs GPT models (e.g., `gpt-4o`, `gpt-4o-mini`).
  - Client: `ChatOpenAI` from `langchain_openai`.
  - Auth: `OPENAI_API_KEY` (and optional base URL `OPENAI_API_BASE`).
- Anthropic API - Runs Claude models (e.g., `claude-3-5-sonnet-latest`).
  - Client: `ChatAnthropic` from `langchain_anthropic`.
  - Auth: `ANTHROPIC_API_KEY`.
- Google Generative AI - Runs Gemini models.
  - Client: `ChatGoogleGenerativeAI` from `langchain_google_genai`.
  - Auth: `GOOGLE_API_KEY`.
- Groq Cloud - Runs fast open-weights models (e.g., Llama).
  - Client: `ChatGroq` from `langchain_groq`.
  - Auth: `GROQ_API_KEY`.
- DeepSeek API - Runs DeepSeek chat models.
  - Client: `ChatDeepSeek` from `langchain_deepseek`.
  - Auth: `DEEPSEEK_API_KEY`.
- xAI API - Runs Grok models.
  - Client: `ChatXAI` from `langchain_xai`.
  - Auth: `XAI_API_KEY`.
- Azure OpenAI - Enterprise deployment of OpenAI models.
  - Client: `AzureChatOpenAI` from `langchain_openai`.
  - Auth: `AZURE_OPENAI_API_KEY`, endpoint `AZURE_OPENAI_ENDPOINT`, and deployment `AZURE_OPENAI_DEPLOYMENT_NAME`.
- OpenRouter API - Proxy client accessing multiple external models.
  - Client: `ChatOpenAI` with base URL `https://openrouter.ai/api/v1`.
  - Auth: `OPENROUTER_API_KEY`, site URL `YOUR_SITE_URL`, name `YOUR_SITE_NAME`.
- GigaChat API - Accesses GigaChat models.
  - Client: `GigaChat` from `langchain_gigachat`.
  - Auth: `GIGACHAT_API_KEY` (or credentials `GIGACHAT_CREDENTIALS`).
- Local Ollama Service - Local LLM server running on host.
  - Client: `ChatOllama` from `langchain_ollama`.
  - Endpoint: `http://localhost:11434` (configurable via `OLLAMA_HOST` and `OLLAMA_BASE_URL`).

## Data Storage

**Primary Database:**
- SQLite database (`app/backend/hedge_fund.db`) - Stores React Flow layout configurations, runs, and user API keys.
  - Connection: via `DATABASE_URL` (defaults to local file path).
  - ORM Client: SQLAlchemy ORM.
  - WAL Mode tuning: Event listener on connect triggers `journal_mode=WAL`, `synchronous=NORMAL`, and `cache_size=-64000` (64MB) for high concurrent reliability.
  - Migrations: Alembic files in `app/backend/alembic/`.

**In-Memory Caching:**
- Run Cache (`src/data/cache.py`) - Key-value structure storing ticker-keyed arrays of prices, metrics, insider trades, and news to bypass redundant external API requests.

**Task Queues & Brokers:**
- Redis - Message broker for async Celery task execution.
  - Connection: via `REDIS_URL` (defaults to `redis://localhost:6379/0`).
  - Client: Celery Redis backend.

## Authentication & Identity

**API Protection:**
- `BACKEND_API_TOKEN` - Static secret key validated on backend endpoints to secure API access.
- `DATABASE_ENCRYPTION_KEY` - Symmetric key used by `Cryptography` library to encrypt/decrypt stored API keys in the SQLite database.

## CI/CD & Deployment

**CI Pipeline:**
- GitHub Actions - Automates backend Python test runs (with Matrix 3.11/3.12), black/isort/flake8 checks, Mypy type-checking, bandit security scans, and frontend npm build/lint.
  - Workflow: `.github/workflows/test.yml`

---

*Integration audit: 2026-06-09*
*Update when adding/removing external services*
