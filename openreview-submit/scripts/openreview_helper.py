#!/usr/bin/env python3
"""Utilities for inspecting and editing OpenReview submissions."""

from __future__ import annotations

import argparse
import getpass
import json
import os
import sys
from typing import Any


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="OpenReview helper utilities")
    parser.add_argument(
        "--baseurl",
        default="https://api2.openreview.net",
        help="OpenReview API base URL.",
    )
    parser.add_argument("--username", help="OpenReview username/email.")
    parser.add_argument("--password", help="OpenReview password.")
    parser.add_argument("--token", help="OpenReview token.")

    subparsers = parser.add_subparsers(dest="command", required=True)

    inspect_parser = subparsers.add_parser("inspect-submission")
    inspect_parser.add_argument("--forum-id", required=True)

    list_parser = subparsers.add_parser("list-own-notes")
    list_parser.add_argument("--signature", required=True)
    list_parser.add_argument("--limit", type=int, default=1000)

    search_parser = subparsers.add_parser("search-profiles")
    search_parser.add_argument("--name", required=True)
    search_parser.add_argument("--limit", type=int, default=10)

    update_parser = subparsers.add_parser("update-authors")
    update_parser.add_argument("--forum-id", required=True)
    update_parser.add_argument("--signature", required=True)
    update_parser.add_argument("--authors-json", required=True)
    update_parser.add_argument("--authorids-json", required=True)
    update_parser.add_argument(
        "--invitation-id",
        help="Override invitation id. Default: current note invitation.",
    )
    update_parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print the edit payload without posting it.",
    )

    return parser


def get_openreview_client(args: argparse.Namespace) -> Any:
    try:
        import openreview
    except ImportError as exc:
        raise SystemExit("Install openreview-py before using this skill.") from exc

    token = args.token or os.environ.get("OPENREVIEW_TOKEN")
    username = args.username or os.environ.get("OPENREVIEW_USERNAME")
    password = args.password or os.environ.get("OPENREVIEW_PASSWORD")

    if token:
        return openreview.api.OpenReviewClient(baseurl=args.baseurl, token=token), openreview

    if not username and sys.stdin.isatty():
        username = input("OpenReview email: ").strip()
    if not password and sys.stdin.isatty():
        password = getpass.getpass("OpenReview password: ")

    if not username or not password:
        raise SystemExit(
            "Provide OPENREVIEW_TOKEN or OPENREVIEW_USERNAME and OPENREVIEW_PASSWORD."
        )

    client = openreview.api.OpenReviewClient(
        baseurl=args.baseurl,
        username=username,
        password=password,
    )
    return client, openreview


def print_json(payload: Any) -> None:
    print(json.dumps(payload, ensure_ascii=False, indent=2))


def command_inspect_submission(client: Any, args: argparse.Namespace) -> int:
    note = client.get_note(args.forum_id)
    payload = {
        "id": note.id,
        "forum": note.forum,
        "number": getattr(note, "number", None),
        "invitation": (getattr(note, "invitations", None) or [None])[0],
        "title": (note.content or {}).get("title", {}).get("value"),
        "authors": (note.content or {}).get("authors", {}).get("value"),
        "authorids": (note.content or {}).get("authorids", {}).get("value"),
        "content_keys": sorted(list((note.content or {}).keys())),
        "license": getattr(note, "license", None),
        "cdate": getattr(note, "cdate", None),
        "pdate": getattr(note, "pdate", None),
        "mdate": getattr(note, "mdate", None),
        "readers": getattr(note, "readers", None),
        "writers": getattr(note, "writers", None),
        "signatures": getattr(note, "signatures", None),
    }
    print_json(payload)
    return 0


def command_list_own_notes(client: Any, args: argparse.Namespace) -> int:
    notes = client.get_notes(signature=args.signature, limit=args.limit)
    rows = []
    for note in notes:
        content = note.content or {}
        title = content.get("title", {}).get("value")
        if not title:
            continue
        rows.append(
            {
                "id": note.id,
                "number": getattr(note, "number", None),
                "invitation": (getattr(note, "invitations", None) or [None])[0],
                "title": title,
                "authors": content.get("authors", {}).get("value"),
                "authorids": content.get("authorids", {}).get("value"),
            }
        )
    print_json(rows)
    return 0


def command_search_profiles(client: Any, args: argparse.Namespace) -> int:
    profiles = client.search_profiles(term=args.name)
    rows = []
    for profile in profiles[: args.limit]:
        content = getattr(profile, "content", {}) or {}
        rows.append(
            {
                "id": profile.id,
                "fullname": (content.get("names", [{}]) or [{}])[0].get("fullname"),
                "history": content.get("history", [])[:3],
            }
        )
    print_json(rows)
    return 0


def command_update_authors(
    client: Any, openreview: Any, args: argparse.Namespace
) -> int:
    note = client.get_note(args.forum_id)
    invitation_id = args.invitation_id or (note.invitations or [None])[0]
    if not invitation_id:
        raise SystemExit("Could not determine invitation id for the target note.")

    invitation = client.get_invitation(invitation_id)
    allowed = set(
        (((getattr(invitation, "edit", None) or {}).get("note", {}) or {}).get("content", {})).keys()
    )
    if not allowed:
        raise SystemExit("Could not determine allowed content fields from invitation.")

    try:
        authors = json.loads(args.authors_json)
        authorids = json.loads(args.authorids_json)
    except json.JSONDecodeError as exc:
        raise SystemExit("authors-json and authorids-json must be valid JSON arrays.") from exc

    if not isinstance(authors, list) or not isinstance(authorids, list):
        raise SystemExit("authors-json and authorids-json must decode to arrays.")
    if len(authors) != len(authorids):
        raise SystemExit("authors and authorids must have the same length.")

    content = {key: value for key, value in (note.content or {}).items() if key in allowed}
    content["authors"] = {"value": authors}
    content["authorids"] = {"value": authorids}

    payload = {
        "invitation": invitation_id,
        "signatures": [args.signature],
        "note": {
            "id": args.forum_id,
            "content": content,
            "license": getattr(note, "license", None),
        },
    }

    if args.dry_run:
        print_json(payload)
        return 0

    response = client.post_note_edit(
        invitation=invitation_id,
        signatures=[args.signature],
        note=openreview.api.Note(
            id=args.forum_id,
            content=content,
            license=getattr(note, "license", None),
        ),
        await_process=True,
    )
    updated = client.get_note(args.forum_id)
    print_json(
        {
            "edit_id": response.get("id"),
            "authors": updated.content.get("authors", {}).get("value"),
            "authorids": updated.content.get("authorids", {}).get("value"),
        }
    )
    return 0


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    client, openreview = get_openreview_client(args)

    if args.command == "inspect-submission":
        return command_inspect_submission(client, args)
    if args.command == "list-own-notes":
        return command_list_own_notes(client, args)
    if args.command == "search-profiles":
        return command_search_profiles(client, args)
    if args.command == "update-authors":
        return command_update_authors(client, openreview, args)
    parser.error(f"Unknown command: {args.command}")
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
