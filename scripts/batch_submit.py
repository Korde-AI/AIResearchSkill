#!/usr/bin/env python3
"""Batch-submit OpenReview papers from CSV, JSON, or JSONL."""

from __future__ import annotations

import argparse
import csv
import getpass
import json
import os
import sys
from pathlib import Path
from typing import Any


DEFAULT_LIST_FIELDS = {
    "authors",
    "authorids",
    "keywords",
    "signatures",
    "readers",
    "writers",
    "nonreaders",
}
DEFAULT_ATTACHMENT_FIELDS = {"pdf"}
META_FIELDS = {
    "submission_invitation",
    "signatures",
    "signature",
    "readers",
    "writers",
    "nonreaders",
    "license",
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Batch-submit papers to OpenReview API v2."
    )
    parser.add_argument(
        "--input-file",
        required=True,
        help="CSV, JSON, or JSONL file describing one submission per record.",
    )
    parser.add_argument(
        "--input-format",
        choices=("csv", "json", "jsonl"),
        help="Override input format detection from file extension.",
    )
    parser.add_argument("--venue-id")
    parser.add_argument("--invitation-id")
    parser.add_argument(
        "--baseurl",
        default="https://api2.openreview.net",
        help="OpenReview API base URL.",
    )
    parser.add_argument("--username")
    parser.add_argument("--password")
    parser.add_argument("--token")
    parser.add_argument("--signature")
    parser.add_argument("--default-readers")
    parser.add_argument("--default-writers")
    parser.add_argument("--default-nonreaders")
    parser.add_argument(
        "--list-fields",
        default=",".join(sorted(DEFAULT_LIST_FIELDS)),
    )
    parser.add_argument(
        "--attachment-fields",
        default=",".join(sorted(DEFAULT_ATTACHMENT_FIELDS)),
    )
    parser.add_argument("--csv-list-separator", default=";")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--await-process", action="store_true")
    parser.add_argument("--stop-on-error", action="store_true")
    return parser.parse_args()


def split_csv_value(raw_value: str, separator: str) -> list[str]:
    items = [part.strip() for part in raw_value.split(separator)]
    return [item for item in items if item]


def parse_jsonish(raw_value: str) -> Any:
    stripped = raw_value.strip()
    if not stripped:
        return ""
    if stripped[0] not in "[{":
        return raw_value
    try:
        return json.loads(stripped)
    except json.JSONDecodeError:
        return raw_value


def clean_record(record: dict[str, Any]) -> dict[str, Any]:
    cleaned: dict[str, Any] = {}
    for key, value in record.items():
        if key is None:
            continue
        normalized_key = key.strip()
        if normalized_key == "":
            continue
        if value is None:
            continue
        if isinstance(value, str):
            stripped = value.strip()
            if stripped == "":
                continue
            cleaned[normalized_key] = stripped
            continue
        cleaned[normalized_key] = value
    return cleaned


def infer_input_format(input_path: Path) -> str:
    suffix = input_path.suffix.lower()
    if suffix == ".csv":
        return "csv"
    if suffix == ".json":
        return "json"
    if suffix in {".jsonl", ".ndjson"}:
        return "jsonl"
    raise ValueError(
        f"Could not infer input format from {input_path.name}. Use --input-format."
    )


def load_records(input_path: Path, input_format: str | None) -> list[dict[str, Any]]:
    chosen_format = input_format or infer_input_format(input_path)
    if chosen_format == "csv":
        with input_path.open("r", encoding="utf-8", newline="") as handle:
            return [
                cleaned
                for row in csv.DictReader(handle)
                for cleaned in [clean_record(row)]
                if cleaned
            ]
    if chosen_format == "json":
        with input_path.open("r", encoding="utf-8") as handle:
            payload = json.load(handle)
        if not isinstance(payload, list):
            raise ValueError("JSON input must be a list of submission objects.")
        return [clean_record(item) for item in payload]
    if chosen_format == "jsonl":
        records = []
        with input_path.open("r", encoding="utf-8") as handle:
            for line_number, line in enumerate(handle, start=1):
                stripped = line.strip()
                if not stripped:
                    continue
                try:
                    payload = json.loads(stripped)
                except json.JSONDecodeError as exc:
                    raise ValueError(
                        f"Invalid JSON on line {line_number} of {input_path}"
                    ) from exc
                if not isinstance(payload, dict):
                    raise ValueError(
                        f"JSONL line {line_number} must contain an object record."
                    )
                records.append(clean_record(payload))
        return records
    raise ValueError(f"Unsupported input format: {chosen_format}")


def normalize_scalar_or_list(
    field_name: str,
    value: Any,
    list_fields: set[str],
    separator: str,
) -> Any:
    if field_name not in list_fields:
        return value
    if isinstance(value, list):
        return value
    if isinstance(value, str):
        maybe_json = parse_jsonish(value)
        if isinstance(maybe_json, list):
            return maybe_json
        return split_csv_value(value, separator)
    return value


def resolve_file_path(raw_path: str, input_dir: Path) -> Path:
    path = Path(raw_path).expanduser()
    if path.is_absolute():
        return path
    return (input_dir / path).resolve()


def get_openreview_client(args: argparse.Namespace) -> tuple[Any | None, Any]:
    if args.dry_run:
        class DryRunOpenReview:
            class api:
                class Note:
                    def __init__(self, **kwargs: Any) -> None:
                        self.kwargs = kwargs

                    def to_json(self) -> dict[str, Any]:
                        return self.kwargs

        return None, DryRunOpenReview()

    try:
        import openreview
    except ImportError as exc:
        raise SystemExit("Install openreview-py before using this skill.") from exc

    token = args.token or os.environ.get("OPENREVIEW_TOKEN")
    username = args.username or os.environ.get("OPENREVIEW_USERNAME")
    password = args.password or os.environ.get("OPENREVIEW_PASSWORD")

    if token:
        return (
            openreview.api.OpenReviewClient(baseurl=args.baseurl, token=token),
            openreview,
        )

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


def build_submission_payload(
    record: dict[str, Any],
    *,
    args: argparse.Namespace,
    input_dir: Path,
    list_fields: set[str],
    attachment_fields: set[str],
    openreview_module: Any,
    client: Any | None,
) -> tuple[str, list[str], list[str] | None, list[str] | None, list[str] | None, Any]:
    invitation_id = record.get("submission_invitation") or args.invitation_id
    if not invitation_id:
        if not args.venue_id:
            raise ValueError("Provide --venue-id or --invitation-id.")
        invitation_id = f"{args.venue_id}/-/Submission"

    content: dict[str, dict[str, Any]] = {}
    for field_name, raw_value in record.items():
        if field_name in META_FIELDS:
            continue
        value = normalize_scalar_or_list(
            field_name, raw_value, list_fields, args.csv_list_separator
        )
        if field_name in attachment_fields:
            if not isinstance(value, str):
                raise ValueError(
                    f"Attachment field '{field_name}' must contain a file path string."
                )
            if value.startswith("/pdf/"):
                content[field_name] = {"value": value}
                continue
            file_path = resolve_file_path(value, input_dir)
            if not file_path.exists():
                raise FileNotFoundError(f"Attachment not found: {file_path}")
            if client is None:
                uploaded_value = str(file_path)
            else:
                uploaded_value = client.put_attachment(
                    str(file_path), invitation_id, field_name
                )
            content[field_name] = {"value": uploaded_value}
            continue
        content[field_name] = {"value": value}

    signature_value = record.get("signatures") or record.get("signature") or args.signature
    signatures = normalize_scalar_or_list(
        "signatures", signature_value, {"signatures"}, args.csv_list_separator
    )
    if isinstance(signatures, str):
        signatures = [signatures]
    if not signatures:
        raise ValueError(
            "Missing signatures. Pass --signature or include signature/signatures per row."
        )

    authorids = content.get("authorids", {}).get("value")
    auto_permissions = None
    if isinstance(authorids, list) and args.venue_id:
        auto_permissions = [args.venue_id] + authorids

    readers = normalize_scalar_or_list(
        "readers",
        record.get("readers") or args.default_readers,
        {"readers"},
        args.csv_list_separator,
    )
    writers = normalize_scalar_or_list(
        "writers",
        record.get("writers") or args.default_writers,
        {"writers"},
        args.csv_list_separator,
    )
    nonreaders = normalize_scalar_or_list(
        "nonreaders",
        record.get("nonreaders") or args.default_nonreaders,
        {"nonreaders"},
        args.csv_list_separator,
    )

    if readers is None and auto_permissions is not None:
        readers = auto_permissions
    if writers is None and auto_permissions is not None:
        writers = auto_permissions

    note_kwargs: dict[str, Any] = {"content": content}
    if "license" in record:
        note_kwargs["license"] = record["license"]
    note = openreview_module.api.Note(**note_kwargs)
    return invitation_id, signatures, readers, writers, nonreaders, note


def main() -> int:
    args = parse_args()
    input_path = Path(args.input_file).expanduser().resolve()
    if not input_path.exists():
        print(f"Input file not found: {input_path}", file=sys.stderr)
        return 2

    records = load_records(input_path, args.input_format)
    if not records:
        print("No submissions found in input file.", file=sys.stderr)
        return 2

    list_fields = {
        field.strip() for field in args.list_fields.split(",") if field.strip()
    }
    attachment_fields = {
        field.strip() for field in args.attachment_fields.split(",") if field.strip()
    }

    client, openreview_module = get_openreview_client(args)

    successes = 0
    failures = 0
    for index, record in enumerate(records, start=1):
        try:
            (
                invitation_id,
                signatures,
                readers,
                writers,
                nonreaders,
                note,
            ) = build_submission_payload(
                record,
                args=args,
                input_dir=input_path.parent,
                list_fields=list_fields,
                attachment_fields=attachment_fields,
                openreview_module=openreview_module,
                client=client,
            )
            title = record.get("title", "<untitled>")
            if args.dry_run:
                print(f"[DRY-RUN] Submission {index}: {title}")
                print(
                    json.dumps(
                        {
                            "invitation": invitation_id,
                            "signatures": signatures,
                            "readers": readers,
                            "writers": writers,
                            "nonreaders": nonreaders,
                            "note": note.to_json(),
                        },
                        ensure_ascii=False,
                        indent=2,
                    )
                )
            else:
                response = client.post_note_edit(
                    invitation=invitation_id,
                    signatures=signatures,
                    readers=readers,
                    writers=writers,
                    nonreaders=nonreaders,
                    note=note,
                    await_process=args.await_process,
                )
                print(
                    f"[OK] Submission {index}: {title} -> edit {response.get('id', '<unknown>')}"
                )
            successes += 1
        except Exception as exc:  # noqa: BLE001
            failures += 1
            print(f"[ERROR] Submission {index} failed: {exc}", file=sys.stderr)
            if args.stop_on_error:
                break

    print(
        f"Finished with {successes} success(es) and {failures} failure(s).",
        file=sys.stderr if failures else sys.stdout,
    )
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
