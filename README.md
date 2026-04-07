# Clinic Review AI

Backend service for automated analysis of clinic reviews using AI.

---

## Overview

This project processes user reviews and converts them into structured insights.

It performs:

- sentiment classification (positive / neutral / negative)
- extraction of key topics (staff, pricing, waiting time, cleanliness, etc.)
- generation of summary reports

The system is designed as part of a data processing pipeline and can be integrated with external data sources.

---

## Architecture

```
Review Sources
   ↓
n8n (data collection & triggers)
   ↓
Python FastAPI service (AI processing)
   ↓
Reports
```

---

## Tech Stack

- Python
- FastAPI
- OpenAI API
- CSV data processing
- n8n (workflow automation)

---

## Project Structure

```
clinic-review-ai/
│
├── python-service/
│   └── app.py
│
├── data/
│   ├── raw/
│   └── processed/
│
├── reports/
│
├── requirements.txt
└── README.md
```

---

## Setup

Install dependencies:

```bash
pip install -r requirements.txt
```

Run the server:

```bash
uvicorn python-service.app:app --reload
```

---

## Environment Variables

Create a `.env` file:

```
OPENAI_API_KEY=your_api_key_here

# Optional: path to CSV file for /analyze-csv endpoint
# Defaults to data/raw/reviews_sample.csv relative to project root
# REVIEWS_CSV_PATH=/custom/path/to/reviews.csv
```

## Data Setup

The `/analyze-csv` endpoint requires a CSV file with the following columns:

- `review_id` — unique review identifier
- `review_text` — text of the review

By default the service looks for `data/raw/reviews_sample.csv`. This directory is not tracked in git, so you need to create it manually:

```bash
mkdir -p data/raw
# place your reviews_sample.csv inside data/raw/
```

Alternatively, set `REVIEWS_CSV_PATH` in `.env` to point to any CSV file.

## Using the /analyze endpoint

Analyzes a single review synchronously.

```
POST /analyze
```

Request body:

```json
{ "review_id": "123", "review_text": "Great service!", "rating": 5 }
```

Success response (`200`):

```json
{
  "review_id": "123",
  "analysis": {
    "sentiment": "positive",
    "topics": ["staff"],
    "summary": "Patient reported a great service experience and praised the staff.",
    "priority": "low",
    "recommended_action": "Share the positive feedback with the clinic team."
  }
}
```

Error response (`502`) — when the AI call or JSON parsing fails:

```json
{ "detail": "Invalid JSON from AI" }
```

---

## Using the /analyze-csv endpoint

CSV analysis runs as a background job. The flow is:

**1. Start the job:**

```
POST /analyze-csv
```

Response:

```json
{ "job_id": "abc-123", "status": "processing" }
```

**2. Poll for results:**

```
GET /jobs/abc-123
```

While processing:

```json
{
  "job_id": "abc-123",
  "status": "processing",
  "created_at": 1704067200.0
}
```

When done:

```json
{
  "job_id": "abc-123",
  "status": "done",
  "created_at": 1704067200.0,
  "sentiment_summary": {"positive": 5, "negative": 2, "neutral": 1},
  "top_topics": [{"topic": "staff", "count": 4}, ...],
  "overall_summary": "The clinic's main strengths are... However, patients consistently report..."
}
```

`overall_summary` is `null` when no usable review analyses were available, or when summary generation failed.

If failed:

```json
{
  "job_id": "abc-123",
  "status": "failed",
  "created_at": 1704067200.0,
  "error": "..."
}
```

**3. Fetch per-review results (paginated):**

```
GET /jobs/abc-123/results?page=1&limit=100
```

```json
{
  "job_id": "abc-123",
  "page": 1,
  "limit": 100,
  "total": 250,
  "pages": 3,
  "results": [...]
}
```

Jobs are kept in memory for status lookup. This in-memory store is **per-process**, so the current implementation is suitable only for a single-worker deployment. In a multi-worker `uvicorn`/`gunicorn` setup, `POST /analyze-csv` and subsequent `GET /jobs/{job_id}` requests may be routed to different workers, causing jobs to appear missing and return `404`. For production deployments with multiple workers or instances, a shared store such as Redis or a database is required. Cleanup is performed opportunistically during subsequent `POST /analyze-csv` requests rather than by a background timer. Long-running jobs in `processing` status may remain queryable for up to 2 hours before they are eligible for eviction.

---

## Current Status

The project is in active development.

Implemented:

- FastAPI service with `/analyze` and `/analyze-csv` endpoints
- structured JSON output from AI
- CSV-based data input with background job processing
- integration with OpenAI API
- paginated per-review results
- overall clinic summary generated after CSV analysis (`overall_summary` field)

Planned:

- integration with external review platforms
- report visualization
- authentication/authorization for API endpoints (the API currently has no auth layer — `overall_summary` and per-review data contain free-form patient text and should be protected before production use)

---

## Purpose

This project is part of a portfolio focused on:

- backend development with Python
- working with LLM APIs
- building data processing pipelines
- service integration

---

## Author

Svetlana Prus
