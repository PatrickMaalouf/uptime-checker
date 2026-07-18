#!/usr/bin/env python3
"""
Uptime Checker
Pings a list of endpoints, flags failures/slow responses, and alerts via email.
"""

import os
import sys
import time
import argparse
import logging
from datetime import datetime, timezone

import smtplib
from email.mime.text import MIMEText

import requests
import yaml
from dotenv import load_dotenv

load_dotenv()  # pulls variables from a local .env file if present

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)
log = logging.getLogger("uptime-checker")


def load_config(path: str) -> dict:
    with open(path, "r") as f:
        return yaml.safe_load(f)


def check_endpoint(url: str, timeout: int, slow_threshold_ms: int) -> dict:
    """Hit one URL and return a result dict. Never raises — errors are captured."""
    start = time.time()
    try:
        resp = requests.get(url, timeout=timeout)
        elapsed_ms = round((time.time() - start) * 1000)
        ok = resp.status_code == 200
        slow = elapsed_ms > slow_threshold_ms
        return {
            "url": url,
            "status_code": resp.status_code,
            "elapsed_ms": elapsed_ms,
            "ok": ok,
            "slow": slow,
            "error": None,
        }
    except requests.exceptions.RequestException as e:
        elapsed_ms = round((time.time() - start) * 1000)
        return {
            "url": url,
            "status_code": None,
            "elapsed_ms": elapsed_ms,
            "ok": False,
            "slow": False,
            "error": str(e),
        }



def send_email_alert(failures, smtp_host, smtp_port, smtp_user, smtp_pass, to_addr):
    body = "\n".join(f"{f['url']} — {f['error'] or f['status_code']}" for f in failures)
    msg = MIMEText(body)
    msg["Subject"] = f"Uptime Alert: {len(failures)} endpoint(s) down"
    msg["From"] = smtp_user
    msg["To"] = to_addr
    with smtplib.SMTP(smtp_host, smtp_port) as server:
        server.starttls()
        server.login(smtp_user, smtp_pass)
        server.send_message(msg)


def send_email_success(results, smtp_host, smtp_port, smtp_user, smtp_pass, to_addr):
    """Send a summary email when all endpoints are healthy."""
    body = "All endpoints are UP and responding normally.\n\n"
    body += "\n".join(f"✅ {r['url']} — {r['elapsed_ms']}ms" for r in results)
    msg = MIMEText(body)
    msg["Subject"] = f"Uptime OK: All {len(results)} endpoint(s) healthy"
    msg["From"] = smtp_user
    msg["To"] = to_addr
    with smtplib.SMTP(smtp_host, smtp_port) as server:
        server.starttls()
        server.login(smtp_user, smtp_pass)
        server.send_message(msg)


def run(config_path: str, once: bool) -> int:
    cfg = load_config(config_path)
    urls = cfg["urls"]
    timeout = cfg.get("timeout_seconds", 10)
    slow_threshold_ms = cfg.get("slow_threshold_ms", 2000)

    smtp_host = os.getenv("SMTP_HOST", "")
    smtp_port = int(os.getenv("SMTP_PORT", "587"))
    smtp_user = os.getenv("SMTP_USER", "")
    smtp_pass = os.getenv("SMTP_PASS", "")
    alert_to = os.getenv("ALERT_TO", "")

    log.info(f"Checking {len(urls)} endpoint(s)...")
    results = [check_endpoint(u, timeout, slow_threshold_ms) for u in urls]

    failures = [r for r in results if not r["ok"]]
    slow = [r for r in results if r["ok"] and r["slow"]]

    for r in results:
        status = "OK" if r["ok"] else "FAIL"
        log.info(f"[{status}] {r['url']} — {r['elapsed_ms']}ms")

    if failures:
        log.warning(f"{len(failures)} endpoint(s) DOWN")
        if smtp_host and smtp_user and alert_to:
            try:
                send_email_alert(failures, smtp_host, smtp_port, smtp_user, smtp_pass, alert_to)
                log.info("Email alert sent.")
            except Exception as e:
                log.error(f"Failed to send email alert: {e}")
        else:
            log.warning("Email alert not configured; skipping.")
    else:
        log.info("All endpoints healthy.")
        if smtp_host and smtp_user and alert_to:
            try:
                send_email_success(results, smtp_host, smtp_port, smtp_user, smtp_pass, alert_to)
                log.info("Success email sent.")
            except Exception as e:
                log.error(f"Failed to send success email: {e}")
        else:
            log.warning("Email not configured; skipping success email.")

    if slow:
        log.warning(f"{len(slow)} endpoint(s) slow (>{slow_threshold_ms}ms)")

    # non-zero exit code = useful for CI/cron failure detection
    return 1 if failures else 0


def main():
    parser = argparse.ArgumentParser(description="Check endpoint uptime and alert on failure.")
    parser.add_argument("--config", default="config.yaml", help="Path to config file")
    args = parser.parse_args()

    exit_code = run(args.config, once=True)
    sys.exit(exit_code)


if __name__ == "__main__":
    main()