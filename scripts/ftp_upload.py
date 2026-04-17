#!/usr/bin/env python3
import ftplib
import os
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
UPLOAD_PATHS = [
    ROOT / "index.html",
    ROOT / "assets",
    ROOT / "data",
]


def env(name):
    value = os.environ.get(name)
    if not value:
        raise RuntimeError(f"Missing required environment variable: {name}")
    return value


def ensure_dir(ftp, path):
    parts = [part for part in path.split("/") if part]
    for part in parts:
        try:
            ftp.mkd(part)
        except ftplib.error_perm:
            pass
        ftp.cwd(part)


def upload_file(ftp, local_path, remote_path):
    remote_dir = str(remote_path.parent).replace("\\", "/")
    original_dir = ftp.pwd()
    if remote_dir not in ("", "."):
        ensure_dir(ftp, remote_dir)

    with local_path.open("rb") as file:
        ftp.storbinary(f"STOR {remote_path.name}", file)

    ftp.cwd(original_dir)


def iter_uploads():
    for path in UPLOAD_PATHS:
        if path.is_file():
            yield path, Path(path.name)
        else:
            for file_path in path.rglob("*"):
                if file_path.is_file():
                    yield file_path, file_path.relative_to(ROOT)


def main():
    host = env("FTP_HOST")
    user = env("FTP_USER")
    password = env("FTP_PASSWORD")
    remote_root = os.environ.get("FTP_REMOTE_DIR", "/")

    with ftplib.FTP(host, timeout=60) as ftp:
        ftp.login(user, password)
        ftp.cwd(remote_root)
        for local_path, remote_path in iter_uploads():
            upload_file(ftp, local_path, remote_path)
            print(f"Uploaded {remote_path}")


if __name__ == "__main__":
    main()
