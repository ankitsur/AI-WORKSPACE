uvicorn app.main:app --reload
.venv\Scripts\Activate.ps1

## DynamoDB Local + Redis (Docker)

From the repo root (`AI-Workspace`):

```powershell
docker compose up -d
```

Create DynamoDB tables (once):

```powershell
cd backend
uv run python scripts/create_dynamodb_tables.py
```

- DynamoDB: `http://localhost:8001`
- Redis: `localhost:6379` (24h TTL on cached conversations)
- FastAPI: `http://localhost:8000`

Chat flow: Redis first for reads; DynamoDB persists each turn after the assistant reply finishes.