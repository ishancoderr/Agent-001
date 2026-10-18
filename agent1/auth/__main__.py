"""Manage the workbench accounts in config/users.yaml.

    python -m agent1.auth add-user <username> [--name "Full Name"]   asks for the password twice
    python -m agent1.auth remove-user <username>
    python -m agent1.auth list-users

--password-stdin reads the password from standard input instead (for scripts).
"""
from __future__ import annotations

import argparse
import getpass
import re
import sys

from .users import USERS_PATH, hash_password, load_users, save_users

MIN_PASSWORD_LENGTH = 10


def main() -> None:
    ap = argparse.ArgumentParser(prog="python -m agent1.auth", description=__doc__.split("\n\n")[0])
    sub = ap.add_subparsers(dest="command", required=True)
    add = sub.add_parser("add-user", help="add an account, or set a new password for one")
    add.add_argument("username")
    add.add_argument("--name", help="display name shown in the workbench")
    add.add_argument("--password-stdin", action="store_true", help="read the password from stdin")
    rm = sub.add_parser("remove-user", help="delete an account")
    rm.add_argument("username")
    sub.add_parser("list-users", help="show the accounts (never the passwords)")
    args = ap.parse_args()

    users = load_users()
    if args.command == "list-users":
        print(f"{USERS_PATH}:")
        for name, account in sorted(users.items()):
            print(f"  {name:<20} {account.get('name', '')}")
        if not users:
            print("  (no accounts yet — add one with add-user)")
        return

    if args.command == "remove-user":
        if users.pop(args.username, None) is None:
            sys.exit(f"no account {args.username!r}")
        save_users(users)
        print(f"removed {args.username}")
        return

    if not re.fullmatch(r"[A-Za-z0-9_.-]{1,64}", args.username):
        sys.exit("a username may use letters, digits, '.', '_' and '-' (at most 64)")
    if args.password_stdin:
        password = sys.stdin.readline().rstrip("\n")
    else:
        password = getpass.getpass("Password: ")
        if getpass.getpass("Repeat password: ") != password:
            sys.exit("the passwords don't match")
    if len(password) < MIN_PASSWORD_LENGTH:
        sys.exit(f"use at least {MIN_PASSWORD_LENGTH} characters")
    existed = args.username in users
    users[args.username] = {"name": args.name or users.get(args.username, {}).get("name") or args.username,
                            "password_hash": hash_password(password)}
    save_users(users)
    print(f"{'updated' if existed else 'added'} {args.username} in {USERS_PATH}")


if __name__ == "__main__":
    main()
