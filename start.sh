#!/bin/bash
# Start both backend (FastAPI) and frontend (Next.js) concurrently

cd "$(dirname "$0")"

echo "Starting CI Insights Engine..."

# Backend
echo "→ Starting FastAPI backend on :8000"
cd backend
pip install -r requirements.txt -q
uvicorn main:app --host 0.0.0.0 --port 8000 --reload &
BACKEND_PID=$!
cd ..

# Frontend
echo "→ Starting Next.js frontend on :3000"
cd frontend
npm install -q
npm run dev &
FRONTEND_PID=$!
cd ..

echo ""
echo "✓ Backend:  http://localhost:8000"
echo "✓ Frontend: http://localhost:3000"
echo ""
echo "Press Ctrl+C to stop both servers"

trap "kill $BACKEND_PID $FRONTEND_PID 2>/dev/null" EXIT
wait
