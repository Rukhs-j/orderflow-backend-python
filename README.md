# OrderFlow — Python

An order-management API demonstrating stock invariants, rollback, idempotent requests, cancellation and concurrent purchases.

This is the Python/FastAPI conversion of the Java portfolio project. It includes a browser UI, REST API, local persistence, sample inputs, tests and optional model integration where relevant.

## Implemented features

- Seeded products and integer-paise pricing.
- An explicit BEGIN IMMEDIATE transaction checks the idempotency key, reserves stock and creates the order atomically.
- Simulated failed/timeout payments roll back the reservation.
- Owner-scoped idempotency keys return the same order for a matching replay and reject conflicting reuse.
- Cancellation restores inventory exactly once; simultaneous requests cannot oversell the last item.

## Run the Windows-ready suite

If you downloaded **All-Python-Projects-Windows-Ready.zip**:

1. Extract the whole ZIP. Keep the shared **runtime** folder beside the five project folders.
2. Open **orderflow-backend**.
3. Double-click **start.bat**.
4. Wait for application startup, then open **http://localhost:8082**.
5. Keep the terminal open; press Ctrl+C to stop.

The Windows x64 suite includes a private Python 3.13.17 runtime and pinned dependencies. It does not modify your system Python or PATH, and the default demo does not need internet, a database server, Java, API keys or a model account.

## Run the individual source ZIP

Install **Python 3.11+**. The first dependency installation needs internet.

Windows: double-click **start.bat**. It creates .venv and installs requirements if a shared runtime is unavailable.

Manual setup:

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe run.py
```

macOS/Linux: run **sh start.sh**, or create a virtual environment and run python run.py yourself.

Interactive API documentation: **http://localhost:8082/docs**. The Swagger UI uses external CDN assets and may need internet; the main project UI and /openapi.json work without those assets.

To change the port in PowerShell:

```powershell
$env:PORT="9090"
.\start.bat
```

## Demo accounts

| User | Password | Role |
| --- | --- | --- |
| alice | demo-pass | Customer/user |
| bob | demo-pass | Separate customer/user |
| agent | demo-pass | Support engineer |
| admin | demo-pass | Administrator |

Start as **alice** in the UI. The API uses HTTP Basic authentication with a synthetic fixed demo password. PBKDF2 is used for comparison, but this is not production identity management.

## Try the project

1. Place a successful order as alice.
2. Replay with the same key and input: the same order ID returns without another stock change.
3. Change quantity but reuse the key: expect 409. Click New key for a new operation.
4. Choose payment failure or timeout: expect 422 and unchanged inventory.
5. Cancel twice: stock is restored only once.
6. Try buying the last-item monitor from two clients.

## API reference

All /api endpoints require authentication.

| Method | Route | Purpose |
| --- | --- | --- |
| GET | /api/products | Products, integer-paise price and stock |
| GET/POST | /api/orders | List/create orders |
| POST | /api/orders/{id}/cancel | Owner/staff cancellation |

Database-backed responses retain **UPPERCASE** keys to preserve the existing UI contract. AI responses use camelCase.

Example in PowerShell:

```powershell
$auth=[Convert]::ToBase64String([Text.Encoding]::ASCII.GetBytes("alice:demo-pass"))
$headers=@{Authorization="Basic $auth"}
$body='{"productId":1,"quantity":1,"requestKey":"demo-order-001","payment":"success"}'
Invoke-RestMethod -Uri "http://localhost:8082/api/orders" -Method Post -Headers $headers -ContentType "application/json" -Body $body
```

Creation returns 200. Input errors return 400, missing records 404, access violations 403, conflicts 409 and configured simulation failures 422/503. Requests declaring more than 256000 bytes are rejected with 413.

## Source code structure

```text
application.py       Routes and create_app factory
services.py          Project-specific models and business rules
core.py              SQLite, demo authentication, retrieval, Ollama adapter
factory.py           Lifespan, worker, errors and static UI
run.py               Application entry point
run_tests.py         Test entry point
requirements.txt     Pinned dependencies
static/              Browser UI; no npm build
tests/               pytest behavior and adapter tests
samples/             Synthetic example inputs
docs/                AI setup, conversion notes and verification
```

Stack: Python, FastAPI, Pydantic, SQLite, httpx, Uvicorn and pytest. Standard-library SQL is used directly; SQLAlchemy and LangChain are not dependencies.

## Data and configuration

Data is stored in **data/app.sqlite3**, with SQLite journal sidecar files as needed. Records survive restart.

To use a new database, stop the app and set DATABASE_PATH to a new filename. To reset, stop the app and rename data to data-backup. Never change database files while the process is running.

Supported environment variables:

| Variable | Default | Purpose |
| --- | --- | --- |
| HOST | 127.0.0.1 | Bind address |
| PORT | 8082 | HTTP port |
| DATABASE_PATH | data/app.sqlite3 | SQLite file |
| AI_MODE | demo | demo or ollama |
| WORKER_ENABLED | true | Enable SyncBridge worker |
| OLLAMA_BASE_URL | http://127.0.0.1:11434 | Local model endpoint |
| OLLAMA_CHAT_MODEL | llama3.2:3b | Installed chat model |
| OLLAMA_EMBED_MODEL | nomic-embed-text | Installed embedding model |

.env.example is a reference; it is not automatically loaded.

## GenAI behavior

This project's primary business workflow does not use a language model.

## Run tests

With an installed environment:

```powershell
.\.venv\Scripts\python.exe run_tests.py
```

From a project in the Windows-ready suite:

```powershell
..\runtime\python.exe run_tests.py
```

Tests use temporary databases, not your demo data. External model contracts use a mock transport. For the restricted preparation environment, a writable --basetemp under verification-local was supplied; ordinary local runs use pytest's temporary directory.

## Design notes and limitations

Payments are local simulations and no money moves. No cart, shipping, external gateway, real refunds, outbox or distributed transaction. SQLite serializes writers; it is appropriate for this local demo, not a high-throughput multi-node order system.

Read [Java to Python mapping](docs/JAVA_TO_PYTHON.md) for transaction and framework differences.

The app binds to loopback by default and is a learning implementation. Production deployment requires real identity management, TLS, an explicit CSRF/origin policy, migrations, monitoring, retention and deployment review. Generated content needs evaluation and human review.

## Extend it

Add order lines, a test payment gateway with durable payment states, reconciliation and an outbox.

## Add to GitHub

Suggested repository name: **orderflow-backend-python**.

Upload the source, tests, requirements, documentation, samples and workflow. Keep .venv, data, caches and real credentials out of Git. The shared Windows runtime belongs in a release bundle, not a source repository.

Suggested description: **An order-management API demonstrating stock invariants, rollback, idempotent requests, cancellation and concurrent purchases.**
