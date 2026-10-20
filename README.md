# CacheCraft

**Turn repeated work into a cache hit.** CacheCraft is a small FastAPI service that transforms paired strings, interleaves the results, and stores both reusable per-string transformations and content-addressed payloads. It is packaged for local development and Docker Compose deployment.

## Highlights

- Exact input repeats return the original payload ID.
- Repeated strings are transformed once and reused across payloads.
- Transformation keys include a version, so changing the transformation algorithm can safely invalidate old entries.
- PostgreSQL is the Compose default; SQLite works for a zero-setup local run and tests.
- Request validation, stable error codes, readiness/liveness checks, and a validated `cache-cli` client are included.

## Run with Docker Compose

```sh
cp .env.example .env
# Set a strong POSTGRES_PASSWORD in .env before deployment.
docker compose up --build
```

The API is available at `http://localhost:8000`; interactive API docs are at `/docs`. Set `API_PORT` to change the host port. Compose reads database credentials and service settings from `.env`. The named `postgres_data` volume keeps database data across container restarts.

For local development without Docker, install Python 3.11+ and run:

```sh
python -m venv .venv
. .venv/bin/activate
pip install -e '.[dev]'
cp .env.example .env
uvicorn app.main:app --reload
```

When running locally, the example environment uses `sqlite:///./cachecraft.db`. Use `DATABASE_URL` to point at another SQLAlchemy-supported database. Set `TRANSFORMER_DELAY_SECONDS` to simulate a slow external transformation.

## API

The API prefix defaults to `/api/v1` and can be changed with `API_PREFIX`.

```http
POST /api/v1/payload
Content-Type: application/json
```

```json
{
  "list_1": ["first string", "second string", "third string"],
  "list_2": ["other string", "another string", "last string"]
}
```

Response (`201 Created`):

```json
{"id":"<content-generated-id>","reused":false}
```

Submitting the same ordered lists again returns the same ID and `reused: true`. Read it with `GET /api/v1/payload/{id}`:

```json
{"output":"FIRST STRING, OTHER STRING, SECOND STRING, ANOTHER STRING, THIRD STRING, LAST STRING"}
```

Both lists must contain the same number of nonblank strings. Each list accepts up to 1,000 entries; each string accepts up to 10,000 characters. Errors use stable codes, for example `PAYLOAD_NOT_FOUND` and `INVALID_INPUT`.

## CLI

The installed `cache-cli` reads validated options through Pydantic Settings. Give exactly one input source (`--json` or `--input`); `-` means standard input/output. Repeated runs demonstrate server-side payload reuse. Output is one JSON object per line.

```sh
cache-cli --json '{"list_1":["hello"],"list_2":["world"]}' --repeat 3
cat request.json | cache-cli --input - --host http://localhost:8000 --output results.jsonl
cache-cli --help
```

Arguments: `--host` (server URL), `--repeat` (1–10,000), `--input` (JSON file or `-`), `--json` (JSON text), and `--output` (file or `-`).

## Configuration

Copy `.env.example` to `.env`. Settings are loaded from environment variables (which take precedence) and `.env`; Compose interpolates its environment from the same file.

| Variable | Purpose | Default |
|---|---|---|
| `APP_NAME` | API title | `CacheCraft API` |
| `APP_ENV` | Deployment environment label | `development` |
| `LOG_LEVEL` | Python log level | `INFO` |
| `DATABASE_URL` | SQLAlchemy connection URL | `sqlite:///./cachecraft.db` |
| `TRANSFORMER_DELAY_SECONDS` | Simulated upstream latency | `0` |
| `CACHE_TTL_SECONDS` | Expiry for transform cache rows; `0` disables expiry | `86400` |
| `CACHE_CLEANUP_INTERVAL_SECONDS` | Reserved cleanup cadence | `3600` |
| `API_PREFIX` | Versioned API prefix | `/api/v1` |
| `API_PORT` | Compose host port | `8000` |
| `POSTGRES_DB`, `POSTGRES_USER`, `POSTGRES_PASSWORD` | Compose database credentials | `cachecraft` |

Use a secrets manager or deployment secrets for production passwords; `.env` is ignored by git.

## Tests and quality checks

```sh
pytest
ruff check .
```

Tests use isolated in-memory SQLite and cover interleaving, identifier reuse, per-string transform reuse, validation, and missing IDs.

## Design notes

`app/api` owns HTTP behavior, `app/schemas` validates boundary data, `app/services` implements cache and transform policy, and `app/db` contains persistence. Error identifiers and client-facing messages live in `app/core/errors.py`. The transformation is an adapter (`app/services/transformer.py`) that can be replaced with an asynchronous provider integration.

For higher traffic, use a production migration tool (such as Alembic) instead of startup `create_all`, run multiple stateless API replicas behind a load balancer, and consider moving slow external transformation calls to a durable job queue. The unique cache key includes the transformation version; concurrent cache misses can still perform duplicate upstream work, so deployments with costly transformations should add a distributed per-key lock or a provider-backed idempotency mechanism.
