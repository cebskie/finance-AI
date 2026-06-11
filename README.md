# AI Finance Document Validation System

A production-grade AI-powered finance workflow system for validating corporate payment documents using OCR, LLM extraction, confidence scoring, fallback orchestration, and human review.

---

# Features

## Document Processing

- PDF upload
- Page splitting
- OCR pipeline
- Image preprocessing
- Document segmentation
- Metadata generation

## AI Extraction

- OCR extraction
- LLM-based field extraction
- Configurable prompts
- Multi-model support
- Confidence scoring

## Validation

- Cross-document consistency checks
- Inconsistency flagging
- Human review workflows

## Finance Workflow

- Payment request creation
- Reimbursement workflow
- Cash advance workflow
- Approval management

---

# Tech Stack

## Frontend
- React.js
- TypeScript
- Tailwind CSS

## Backend
- FastAPI
- PostgreSQL
- Celery
- Redis

## AI/OCR
- Tesseract
- PaddleOCR
- OpenRouter

## Storage
- MinIO

---

# Project Structure

```txt
project-root/
│
├── AGENTS.md
├── README.md
├── docker-compose.yml
├── .env.example
├── docs/
│   ├── architecture.md
│   ├── roadmap.md
│   ├── workflow.md
│   ├── extraction-rules.md
│   ├── fallback-strategy.md
│   ├── prompts/
│   └── json-schema/
│
├── backend/
│   ├── app/
│   ├── tests/
│   └── requirements/
│
├── frontend/
│   ├── src/
│   └── public/
│
└── infrastructure/
````

---

# Initial Setup

## Backend

```bash
cd backend
python -m venv venv
pip install -r requirements/dev.txt
```

## Frontend

```bash
cd frontend
npm install
```

## Start Infrastructure

```bash
docker-compose up -d
```

---

# Development Workflow

1. Design architecture first
2. Implement one service at a time
3. Add tests immediately
4. Add structured logs
5. Add confidence scoring
6. Add retries/fallbacks
7. Add human review hooks