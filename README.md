# Cooky Backend

## Setup

1.  **Environment Variables**:
    Update `.env` with your credentials.
    
    ```
    SPOONACULAR_API_KEY=your_key
    DATABASE_URL=postgresql+asyncpg://postgres:1234@localhost:5432/cooky
    ```

2.  **Install Dependencies**:
    ```bash
    pip install -r requirements.txt
    ```

3.  **Database**:
    Ensure PostgreSQL is running.
    ```bash
    python app/scripts/init_db.py
    alembic revision --autogenerate -m "Initial"
    alembic upgrade head
    ```

## Run

```bash
python -m uvicorn app.main:app --reload
```

## How to Test

### Option 1: Swagger UI (Recommended)
Open your browser and verify via the interactive documentation:
[http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)

1.  Look for `POST /admin/spoonacular/import-recipe/{id}`.
2.  Click **Try it out**.
3.  Enter `654959` in `spoonacular_id`.
4.  Click **Execute**.

### Option 2: PowerShell
```powershell
Invoke-RestMethod -Method Post -Uri "http://127.0.0.1:8000/admin/spoonacular/import-recipe/654959"
```

> **Note**: This import will now also fetch detailed nutrition for each *new* ingredient found. This consumes additional Spoonacular API quota (1 call per new ingredient).

## Batch Translation

```bash
python app/scripts/run_translation_batch.py
```
