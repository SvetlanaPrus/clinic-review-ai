from fastapi import FastAPI
from pydantic import BaseModel
import json
import csv
import os
from dotenv import load_dotenv
from openai import OpenAI

# load .env
load_dotenv()

# init OpenAI
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

app = FastAPI()


class Review(BaseModel):
    review_id: str
    rating: int
    review_text: str


@app.get("/")
def read_root():
    return {"message": "API is working"}


@app.post("/analyze")
def analyze_review(review: Review):
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
    {review.review_text}
    """

    response = client.chat.completions.create(
        model="gpt-4.1-mini",
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
    except:
        parsed = {"error": "Invalid JSON from AI", "raw": raw_output}

    return {
        "review_id": review.review_id,
        "analysis": parsed
}


@app.get("/analyze-csv")
def analyze_csv():
    results = []

    with open("../data/raw/reviews_sample.csv", newline="", encoding="utf-8") as csvfile:
        reader = csv.DictReader(csvfile)

        for row in reader:
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
            {row["review_text"]}
            """

            response = client.chat.completions.create(
                model="gpt-4.1-mini",
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
            except:
                parsed = {"error": "Invalid JSON from AI", "raw": raw_output}

            results.append({
                "review_id": row["review_id"],
                "analysis": parsed
            })

    return {"results": results}