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
```

---

## Current Status

The project is in active development.

Implemented:

- basic FastAPI service
- CSV-based data input
- integration with OpenAI API

Planned:

- structured JSON output from AI
- API endpoints for uploading reviews
- integration with external review platforms
- report visualization

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
