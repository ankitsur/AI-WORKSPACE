uvicorn app.main:app --reload
.venv\Scripts\Activate.ps1

## DynamoDB Local (Docker)

From the repo root (`AI-Workspace`):

```powershell
docker compose up -d
```

Create tables (once):

```powershell
cd backend
uv run python scripts/create_dynamodb_tables.py
```

Endpoint: `http://localhost:8000` (DynamoDB). The FastAPI app also defaults to port 8000 — run the API on another port if both run locally, e.g. `uvicorn app.main:app --reload --port 8001`, and set `DYNAMODB_ENDPOINT_URL=http://localhost:8000`.

Data directory: `../dynamodb-data` (bind-mounted into the container).

Stop DynamoDB (data is kept on disk):

```powershell
docker compose down
```