# ScamShield (SATARK NETRA engine) - PS01 Cyber Fraud / Phishing / Malicious Apps
Rajasthan Police Hackathon 2026. One project: React frontend + FastAPI backend + SATARK NETRA analysis engine.

```
scamshield/
  frontend/                React + Vite portal (unchanged UI; only vite base and the heat-list filter list were adjusted)
  backend/
    app/
      main.py              FastAPI app, CORS, serves the built frontend
      api.py               all /api routes
      config.py  db.py  schemas.py
      services/
        core.py            loads the SATARK NETRA engine
        analysis.py        engine output -> UI shape, blacklist, case creation (message / url / website / apk / store link)
        fetcher.py         safe page download (blocks private addresses)
        similarity.py      repeat-campaign detection (TF-IDF cosine)
        reports.py         PDF + HTML case report
        assistant.py       "Ask AI" investigation assistant (LLM optional, rule-based fallback)
    satark_core/           YOUR model + analyzers (message_model_v3.pkl, url_features, website_analyzer, apk_analyzer ...)
    samples/               safe test APKs
    scripts/               seed_demo.py, selftest.py
    static/                put the built frontend here
```

## 1. Set up the backend (Python 3.11+ recommended)
```bash
cd scamshield/backend
python -m venv venv
# Windows:        venv\Scripts\activate
# macOS / Linux:  source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env          # Windows: copy .env.example .env   (set DEEP_CHECKS=0 if you are offline)
python scripts/selftest.py    # must end with "25 passed, 0 failed"
python scripts/seed_demo.py --reset     # synthetic demo cases (optional but recommended for the demo)
uvicorn app.main:app --reload --port 8000
```
API docs: http://localhost:8000/docs

If `pip` cannot install scikit-learn 1.9.1, install the newest one and re-create the model file:
`cd satark_core && python train_message_model.py` (it overwrites `message_model_v3.pkl`).

## 2. Run the frontend
Development (hot reload):
```bash
cd scamshield/frontend
npm install
npm run dev            # http://localhost:5173  (proxies /api to :8000)
```
Single-server demo / deployment:
```bash
npm run build
# copy everything inside frontend/dist into backend/static  (so backend/static/index.html and backend/static/assets/ exist)
# Windows: xcopy dist\* ..\backend\static\ /E /Y      macOS/Linux: cp -r dist/* ../backend/static/
cd ../backend && uvicorn app.main:app --port 8000      # open http://localhost:8000
```
Login/sign-up in the UI is still the frontend-only mock (localStorage). Any email + password works for a demo.

## 3. API (what the React app calls)
| Method | Path | Purpose |
|---|---|---|
| POST | /api/analyze/message `{text, reporter, channel}` | SMS / WhatsApp / email / social text |
| POST | /api/analyze/url `{url, reporter}` | link: rules + live domain age, redirects, SSL |
| POST | /api/analyze/website `{url}` or `{html}` | Ponzi / MLM / betting / credential-form analysis |
| POST | /api/analyze/apk (multipart `file`) | static APK analysis (permissions, URLs, IPs, cert, known-bad match) |
| POST | /api/analyze/store-link (form `link`) | Play Store listing |
| GET | /api/check?url= | fast warn-before-open (browser extension / bot) |
| GET | /api/cases?q&level&kind, /api/cases/{id}, /links, /similar, /report?format=pdf\|html\|json | case register |
| GET | /api/heatlist?type=, /api/graph, /api/stats | heat-list and linked identifiers |
| POST | /api/assistant `{question, case_id}` | investigation assistant |

Every analysis returns: `case_id, kind, level (Low/Medium/High), score (0-1), verdict, advice, indicators[{explanation, category, source, weight, evidence}], identifiers{}, info{}`.

## 4. PS01 requirement coverage
| Requirement | Where |
|---|---|
| Message / URL risk level with reasons | `analysis.analyze_message / analyze_url` (classifier + rules) |
| SMS, email, WhatsApp, social text; urgency, impersonation, fake KYC | `engine.MSG_RULES` + model, channel stored per case |
| Look-alike domains, domain age, redirects, HTTPS, blacklist | `url_features`, `live_checks()`, heat-list blacklist (+20) |
| APK permissions, URLs/IPs, package metadata, known-bad comparison | `apk_analyzer`, `known_bad_apps.json` |
| Website promises / MLM / betting, hosting, UPI-bank-phone-crypto extraction | `website_analyzer`, resolved IP + reverse DNS in details |
| Low / Medium / High with triggered indicators; warn before opening | result panel, `/api/check`, Link safety page |
| Searchable history, linked domains/apps/phones/payment IDs | `/api/cases`, `/api/cases/{id}/links`, `/api/graph` |
| Repeat-content similarity | `similarity.py` |
| Evidence snapshot + downloadable report | SHA-256 in case, PDF / HTML report |
| Citizens and officers submit; heat-list | Report page, `/api/heatlist` |
| Out of scope (not built on purpose) | dynamic sandbox, takedown, private data |

## 5. Honest limits (say these to the judges)
- The message model is trained on SYNTHETIC data: scam-vs-genuine about 89% with whole templates held out (see satark_core). Retrain with the R4C sample set: put rows in `satark_core/messages_synthetic.csv` (text,label,template) and run `python train_message_model.py`.
- URL, APK and website checks are rule based and were tested on small hand-made sets.
- Live checks need internet (RDAP, redirects, SSL). Offline they are skipped and the details table says so.
- `known_bad_apps.json` holds one sample entry. Add real packages or cert hashes.
- No server-side login yet; do not expose this publicly without adding auth.

## 6. Optional LLM assistant
Set `ANTHROPIC_API_KEY` in `backend/.env`. The assistant then writes answers from case records only and cites case numbers. Without a key, a rule-based assistant answers from the same records.

## 7. Demo flow (3 minutes)
1. Analyse tab: paste the SBI KYC SMS -> High, indicators with evidence. 2. Link safety: `http://sbi-kyc-update.top/login` -> blocked page.
3. Analyse -> Android app: upload `backend/samples/test_loan.apk`. 4. Case register -> open a case -> linked cases, similar content, PDF report.
5. Heat-list and Linked identifiers: the same phone and UPI ID across SMS, website and app. 6. Ask AI about the case.
