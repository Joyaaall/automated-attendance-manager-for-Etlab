# Etlab Attendance Manager

Unofficial student dashboard and API for compatible college portals hosted on `etlab.app` or `etlab.in`, adapted from the RIT Etlab Portal API by devadathanmb. It scrapes Etlab pages; installations with different markup may require parser updates.

## Student dashboard

Open `/`, enter your college Etlab address with or without `https://`, and then sign in using that portal's username and password. The backend validates the portal before credentials are accepted. No manual cookie entry is needed.

A four-step onboarding tutorial appears on every fresh visit and can be skipped immediately. Its completion is not tracked or stored. Creator support links point to `https://buymeacoffee.com/joyalaliyas` and open in a separate tab.

- Attendance: each subject's percentage, recorded hours, additional hours you can miss, or attended hours needed to reach your chosen target.
- My timetable: assign subjects per period or import Etlab's timetable, review unassigned slots, choose the lunch boundary, and save your custom week.
- Leave planner: compare full-day and after-lunch leave for the next 14 days. Select multiple dates to check their combined per-subject impact.

The 75% initial target is a calculator setting, not a verified college policy. Calculations use exact hour counts rather than rounded percentages. Each period is one attendance hour; repeated lab periods count separately. Missing future classes adds to conducted hours without adding present hours. Future attended classes are not assumed. Unknown slots or attendance block recommendations; holidays, special schedules, exemptions, and college permission rules must be checked separately.

Only timetable and target preferences persist in this browser, separately per portal, account, and semester. Passwords and session tokens are not saved by the app; refreshing requires selecting the portal and signing in again. On mobile, wide attendance/timetable tables scroll horizontally. See `docs/frontend-design.md` for design references and assumptions.

## Configuration

Legacy single-portal defaults in `config.py`:

- `BASE_URL`: `https://asiet.etlab.app` (no trailing slash)
- `COOKIE_KEY`: `ASIETSESSIONID`

`COOKIE_KEY` is the cookie **name**, not the cookie value and not `YII_CSRF_TOKEN`. These defaults preserve older raw-cookie API clients; dashboard logins discover the selected portal's session cookie and return a signed portal-bound token. No personal cookies or passwords belong in source code.

If `ETLAB_TOKEN_SECRET` is unset, the process generates a random secret at startup; Gunicorn preloads the app so all local workers share it. Set a long random deployment secret when tokens must survive restarts or when running multiple containers/replicas. `ETLAB_TOKEN_MAX_AGE` defaults to 43,200 seconds. Portal selection currently accepts HTTPS subdomains of `etlab.app` and `etlab.in`; HTTP, IP addresses, embedded credentials, custom ports, query strings, fragments, and unrelated domains are rejected.

## Run locally

Use Python 3.11 or 3.12 with these dependency pins. The original `rpds-py==0.10.6` dependency crashed under Python 3.14 during local verification.

```bash
python3.12 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

gunicorn --workers 2 --timeout 60 --bind 127.0.0.1:5000 run:app
```

If Ubuntu reports that `ensurepip` is unavailable, install the matching `python3.12-venv` package first. A working Python 3.12 `.venv` has already been prepared in this checkout.

- Dashboard: http://127.0.0.1:5000/
- Status: http://127.0.0.1:5000/api/status
- Swagger UI: http://127.0.0.1:5000/apidocs/
- OpenAPI/Swagger specification: http://127.0.0.1:5000/apispec_1.json

`python run.py` also runs the development server on port 5000. It is not intended for public deployment.

## Docker

```bash
docker compose up --build -d
curl http://127.0.0.1:5000/api/status
```

The container listens on port 8000; the current Compose configuration publishes it on **0.0.0.0:5000**, preserving the selected all-interface binding. Use the host's private/Tailscale address, not `0.0.0.0`, in your browser. Do not forward this port from your router; use loopback binding if network access is unnecessary. Local virtual environments, Git history, cookies, `.env` files, and development-only Node packages are excluded from the build context.

## Authentication

There are two ways to authenticate:

1. POST `portal_url`, `username`, and `password` as JSON to `/api/login`. Use the returned signed, time-limited, portal-bound `token` for subsequent requests.
2. Legacy ASIET-only clients may still use the current **value** of the configured `ASIETSESSIONID` cookie directly, without calling `/api/login`.

Send either `Authorization: ***` or `Authorization: Bearer ***`. Portal-bound tokens carry the validated portal origin, detected cookie name, and Etlab session value with an integrity signature and expiry. They are credentials: keep them out of storage, logs, source files, screenshots, and shell history.

Avoid putting real session values in source files, Git, screenshots, shell history, or shared logs. Example using a hidden shell prompt:

```bash
read -r -s -p 'ASIETSESSIONID: ' ETLAB_TOKEN; printf '\n'
curl -H "Authorization: Bearer $ETLAB_TOKEN" http://127.0.0.1:5000/api/profile
curl -H "Authorization: Bearer $ETLAB_TOKEN" 'http://127.0.0.1:5000/api/attendance?semester=5'
curl -H "Authorization: Bearer $ETLAB_TOKEN" http://127.0.0.1:5000/api/timetable
curl -H "Authorization: Bearer $ETLAB_TOKEN" 'http://127.0.0.1:5000/api/present?semester=5&month=9&year=2026'
curl -H "Authorization: Bearer $ETLAB_TOKEN" 'http://127.0.0.1:5000/api/absent?semester=5&month=9&year=2026'
unset ETLAB_TOKEN
```

A session cookie is a credential. If it has been shared, log out of Etlab and log back in, then use the new cookie value. `/api/logout` invalidates that Etlab session, including the browser session if the cookie came from your browser.

## Endpoints

| Method | Path | Parameters | Authentication |
| --- | --- | --- | --- |
| GET | `/api/status` | None | None |
| POST | `/api/portal/check` | JSON `portal_url` | None |
| POST | `/api/login` | JSON `portal_url`, `username`, `password` | None |
| GET | `/api/profile` | None | Session token |
| GET | `/api/semesters` | None | Session token |
| GET | `/api/attendance` | `semester` (1–8) | Session token |
| GET | `/api/subject-names` | `semester` (1–8) | Session token |
| GET | `/api/timetable` | None | Session token |
| GET | `/api/present` | `semester`, `month` (1–12), `year` | Session token |
| GET | `/api/absent` | `semester`, `month` (1–12), `year` | Session token |
| GET | `/api/logout` | None | Session token |

Attendance includes `total_present_hours`, `total_hours`, and `total_percentage`. The old misspelled `total_perecentage` remains as a compatibility alias.

Subject rows include `subject_name` when the attendance header supplies one. `/api/subject-names` supplements names from present/absent entries in the portal-selected month and the previous available month, using the requested semester. The dashboard loads these labels asynchronously, with the timetable as a fallback. It does not guess names from course codes; a subject with no supplied label or recent records can remain unnamed. Name lookup failures do not change attendance counts or eligibility.

Timetable keys are weekday names (`monday`, etc.), with `period-1` through the available periods. Names and teachers are extracted from Etlab's CSV export, preserving quoted multiline cells.

Missing/expired sessions return JSON with HTTP 401. Upstream network failures return 502 and timeouts return 504. Profile and monthly-attendance parser failures return 502. Missing semester data/timetable returns 404. Portal content still depends on the account's available records.

## Verification

```bash
.venv/bin/python -m unittest discover -s tests -v
.venv/bin/pip check
npm ci
npm test
# Start the Flask app on 127.0.0.1:5001 before browser tests:
# .venv/bin/flask --app run run --host 127.0.0.1 --port 5001 --no-debugger --no-reload
npx playwright install chromium
npm run test:browser
```

Tests use synthetic, non-personal HTML/CSV fixtures and mocked upstream HTTP responses. No real credentials are needed. The suite covers portal normalization, unsafe-address rejection, session-cookie detection, portal-bound routing, and tampered-token rejection.

Browser tests cover portal selection/errors, login/errors, per-subject budgets, cumulative full/afternoon plans, credential-storage checks, semester-switch failures, and mobile layout. Set `PLAYWRIGHT_CHROMIUM_EXECUTABLE_PATH` to an existing Chromium binary if Playwright's browser download is unavailable. Set `BROWSER_TEST_URL` to test another local instance (default `http://127.0.0.1:5001`). Node/Playwright are development-only; production serves the frontend directly from Flask. Successful login and parser compatibility still depend on the selected college's Etlab installation.

## Security and deployment

Keep this API local or behind private access such as an SSH tunnel/Tailscale. A public deployment needs HTTPS, login rate limiting, a strong `ETLAB_TOKEN_SECRET`, and an appropriate access policy. The portal allowlist deliberately prevents the server from becoming an arbitrary URL proxy. Do not expose Flask's debug server.

## License

GPL 3.0; see [LICENSE.md](./LICENSE.md). Original repository: https://github.com/devadathanmb/rit-etlab-api.
