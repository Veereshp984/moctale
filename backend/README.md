# Recommendation Engine Backend

This backend package implements a lightweight collaborative filtering recommendation service backed by TensorFlow. It covers data ingestion from interaction logs, model training, saved model management, and an inference API exposed via FastAPI.

## Project layout

```
backend/
  app/
    data/pipeline.py       # Ingestion + dataset preparation utilities
    model/train.py         # Training entrypoint and model builder
    model/recommender.py   # Runtime model + recommendation logic
    service/api.py         # FastAPI application exposing recommendations
  data/sample_interactions.jsonl  # Example training data
  models/latest/                   # Checked-in trained model artifacts
  tests/                           # pytest-based unit and smoke tests
  requirements.txt                 # Python dependencies
```

## Environment setup

The repository targets Python 3.12. Because the system Python is marked as externally managed (PEP 668), create a virtual environment before installing dependencies:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r backend/requirements.txt
```

## Data ingestion pipeline

`backend/app/data/pipeline.py` normalises raw interaction payloads (playlist additions, likes) into a weighted implicit-feedback dataset. It provides helpers to:

- Load JSON/JSONL interaction logs.
- Map string identifiers to contiguous integer indices suitable for embeddings.
- Generate positive/negative training samples with configurable negative sampling.
- Produce popularity scores and user histories used for fallback recommendations.

## Training the model

Use the training CLI to retrain the model from a new interaction log:

```bash
PYTHONPATH=backend python -m app.model.train \
  --data-path path/to/interactions.jsonl \
  --model-dir backend/models/latest \
  --embedding-dim 32 \
  --epochs 10 \
  --batch-size 256 \
  --learning-rate 0.001 \
  --num-negatives 4 \
  --seed 42
```

The script writes:

- `model.keras` – the trained Keras model in the specified directory.
- `metadata.json` – entity mappings, interaction summaries, and training metadata.

A small, pre-trained model using `backend/data/sample_interactions.jsonl` is checked in under `backend/models/latest/` for convenience.

## Running the API

Start the FastAPI service with Uvicorn:

```bash
PYTHONPATH=backend uvicorn app.service.api:app --reload --port 8000
```

By default the service reads the model from `backend/models/latest`. Override the location with the `RECOMMENDER_MODEL_DIR` environment variable.

### Endpoints

- `GET /health` – readiness probe.
- `GET /recommendations/{user_id}?limit=10` – returns personalised recommendations. If the user is unknown or insufficient personalised results are available, the service expands the response with popularity-based fallbacks and flags the response via `fallback_used`.
- `GET /discovery/movies/popular?limit=10&language=en-US&region=US` – fetches trending TMDb titles mapped to internal DTOs with caching for common requests.
- `GET /discovery/movies/search?query=tron&page=1&language=en-US` – proxies movie searches to TMDb while normalising the payload to the service schema.
- `GET /discovery/music/popular?limit=10&market=US` – surfaces Spotify new releases as curated music picks with caching and rate limit handling.
- `GET /discovery/music/search?query=ambient&limit=10&market=US` – performs Spotify track searches and returns streamlined music summaries.

### External provider credentials

Set the following environment variables before starting the API when the discovery endpoints are required:

- `TMDB_API_KEY` – server-side key for The Movie Database.
- `SPOTIFY_CLIENT_ID` / `SPOTIFY_CLIENT_SECRET` – Spotify application credentials used for the client credentials flow. Tokens are fetched and refreshed automatically.

## Testing

Pytest-based unit tests cover the data pipeline and provide a smoke test for the FastAPI endpoint:

```bash
PYTHONPATH=backend pytest backend/tests
```

The API smoke test trains a tiny in-memory model to guarantee the service wiring remains intact.
