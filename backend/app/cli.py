"""管理者帳號建立工具。

用法：
    python -m app.cli create-admin

互動輸入帳號、Email、密碼，或透過環境變數 ADMIN_USERNAME / ADMIN_EMAIL /
ADMIN_PASSWORD 提供（適合 CI 或全自動部署腳本，密碼不會出現在 shell history）。
"""

import argparse
import asyncio
import getpass
import os
import sys

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError

from app.core.database import SessionLocal
from app.core.security import hash_password
from app.models.user import User


def _read_credentials() -> tuple[str, str, str]:
    username = os.environ.get("ADMIN_USERNAME")
    email = os.environ.get("ADMIN_EMAIL")
    password = os.environ.get("ADMIN_PASSWORD")

    if username and email and password:
        return username, email, password

    username = username or input("帳號: ").strip()
    email = email or input("Email: ").strip()
    if password:
        return username, email, password

    password = getpass.getpass("密碼: ")
    confirm = getpass.getpass("確認密碼: ")
    if password != confirm:
        print("錯誤：兩次輸入的密碼不一致。", file=sys.stderr)
        sys.exit(1)
    return username, email, password


async def _create_admin(username: str, email: str, password: str) -> None:
    if not username or not email or not password:
        print("錯誤：帳號、Email、密碼皆為必填。", file=sys.stderr)
        sys.exit(1)

    async with SessionLocal() as db:
        existing = await db.execute(
            select(User).where((User.username == username) | (User.email == email))
        )
        if existing.scalar_one_or_none():
            print(f"錯誤：帳號「{username}」或 Email「{email}」已存在，未建立新帳號。", file=sys.stderr)
            sys.exit(1)

        db.add(User(username=username, email=email, hashed_password=hash_password(password)))
        try:
            await db.commit()
        except IntegrityError:
            await db.rollback()
            print(f"錯誤：帳號「{username}」或 Email「{email}」已存在，未建立新帳號。", file=sys.stderr)
            sys.exit(1)

    print(f"已建立管理者帳號：{username}")


def main() -> None:
    parser = argparse.ArgumentParser(prog="python -m app.cli")
    subparsers = parser.add_subparsers(dest="command", required=True)
    subparsers.add_parser("create-admin", help="建立管理者帳號（單一管理者，重複執行不會建立重複帳號）")

    args = parser.parse_args()
    if args.command == "create-admin":
        username, email, password = _read_credentials()
        asyncio.run(_create_admin(username, email, password))


if __name__ == "__main__":
    main()
