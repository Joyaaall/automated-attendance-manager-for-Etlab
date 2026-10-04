# Etlab Attendance Manager

Unofficial student dashboard and API for compatible college portals hosted on `etlab.app` or `etlab.in`, adapted from the RIT Etlab Portal API by devadathanmb. It scrapes Etlab pages; installations with different markup may require parser updates.

> [!IMPORTANT]
> This is an unofficial community project. It is not affiliated with, endorsed by, or operated by Etlab, APJ Abdul Kalam Technological University, or any college. Compatibility depends on the HTML and CSV structure exposed by each Etlab installation.

## Attribution and project origin

The API layer was adapted from **[RIT Etlab Portal API](https://github.com/devadathanmb/rit-etlab-api)** by [devadathanmb](https://github.com/devadathanmb). The upstream project provided the original Flask API and Etlab scraping foundation.

This modified version adds a multi-portal browser dashboard, portal validation, signed portal-bound sessions, automatic semester discovery, subject-name enrichment, attendance calculations, timetable management, leave planning, responsive layouts, expanded tests, and deployment hardening.

The project remains licensed under the **GNU General Public License v3.0**. Retain the upstream attribution and GPL license when redistributing a modified version, and provide the corresponding source as required by GPL-3.0.

## How it works

```text
Browser or API client
        |
        v
Attendance Manager (Flask + Gunicorn)
        |
        | Authenticated HTTPS requests
        v
Selected college Etlab portal
```

1. The user supplies a college Etlab address.
2. The server validates that it is an HTTPS subdomain of `etlab.app` or `etlab.in` and checks for a compatible login page.
3. Credentials are forwarded to the selected portal over HTTPS.
4. After login, the detected Etlab session cookie, its name, and the portal origin are wrapped in a signed, expiring token.
5. Protected API routes use that token to request and parse data from the selected portal.

The application does not include a user database. Signed tokens and raw Etlab cookies are still active credentials and must be protected like passwords.

## Student dashboard

Open `/`, enter your college Etlab address with or without `https://`, and then sign in using that portal's username and password. The backend validates the portal before credentials are accepted. No manual cookie entry is needed.

A four-step onboarding tutorial appears on every fresh visit and can be skipped immediately. Its completion is not tracked or stored. Creator support links point to `https://buymeacoffee.com/joyalaliyas` and open in a separate tab.

- Attendance: each subject's percentage, recorded hours, additional hours you can miss, or attended hours needed to reach your chosen target.
- My timetable: assign subjects per period or import Etlab's timetable, review unassigned slots, choose the lunch boundary, and save your custom week.
- Leave planner: compare full-day and after-lunch leave for the next 14 days. Select multiple dates to check their combined per-subject impact.

The 75% initial target is a calculator setting, not a verified college policy. Calculations use exact hour counts rather than rounded percentages. Each period is one attendance hour; repeated lab periods count separately. Missing future classes adds to conducted hours without adding present hours. Future attended classes are not assumed. Unknown slots or attendance block recommendations; holidays, special schedules, exemptions, and college permission rules must be checked separately.

Only timetable and target preferences persist in this browser, separately per portal, account, and semester. Passwords and session tokens are not saved by the app; refreshing requires selecting the portal and signing in again. On mobile, wide attendance/timetable tables scroll horizontally. See `docs/frontend-design.md` for design references and assumptions.

## Configuration

Configuration is read from environment variables:

| Variable | Required | Default | Purpose |
| --- | --- | --- | --- |
| `ETLAB_TOKEN_SECRET` | Strongly recommended | Random startup value | Signs portal-bound session tokens. Set the same stable value on every worker or replica. |
| `ETLAB_TOKEN_MAX_AGE` | No | `43200` | Maximum signed-token lifetime in seconds; the default is 12 hours. |
| `ETLAB_BASE_URL` | No | `https://asiet.etlab.app` | Legacy default portal used by raw-cookie clients. |
| `ETLAB_COOKIE_KEY` | No | `ASIETSESSIONID` | Legacy default session-cookie **name**, not its value. |

`COOKIE_KEY` is the cookie **name**, not the cookie value and not `YII_CSRF_TOKEN`. These defaults preserve older raw-cookie API clients; dashboard logins discover the selected portal's session cookie and return a signed portal-bound token. No personal cookies or passwords belong in source code.

If `ETLAB_TOKEN_SECRET` is unset, the process generates a random secret at startup; Gunicorn preloads the app so all local workers share it. Set a long random deployment secret when tokens must survive restarts or when running multiple containers/replicas. `ETLAB_TOKEN_MAX_AGE` defaults to 43,200 seconds. Portal selection currently accepts HTTPS subdomains of `etlab.app` and `etlab.in`; HTTP, IP addresses, embedded credentials, custom ports, query strings, fragments, and unrelated domains are rejected.

Generate a signing secret with:

```bash
python3 -c 'import secrets; print(secrets.token_urlsafe(48))'
```

Store the result in a protected `.env` file or deployment secret manager. Never commit it to Git.

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

### 1. Clone and enter the repository

```bash
git clone https://github.com/YOUR_GITHUB_USERNAME/rit-etlab-api.git
cd rit-etlab-api
```

### 2. Create a protected environment file

```bash
python3 -c 'import secrets; print("ETLAB_TOKEN_SECRET=" + secrets.token_urlsafe(48))' > .env
printf 'ETLAB_TOKEN_MAX_AGE=43200\n' >> .env
chmod 600 .env
```

The included `.gitignore` excludes `.env`.

### 3. Pass the environment to the container

Create `docker-compose.override.yml`:

```yaml
services:
  etlab-asiet:
    environment:
      ETLAB_TOKEN_SECRET: ${ETLAB_TOKEN_SECRET}
      ETLAB_TOKEN_MAX_AGE: ${ETLAB_TOKEN_MAX_AGE:-43200}
      ETLAB_BASE_URL: ${ETLAB_BASE_URL:-https://asiet.etlab.app}
      ETLAB_COOKIE_KEY: ${ETLAB_COOKIE_KEY:-ASIETSESSIONID}
```

Docker Compose reads `.env` for substitution; the override explicitly injects those values into the application container.

### 4. Build, start, and verify

```bash
docker compose up --build -d
docker compose ps
curl --fail http://127.0.0.1:5000/api/status
```

Expected response:

```json
{"message":"I am alive"}
```

The container listens on port `8000`; Compose publishes it as host port `5000`. Open:

- Dashboard: `http://HOST_ADDRESS:5000/`
- Status: `http://HOST_ADDRESS:5000/api/status`
- Swagger UI: `http://HOST_ADDRESS:5000/apidocs/`
- OpenAPI document: `http://HOST_ADDRESS:5000/apispec_1.json`

### 5. Logs, updates, and shutdown

```bash
# Follow logs
docker compose logs -f --tail=100

# Pull code changes and rebuild
git pull
docker compose up --build -d

# Stop and remove the container and Compose network
docker compose down
```

### Network exposure

The current Compose configuration publishes `0.0.0.0:5000`, which exposes the service on every host interface. Use the host's private/Tailscale address, not `0.0.0.0`, in your browser. Do not forward this port directly from your router.

For same-machine access only, change the port mapping in `docker-compose.yml` to:

```yaml
ports:
  - "127.0.0.1:5000:8000"
```

For remote personal access, prefer Tailscale, WireGuard, or an SSH tunnel. A public deployment should use HTTPS, an access policy, login rate limiting, request-size limits, monitoring, and regular dependency updates.

## Production service without Docker

Create a virtual environment and install the dependencies as described in **Run locally**, then create a protected environment file:

```bash
python3 -c 'import secrets; print("ETLAB_TOKEN_SECRET=" + secrets.token_urlsafe(48))' > .env
printf 'ETLAB_TOKEN_MAX_AGE=43200\n' >> .env
chmod 600 .env
```

Create `/etc/systemd/system/attendance-manager.service`, replacing `YOUR_USER` and paths as needed:

```ini
[Unit]
Description=Attendance Manager
After=network-online.target
Wants=network-online.target

[Service]
Type=simple
User=YOUR_USER
Group=YOUR_USER
WorkingDirectory=/home/YOUR_USER/rit-etlab-api
EnvironmentFile=/home/YOUR_USER/rit-etlab-api/.env
ExecStart=/home/YOUR_USER/rit-etlab-api/.venv/bin/gunicorn --workers 2 --preload --timeout 60 --bind 127.0.0.1:5000 run:app
Restart=on-failure
RestartSec=5
PrivateTmp=true
NoNewPrivileges=true

[Install]
WantedBy=multi-user.target
```

Enable and verify the service:

```bash
sudo systemctl daemon-reload
sudo systemctl enable --now attendance-manager
sudo systemctl status attendance-manager
curl --fail http://127.0.0.1:5000/api/status
```

View service logs with:

```bash
journalctl -u attendance-manager -f
```

Keep Gunicorn bound to loopback when using a reverse proxy. Add HTTPS before making the service public, and never expose Flask's development server.

## Authentication

There are two ways to authenticate:

1. POST `portal_url`, `username`, and `password` as JSON to `/api/login`. Use the returned signed, time-limited, portal-bound `token` for subsequent requests.
2. Legacy ASIET-only clients may still use the current **value** of the configured `ASIETSESSIONID` cookie directly, without calling `/api/login`.

Send either `Authorization: YOUR_TOKEN` or `Authorization: Bearer YOUR_TOKEN`. Portal-bound tokens carry the validated portal origin, detected cookie name, and Etlab session value with an integrity signature and expiry. They are credentials: keep them out of storage, logs, source files, screenshots, and shell history.

Avoid putting real session values in source files, Git, screenshots, shell history, or shared logs. Example using a hidden shell prompt:

```bash
read -r -s -p 'Signed Etlab token: ' ETLAB_TOKEN; printf '\n'
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
