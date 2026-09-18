from __future__ import annotations

import os
import pwd
import sys
from pathlib import Path

APP_USER = "appuser"
ALLOWED_DATABASE_ROOTS = (
    Path("/data"),
    Path("/app"),
)


def _is_allowed_database_parent(parent: Path) -> bool:
    resolved = parent.resolve()
    return any(
        resolved == root or resolved.is_relative_to(root)
        for root in ALLOWED_DATABASE_ROOTS
    )


def _prepare_database_directory() -> None:
    database_path = Path(
        os.getenv("DATABASE_PATH", "/data/omnipool.db")
    )
    parent = database_path.parent

    if not _is_allowed_database_parent(parent):
        raise RuntimeError(
            "container_database_path_must_live_under_/data_or_/app"
        )

    parent.mkdir(parents=True, exist_ok=True)

    if os.geteuid() != 0:
        return

    account = pwd.getpwnam(APP_USER)
    uid = account.pw_uid
    gid = account.pw_gid

    # Runtime volume mounts replace image-time ownership. Fix only the
    # database directory and SQLite sidecar files, then permanently drop
    # privileges before importing or starting the application.
    os.chown(parent, uid, gid, follow_symlinks=False)
    for suffix in ("", "-wal", "-shm"):
        candidate = Path(f"{database_path}{suffix}")
        if candidate.exists():
            os.chown(
                candidate,
                uid,
                gid,
                follow_symlinks=False,
            )

    os.initgroups(APP_USER, gid)
    os.setgid(gid)
    os.setuid(uid)


def main() -> None:
    _prepare_database_directory()

    if os.geteuid() == 0:
        raise RuntimeError("refusing_to_start_application_as_root")

    port = os.getenv("PORT", "8000")
    args = [
        sys.executable,
        "-m",
        "uvicorn",
        "backend.app:app",
        "--host",
        "0.0.0.0",
        "--port",
        port,
        "--workers",
        "1",
        "--no-access-log",
    ]
    os.execv(sys.executable, args)


if __name__ == "__main__":
    main()
