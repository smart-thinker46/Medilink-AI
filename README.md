# Medilink AI Platform (Phase 2 retrieval)

Private, hospital-hosted, advisory-only AI for Medilink HMIS. No external AI API is ever called.

## What is built
| Piece | File | Rule it enforces |
|---|---|---|
| AI Gateway | `gateway.py` | authz -> safety -> context -> model -> validation -> audit, for every request |
| Local inference client | `llm.py` | refuses any endpoint that is not loopback / private IP / allow-listed host |
| Authorization adapter | `authz.py` | AI inherits Medilink permissions + care-team check; no own DB account |
| Context builder | `context.py` | purpose-limited, identifiers stripped, every fact numbered `[S#]` with a source record ref |
| Safety engine | `safety.py` | refuses command-style requests; blocks uncited, fake-cited or directive/diagnostic output |
| Audit trail | `audit.py` | AI_REQUEST / AI_OUTPUT / HUMAN_ACTION, hash-chained, tamper-evident |
| Knowledge assistant | `rag.py` | answers only from approved docs, cites doc + version, says "not found" otherwise |
| Phase 1 analytics | `analytics.py` | duplicate patients, queue forecast, revenue leakage, discount outliers, feedback themes |
| Medilink identity bridge | `backend.py` | forwards the caller's Medilink bearer token; no AI service account or database credentials |
| Backend reader | `backend.py` | read-only, purpose-limited patient context through the existing patient API |
| Operational controls | `rate_limit.py`, `app.py` | per-user request cap, transcript size cap, health endpoint and audit events for analytics |
| AI contracts and router | `contracts.py`, `router.py` | standard task, priority and route decisions; deterministic work is never sent to an LLM |
| Knowledge access filter | `rag.py` | optional document `allowed_roles` and `facility_id` metadata are enforced before retrieval |
| Hybrid retrieval | `rag.py`, `knowledge/embeddings.py` | BM25-style keyword ranking plus deterministic local semantic similarity; no external embedding calls |
| Evidence contract | `knowledge/grounding.py`, `knowledge/retrieval.py` | authorized chunks carry document/version/source metadata and are supplied as evidence, never executable instructions |
| PostgreSQL/pgvector schema | `sql/001_knowledge_pgvector.sql` | isolated document/chunk tables with vector(256) and HNSW index for an on-premise persistent store |
| Optional pgvector adapter | `knowledge/pgvector.py` | dependency-injected retrieval against the HMIS PostgreSQL database |

Phase 1 capabilities: patient summary, documentation draft, knowledge assistant, duplicate detection,
queue intelligence, revenue leakage / billing anomalies, feedback intelligence.

The gateway has **no write path** into any Medilink module. `HMISReader` is read-only; a human
"accepted/edited/rejected" decision is only recorded in the audit log, and saving to the EMR remains the
domain module's job.

## Run
On Debian/Parrot, use a virtual environment; do not use `--break-system-packages`.

    python3 -m venv .venv
    .venv/bin/python -m pip install -r requirements.txt
    .venv/bin/python -m pytest -q
    MEDILINK_MOCK_LLM=1 .venv/bin/uvicorn medilink_ai.app:create_app --factory --port 8088
    curl -H "X-User-Id: dr.amina" localhost:8088/v1/summary/P123

## PostgreSQL foundation (Step 5.1)

The database layer is optional and lazy-loaded, so the existing JSON retrieval
path still works when database dependencies or `DATABASE_URL` are absent. To
enable it, install the added SQLAlchemy/psycopg/pgvector dependencies inside
the virtual environment, copy `.env.example` to `.env`, set `DATABASE_URL`,
then run `pytest -q tests/db`. The database checks are skipped intentionally
when no URL is configured.

## Local Ollama setup (Step 2)

The default local runtime is Ollama's native API. In a separate terminal, start
Ollama and install the initial CPU-friendly model once:

    ollama serve
    ollama pull qwen2.5:0.5b
    curl -sS http://127.0.0.1:11434/api/tags

Start the gateway with the same model name:

    export MEDILINK_LLM_URL=http://127.0.0.1:11434
    export MEDILINK_LLM_MODEL=qwen2.5:0.5b
    export MEDILINK_LLM_PROTOCOL=ollama
    .venv/bin/uvicorn medilink_ai.app:create_app --factory --port 8088

The gateway calls Ollama's `/api/chat` endpoint with non-streaming output and
bounded context, generation length, and CPU thread count. It returns a safe
`unavailable` result if Ollama is stopped or cannot complete a response.

For vLLM or llama.cpp, set `MEDILINK_LLM_PROTOCOL=openai-compatible` and use an
OpenAI-compatible `/v1/chat/completions` endpoint. All model endpoints must be
loopback, private-network addresses, or explicitly allow-listed; public AI APIs
are rejected.

## Production Medilink integration
Set `MEDILINK_AUTH_MODE=medilink`, `MEDILINK_BACKEND_URL` to the private Medilink API address,
and optionally `MEDILINK_BACKEND_ALLOWED_HOSTS` for a private DNS name. The gateway requires a
normal `Authorization: Bearer <Medilink JWT>` header and uses `/security/access/me` plus
`/patients/:id`; it does not validate a copied JWT secret, connect to PostgreSQL, or hold a
privileged AI account. Patient visibility is therefore enforced by Medilink itself.

Production requests should be made with the logged-in user's bearer token. Configure dedicated
`ai.*` permissions in Medilink RBAC as they become available; current role mappings are a
conservative compatibility fallback and should not be treated as a replacement for RBAC grants.

Every successful AI response includes model version, evidence count, source references and an
evidence-strength label. Generated clinical text is not duplicated in the audit database: audit
entries retain its SHA-256 digest and length instead.

Approved Markdown knowledge documents may include metadata in their first 20 lines:

    version: 3.2
    allowed_roles: doctor,nurse
    facility_id: facility-uuid   # optional; omit for all facilities
    classification: INTERNAL

Documents without `allowed_roles` are available to authenticated users. Restricted documents
must always declare their roles and, where relevant, a facility.

## Before any clinical use
1. Configure the production Medilink identity bridge described above and validate it with role and patient-visibility tests.
2. Choose the model by evaluating candidates on your hardware with clinician-written test cases
   (summary accuracy, hallucination rate, English/Kiswahili) - not by leaderboard.
3. Replace the sample policies in `knowledge/` with approved ones.
4. The regex safety layer is a backstop, not the main control. Add clinical safety review and a red-team test set.
5. Queue forecast is a simple formula; swap in a validated learned model once you have hospital history.
6. Add backend-owned, read-only adapters for orders, results, encounters, billing, queues, feedback and incidents before enabling their AI capabilities.
7. Complete DPIA, lawful basis, encrypted audit retention/backups, incident response, model approval/rollback and clinical governance review.

## Step 5: persistent semantic retrieval

The default development store is the atomic JSON file under `data/knowledge/processed`.
For production, review and apply the isolated schema to the private HMIS PostgreSQL database
(the `vector` extension must be enabled in that database):

    psql "$DATABASE_URL" -f sql/001_knowledge_pgvector.sql

`knowledge/pgvector.py` provides a database adapter through a deployment-owned connection
factory. It applies organization, facility, department, role/user, classification, and effective
date filters before returning evidence. Do not add a second database password to the AI service;
reuse the protected deployment secret and keep the adapter read-only unless a separately reviewed
ingestion worker is enabled.

### Step 5.2 schema initialization

The ORM mappings in `knowledge/db_models.py` match the existing `ai_knowledge_documents` and
`ai_knowledge_chunks` schema and use the same 256-dimensional embedding contract as the local
embedder. After installing the database dependencies and configuring `.env`, initialize or verify
the schema with:

    .venv/bin/python -m medilink_ai.db.init_db
    .venv/bin/pytest -q tests/db

The JSON retrieval store remains available during this migration checkpoint; it is not deleted or
silently replaced.

The built-in hashing embedder is deterministic and offline. It is a retrieval fallback, not a
clinical model. A locally hosted embedding service can replace `EmbeddingService` without
changing authorization, evidence, citation, or no-evidence behavior.

### Step 5.3 embedding service

`knowledge/embeddings.py` now exposes a cached, replaceable provider interface. The default
`hashing` backend is offline and matches the current `vector(256)` schema, so it works on the
CPU-only development machine without downloading a model. The optional Sentence Transformers
backend can be enabled after installation and model provisioning:

    MEDILINK_EMBEDDING_BACKEND=sentence-transformers
    MEDILINK_EMBEDDING_MODEL=sentence-transformers/all-MiniLM-L6-v2
    MEDILINK_EMBEDDING_DIMENSION=384

The configured dimension must match the PostgreSQL vector column. Changing from the default 256
dimension requires a reviewed schema migration and re-embedding the existing corpus; the service
fails fast instead of silently writing incompatible vectors.

Benchmark the active provider with:

    .venv/bin/python tests/knowledge/benchmark_embeddings.py

### Step 5.4 vector search

The PostgreSQL path now includes a repository boundary, embedding-at-ingestion service,
pgvector similarity search, and an authorization-aware search wrapper:

- `knowledge/repository.py` owns persistence operations.
- `knowledge/vector_ingestion.py` embeds prepared chunks once and stores their vectors.
- `knowledge/vector_search.py` ranks stored chunks by cosine similarity.
- `knowledge/authorized_vector_search.py` applies organization, facility, department, role,
  user, classification, and effective-date checks before returning evidence.

Vector similarity is never treated as authorization. The public API continues using the JSON
retrieval path until the PostgreSQL store is explicitly enabled and evaluated.

### Step 5.5 hybrid retrieval

The PostgreSQL retrieval path now supports exact HMIS terminology and semantic matching together:

- `knowledge/keyword_search.py` performs PostgreSQL full-text search over document titles and chunk content.
- `knowledge/vector_search.py` performs pgvector cosine similarity search.
- `knowledge/hybrid_search.py` filters both candidate pools with the Medilink access context, then combines their ranks with Reciprocal Rank Fusion (`k=60`).
- `knowledge/hybrid_schemas.py` exposes ranking evidence without accepting organization, facility, or role values from the client.

The authorized endpoint is:

    POST /v1/knowledge/hybrid-search
    {"query":"How do we prevent duplicate patient registration?","top_k":5}

It requires the normal Medilink bearer token and returns `keyword_rank`, `vector_rank`, and
`hybrid_score` for every source. The JSON retrieval endpoint remains available as the development
fallback; hybrid retrieval uses the configured PostgreSQL/pgvector database explicitly.

### Step 5.6 reranking and evidence assembly

The hybrid candidate pool now passes through a CPU-friendly second-stage reranker and a separate
evidence assembler:

- `knowledge/database_filters.py` applies tenant, facility, department, classification, role/user, and effective-date constraints in the SQL statement.
- `knowledge/reranking.py` and `knowledge/local_reranker.py` combine RRF with deterministic query-term, phrase, title, and identifier signals.
- `knowledge/retrieval_pipeline.py` coordinates authorized hybrid retrieval and reranking.
- `knowledge/evidence_assembler.py` deduplicates content, preserves source/version metadata, assigns `[S1]`-style citations, and enforces source and character limits.
- `knowledge/evidence_pipeline.py` provides the complete retrieval-to-evidence boundary without calling Ollama.

Raw chunk text is not returned by the hybrid search API. Evidence assembly remains a separate
server-side stage so prompt construction can enforce provenance and context limits before inference.

### Step 5.7 grounded LLM generation

The structured generation path is available through `POST /v1/knowledge/ask`. It uses the
authenticated Medilink context, database-filtered retrieval, reranking, bounded evidence assembly,
JSON-constrained Ollama generation, citation validation, and a supplementary high-risk safety check.
The model never receives database credentials or authorization fields from the client. If no
authorized evidence is found, the service returns `INSUFFICIENT_EVIDENCE` without calling Ollama.

Configure the local provider with `OLLAMA_BASE_URL`, `OLLAMA_CHAT_MODEL`, `OLLAMA_TIMEOUT_SECONDS`,
`OLLAMA_TEMPERATURE`, `OLLAMA_NUM_PREDICT`, and `OLLAMA_KEEP_ALIVE`; defaults target the local
`qwen2.5:0.5b` model.

### Step 5.8 evaluation and reliability

The evaluation package under `medilink_ai/evaluation/` provides versioned JSON cases, typed results,
retrieval/citation/keyword/authorization/safety metrics, latency percentiles, configurable evaluation
gates, and JSON/Markdown reports. The controlled dataset at
`tests/evaluation/datasets/knowledge_assistant_v1.json` contains synthetic hospital scenarios only;
it must not be replaced with patient data. Integrate `EvaluationRunner` with a model or assistant
adapter to compare configurations without weakening authorization or grounding checks.

Run the real assistant evaluation from the AI project root after configuring PostgreSQL and Ollama:

    # Use a separate database; never load fixtures into the live HMIS database.
    export MEDILINK_ENVIRONMENT=evaluation
    export OLLAMA_BASE_URL=http://127.0.0.1:11434
    export OLLAMA_CHAT_MODEL=qwen2.5:0.5b
    export OLLAMA_TIMEOUT_SECONDS=180
    .venv/bin/python -m medilink_ai.db.init_db
    .venv/bin/python -m medilink_ai.evaluation --load-fixtures \
      --fixture-path tests/evaluation/fixtures/knowledge_documents.json \
      --json-report evaluation-report.json \
      --markdown-report evaluation-report.md

The fixture flag is deliberately restricted to `MEDILINK_ENVIRONMENT=evaluation`. It inserts only
the controlled synthetic documents and is idempotent; it does not import patient data. If the
database is not isolated, omit `--load-fixtures` and point `DATABASE_URL` at an already prepared
evaluation database instead.

To run the evaluation against an already prepared evaluation database:

    .venv/bin/python -m medilink_ai.evaluation \
      --json-report evaluation-report.json \
      --markdown-report evaluation-report.md

Critical authorization or safety failures produce `BLOCKED` and a non-zero exit status regardless
of the aggregate pass rate.

#### Isolated evaluation database

Evaluation must not share the application knowledge database. Configure a separate
`EVALUATION_DATABASE_URL` (for example, the `medilink_ai_eval` database) alongside `DATABASE_URL`.
With PostgreSQL and pgvector available, initialize and load only synthetic fixtures with:

    export MEDILINK_ENVIRONMENT=evaluation
    .venv/bin/python -m medilink_ai.evaluation.load_fixtures

The command is guarded by the evaluation environment and uses the same ORM schema, embedding
service, authorization filters, retrieval pipeline, and evidence assembler as production. Running
`python -m medilink_ai.evaluation --load-fixtures` also selects the isolated session automatically.
Never set `EVALUATION_DATABASE_URL` to the live HMIS database.

To measure retrieval independently of Qwen/Ollama:

    .venv/bin/python -m medilink_ai.evaluation --retrieval-only --top-k 5

This runs the real authorized hybrid retrieval, reranker, and evidence assembler, then reports
document-level precision, recall, and reciprocal rank. It does not invoke a language model.
