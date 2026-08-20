"""Periodic mysqldump backup loop.

Reads DATABASE_URL from the backend env (no hardcoded creds), dumps the app
database to /workspace/backups/ every 30 minutes while the container is active,
and keeps the 5 most recent dumps. A dump also happens immediately on service
start — which lands right after any container pause/resume, the exact moment
the database is most at risk.

Run: cd /workspace/backend && .venv/bin/python -m scripts.backup_db
"""
from __future__ import annotations

import gzip
import logging
import os
import shutil
import subprocess
import time
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import unquote, urlparse

from app.config import get_settings

BACKUP_DIR = Path("/workspace/backups")
INTERVAL_SECONDS = 30 * 60
KEEP = 5

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("db-backup")


def _parse_db_url(url: str) -> tuple[str, str, str, int, str]:
    p = urlparse(url)
    if p.scheme not in ("mysql", "mysql+pymysql"):
        raise ValueError(f"backup supports MySQL only, got {p.scheme!r}")
    return unquote(p.username or ""), unquote(p.password or ""), p.hostname or "127.0.0.1", p.port or 3306, p.path.lstrip("/")


def dump_once() -> Path | None:
    settings = get_settings()
    user, password, host, port, dbname = _parse_db_url(settings.sqlalchemy_url)
    stamp = datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")
    out = BACKUP_DIR / f"appdb-{stamp}.sql.gz"
    plain = out.with_suffix("").with_suffix(".sql")  # appdb-<stamp>.sql

    env = dict(os.environ)
    # password via env, never on the command line
    env["MYSQL_PWD"] = password

    # 1) dump to a plain file — a gzip wrapper passed to subprocess stdout
    #    writes raw bytes to the fd and silently bypasses compression
    with open(plain, "wb") as f:
        proc = subprocess.run(
            [
                "mysqldump",
                f"--host={host}", f"--port={port}", f"--user={user}",
                "--single-transaction", "--routines", "--triggers",
                dbname,
            ],
            stdout=f, stderr=subprocess.PIPE, env=env,
        )
    if proc.returncode != 0 or plain.stat().st_size < 100:
        plain.unlink(missing_ok=True)
        log.error("dump failed: %s", proc.stderr.decode()[:200])
        return None

    # 2) compress, verify gzip integrity, then swap in
    tmp_gz = out.with_suffix(".gz.tmp")
    with open(plain, "rb") as f_in, gzip.open(tmp_gz, "wb") as f_out:
        shutil.copyfileobj(f_in, f_out)
    tmp_gz.rename(out)
    plain.unlink(missing_ok=True)
    check = subprocess.run(["gunzip", "-t", str(out)], capture_output=True)
    if check.returncode != 0:
        out.unlink(missing_ok=True)
        log.error("gzip verification failed — discarding backup")
        return None
    log.info("dumped %s (%d KB)", out.name, out.stat().st_size // 1024)
    _prune()
    return out


def _prune() -> None:
    dumps = sorted(BACKUP_DIR.glob("appdb-*.sql.gz"))
    for old in dumps[:-KEEP]:
        old.unlink(missing_ok=True)
        log.info("pruned %s", old.name)


def main() -> None:
    BACKUP_DIR.mkdir(parents=True, exist_ok=True)
    log.info("db-backup started — every %ds to %s (keep %d)", INTERVAL_SECONDS, BACKUP_DIR, KEEP)
    while True:
        try:
            dump_once()
        except Exception:  # noqa: BLE001 — never kill the loop
            log.exception("backup iteration failed")
        time.sleep(INTERVAL_SECONDS)


if __name__ == "__main__":
    main()
