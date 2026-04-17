*Competitive Intelligence Insights Engine*
~ Blue Shield of California Capstone Project
Project Overview: Building an insights engine to extract competitive intelligence from unstructured data sources using NLP and Generative AI. Analyzing 24+ earnings call transcripts from three key competitors plus SEC filings, social media, and press releases to uncover product strategies, market positioning, and financial impact.

? Key Questions We're Answering

#Can analytical tools summarize/extract insights from unstructured data?
Earnings calls, SEC filings, social media, press releases

#Can insights be tied to financial performance or stock price?
Correlate competitor product announcements with stock price movements

#What competitor products/services are making an "impact" (creating buzz)?
Trend analysis across sources, sentiment tracking

#Can tools be packaged into an "insights engine" for reuse?
Modular, deployable pipeline for new competitor analyses

#What GenAI techniques improve insights?
LLM-powered summaries, trend detection, competitive positioning

# Blue Shield Competitor Insight Engine — Backend

RAG-powered search backend using **AWS Bedrock (Claude 3.5 Sonnet v2)** + **ChromaDB** + **FastAPI**.

## Project Structure

```
insight_engine/
├── main.py            # FastAPI app + all endpoints
├── rag_engine.py      # Embeddings, vector store, LLM generation
├── ingestion.py       # PDF, URL, and text ingestion
├── test_pipeline.py   # Quick smoke test
├── requirements.txt
└── .env.example       # Copy to .env and fill in your AWS keys
```

---

## Setup (5 minutes)

### 1. Install dependencies
```bash
cd insight_engine
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Configure AWS credentials
```bash
cp .env.example .env
# Edit .env and paste in your AWS keys from UCI
```

Your `.env` needs:
```
AWS_ACCESS_KEY_ID=AKIA...
AWS_SECRET_ACCESS_KEY=...
AWS_REGION=us-west-2
```

> **Important:** Make sure your AWS IAM user has `AmazonBedrockFullAccess` policy attached.
> Also enable **Claude 3.5 Sonnet v2** and **Amazon Titan Embeddings v2** in the AWS Bedrock console under "Model access".

### 3. Test the pipeline
```bash
python test_pipeline.py
```
This ingests 3 sample competitor plans and runs 3 test queries. If you see answers, everything works!

### 4. Start the API server
```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

API docs available at: http://localhost:8000/docs

---

## API Endpoints

### Search (main endpoint)
```bash
POST /search
{
  "query": "Which competitor has the lowest deductible?"
}
```
Response:
```json
{
  "answer": "Kaiser Permanente has no deductible...",
  "sources": ["Kaiser Permanente CA 2024 HMO"],
  "chunks_used": 5
}
```

### Ingest a PDF
```bash
curl -X POST http://localhost:8000/ingest/pdf \
  -F "file=@anthem_2024_plan.pdf" \
  -F "source_name=Anthem 2024 PPO Plan"
```

### Ingest a web page
```bash
POST /ingest/url
{
  "url": "https://www.anthem.com/ca/shop-plans",
  "source_name": "Anthem CA Plans Page"
}
```

### Ingest multiple URLs at once
```bash
POST /ingest/urls
{
  "urls": [
    "https://healthy.kaiserpermanente.org/california/plans",
    "https://www.uhc.com/health-insurance/individual-family-plans/california"
  ]
}
```

### Check vector store stats
```bash
GET /stats
```

---

## Connecting to Base44 Frontend

In your Base44 app, make API calls to your backend:

```javascript
// Example: call from Base44
const response = await fetch("http://localhost:8000/search", {
  method: "POST",
  headers: { "Content-Type": "application/json" },
  body: JSON.stringify({ query: searchInput }),
});
const data = await response.json();
// data.answer, data.sources
```

When deploying, replace `localhost:8000` with your server URL and add it to the CORS origins in `main.py`.

---

## Recommended Competitors to Ingest

| Competitor | Good data sources |
|---|---|
| Kaiser Permanente | healthy.kaiserpermanente.org/california |
| Anthem Blue Cross | anthem.com/ca |
| UnitedHealthcare | uhc.com/california |
| Cigna | cigna.com/california |
| Aetna | aetna.com/individuals-families |
| Health Net | healthnet.com |

---

## Deployment (optional)

To deploy on AWS EC2 or any Linux server:
```bash
pip install gunicorn
gunicorn main:app -w 4 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000
```

Or use a free tier on **Render.com** or **Railway.app** by pushing this folder as a repo.
