# SUDARSHAN frontend (React + Vite)
Dev:   `cd frontend && npm install && npm run dev`  (http://localhost:5173, proxies /api to FastAPI :8000)
Build: `npm run build`, then copy everything in `dist/` into `scamshield/static/`.
Backend: see ../README.md (`cd backend && uvicorn app.main:app --reload`).
- Login / sign-up is a frontend-only mock (`src/auth.js`, localStorage). Replace with server-side auth later; keep the function names.
- `src/api.js` is the only file calling the backend. `POST /api/assistant {question, case_id?} -> {answer, sources[]}` powers the Ask AI panel (add when the LLM is ready).
- `src/pages/About.jsx` holds the PS01 coverage matrix. Update statuses honestly as you build.


## Rajasthan government portal visual refresh
The authentication landing page uses the bundled `public/assets/rajasthan-cyber-bg.png` palace/cyber background and the custom ScamShield shield monogram in `src/components/BrandMark.jsx`. The authentication flow and existing app routes are retained.
