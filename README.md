# Project Hub — Academic Project Management & Showcase Platform

[![Python](https://img.shields.io/badge/Python-3.12-blue.svg)](https://www.python.org/)
[![Flask](https://img.shields.io/badge/Flask-3.0.3-green.svg)](https://flask.palletsprojects.com/)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-Supabase-336791.svg)](https://supabase.com/)
[![Tests](https://img.shields.io/badge/Tests-29%2F29%20Passing-brightgreen.svg)](https://github.com/mani-538/PROJECT_HUB/tree/rework/deployment-ready/tests)
[![Live Demo](https://img.shields.io/badge/Live%20Demo-Render-46E3B7.svg)](https://project-hub-mani.onrender.com)

> **Live Demo**: [https://project-hub-mani.onrender.com](https://project-hub-mani.onrender.com)
>
> ⚡ Free-tier hosting — first request may take up to 60 seconds to wake the server after inactivity.

---

## 📌 Problem Statement

Academic institutions routinely struggle with fragmented project coordination:

- Submissions and reports are scattered across email threads and shared drives.
- There is no systematic access control over who can view or download student work.
- Standard deployment platforms erase uploaded files on every container restart.
- Certificate issuance and administrative reporting are entirely manual.

**Project Hub** solves each of these with a single, secure, role-based web platform backed by a persistent PostgreSQL database and private object storage.

---

## 🎯 Who It's For

| User | Core Workflow |
| :--- | :--- |
| **Students** | Submit proposals, upload versioned project archives, collaborate with verified teammates, track queries, use offline assistants, and download signed PDF certificates. |
| **Administrators** | Moderate submissions, approve or reject projects, generate audit PDF reports, respond to student inquiries, issue certificates, and manage the public showcase. |

---

## 🏗️ Architecture

```
                     ┌──────────────────────────────────────────┐
                     │           Browser / Client               │
                     │  (HTML5, Vanilla CSS, Bootstrap Icons)   │
                     └───────────────────┬──────────────────────┘
                                         │ HTTPS + CSRF Token
                                         ▼
                     ┌──────────────────────────────────────────┐
                     │         WSGI Server (Gunicorn)           │
                     │          Flask Application               │
                     └───┬───────────────────────────────┬──────┘
                         │                               │
                         ▼                               ▼
       ┌─────────────────────────────┐   ┌──────────────────────────────┐
       │     Application Routes      │   │    Unified Storage Adapter   │
       │  routes/auth.py  (RBAC)     │   │       utils/storage.py       │
       │  routes/student.py          │   └───────────┬──────────────────┘
       │  routes/admin.py            │               │
       │  utils/csrf.py              │       ┌───────┴──────────┐
       └────────────┬────────────────┘       │                  │
                    │                   Local Disk        Supabase Storage
                    ▼                  (dev only)         (private bucket)
             SQLAlchemy ORM
                    │
       ┌────────────┴──────────────┐
       │                           │
  SQLite (dev)         PostgreSQL via Supabase
                       (Session Pooler, SSL)
```

### Technology Stack

| Layer | Technology |
| :--- | :--- |
| **Language / Runtime** | Python 3.12 |
| **Web Framework** | Flask 3.0.3 (Application Factory pattern) |
| **Authentication** | Flask-Login 0.6.3, Werkzeug password hashing |
| **Database ORM** | SQLAlchemy 2.0.48, Flask-SQLAlchemy 3.1.1 |
| **Database (cloud)** | PostgreSQL via Supabase Session Pooler (`sslmode=require`) |
| **Object Storage** | Supabase Storage — private bucket, REST API, authenticated download |
| **PDF Generation** | ReportLab 4.2.2 (certificates & system reports) |
| **CSRF Protection** | Custom `utils/csrf.py` — `hmac.compare_digest`, session-backed, same-origin only |
| **WSGI Server** | Gunicorn 23.0.0 |
| **Hosting** | Render (free tier) |

---

## 💡 Verified Features

> All features in this table were exercised in the live integration test run on 2026-10-15 against the deployed Render instance and Supabase cloud services.

| Module | Feature | Notes | Verified |
| :--- | :--- | :--- | :--- |
| **Auth** | Role-Based Access Control | Distinct student / admin portals; role escalation blocked | ✅ |
| **Auth** | Session Hardening | Blocked/inactive accounts invalidated on every request | ✅ |
| **Auth** | Redirect Protection | Open-redirect validation rejects external destinations | ✅ |
| **Auth** | Public Admin Signup Disabled | No route or form for self-service admin registration | ✅ |
| **Security** | CSRF Protection | `hmac.compare_digest` constant-time check on all POST/PATCH forms | ✅ |
| **Security** | File Authorization | Downloads restricted to project owner, verified team member, or admin | ✅ |
| **Security** | Filename Collision Prevention | UUID prefix ensures uniqueness; legacy filenames remain accessible | ✅ |
| **Security** | Destructive Safeguards | Account deletion disabled in trial mode (`DISABLE_DESTRUCTIVE_ADMIN=true`) | ✅ |
| **Security** | No Hardcoded Secrets | `SECRET_KEY` required from environment; app refuses to start without it | ✅ |
| **Projects** | Submission | Proposals with category, domain, tech stack, and file attachments | ✅ |
| **Projects** | Versioned Updates | Iterative uploads with notes and changelog history | ✅ |
| **Projects** | Team Collaboration | Teammates linked by authenticated user ID (not unverified email) | ✅ |
| **Moderation** | Approval Workflow | Admin approve/reject with notes and grading | ✅ |
| **Moderation** | Public Showcase | Completed projects spotlighted; raw attachments never exposed publicly | ✅ |
| **Communication** | Query Ticketing | Students raise issues; admins reply with logged timestamps | ✅ |
| **Documents** | PDF Certificates | Dynamic certificate generation uploaded to private cloud storage | ✅ |
| **Documents** | PDF Audit Reports | Real-time aggregate system reports with platform metrics | ✅ |
| **Storage** | Cloud-First Persistence | Files go to Supabase Storage; failure raises error and never silently falls back to local disk | ✅ |
| **Storage** | Ephemeral-Disk Survival | App restart with local cache wiped; files served directly from Supabase private endpoint | ✅ |
| **Health** | Health Check API | `GET /health` returns JSON with DB connectivity status | ✅ |
| **Assistants** | Project Suggester | **Simulated/rule-based** — curated catalog, no external AI API | ✅ |
| **Assistants** | Description Generator | **Simulated/rule-based** — standardized proposal templates | ✅ |
| **Assistants** | Resume Readiness | **Simulated/heuristic** — offline layout and keyword checklist | ✅ |

> [!NOTE]
> **Honest disclosure**: The Project Topic Suggester, Description Generator, and Resume Readiness Reviewer are **rule-based, heuristic assistants** built from curated templates and layout checks. They run entirely offline without paid AI APIs or external network calls.
>
> **Certificate verification**: Issued PDFs display metadata and a unique certificate ID. There is no public certificate lookup URL or external verification endpoint in this release.

---

## 🛡️ Security Controls

1. **No Hardcoded Secrets** — `SECRET_KEY` is enforced from the environment. The application raises a `RuntimeError` at startup if it is absent in production.

2. **Strict Cloud Storage** — `utils/storage.py` uploads to Supabase Storage **before** writing locally. Any cloud failure raises an immediate `RuntimeError` and never silently falls back to the ephemeral local disk.

3. **Account State Invariance** — `flask init-db` seeds only **missing** trial accounts. Existing blocked or inactive accounts are always skipped without modifying their status, password, or role. Verified by automated regression test.

4. **File Access Enforcement** — A student's email appearing as a collaborator does **not** grant download access. The system requires an authenticated session linked to a confirmed team membership record by user ID.

5. **CSRF Hardening** — Custom implementation with `hmac.compare_digest` (timing-safe), per-session token rotation on login/logout, and a JavaScript fetch interceptor that only attaches tokens to same-origin requests.

6. **Demo Deployment Safeguards** — `DISABLE_DESTRUCTIVE_ADMIN=true` disables user account deletion from the admin panel, preventing malicious teardown of the trial environment during public evaluation.

---

## 🧪 Test Results

Tests run against an **isolated in-memory SQLite database** — the live Supabase database and storage bucket are never touched by the test suite.

```bash
# Run full suite
python -m unittest discover tests -v
```

### 29 / 29 Tests Passing

```
test_feature_matrix.FeatureMatrixTestCase (14 tests)
  test_01_student_login_and_logout ............ ok
  test_02_invalid_login ....................... ok
  test_03_role_student_cannot_access_admin .... ok
  test_04_role_admin_access .................. ok
  test_05_blocked_session_rejected_immediately  ok
  test_06_open_redirect_prevented ............ ok
  test_07_csrf_missing_token_rejected ........ ok
  test_08_csrf_invalid_token_rejected ........ ok
  test_09_project_submission_and_file_isolation ok
  test_10_project_updates_and_versions ....... ok
  test_11_queries_and_replies ................ ok
  test_12_admin_actions_and_destructive_safeguards ok
  test_13_reports_and_certificates ........... ok
  test_14_simulated_helper_features .......... ok

test_phase1_security.Phase1SecurityTestCase (15 tests)
  test_create_admin_cli_command .............. ok
  test_csrf_protection_blocks_missing_tokens . ok
  test_init_db_preserves_blocked_and_inactive  ok  <- account state invariance
  test_login_redirect_validation ............. ok
  test_no_automatic_default_admin ............ ok
  test_project_file_access_permissions ....... ok
  test_public_admin_registration_disabled .... ok
  test_requirements_utf8_normalized .......... ok
  test_secret_key_required_from_env .......... ok
  test_token_constant_time_comparison ........ ok
  test_unverified_email_no_team_access ....... ok
  test_upload_collision_prevention ........... ok
  ... (3 additional security boundary tests)

Ran 29 tests in 24.280s   OK
```

---

## 💻 Local Development Setup

### Prerequisites
- Python 3.10+ (3.12 recommended)
- Git

### Steps

```bash
# 1. Clone and switch branch
git clone https://github.com/mani-538/PROJECT_HUB.git
cd PROJECT_HUB
git checkout rework/deployment-ready

# 2. Create and activate virtual environment
python -m venv .venv
# Windows (PowerShell):
.venv\Scripts\Activate.ps1
# Linux / macOS:
source .venv/bin/activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Configure environment
cp .env.example .env
# Edit .env — generate SECRET_KEY:
python -c "import secrets; print(secrets.token_hex(32))"

# 5. Initialize database and seed trial accounts
flask init-db

# 6. Run local server
flask run --port 5000
```

Access the platform at `http://127.0.0.1:5000`.

> [!TIP]
> Omitting Supabase variables in `.env` runs the app in local-filesystem mode with SQLite — suitable for offline development. Add Supabase credentials to target the cloud database and storage bucket.

---

## 🚀 Deployment Guide (Render + Supabase — Free Tier)

### Service Overview

| Service | Free Limit | Notes |
| :--- | :--- | :--- |
| **Render Web Service** | 750 hrs/month, 512 MB RAM | Ephemeral filesystem; spins down after 15 min idle |
| **Supabase PostgreSQL** | 500 MB storage | Persistent; survives restarts and redeploys |
| **Supabase Storage** | 500 MB + 5 GB bandwidth | Private bucket; persistent object storage |

### Step 1 — Supabase Setup

1. Create a free project at [supabase.com](https://supabase.com/).
2. **Database**: Go to **Settings → Database** → copy the **Session pooler** URI (`postgres://postgres.[REF]:[PASSWORD]@aws-0-[REGION].pooler.supabase.com:5432/postgres`).
3. **Storage**: Go to **Storage → New Bucket**:
   - Name: `projecthub-uploads`
   - Public: **OFF** (private bucket)
4. **API Keys**: Go to **Settings → API** → copy **Project URL** and **`service_role` key**.

### Step 2 — Render Deployment

1. Sign in at [render.com](https://render.com/) → **New → Web Service**.
2. Connect `mani-538/PROJECT_HUB`, branch `rework/deployment-ready` (or `main` after merge).
3. Service settings:
   - **Environment**: Python 3
   - **Build Command**: `pip install -r requirements.txt && flask init-db`
   - **Start Command**: `gunicorn "app:create_app()"`
   - **Plan**: Free
   - **Health Check Path**: `/health`

### Step 3 — Environment Variables

| Variable | Required | Description |
| :--- | :--- | :--- |
| `SECRET_KEY` | **Yes** | 32+ char random secret (`python -c "import secrets; print(secrets.token_hex(32))"`) |
| `DATABASE_URL` | **Yes** | Supabase Session Pooler URI with `?sslmode=require` appended |
| `SUPABASE_URL` | **Yes** | `https://[REF].supabase.co` |
| `SUPABASE_SERVICE_ROLE_KEY` | **Yes** | `service_role` key from Supabase API settings |
| `SUPABASE_STORAGE_BUCKET` | **Yes** | `projecthub-uploads` |
| `DISABLE_DESTRUCTIVE_ADMIN` | **Yes** | `true` (protects trial accounts from deletion) |
| `FLASK_DEBUG` | **Yes** | `false` |
| `INITIAL_ADMIN_PASSWORD` | Optional | Admin trial account password (set before first `init-db`) |
| `INITIAL_STUDENT_PASSWORD` | Optional | Student trial account password (set before first `init-db`) |

> [!IMPORTANT]
> **Never commit `.env` or any Supabase keys to Git.** `.env` is already in `.gitignore`.

### Creating an Admin Account on Your Own Deployment

```bash
# Run via Render Shell or locally
flask create-admin \
  --username youradmin \
  --email admin@yourdomain.com \
  --name "Your Name" \
  --department "Administration"
# You will be prompted securely for a password
```

---

## 📋 Trial Access (Live Demo)

Two trial accounts are pre-seeded in the live deployment:

| Role | Email | Notes |
| :--- | :--- | :--- |
| **Student** | `student@projecthub.com` | Full submission, update, query, certificate, and assistant workflows. |
| **Admin** | `admin@projecthub.com` | Private. Contact the repository owner or use `flask create-admin` on your own deployment. |

> [!CAUTION]
> Do not attempt to delete or block the trial accounts in the live demo — destructive admin actions are disabled for public evaluation. The student account password is available on request; admin credentials are kept private.

---

## ⚠️ Known Limitations

| Limitation | Detail |
| :--- | :--- |
| **Cold Starts** | Free Render tier spins down after 15 min idle. First request can take up to 60 seconds. |
| **Simulated AI Assistants** | Project suggester, description generator, and resume readiness reviewer are rule-based heuristics — not backed by any LLM or external AI API. |
| **No Public Certificate Verification** | Issued certificates contain a unique ID and metadata, but there is no public `/verify/<id>` lookup endpoint in this release. |
| **No Email Dispatch** | Notifications are in-app only. No transactional email (SendGrid / SES) is integrated. |
| **Free Storage Limits** | Supabase free tier allows 500 MB object storage and 5 GB monthly bandwidth. |
| **Database Connection Pooling** | Using Supabase Session Pooler (port 5432). Transaction mode (port 6543) is not used to maintain SQLAlchemy compatibility. |

---

## 🔮 Roadmap

- Transactional email notifications (SendGrid / AWS SES).
- Public certificate verification endpoint.
- Real-time faculty–student chat (WebSockets).
- OAuth / SSO integration (Google Workspace / Microsoft 365 Education).
- Automated plagiarism and similarity checking for submitted archives.

---

## 📄 License

This project is licensed under the [MIT License](LICENSE).
