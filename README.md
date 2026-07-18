# Uptime Checker

**A lightweight Python tool that monitors website availability, detects slow responses, and sends email alerts when endpoints go down.**

Built as a real-world systems analyst portfolio project demonstrating monitoring fundamentals, automation, and incident alerting — skills that translate directly to production infrastructure work.

---

## Table of Contents

- [Problem Statement](#problem-statement)
- [Solution Overview](#solution-overview)
- [Architecture](#architecture)
- [How It Works](#how-it-works)
- [Project Structure](#project-structure)
- [Setup & Installation](#setup--installation)
- [Configuration](#configuration)
- [Usage](#usage)
- [Sample Output](#sample-output)
- [Design Decisions](#design-decisions)
- [Future Improvements](#future-improvements)
- [Technologies Used](#technologies-used)

---

## Problem Statement

Organizations rely on web services being available 24/7. When a website or API goes down — even briefly — it can mean lost revenue, degraded user experience, and SLA violations. Teams need a way to:

1. **Continuously verify** that critical endpoints are reachable and responding correctly.
2. **Detect performance degradation** before it becomes a full outage.
3. **Alert the right people immediately** when something goes wrong, without relying on end-user reports.

Most enterprise monitoring tools (Datadog, PagerDuty, Pingdom) solve this at scale, but they are often overkill for small teams or personal projects — and understanding how they work under the hood is a valuable skill for any systems analyst.

---

## Solution Overview

**Uptime Checker** is a CLI tool that:

- Reads a list of URLs from a YAML configuration file.
- Sends an HTTP GET request to each endpoint with a configurable timeout.
- Classifies each response as **healthy**, **slow**, or **down** based on status code and response time.
- Sends an **email alert** (via SMTP/TLS) listing every failed endpoint when one or more are unreachable.
- Returns a non-zero exit code on failure, making it compatible with **cron jobs**, **CI pipelines**, and **task schedulers** for automated monitoring.

---

## Architecture

```
┌─────────────────────────────────────────────────────────┐
│                     Uptime Checker                      │
│                                                         │
│  ┌─────────────┐    ┌──────────────┐    ┌────────────┐  │
│  │ config.yaml │───▶│   main.py    │───▶│  Console   │  │
│  │  (URLs +    │    │              │    │   Logs     │  │
│  │  thresholds)│    │  1. Load cfg │    └────────────┘  │
│  └─────────────┘    │  2. Check    │                    │
│                     │     endpoints│    ┌────────────┐  │
│  ┌─────────────┐    │  3. Classify │───▶│   Email    │  │
│  │    .env     │───▶│     results  │    │   Alert    │  │
│  │ (SMTP creds)│    │  4. Alert    │    │  (SMTP)    │  │
│  └─────────────┘    └──────────────┘    └────────────┘  │
│                                                         │
└─────────────────────────────────────────────────────────┘
```

---

## How It Works

### 1. Configuration Loading
The tool reads `config.yaml` to get the list of target URLs, the HTTP timeout, and the slow-response threshold. SMTP credentials are loaded from a `.env` file to keep secrets out of version control.

### 2. Endpoint Health Checks
Each URL receives an HTTP GET request. The tool measures:
- **Status code** — only `200` is considered healthy.
- **Response time** — compared against the configurable `slow_threshold_ms`.
- **Connection errors** — DNS failures, timeouts, and refused connections are all captured gracefully without crashing.

### 3. Result Classification
Every result is categorized as one of:

| Status | Condition |
|--------|-----------|
| ✅ **OK** | HTTP 200 and response time within threshold |
| ⚠️ **Slow** | HTTP 200 but response time exceeds threshold |
| ❌ **Down** | Non-200 status code, timeout, DNS failure, or connection error |

### 4. Email Alerting
When one or more endpoints are classified as **down**, the tool composes a plain-text email listing each failed URL with its error details, and sends it via SMTP over TLS. If SMTP is not configured, it logs a warning and continues — the tool never crashes due to alerting misconfiguration.

### 5. Exit Code
The process exits with code `1` if any endpoint is down, and `0` if all are healthy. This makes it easy to integrate with:
- **Cron** — schedule checks every 5 minutes.
- **CI/CD pipelines** — add a post-deploy health check step.
- **Windows Task Scheduler** — automate on Windows servers.

---

## Project Structure

```
uptime-checker/
├── .github/
│   └── workflows/
│       └── uptime.yml   # GitHub Actions scheduled workflow
├── main.py              # Core logic: endpoint checking, alerting, CLI
├── config.yaml          # List of URLs and monitoring thresholds
├── requirements.txt     # Python dependencies
├── .env.example         # Template for SMTP credentials
├── .env                 # Actual SMTP credentials (git-ignored)
├── .gitignore           # Excludes .env, venv/, __pycache__/
└── README.md            # This file
```

---

## Setup & Installation

### Prerequisites
- Python 3.10+
- A Gmail account with [App Passwords](https://support.google.com/accounts/answer/185833) enabled (or any SMTP provider)

### Steps

```bash
# 1. Clone the repository
git clone https://github.com/PatrickMaalouf/uptime-checker.git
cd uptime-checker

# 2. Create and activate a virtual environment
python -m venv venv
venv\Scripts\activate        # Windows
# source venv/bin/activate   # macOS / Linux

# 3. Install dependencies
pip install -r requirements.txt

# 4. Set up your environment variables
cp .env.example .env
# Edit .env with your SMTP credentials (see Configuration below)
```

---

## Configuration

### `config.yaml` — Monitoring Targets

```yaml
urls:
  - https://example.com
  - https://api.github.com
  - https://your-app.com

timeout_seconds: 10         # Max wait time per request (seconds)
slow_threshold_ms: 2000     # Response times above this are flagged as slow (ms)
```

### `.env` — SMTP Credentials

```env
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=you@gmail.com
SMTP_PASS=your-app-password
ALERT_TO=recipient@example.com
```

| Variable | Description |
|----------|-------------|
| `SMTP_HOST` | SMTP server hostname (e.g., `smtp.gmail.com`, `smtp.office365.com`) |
| `SMTP_PORT` | SMTP port — `587` for STARTTLS (recommended) |
| `SMTP_USER` | Sender email address |
| `SMTP_PASS` | App password or SMTP credential (never your real password) |
| `ALERT_TO` | Recipient email address for alert notifications |

---

## Usage

```bash
# Run with default config
python main.py

# Run with a custom config file
python main.py --config /path/to/custom-config.yaml
```

### Automated via GitHub Actions (Active ✅)

This project includes a GitHub Actions workflow (`.github/workflows/uptime.yml`) that runs the checker **every 5 minutes** automatically — no server or cron setup required.

- **Schedule:** `*/5 * * * *` (every 5 minutes)
- **Manual trigger:** Go to **Actions** → **Uptime Check** → **Run workflow**
- **Secrets:** SMTP credentials are stored as [GitHub Repository Secrets](https://docs.github.com/en/actions/security-guides/encrypted-secrets) — never exposed in code.
- **Failure detection:** The workflow exits with code `1` when endpoints are down, marking the run as failed in the Actions dashboard.

### Alternative: Cron (Linux/macOS)

```bash
# Check every 5 minutes
*/5 * * * * cd /path/to/uptime-checker && /path/to/venv/bin/python main.py >> /var/log/uptime.log 2>&1
```

### Alternative: Task Scheduler (Windows)

Create a scheduled task that runs:
```
C:\path\to\venv\Scripts\python.exe C:\path\to\uptime-checker\main.py
```

---

## Sample Output

### All Healthy
```
2026-07-18 18:04:26 [INFO] Checking 3 endpoint(s)...
2026-07-18 18:04:27 [INFO] [OK] https://example.com — 485ms
2026-07-18 18:04:27 [INFO] [OK] https://api.github.com — 539ms
2026-07-18 18:04:27 [INFO] All endpoints healthy.
```

### Endpoint Down (with Email Alert)
```
2026-07-18 18:04:26 [INFO] Checking 3 endpoint(s)...
2026-07-18 18:04:27 [INFO] [OK] https://example.com — 485ms
2026-07-18 18:04:27 [INFO] [OK] https://api.github.com — 539ms
2026-07-18 18:04:27 [INFO] [FAIL] https://your-client-site.com — 32ms
2026-07-18 18:04:27 [WARNING] 1 endpoint(s) DOWN
2026-07-18 18:04:30 [INFO] Email alert sent.
```

### Email Alert Received

> **Subject:** Uptime Alert: 1 endpoint(s) down
>
> **Body:**
> `https://your-client-site.com` — HTTPSConnectionPool(host='your-client-site.com', port=443): Max retries exceeded with url: / (Caused by NameResolutionError: Failed to resolve 'your-client-site.com')

---

## Design Decisions

| Decision | Rationale |
|----------|-----------|
| **Single-file architecture** | Keeps the project simple and easy to audit — no framework overhead for a focused CLI tool. |
| **YAML for configuration** | Human-readable, supports lists natively, and is a standard in DevOps tooling (Ansible, Kubernetes, CI configs). |
| **`.env` for secrets** | Industry-standard pattern (12-Factor App) — separates config from code and keeps credentials out of Git. |
| **Graceful error handling** | Each endpoint check is wrapped in try/except — one failing URL never crashes the entire run. |
| **Non-zero exit codes** | Enables integration with cron, CI/CD, and monitoring systems that rely on exit codes to detect failure. |
| **Email over Slack** | Email is universally accessible, requires no third-party webhook setup, and works across all organizations. |
| **STARTTLS encryption** | SMTP traffic is encrypted in transit — credentials and alert content are never sent in plaintext. |
| **GitHub Actions for scheduling** | Free hosted cron — no server to maintain, runs on Ubuntu runners, and secrets are managed via GitHub's encrypted secrets. |

---

## Future Improvements

- [x] **GitHub Actions workflow** — runs the checker on a schedule every 5 minutes via GitHub-hosted runners.
- [ ] **Retry logic** — retry failed endpoints before alerting to reduce false positives from transient network issues.
- [ ] **HTML email reports** — richer alert emails with color-coded status tables.
- [ ] **Response body validation** — check that responses contain expected content, not just a 200 status.
- [ ] **Persistent logging** — write results to a SQLite database or CSV for historical trend analysis.
- [ ] **Dashboard** — a simple web UI to visualize uptime history over time.
- [ ] **Multi-channel alerting** — add Slack, Microsoft Teams, or SMS as additional notification channels.

---

## Technologies Used

| Technology | Purpose |
|------------|---------|
| **Python 3** | Core programming language |
| **requests** | HTTP client for endpoint health checks |
| **PyYAML** | YAML configuration file parsing |
| **python-dotenv** | Load environment variables from `.env` files |
| **smtplib** (stdlib) | SMTP email sending with TLS encryption |
| **argparse** (stdlib) | Command-line argument parsing |
| **logging** (stdlib) | Structured, timestamped console output |
| **GitHub Actions** | Scheduled automation — runs checks every 5 minutes on hosted runners |

---

## License

This project is open source and available under the [MIT License](LICENSE).
