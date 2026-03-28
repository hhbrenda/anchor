# AI Accountability Coach

A prototype web application to help you track goals with an AI coach.

## 📂 Project Structure
- `backend/`: FastAPI Python server (LLM and API).
- `frontend/`: Astro + React web application.

## 🚀 Setup & Run

### 1. Backend
Open a terminal in the `backend` folder:
```bash
cd backend
# Create virtual env (optional but recommended)
python -m venv venv
# Windows
.\venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Run Server
# (Make sure to set OPENAI_API_KEY in .env or environment if you want Real Mode)
# If no key is set, it defaults to MOCK MODE (free, deterministic).
uvicorn main:app --reload
```
Backend runs on `http://localhost:8000`.

### 2. Frontend
Open a new terminal in the `frontend` folder:
```bash
cd frontend
npm install
npm run dev
```
Frontend runs on `http://localhost:4321`.

## 🧪 Testing the Prototype
1. **Mock Mode**: Start backend without an API key. Go to the frontend.
2. **Chat**: Type "I want to run a marathon".
3. **Plan**: The AI should ask clarifying questions (in Mock mode, it might just be supportive or use the fallback plan immediately depending on logic). 
4. **Force Plan**: In the Chat panel, click "Force Create Plan" to see the structured task list (Mock Data).
5. **Tasks**: Go to "Plan" or "Tasks" tab. Edit tasks, mark them complete.
6. **Dashboard**: Check the Progress tab to see stats update.
7. **Settings**: Try "Delete All Data" to reset.

## 🛠️ Key Design Choices
- **Astro + React**: Selected for performance (Astro) and rich interactive UI (React).
- **FastAPI**: Lightweight, high-performance Python backend ideal for LLM wrapping.
- **LocalStorage**: Privacy-first approach. No database needed for this prototype; user data lives in the browser.
- **Mock Mode**: Ensures the app is testable without paying for API credits immediately.
