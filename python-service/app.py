from fastapi import FastAPI, HTTPException, BackgroundTasks
from pydantic import BaseModel
import json
import csv
import os
import uuid
from dotenv import load_dotenv
from openai import OpenAI
from collections import Counter
from pathlib import Path

# load .env
load_dotenv()

CSV_FILE_PATH = os.getenv("REVIEWS_CSV_PATH") or Path(__file__).resolve().parent.parent / "data" / "raw" / "reviews_sample.csv"
OPENAI_MODEL = "gpt-4.1-mini"
KEY_SENTIMENT = "sentiment"
KEY_TOPICS = "topics"
REQUIRED_COLUMNS = {"review_id", "review_text"}

# In-memory job store: maps job_id -> job status and results.
# For production, replace with a persistent store (e.g. Redis, database).
jobs: dict = {}

# init OpenAI
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

app = FastAPI()


class Review(BaseModel):
    review_id: str
    rating: int
    review_text: str


def analyze_with_ai(text: str):
    prompt = f"""
Analyze this clinic review.

Return ONLY valid JSON with this structure:

{{
  "sentiment": "positive | neutral | negative",
  "topics": ["topic1", "topic2"],
  "summary": "short summary",
  "priority": "low | medium | high",
  "recommended_action": "action text"
}}

Review:
{text}
"""

    response = client.chat.completions.create(
        model=OPENAI_MODEL,
        messages=[
            {"role": "user", "content": prompt}
        ]
    )

    raw_output = response.choices[0].message.content

    clean_output = raw_output.strip()
    clean_output = clean_output.replace("```json", "")
    clean_output = clean_output.replace("```", "")
    clean_output = clean_output.strip()

    try:
        parsed = json.loads(clean_output)
    except (json.JSONDecodeError, TypeError):
        # Log raw output server-side for debugging; do not expose it to the client
        print(f"Failed to parse AI output: {raw_output}")
        parsed = {"error": "Invalid JSON from AI"}

    return parsed


def process_csv_job(job_id: str):
    """
    Background task: reads the CSV and calls OpenAI for each row.
    Results are stored in the jobs dict under the given job_id.
    The client polls GET /jobs/{job_id} to check status and retrieve results.
    """
    try:
        csvfile_handle = open(CSV_FILE_PATH, newline="", encoding="utf-8")
    except FileNotFoundError:
        jobs[job_id] = {"status": "failed", "error": f"CSV file not found: {CSV_FILE_PATH}"}
        return

    results = []

    with csvfile_handle as csvfile:
        reader = csv.DictReader(csvfile)

        if not REQUIRED_COLUMNS.issubset(reader.fieldnames or []):
            # Use sorted() for a stable, client-friendly column list instead of Python set repr
            jobs[job_id] = {
                "status": "failed",
                "error": f"CSV must contain columns: {', '.join(sorted(REQUIRED_COLUMNS))}"
            }
            return

        for row in reader:
            analysis = analyze_with_ai(row["review_text"])
            results.append({
                "review_id": row["review_id"],
                "analysis": analysis
            })

    sentiment_counts = Counter(
        item["analysis"][KEY_SENTIMENT]
        for item in results
        if isinstance(item.get("analysis"), dict)
        and KEY_SENTIMENT in item["analysis"]
    )

    topics = []

    for item in results:
        analysis = item.get("analysis")
        if isinstance(analysis, dict) and KEY_TOPICS in analysis and isinstance(analysis[KEY_TOPICS], list):
            for topic in analysis[KEY_TOPICS]:
                if isinstance(topic, str):
                    normalized_topic = topic.strip()
                    if normalized_topic:
                        topics.append(normalized_topic)

    topic_counts = Counter(topics)

    # Store completed results so the client can retrieve them via GET /jobs/{job_id}
    jobs[job_id] = {
        "status": "done",
        "results": results,
        "sentiment_summary": dict(sentiment_counts),
        "top_topics": [
            {"topic": topic, "count": count}
            for topic, count in topic_counts.most_common()
        ]
    }


@app.get("/")
def read_root():
    return {"message": "API is working"}


@app.post("/analyze")
def analyze_review(review: Review):
    analysis = analyze_with_ai(review.review_text)

    return {
        "review_id": review.review_id,
        "analysis": analysis
    }


@app.post("/analyze-csv")
def analyze_csv(background_tasks: BackgroundTasks):
    """
    Starts CSV analysis as a background job.
    Returns job_id immediately — client should poll GET /jobs/{job_id} for results.
    """
    job_id = str(uuid.uuid4())

    # Mark job as processing before starting background task
    jobs[job_id] = {"status": "processing"}

    background_tasks.add_task(process_csv_job, job_id)

    return {"job_id": job_id, "status": "processing"}


@app.get("/jobs/{job_id}")
def get_job(job_id: str):
    """
    Returns the current status and results of a background job.
    Status values: "processing" | "done" | "failed"
    """
    job = jobs.get(job_id)

    if job is None:
        raise HTTPException(status_code=404, detail=f"Job not found: {job_id}")

    return job
