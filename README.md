# Project Hub – Academic Project Management & Showcase Platform

[![Python](https://img.shields.io/badge/Python-3.12-blue.svg)](https://www.python.org/)
[![Flask](https://img.shields.io/badge/Flask-3.0.3-green.svg)](https://flask.palletsprojects.com/)
[![SQLAlchemy](https://img.shields.io/badge/SQLAlchemy-2.0.48-red.svg)](https://www.sqlalchemy.org/)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-Supabase-336791.svg)](https://supabase.com/)
[![Tests](https://img.shields.io/badge/Tests-28%2F28%20Passing-brightgreen.svg)]()

Project Hub is an academic capstone and engineering project management platform designed for universities, colleges, and technical institutions. It provides a secure, role-based workflow for proposal submissions, iterative version tracking, peer collaboration, administrative moderation, dynamic PDF certification, and a public showcase for completed projects.

---

## 📌 Problem Statement & Intended Users

### The Problem
Academic institutions frequently struggle with fragmented project coordination:
- Submissions and reports scattered across email threads and shared drives.
- Risk of unauthorized file access and lack of audit logging.
- Ephemeral hosting deployments losing student uploads upon container spin-down.
- Manual certificate issuance and administrative reporting.

### Intended Users
1. **Students**: Submit proposals, manage versioned project archives, collaborate with verified teammates, receive faculty feedback, track query resolutions, utilize heuristic preparation assistants, and download verified completion certificates.
2. **Administrators & Reviewers**: Moderate submissions, approve or request revisions, toggle completed projects into the public showcase, respond to student inquiries, generate dynamic audit reports, and issue certificates.

---

## 🏗️ System Architecture & Technology Stack

```
                     ┌─────────────────────────────────────────┐
                     │          Browser / Client UI            │
                     │  (HTML5, Vanilla CSS, Bootstrap Icons)  │
                     └────────────────────┬────────────────────┘
                                          │ HTTPS (CSRF Token)
                                          ▼
                     ┌─────────────────────────────────────────┐
                     │            WSGI Server                  │
                     │        (Gunicorn / Flask App)           │
                     └──────┬───────────────────────────┬──────┘
                            │                           │
                            ▼                           ▼
          ┌──────────────────────────────────┐   ┌────────────────────────────────┐
          │      Application Layer (Flask)   │   │     Unified Storage Adapter    │
          │  - routes/auth.py (RBAC & Auth)  │   │        (utils/storage.py)      │
          │  - routes/student.py (Workflows) │   └──────┬──────────────────┬──────┘
          │  - routes/admin.py (Moderation)  │          │                  │
          │  - utils/csrf.py (Timing-Safe)   │   (Local Dev)        (Production)
          └─────────────────┬────────────────┘          │                  │
                            │                           ▼                  ▼
                            ▼                     Local Disk        Supabase Storage
                     SQLAlchemy ORM               (/uploads)        (Private Bucket)
                            │
               ┌────────────┴────────────┐
               ▼                         ▼
         SQLite (Dev)          PostgreSQL (Supabase)
```

### Core Technologies
- **Backend Framework**: Python 3.12, Flask 3.0.3 (Application Factory pattern).
- **Authentication & RBAC**: Flask-Login 0.6.3 with secure session validation and user status verification.
- **Database & ORM**: SQLAlchemy 2.0.48, Flask-SQLAlchemy 3.1.1, PostgreSQL driver `psycopg2-binary 2.9.13` (with SQLite fallback for local development).
- **Object Storage**: Custom unified storage adapter (`utils/storage.py`) connecting to private Supabase Storage via REST API for persistent cloud hosting, with automatic local filesystem caching and fallback.
- **Document Generation**: ReportLab 4.2.2 for automated PDF certificates and administrative system reports.
- **Security & CSRF**: Zero-dependency session-backed CSRF protection (`utils/csrf.py`) with constant-time token comparison (`hmac.compare_digest`), session token rotation, and same-origin fetch interceptors.

---

## 💡 Implemented Features & Honest Labeling

| Module | Feature | Implementation Details | Status |
| :--- | :--- | :--- | :--- |
| **Authentication** | Role-Based Access Control | Distinct student and admin portals; public admin signup disabled | PASS |
| **Authentication** | Session Hardening | Blocked/deactivated accounts revoked immediately on active sessions | PASS |
| **Authentication** | Redirect Protection | Open redirect validation rejects external domains | PASS |
| **Security** | CSRF Protection | Constant-time token verification on all POST forms and fetch requests | PASS |
| **Security** | File Authorization | Project downloads restricted to owner, verified team members, or admin | PASS |
| **Security** | Collision Prevention | Cryptographically random UUID filename prefixes with clean download headers | PASS |
| **Security** | Destructive Safeguards | User deletion disabled in trial deployment; self-deletion/blocking prohibited | PASS |
| **Projects** | Submission & Updates | Proposals with category, domain, tech stack, and versioned file attachments | PASS |
| **Projects** | Version Control | Iterative version uploads with notes and changelog history | PASS |
| **Projects** | Team Collaboration | Multi-student collaboration with verified account linkage | PASS |
| **Moderation** | Project Review | Admin approval, rejection, grading, and feedback workflow | PASS |
| **Moderation** | Public Showcase | Completed projects spotlighted in public showcase gallery | PASS |
| **Communication**| Query System | Student inquiry ticketing system with administrative responses | PASS |
| **Documents** | Completion Certificates | Automated dynamic PDF certificate generation with verification details | PASS |
| **Documents** | System Audit Reports | Real-time aggregate PDF reporting with platform metrics | PASS |
| **Health** | Health Check API | `/health` endpoint reporting service and database connection status | PASS |
| **Assistant** | Project Suggester | **Simulated / Rule-based**: Curated catalog of engineering project ideas | PASS |
| **Assistant** | Description Generator | **Simulated / Rule-based**: Standardized proposal and problem statement templates | PASS |
| **Assistant** | Resume Readiness | **Simulated / Heuristic**: Offline document readiness and formatting checklist | PASS |

> [!NOTE]
> **Honest Feature Disclosure**: The Project Topic Suggester, Description Generator, and Resume Readiness Reviewer are engineered as **rule-based, heuristic assistants** using curated templates and layout checks. They operate entirely offline without third-party paid AI APIs or external data leakage.

---

## 🛡️ Security Hardening & Architectural Decisions

1. **No Hardcoded Secrets or Auto-Seeded Credentials**:
   `SECRET_KEY` is strictly required via the environment; the application will refuse to start in production without it. Default admin creation and plaintext logging have been completely removed in favor of a secure CLI command (`flask create-admin`) with interactive confirmation.
2. **Persistence Over Ephemeral Filesystems**:
   Render web services operate on ephemeral containers where disk changes are lost on redeploy. All uploads (project files, versions, resumes, avatars, certificates, reports) are routed through `utils/storage.py` to a private Supabase Storage bucket, ensuring persistence across restarts.
3. **Strict File Access Authorization**:
   Listing an email address as a collaborator does **not** grant access. The system requires an authenticated student account linked by unique user ID or ownership. Public showcase visibility does not expose raw project source files or attachments.
4. **Trial Deployment Defenses**:
   In trial/demo mode (`DISABLE_DESTRUCTIVE_ADMIN=true`), administrative deletion of user accounts is disabled to prevent malicious disruption while allowing full evaluation of platform capabilities.

---

## 🧪 Testing Evidence & Automated Verification

The repository includes a comprehensive automated test suite verifying all security boundaries and core workflows against an isolated SQLite test database.

```bash
# Run the complete test suite
python -m unittest discover tests -v
```

### Automated Test Results: 28 / 28 PASSING
```
test_01_student_login_and_logout (test_feature_matrix.FeatureMatrixTestCase) ... ok
test_02_invalid_login (test_feature_matrix.FeatureMatrixTestCase) ... ok
test_03_role_student_cannot_access_admin (test_feature_matrix.FeatureMatrixTestCase) ... ok
test_04_role_admin_access (test_feature_matrix.FeatureMatrixTestCase) ... ok
test_05_blocked_session_rejected_immediately (test_feature_matrix.FeatureMatrixTestCase) ... ok
test_06_open_redirect_prevented (test_feature_matrix.FeatureMatrixTestCase) ... ok
test_07_csrf_missing_token_rejected (test_feature_matrix.FeatureMatrixTestCase) ... ok
test_08_csrf_invalid_token_rejected (test_feature_matrix.FeatureMatrixTestCase) ... ok
test_09_project_submission_and_file_isolation (test_feature_matrix.FeatureMatrixTestCase) ... ok
test_10_project_updates_and_versions (test_feature_matrix.FeatureMatrixTestCase) ... ok
test_11_queries_and_replies (test_feature_matrix.FeatureMatrixTestCase) ... ok
test_12_admin_actions_and_destructive_safeguards (test_feature_matrix.FeatureMatrixTestCase) ... ok
test_13_reports_and_certificates (test_feature_matrix.FeatureMatrixTestCase) ... ok
test_14_simulated_helper_features (test_feature_matrix.FeatureMatrixTestCase) ... ok
test_01_public_admin_signup_disabled (test_phase1_security.Phase1SecurityTestCase) ... ok
test_02_admin_role_select_ui_removed (test_phase1_security.Phase1SecurityTestCase) ... ok
test_03_create_admin_cli_success (test_phase1_security.Phase1SecurityTestCase) ... ok
test_04_create_admin_cli_never_overwrites_existing (test_phase1_security.Phase1SecurityTestCase) ... ok
test_05_secret_key_enforced_from_env (test_phase1_security.Phase1SecurityTestCase) ... ok
test_06_blocked_user_session_invalidation (test_phase1_security.Phase1SecurityTestCase) ... ok
test_07_open_redirect_prevention (test_phase1_security.Phase1SecurityTestCase) ... ok
test_08_project_file_authorization_isolation (test_phase1_security.Phase1SecurityTestCase) ... ok
test_09_unverified_email_does_not_grant_team_access (test_phase1_security.Phase1SecurityTestCase) ... ok
test_10_csrf_protection_blocks_missing_or_invalid_tokens (test_phase1_security.Phase1SecurityTestCase) ... ok
test_11_csrf_constant_time_comparison (test_phase1_security.Phase1SecurityTestCase) ... ok
test_12_upload_filename_collision_prevention (test_phase1_security.Phase1SecurityTestCase) ... ok
test_13_existing_legacy_filenames_remain_accessible (test_phase1_security.Phase1SecurityTestCase) ... ok
test_14_requirements_utf8_normalized (test_phase1_security.Phase1SecurityTestCase) ... ok
----------------------------------------------------------------------
Ran 28 tests in 25.152s

OK
```

---

## 💻 Local Installation & Setup

### Prerequisites
- Python 3.10+ (Python 3.12 recommended)
- Git

### Steps
1. **Clone the repository and switch to the rework branch**:
   ```bash
   git clone https://github.com/mani-538/PROJECT_HUB.git
   cd PROJECT_HUB
   git checkout rework/deployment-ready
   ```

2. **Create and activate a virtual environment**:
   ```bash
   python -m venv .venv
   # Windows (PowerShell):
   .venv\Scripts\Activate.ps1
   # Linux / macOS:
   source .venv/bin/activate
   ```

3. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure environment variables**:
   ```bash
   # Copy example configuration
   cp .env.example .env
   ```
   Generate a secure secret key:
   ```bash
   python -c "import secrets; print(secrets.token_hex(32))"
   ```
   Add this key to your `.env` file under `SECRET_KEY`.

5. **Initialize database and verify trial accounts**:
   ```bash
   flask init-db
   ```

6. **Start local development server**:
   ```bash
   flask run --port 5000
   ```
   Access the platform at `http://127.0.0.1:5000`.

---

## 🚀 Free Deployment Guide (Render + Supabase)

This setup runs entirely within the **free tiers** of Render and Supabase without incurring any cost.

### Service Architecture & Free Limits
- **Render Web Service (Free Tier)**: 512MB RAM, shared CPU, 750 free instance hours/month. Spins down on 15 minutes of inactivity. Ephemeral filesystem.
- **Supabase PostgreSQL (Free Tier)**: 500MB database, 2 free projects, direct PostgreSQL connection string.
- **Supabase Storage (Free Tier)**: 500MB persistent object storage, 5GB bandwidth, private buckets.

### Step 1: Set Up Supabase Database & Storage
1. Log in to [Supabase](https://supabase.com/) and create a free project (e.g., `project-hub-prod`).
2. Go to **Project Settings** -> **Database** and copy the **URI connection string** (`postgresql://postgres:[PASSWORD]@db.[REF].supabase.co:5432/postgres`).
3. Go to **Storage** -> **New Bucket**:
   - Bucket name: `projecthub-uploads`
   - Privacy: **Private** (leave Public turned OFF).
4. Go to **Project Settings** -> **API** and copy:
   - **Project URL** (`https://[REF].supabase.co`)
   - **Service Role Secret Key** (`service_role` key - needed for secure backend uploads).

### Step 2: Deploy on Render
1. Log in to [Render](https://render.com/) and click **New +** -> **Web Service**.
2. Connect your GitHub repository (`mani-538/PROJECT_HUB`) and select branch `rework/deployment-ready` (or `main` after merging).
3. Configure the service settings:
   - **Name**: `project-hub`
   - **Environment**: `Python 3`
   - **Region**: Choose the region closest to your Supabase region.
   - **Build Command**: `pip install -r requirements.txt && flask init-db`
   - **Start Command**: `gunicorn "app:create_app()"`
   - **Plan**: `Free`

### Step 3: Configure Environment Variables on Render
Add the following under **Environment Variables** in Render's dashboard:

| Variable Name | Required | Description |
| :--- | :--- | :--- |
| `SECRET_KEY` | **Yes** | 32+ character cryptographically secure random string |
| `DATABASE_URL` | **Yes** | Supabase PostgreSQL connection string |
| `SUPABASE_URL` | **Yes** | Supabase project URL (`https://[REF].supabase.co`) |
| `SUPABASE_SERVICE_ROLE_KEY` | **Yes** | Supabase `service_role` secret key |
| `SUPABASE_STORAGE_BUCKET` | **Yes** | `projecthub-uploads` |
| `DISABLE_DESTRUCTIVE_ADMIN` | **Yes** | `true` (safeguards demo accounts against deletion) |
| `FLASK_DEBUG` | **Yes** | `false` |
| `PYTHON_VERSION` | Optional | `3.12.0` |

### Step 4: Health Check Configuration
In the Render Web Service settings, set the **Health Check Path** to:
```
/health
```

### Rollback & Migration Recovery
- **Database Reset / Migration**: If the PostgreSQL schema needs re-initialization, run `flask init-db` from the Render Shell or deployment build step. Existing records and tables are preserved safely.
- **Rollback**: In the Render dashboard, navigate to **Deploys** and click **Rollback to this deploy** on any previous successful commit.

---

## 📋 Evaluation Accounts (Trial Access)

| Role | Username / Identifier | Notes |
| :--- | :--- | :--- |
| **Student** | `student@projecthub.com` | Standard student trial account with full submission and update capabilities. |
| **Admin** | `admin@projecthub.com` | Administrator access is private. To create an admin account on your deployment, run `flask create-admin` via Render Shell or set `INITIAL_ADMIN_PASSWORD` during first initialization. |

---

## 🔮 Known Limitations & Roadmap

1. **Email / SMS Dispatch**: Notifications currently operate via in-app feeds; future integration with SendGrid or AWS SES will support transactional email alerts.
2. **Plagiarism & Code Analysis**: Automated repository similarity checking and static analysis for submitted project archives.
3. **Real-Time Faculty Chat**: Upgrading the query resolution system to real-time WebSockets for live mentoring sessions.
4. **OAuth / SSO**: Integration with university Single Sign-On (Google Workspace / Microsoft 365 Education).

---

## 📄 License
This project is licensed under the MIT License.
