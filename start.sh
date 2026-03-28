#!/bin/bash

# Trap SIGINT to kill background processes when script exits
trap 'kill $(jobs -p)' SIGINT

# Start Backend
echo "Starting Backend..."
cd backend
# No venv activation as per request
uvicorn main:app --reload &
BACKEND_PID=$!
cd ..

# Start Frontend
echo "Starting Frontend..."
cd frontend
npm run dev -- --open &
FRONTEND_PID=$!
cd ..

echo "Application is running!"
echo "Backend: http://localhost:8000"
echo "Frontend: http://localhost:4321"
echo "Press Ctrl+C to stop."

wait $BACKEND_PID $FRONTEND_PID
