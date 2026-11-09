#!/usr/bin/env python3
"""Optional, private PRD Screen Fidelity history. Python 3.10+, stdlib only."""
import argparse
from collections import Counter
from contextlib import closing, contextmanager
from copy import deepcopy
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import re
import shutil
import sqlite3
import stat
import subprocess
import sys
import tempfile
import uuid
import zipfile

SKILL_DIR = Path(__file__).resolve().parents[1]
SCHEMA_VERSION = "1.0"
DEFAULT_LIMITS = {"max_files": 1000, "max_file_bytes": 20 * 1024 * 1024,
                  "max_total_bytes": 100 * 1024 * 1024}


class HistoryError(Exception):
    def __init__(self, message, code=2):
        super().__init__(message)
        self.code = code


def now():
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def canonical(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True,
                      separators=(",", ":"), allow_nan=False).encode("utf-8")


def sha(data):
    return hashlib.sha256(data).hexdigest()


def digest(record):
    return sha(canonical({k: v for k, v in record.items() if k != "content_digest"}))


def no_links(path):
    path = Path(os.path.abspath(path))
    for part in (path, *path.parents):
        if part.is_symlink() or (part.exists() and getattr(part.lstat(), "st_file_attributes", 0) & 0x400):
            raise HistoryError("Symlink/junction access refused", 4)
    return path


def inside(root, relative):
    # Treat Windows separators as separators on every host, including ZIP input.
    value = str(relative).replace("\\", "/")
    p = PurePosixPath(value)
    if not value or p.is_absolute() or any(s in ("..", "") for s in p.parts) or ":" in value:
        raise HistoryError("Unsafe relative path", 2)
    root = no_links(root)
    target = no_links(root.joinpath(*p.parts))
    if not target.is_relative_to(root):
        raise HistoryError("Path escapes storage root", 2)
    return target


def read_json(path):
    try:
        return json.loads(no_links(path).read_text(encoding="utf-8-sig"),
                          parse_constant=lambda _: (_ for _ in ()).throw(ValueError()))
    except (ValueError, UnicodeError):
        raise HistoryError("Invalid JSON (contents omitted)") from None


def parse_json(data):
    return json.loads(data, parse_constant=lambda _: (_ for _ in ()).throw(ValueError("Non-finite JSON number")))


def atomic(path, data):
    path = no_links(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temporary = tempfile.mkstemp(prefix=".pending-", dir=path.parent)
    try:
        with os.fdopen(fd, "wb") as stream:
            stream.write(data)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, path)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)


def save_json(path, value):
    atomic(path, canonical(value) + b"\n")


@contextmanager
def locked(root):
    # ponytail: one OS lock per history store; shard only if measured contention warrants it.
    root = no_links(root)
    root.mkdir(parents=True, exist_ok=True)
    with inside(root, ".lock").open("a+b") as handle:
        handle.seek(0)
        if os.name == "nt":
            import msvcrt
            handle.write(b"0")
            handle.flush()
            handle.seek(0)
            try:
                msvcrt.locking(handle.fileno(), msvcrt.LK_NBLCK, 1)
            except OSError:
                raise HistoryError("History store busy; retry the command", 3) from None
        else:
            import fcntl
            try:
                fcntl.flock(handle, fcntl.LOCK_EX | fcntl.LOCK_NB)
            except OSError:
                raise HistoryError("History store busy; retry the command", 3) from None
        try:
            yield
        finally:
            if os.name == "nt":
                handle.seek(0)
                msvcrt.locking(handle.fileno(), msvcrt.LK_UNLCK, 1)
            else:
                fcntl.flock(handle, fcntl.LOCK_UN)


def schema_errors(value, schema, top=None, location="record"):
    """Validate the deliberately small JSON Schema subset used by our two schemas."""
    top = top or schema
    if "$ref" in schema:
        return schema_errors(value, top["$defs"][schema["$ref"].split("/")[-1]], top, location)
    if "anyOf" in schema:
        return [] if any(not schema_errors(value, s, top, location) for s in schema["anyOf"]) else [location + ": invalid alternative"]
    kinds = {"object": dict, "array": list, "string": str, "integer": int,
             "number": (int, float), "boolean": bool, "null": type(None)}
    expected = schema.get("type")
    if expected:
        expected = [expected] if isinstance(expected, str) else expected
        if not any(isinstance(value, kinds[k]) and not (k in ("integer", "number") and isinstance(value, bool)) for k in expected):
            return [location + ": wrong type"]
    errors = []
    if "enum" in schema and value not in schema["enum"]:
        errors.append(location + ": invalid enum")
    if isinstance(value, dict):
        errors.extend(location + ": missing " + k for k in schema.get("required", []) if k not in value)
        for k, v in value.items():
            if k in schema.get("properties", {}):
                errors.extend(schema_errors(v, schema["properties"][k], top, location + "." + k))
            elif schema.get("additionalProperties") is False:
                errors.append(location + ": unknown field")
    if isinstance(value, list):
        for i, v in enumerate(value):
            errors.extend(schema_errors(v, schema.get("items", {}), top, f"{location}[{i}]"))
    if isinstance(value, str):
        if len(value) < schema.get("minLength", 0) or len(value) > schema.get("maxLength", float("inf")):
            errors.append(location + ": invalid length")
        if "pattern" in schema and not re.fullmatch(schema["pattern"], value):
            errors.append(location + ": invalid pattern")
    if isinstance(value, (int, float)) and value < schema.get("minimum", -float("inf")):
        errors.append(location + ": below minimum")
    return errors


def validate_record(record):
    errors = schema_errors(record, read_json(SKILL_DIR / "schemas/usage-record.schema.json"))
    if errors:
        return errors
    r = record
    try:
        if str(uuid.UUID(r["run_id"])) != r["run_id"]:
            errors.append("run_id must be canonical UUID")
        for key in ("recorded_at", "ended_at", "last_edited_at"):
            if r.get(key) is not None and datetime.fromisoformat(r[key]).utcoffset() is None:
                errors.append(key + " needs timezone")
        occurrence = r["occurred_at"]
        if r["time_precision"] == "unknown" and occurrence is not None:
            errors.append("Unknown occurrence must be null")
        elif r["time_precision"] == "date_only":
            if not isinstance(occurrence, str) or not re.fullmatch(r"\d{4}-\d{2}-\d{2}", occurrence):
                errors.append("date_only requires a date without invented time")
            else:
                datetime.strptime(occurrence, "%Y-%m-%d")
        elif r["time_precision"] == "exact":
            if not occurrence or datetime.fromisoformat(occurrence).utcoffset() is None:
                errors.append("Exact occurrence needs timezone")
    except (ValueError, TypeError):
        errors.append("Invalid UUID or timestamp")
    if (r["revision"] == 1) != (r["parent_digest"] is None):
        errors.append("Revision/parent mismatch")
    if r.get("content_digest") and r["content_digest"] != digest(r):
        errors.append("Record content digest mismatch")
    if r["lifecycle"] == "finished" and not r.get("ended_at"):
        errors.append("Finished requires an explicit end timestamp")
    evidence = {e["evidence_id"]: e for e in r["evidence"]}
    if len(evidence) != len(r["evidence"]):
        errors.append("Duplicate evidence ID")
    for e in evidence.values():
        for key in ("reviewed_at", "captured_at"):
            if e.get(key):
                try:
                    if datetime.fromisoformat(e[key]).utcoffset() is None:
                        errors.append("Evidence timestamp needs timezone")
                except ValueError:
                    errors.append("Invalid evidence timestamp")
        if e.get("relative_path"):
            try:
                p = PurePosixPath(e["relative_path"])
                if len(p.parts) != 4 or p.parts[:3] != ("records", r["run_id"], "evidence"):
                    raise HistoryError("Evidence path must belong to this run")
                inside(Path(tempfile.gettempdir()), e["relative_path"])
            except HistoryError:
                errors.append("Unsafe evidence path")
        if e.get("derived_from") and e["derived_from"] == e.get("sha256"):
            errors.append("Redaction must have a new hash")
    if errors:
        return errors
    def reviewed(ids, final=False):
        for ident in ids:
            e = evidence.get(ident, {})
            if e.get("availability") != "available" or not e.get("sha256") or not e.get("reviewed_by") or not e.get("reviewed_at"):
                continue
            if not final or (e.get("kind") == "final_capture" and
                             (not r.get("last_edited_at") or (e.get("captured_at") and
                              datetime.fromisoformat(e["captured_at"]) >= datetime.fromisoformat(r["last_edited_at"])))):
                return True
        return False
    for s in r["screen_checks"]:
        if any(i not in evidence for i in s["evidence_ids"]):
            errors.append("Unknown screen evidence ID")
        if s["visual_verification"] == "not_verified" and s["visual_outcome"] != "undetermined":
            errors.append("Unverified screen outcome must be undetermined")
        if s["visual_verification"] == "compared" and not reviewed(s["evidence_ids"]):
            errors.append("Compared screen needs explicitly reviewed evidence")
        if s["visual_outcome"] == "authorized_deviations" and not s.get("authority_ref"):
            errors.append("Deviation requires actual authority reference")
    for f in r["findings"]:
        if f["status"] == "fixed_verified" and not reviewed(f["evidence_ids"], final=True):
            errors.append("Verified fix requires reviewed post-edit evidence")
        if f["status"] == "authorized_deviation" and not f.get("authority_ref"):
            errors.append("Authorized finding requires authority reference")
    o, screens = r["outcomes"], r["screen_checks"]
    verified = [s["visual_verification"] for s in screens]
    expected_verification = ("compared" if verified and all(v == "compared" for v in verified)
                             else "partial" if any(v != "not_verified" for v in verified) else "not_verified")
    if o["visual_verification"] != expected_verification:
        errors.append("Aggregate verification conflicts with actual coverage")
    if o["visual_verification"] == "compared" and (not screens or any(s["visual_verification"] != "compared" for s in screens)):
        errors.append("Aggregate compared requires all screen checks compared")
    if o["visual_verification"] == "not_verified" and o["visual_outcome"] != "undetermined":
        errors.append("Unverified outcome must remain undetermined")
    visual_failure = any(s["visual_outcome"] == "needs_correction" for s in screens) or any(
        f["status"] == "open" and f["severity"] in ("blocking", "major") for f in r["findings"])
    if visual_failure and o["visual_outcome"] != "needs_correction":
        errors.append("Known visual correction has priority")
    if o["visual_outcome"] in ("meets_requirements", "authorized_deviations"):
        if not screens or o["visual_verification"] != "compared" or any(s["visual_outcome"] not in ("meets_requirements", "authorized_deviations") for s in screens):
            errors.append("Visual acceptance requires accepted compared screens")
        if o["visual_outcome"] == "authorized_deviations" and not any(s.get("authority_ref") for s in screens):
            errors.append("Aggregate deviation requires authority")
    required = [f for f in r["functional_checks"] if f["required"]]
    checks = required or r["functional_checks"]
    if any(f["result"] == "failed" for f in checks):
        functional = "failed"
    elif not checks:
        functional = "not_verified"
    elif all(f["result"] == "passed" for f in checks):
        functional = "passed"
    elif all(f["result"] == "not_applicable" and f.get("reason") for f in checks):
        functional = "not_applicable"
    else:
        functional = "partial" if any(f["result"] in ("passed", "failed", "not_applicable") for f in checks) else "not_verified"
    if o["functional_outcome"] != functional:
        errors.append("Functional outcome conflicts with check results")
    if o["delivery_status"] == "complete":
        if r["lifecycle"] != "finished":
            errors.append("Complete delivery requires finished lifecycle")
        if r["task_type"] != "compare":
            if r["task_type"] == "unknown" or o["visual_outcome"] not in ("meets_requirements", "authorized_deviations") or functional not in ("passed", "not_applicable"):
                errors.append("Implementation cannot complete with unresolved checks")
            if any(not reviewed(s["evidence_ids"], final=True) for s in screens):
                errors.append("Implementation needs final post-edit captures")
    if r["skill"]["activation_evidence"] == "confirmed_load" and not r["source_refs"]:
        errors.append("Confirmed load requires a source locator")
    return errors


def new_record(project, alias=None, task="unknown", kind="live_run"):
    return {"schema_version": SCHEMA_VERSION, "run_id": str(uuid.uuid4()), "revision": 1,
            "parent_digest": None, "record_kind": kind, "project_id": project,
            "project_alias": alias, "task_type": task, "task_summary": "",
            "occurred_at": now() if kind == "live_run" else None, "recorded_at": now(),
            "time_precision": "exact" if kind == "live_run" else "unknown",
            "skill": {"name": "prd-screen-fidelity", "version": None, "commit": None,
                      "instruction_hashes": [], "activation_evidence": "unknown"},
            "environment": {"host": None, "host_version": None, "model": None, "os": None},
            "lifecycle": "started" if kind == "live_run" else "unknown", "ended_at": None,
            "source_refs": [], "screen_checks": [], "functional_checks": [], "evidence": [],
            "findings": [], "outcomes": {"visual_verification": "not_verified",
            "visual_outcome": "undetermined", "functional_outcome": "not_verified", "delivery_status": "unknown"},
            "collection": {"mode": "local" if kind == "live_run" else "manual_import",
                           "record_validation": "pending", "review_state": "received", "aggregate": False},
            "privacy": {"visibility": "private", "public_export_allowed": False, "sensitive_review": "pending"},
            "change_reason": "Initial record"}


def patch_record(record, patch):
    for key, value in patch.items():
        if isinstance(value, dict) and isinstance(record.get(key), dict):
            patch_record(record[key], value)
        else:
            record[key] = deepcopy(value)
    return record


class Store:
    def __init__(self, root):
        self.root = no_links(root)
        if self.root.is_relative_to(SKILL_DIR):
            raise HistoryError("History must be outside the installed skill")

    def path(self, relative):
        return inside(self.root, relative)

    def config(self):
        p = self.path("config.json")
        if not p.exists():
            raise HistoryError("History not configured; run init explicitly", 4)
        return read_json(p)

    def enabled(self):
        return self.config()["mode"] != "off"

    def registry(self):
        return read_json(self.path("sources/registry.json"))

    def latest(self, run_id):
        if str(uuid.UUID(run_id)) != run_id:
            raise HistoryError("Invalid run ID")
        files = sorted(self.path(f"records/{run_id}/revisions").glob("*/record.json"))
        if not files:
            raise HistoryError("Run not found", 4)
        return read_json(files[-1])

    def records(self):
        result, errors = [], []
        for directory in sorted(self.path("records").glob("*")):
            try:
                no_links(directory)
                records = sorted(directory.glob("revisions/*/record.json"))
                previous = None
                for path in records:
                    record = read_json(path)
                    issues = validate_record(record)
                    if issues or record["run_id"] != directory.name or record["revision"] != (previous["revision"] + 1 if previous else 1) or record["parent_digest"] != (digest(previous) if previous else None):
                        raise HistoryError("Invalid stored revision chain")
                    previous = record
                if previous:
                    result.append(previous)
            except (HistoryError, OSError, ValueError, TypeError):
                errors.append({"item": directory.name, "status": "invalid"})
        return result, errors

    def quarantine(self, data, reason):
        ident = sha(data)
        folder = self.path(f"quarantine/{ident}")
        save_json(folder / "receipt.json", {"status": reason, "file_sha256": ident})
        atomic(folder / "payload.bin", data)
        return ident

    def put(self, record, dry_run=False, preview=None):
        errors = validate_record(record)
        if errors:
            if not dry_run:
                self.quarantine(canonical(record), "invalid_record")
            return {"run_id": record.get("run_id"), "status": "invalid", "errors": errors}
        r = deepcopy(record)
        r["content_digest"] = digest(r)
        path = self.path(f"records/{r['run_id']}/revisions/{r['revision']:04d}/record.json")
        key = (r["run_id"], r["revision"])
        old = preview.get(key) if preview is not None else None
        if path.exists() or old:
            if digest(old or read_json(path)) == r["content_digest"]:
                return {"run_id": r["run_id"], "status": "duplicate"}
            if not dry_run:
                self.quarantine(canonical(r), "revision_conflict")
            return {"run_id": r["run_id"], "status": "conflict"}
        if r["revision"] == 1 and r["record_kind"] == "historical_import" and r["source_refs"]:
            # The first source ref identifies the original execution interval; others add context.
            origin = r["source_refs"][0]
            if origin["content_hash"]:
                existing, _ = self.records()
                existing += list((preview or {}).values())
                duplicate = next((v for v in existing if v["record_kind"] == "historical_import" and v["source_refs"] and
                                  (v["source_refs"][0]["content_hash"], v["source_refs"][0]["locator"]) == (origin["content_hash"], origin["locator"])), None)
                if duplicate:
                    return {"run_id": duplicate["run_id"], "status": "duplicate", "basis": "source_hash_and_interval"}
        if r["revision"] > 1:
            try:
                parent = (preview or {}).get((r["run_id"], r["revision"] - 1)) or self.latest(r["run_id"])
            except HistoryError:
                parent = None
            if not parent or r["parent_digest"] != digest(parent) or r["revision"] != parent["revision"] + 1:
                if not dry_run:
                    self.quarantine(canonical(r), "parent_conflict")
                return {"run_id": r["run_id"], "status": "conflict"}
        if not dry_run:
            save_json(path, r)
            if r["record_kind"] == "historical_import" and r["source_refs"]:
                ref = r["source_refs"][0]
                candidate = self.path(f"imports/candidates/{sha(canonical([ref['content_hash'], ref['locator']]))}.json")
                if candidate.exists():
                    linked = read_json(candidate)
                    linked.update(status="linked", run_id=r["run_id"])
                    save_json(candidate, linked)
        elif preview is not None:
            preview[key] = r
        return {"run_id": r["run_id"], "revision": r["revision"], "status": "planned" if dry_run else "stored"}

    def evidence_status(self, record):
        statuses = []
        for e in record["evidence"]:
            status = "external_unchecked"
            if e.get("relative_path"):
                try:
                    p = self.path(e["relative_path"])
                    status = "missing" if not p.is_file() else "available" if sha(p.read_bytes()) == e["sha256"] else "hash_mismatch"
                except (HistoryError, OSError):
                    status = "blocked"
            statuses.append({"evidence_id": e["evidence_id"], "status": status})
        return statuses


def import_files(store, source_id, dry=False):
    registry = store.registry()
    source = next((s for s in registry["sources"] if s["source_id"] == source_id), None)
    if not source:
        raise HistoryError("Source not registered")
    unavailable = "not_configured" if not source["location"] else None
    try:
        root = no_links(source["location"]) if source["location"] else None
        if root and not root.exists():
            unavailable = "blocked"
    except (OSError, HistoryError):
        unavailable = "blocked"
    if unavailable:
        if not dry:
            source.update(scan_status=unavailable, last_scanned_at=now())
            save_json(store.path("sources/registry.json"), registry)
        return [{"status": unavailable, "source_id": source_id}]
    limits = store.config()["limits"]
    files, excluded = [], 0
    if root.is_file():
        files = [root]
    else:
        for base, dirs, names in os.walk(root, followlinks=False):
            safe_dirs = []
            for name in dirs:
                try:
                    no_links(Path(base) / name)
                    if name not in (".git", "node_modules", ".dart_tool", "build", ".venv"):
                        safe_dirs.append(name)
                except HistoryError:
                    excluded += 1
            dirs[:] = safe_dirs
            for name in names:
                p = Path(base) / name
                rel = p.relative_to(root).as_posix()
                if any(PurePosixPath(rel).match(pattern) for pattern in source["scope"]):
                    files.append(p)
                if len(files) > limits["max_files"]:
                    raise HistoryError("Source file count limit exceeded")
    items, total = [], 0
    preview = {} if dry else None
    existing, _ = store.records()
    source_keys = {(ref["content_hash"], ref["locator"]) for r in existing for ref in r["source_refs"]}
    for p in sorted(files):
        locator = p.name if root.is_file() else p.relative_to(root).as_posix()
        try:
            no_links(p)
            size = p.stat().st_size
            total += size
            if size > limits["max_file_bytes"] or total > limits["max_total_bytes"]:
                raise HistoryError("Source size limit exceeded")
            data = p.read_bytes()
            if p.suffix.lower() == ".zip":
                items.extend(merge_zip(store, p, dry))
                continue
            try:
                obj = parse_json(data.decode("utf-8-sig")) if p.suffix.lower() == ".json" else None
            except (ValueError, UnicodeError):
                if not dry:
                    store.quarantine(data, "invalid_json")
                items.append({"item": locator, "status": "invalid"})
                continue
            if isinstance(obj, dict) and "schema_version" in obj and "run_id" in obj:
                items.append(store.put(obj, dry, preview))
                continue
            text = data.decode("utf-8-sig", errors="replace")
            # Deliberately candidates only: even a report saying 'passed' is not verification.
            hits = [i for i, line in enumerate(text.splitlines(), 1) if "prd-screen-fidelity" in line.lower()]
            if not hits:
                excluded += 1
                continue
            locator += ":lines:" + ",".join(map(str, hits))
            key = (sha(data), locator)
            candidate_id = sha(canonical(key))
            candidate_path = store.path(f"imports/candidates/{candidate_id}.json")
            if key in source_keys or candidate_path.exists():
                items.append({"item": candidate_id, "status": "duplicate"})
            else:
                candidate = {"candidate_id": candidate_id, "source_id": source_id,
                             "locator": locator, "content_hash": sha(data), "activation_evidence": "mentioned_only",
                             "status": "needs_information", "occurred_at": None, "skill_version": None,
                             "note": "Mention candidate; inspect source within registered scope before creating a historical record."}
                if not dry:
                    save_json(candidate_path, candidate)
                items.append({"item": candidate_id, "status": "candidate"})
        except (HistoryError, OSError) as error:
            items.append({"item": locator, "status": "blocked" if isinstance(error, OSError) or getattr(error, "code", 2) == 4 else "invalid"})
    if not dry:
        counts = Counter(i["status"] for i in items)
        unresolved = sum(c["source_id"] == source_id and c["status"] != "linked" for c in
                         (read_json(p) for p in store.path("imports/candidates").glob("*.json")))
        source.update(scan_status="partial" if counts["blocked"] or counts["invalid"] else "checked",
                      last_scanned_at=now(), candidate_count=counts["candidate"], imported_count=counts["stored"],
                      duplicate_count=counts["duplicate"], excluded_count=excluded,
                      unresolved_count=unresolved + counts["conflict"] + counts["invalid"] + counts["blocked"])
        save_json(store.path("sources/registry.json"), registry)
        receipt_id = sha(canonical({"source_id": source_id, "items": items}))
        save_json(store.path(f"imports/{receipt_id}/receipt.json"), {"source_id": source_id, "items": items, "excluded_count": excluded})
    return items


def merge_zip(store, archive, dry=False):
    """Never extract arbitrary archive paths, even into a temporary directory."""
    limits = store.config()["limits"]
    items = []
    preview = {} if dry else None
    with zipfile.ZipFile(no_links(archive)) as package:
        members = package.infolist()
        if len(members) > limits["max_files"] or sum(m.file_size for m in members) > limits["max_total_bytes"]:
            raise HistoryError("Archive limits exceeded")
        seen = set()
        for member in members:
            inside(store.root, member.filename)
            if member.filename in seen or member.file_size > limits["max_file_bytes"] or stat.S_ISLNK(member.external_attr >> 16):
                raise HistoryError("Unsafe archive member")
            seen.add(member.filename)
        if "manifest.json" in seen:
            manifest = json.loads(package.read("manifest.json"))
            if manifest.get("kind") == "public_summary":
                raise HistoryError("Public summaries are not importable usage records")
        for member in sorted(members, key=lambda m: m.filename):
            if not member.filename.endswith("/record.json"):
                continue
            data = package.read(member)
            try:
                record = parse_json(data)
                issues = validate_record(record)
                if issues:
                    raise HistoryError("Invalid imported record")
                evidence_data = []
                for e in record["evidence"]:
                    path = e.get("relative_path")
                    if path and path in seen:
                        blob = package.read(path)
                        if sha(blob) != e["sha256"]:
                            raise HistoryError("Evidence hash mismatch")
                        evidence_data.append((path, blob))
                result = store.put(record, dry_run=True, preview=preview)
                if not dry:
                    if result["status"] == "planned":
                        for path, blob in evidence_data:
                            target = store.path(path)
                            if target.exists() and sha(target.read_bytes()) != sha(blob):
                                raise HistoryError("Stored evidence hash conflict")
                            atomic(target, blob)
                    result = store.put(record)
                items.append(result)
            except (HistoryError, ValueError, TypeError, KeyError):
                if not dry:
                    store.quarantine(data, "invalid_archive_record")
                items.append({"item": sha(data), "status": "invalid"})
    if not dry:
        ident = sha(no_links(archive).read_bytes())
        save_json(store.path(f"imports/{ident}/receipt.json"), {"archive_sha256": ident, "items": items})
    return items


def report_data(store, project=None):
    records, invalid = store.records()
    if project:
        records = [r for r in records if r["project_id"] == project]
    candidates = [read_json(p) for p in store.path("imports/candidates").glob("*.json")]
    sources = store.registry()["sources"]
    rows = []
    for r in records:
        statuses = store.evidence_status(r)
        rows.append({"run_id": r["run_id"], "project_id": r["project_id"], "version": r["skill"]["version"],
                     "kind": r["record_kind"], "task_type": r["task_type"], "activation": r["skill"]["activation_evidence"],
                     "lifecycle": r["lifecycle"], "outcomes": r["outcomes"], "aggregate": r["collection"]["aggregate"],
                     "evidence_status": statuses, "checks": len(r["screen_checks"]),
                     "supplied_matches": sum(s["reference_kind"] == "supplied" and s["visual_verification"] == "compared" and s["visual_outcome"] == "meets_requirements" and
                                             all(e["status"] == "available" for e in statuses if e["evidence_id"] in s["evidence_ids"]) for s in r["screen_checks"]),
                     "findings": [{k: f[k] for k in ("finding_id", "tag", "severity", "status")} for f in r["findings"]],
                     "observed_metrics": r.get("observed_metrics", {})})
    eligible = [r for r in rows if not r["aggregate"] and r["activation"] in ("confirmed_load", "self_reported")]
    return {"record_count": len(rows), "usage_count": len(eligible), "usage_denominator": "Unique non-aggregate run IDs with confirmed_load or self_reported; benchmarks separate below",
            "by_kind": dict(Counter(r["kind"] for r in rows)),
            "usage_by_kind": dict(Counter(r["kind"] for r in eligible)),
            "activation": dict(Counter(r["activation"] for r in rows)), "aggregate_records": sum(r["aggregate"] for r in rows),
            "mention_candidates": sum(c["status"] != "linked" for c in candidates), "linked_candidates": sum(c["status"] == "linked" for c in candidates),
            "unverified_visual": sum(r["outcomes"]["visual_verification"] == "not_verified" for r in rows),
            "unknown_versions": sum(r["version"] is None for r in rows), "lifecycle": dict(Counter(r["lifecycle"] for r in rows)),
            "sources": {"registered": len(sources), "by_status": dict(Counter(s["scan_status"] for s in sources)),
                        "items": [{k: s[k] for k in ("source_id", "scan_status", "candidate_count", "imported_count", "duplicate_count", "excluded_count", "unresolved_count")} for s in sources]},
            "invalid_records": invalid, "runs": rows,
            "limits": "Recorded claims are not independently verified facts. Unknowns are included explicitly; no overall success rate or causal skill benefit is calculated. Candidate/source counts are store-wide."}


def markdown_report(data):
    lines = ["# PRD Screen Fidelity history", "", data["limits"], "",
             f"Records: {data['record_count']}; usage records: {data['usage_count']}; mention candidates: {data['mention_candidates']}; aggregates: {data['aggregate_records']}.",
             data["usage_denominator"], "", f"Unknown versions: {data['unknown_versions']}; visually unverified: {data['unverified_visual']} (denominator: {data['record_count']} records).", "",
             "## Collection scope", "", "```json", json.dumps(data["sources"], ensure_ascii=False, indent=2), "```", "",
             "## Project / version / issues / missing evidence", ""]
    for r in data["runs"]:
        # Free text cannot break Markdown fences or create active HTML/links.
        lines += ["```json", json.dumps(r, ensure_ascii=True, indent=2), "```", ""]
    return "\n".join(lines)


def export_bundle(store, public=False, run_id=None):
    records, invalid = store.records()
    if invalid:
        raise HistoryError("Invalid stored records; validate before export")
    if run_id:
        records = [r for r in records if r["run_id"] == run_id]
        if not records:
            raise HistoryError("Run not found", 4)
    if public and any(not r["privacy"]["public_export_allowed"] or r["privacy"]["sensitive_review"] != "approved" for r in records):
        raise HistoryError("Public export requires explicit permission and completed sensitive review")
    ident = str(uuid.uuid4())
    target = store.path(f"exports/{ident}.zip")
    fd, name = tempfile.mkstemp(prefix=".pending-", dir=target.parent if target.parent.exists() else store.root)
    os.close(fd)
    try:
        with zipfile.ZipFile(name, "w", zipfile.ZIP_DEFLATED) as output:
            manifest = {"schema_version": SCHEMA_VERSION, "kind": "public_summary" if public else "private_history", "run_ids": [r["run_id"] for r in records], "exported_at": now()}
            output.writestr("manifest.json", canonical(manifest))
            copied = set()
            for r in records:
                if public:
                    # Strict allowlist: no aliases, free text, paths, URLs, host strings or claims of truth.
                    summary = {k: r[k] for k in ("schema_version", "run_id", "record_kind", "task_type", "lifecycle", "outcomes")}
                    summary["activation_evidence"] = r["skill"]["activation_evidence"]
                    summary["claim_basis"] = "Recorded assertions; export is not independent verification"
                    summary["evidence_availability"] = dict(Counter(e["status"] for e in store.evidence_status(r)))
                    summary["evidence"] = []
                    for e in r["evidence"]:
                        if e.get("public_export_allowed") and e.get("sensitive_review") == "approved" and e.get("derived_from") and e.get("relative_path"):
                            blob = store.path(e["relative_path"]).read_bytes()
                            if sha(blob) != e["sha256"]:
                                raise HistoryError("Evidence hash mismatch")
                            path = f"evidence/{e['sha256']}.bin"
                            if path not in copied:
                                output.writestr(path, blob)
                                copied.add(path)
                            summary["evidence"].append({"sha256": e["sha256"], "derived_from": e["derived_from"], "path": path})
                    output.writestr(f"summaries/{r['run_id']}.json", canonical(summary))
                else:
                    for path in sorted(store.path(f"records/{r['run_id']}/revisions").glob("*/record.json")):
                        output.writestr(path.relative_to(store.root).as_posix(), no_links(path).read_bytes())
                        for e in read_json(path)["evidence"]:
                            rel = e.get("relative_path")
                            if rel and rel not in copied and store.path(rel).is_file():
                                blob = store.path(rel).read_bytes()
                                if sha(blob) != e["sha256"]:
                                    raise HistoryError("Evidence hash mismatch")
                                output.writestr(rel, blob)
                                copied.add(rel)
        target.parent.mkdir(parents=True, exist_ok=True)
        os.replace(name, target)
        save_json(store.path(f"exports/{ident}.receipt.json"), manifest)
        return target
    finally:
        if os.path.exists(name):
            os.unlink(name)


def result_code(items):
    statuses = {i["status"] for i in items}
    failures = statuses & {"invalid", "blocked", "conflict", "not_configured"}
    if not failures:
        return 0
    if len(failures) > 1 or statuses - failures:
        return 5
    return {"invalid": 2, "conflict": 3, "blocked": 4, "not_configured": 4}[next(iter(failures))]


def parser():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--history-root", default=os.getenv("PSF_HISTORY_HOME", str(Path.home() / "prd-screen-fidelity-history")))
    p.add_argument("--json", action="store_true")
    subs = p.add_subparsers(dest="command", required=True)
    init = subs.add_parser("init")
    init.add_argument("--mode", choices=("off", "local", "local_with_sync"), default="off")
    init.add_argument("--sync-root")
    init.add_argument("--allow-evidence", action="store_true")
    init.add_argument("--retention-days", type=int)
    for name, default in DEFAULT_LIMITS.items():
        init.add_argument("--" + name.replace("_", "-"), type=int, default=default)
    src = subs.add_parser("sources").add_subparsers(dest="source_command", required=True)
    src.add_parser("list")
    add = src.add_parser("add")
    add.add_argument("--source-id", required=True)
    add.add_argument("--type", default="project_folder", choices=("project_folder", "git_repo", "report", "exported_conversation", "issue_pr", "external_submission"))
    add.add_argument("--location")
    add.add_argument("--alias")
    add.add_argument("--scope", nargs="+", default=["*.md", "*.html", "*.json", "*.txt"])
    for name in ("start", "update", "finish", "run"):
        cmd = subs.add_parser(name)
        cmd.add_argument("--patch", help="JSON fields; unknown facts stay null")
        if name in ("start", "run"):
            cmd.add_argument("--project", required=True)
            cmd.add_argument("--alias")
            cmd.add_argument("--project-path")
            cmd.add_argument("--task", choices=("implement", "compare", "scoped_redesign", "unknown"), default="unknown")
            cmd.add_argument("--kind", choices=("live_run", "historical_import", "benchmark"), default="live_run")
        else:
            cmd.add_argument("--run-id", required=True)
            cmd.add_argument("--parent-digest", required=True)
            cmd.add_argument("--reason", required=True)
        if name == "run":
            cmd.add_argument("argv", nargs=argparse.REMAINDER)
    validate = subs.add_parser("validate")
    validate.add_argument("--run-id")
    validate.add_argument("--file")
    imp = subs.add_parser("import")
    imp.add_argument("--source-id", required=True)
    imp.add_argument("--dry-run", action="store_true")
    merge = subs.add_parser("merge")
    merge.add_argument("archive")
    merge.add_argument("--dry-run", action="store_true")
    report = subs.add_parser("report")
    report.add_argument("--project")
    export = subs.add_parser("export")
    export.add_argument("--public", action="store_true")
    export.add_argument("--run-id")
    subs.add_parser("rebuild-index")
    subs.add_parser("sync")
    purge = subs.add_parser("purge")
    purge.add_argument("--run-id", required=True)
    purge.add_argument("--confirm-run-id", required=True)
    attach = subs.add_parser("attach")
    attach.add_argument("--run-id", required=True)
    attach.add_argument("--parent-digest", required=True)
    attach.add_argument("--file", required=True)
    attach.add_argument("--kind", default="capture")
    attach.add_argument("--derived-from")
    return p


def execute(args):
    store = Store(args.history_root)
    command = args.command
    if command == "init":
        if args.mode == "local_with_sync" and not args.sync_root:
            raise HistoryError("local_with_sync requires an explicitly authorized private directory")
        if any(getattr(args, k) <= 0 for k in DEFAULT_LIMITS) or (args.retention_days is not None and args.retention_days < 1):
            raise HistoryError("Limits must be positive")
        if args.sync_root and no_links(args.sync_root) == store.root:
            raise HistoryError("Sync destination must differ from local storage")
        with locked(store.root):
            save_json(store.path("config.json"), {"schema_version": SCHEMA_VERSION, "mode": args.mode,
                "allow_evidence": args.allow_evidence, "sync_root": str(no_links(args.sync_root)) if args.sync_root else None,
                "retention_days": args.retention_days, "limits": {k: getattr(args, k) for k in DEFAULT_LIMITS},
                "allowed_fields": "usage-record.schema.json; raw conversations and environment dumps excluded"})
            if not store.path("sources/registry.json").exists():
                save_json(store.path("sources/registry.json"), {"schema_version": SCHEMA_VERSION, "sources": []})
        return {"status": "configured", "mode": args.mode}, 0
    config = store.config()
    if not store.enabled() and command in ("start", "update", "finish", "import", "merge", "attach", "sync"):
        return {"status": "off", "note": "Continue the product task without history"}, 0
    if command == "sources":
        if args.source_command == "list":
            return store.registry(), 0
        with locked(store.root):
            registry = store.registry()
            if any(s["source_id"] == args.source_id for s in registry["sources"]):
                raise HistoryError("Source ID already exists", 3)
            location = str(no_links(args.location)) if args.location else None
            if location and Path(location).is_dir() and store.root.is_relative_to(Path(location)):
                raise HistoryError("History must be outside registered source project")
            source = {"source_id": args.source_id, "type": args.type, "alias": args.alias,
                      "location": location, "scope": args.scope, "owner": None,
                      "scan_status": "pending" if location else "not_configured", "last_scanned_at": None,
                      "candidate_count": 0, "imported_count": 0, "duplicate_count": 0, "excluded_count": 0, "unresolved_count": 0}
            registry["sources"].append(source)
            errors = schema_errors(registry, read_json(SKILL_DIR / "schemas/source-registry.schema.json"))
            if errors:
                raise HistoryError("; ".join(errors))
            save_json(store.path("sources/registry.json"), registry)
        return {"status": "registered", "source_id": args.source_id}, 0
    if command in ("start", "update", "finish", "attach", "run"):
        if command == "run":
            argv = args.argv[1:] if args.argv[:1] == ["--"] else args.argv
            if not argv:
                raise HistoryError("Wrapper requires an explicit command after --")
            if not store.enabled():
                code = subprocess.call(argv, shell=False)
                return {"status": "off", "process_exit_code": code}, 0 if code == 0 else 5
        with locked(store.root):
            if command in ("start", "run"):
                if args.project_path and store.root.is_relative_to(no_links(args.project_path)):
                    raise HistoryError("History must be outside project code")
                record = new_record(args.project, args.alias, args.task, args.kind)
                previous = None
            else:
                previous = store.latest(args.run_id)
                if digest(previous) != args.parent_digest:
                    ancestors = [read_json(p) for p in store.path(f"records/{args.run_id}/revisions").glob("*/record.json")]
                    previous = next((p for p in ancestors if digest(p) == args.parent_digest), None)
                    if previous is None:
                        raise HistoryError("Unknown parent digest", 3)
                record = deepcopy(previous)
                record.pop("content_digest", None)
                record.update(revision=previous["revision"] + 1, parent_digest=digest(previous), recorded_at=now(), change_reason=getattr(args, "reason", "Attach evidence"))
            if command == "attach":
                if not config["allow_evidence"]:
                    raise HistoryError("Evidence collection not enabled")
                path = no_links(args.file)
                if path.stat().st_size > config["limits"]["max_file_bytes"]:
                    raise HistoryError("Evidence size limit exceeded")
                blob = path.read_bytes()
                folder = store.path(f"records/{record['run_id']}/evidence")
                existing = list(folder.glob("*"))
                if len(existing) >= config["limits"]["max_files"] or sum(no_links(p).stat().st_size for p in existing) + len(blob) > config["limits"]["max_total_bytes"]:
                    raise HistoryError("Evidence count/total size limit exceeded")
                suffix = path.suffix.lower() if re.fullmatch(r"\.[a-z0-9]{1,8}", path.suffix.lower()) else ".bin"
                relative = f"records/{record['run_id']}/evidence/{sha(blob)}{suffix}"
                record["evidence"].append({"evidence_id": str(uuid.uuid4()), "kind": args.kind,
                    "relative_path": relative, "sha256": sha(blob), "availability": "available", "supports": [],
                    "reviewed_by": None, "reviewed_at": None, "captured_at": None, "derived_from": args.derived_from,
                    "public_export_allowed": False, "sensitive_review": "pending"})
            elif args.patch:
                patch = read_json(args.patch)
                if not isinstance(patch, dict) or set(patch) & {"schema_version", "run_id", "revision", "parent_digest", "content_digest", "recorded_at"}:
                    raise HistoryError("Patch cannot replace record identity or revision chain")
                patch_record(record, patch)
            if command == "finish":
                record.update(lifecycle="finished", ended_at=now())
            record["collection"]["record_validation"] = "valid"
            errors = validate_record(record)
            if errors:
                raise HistoryError("; ".join(errors))
            if record["outcomes"]["delivery_status"] == "complete" and record["task_type"] != "compare" and any(
                    e["status"] != "available" for e in store.evidence_status(record)):
                raise HistoryError("Implementation completion requires currently available local evidence")
            if command == "attach":
                atomic(store.path(relative), blob)
            item = store.put(record)
            item["content_digest"] = digest(store.latest(item["run_id"])) if item["status"] == "duplicate" else digest(record)
        if command == "run":
            try:
                code = subprocess.call(argv, shell=False)
                state = "finished"
            except KeyboardInterrupt:
                code, state = 130, "interrupted"
            record.pop("content_digest", None)
            record.update(revision=record["revision"] + 1, parent_digest=digest(record), recorded_at=now(),
                          lifecycle=state, ended_at=now(), change_reason="Wrapper observed process termination; exit code is not task acceptance")
            record["process_exit_code"] = code
            try:
                with locked(store.root):
                    end = store.put(record)
                return {"start": item, "end": end, "process_exit_code": code}, result_code([end]) or (0 if code == 0 else 5)
            except (OSError, HistoryError):
                return {"start": item, "status": "end_record_pending", "process_exit_code": code,
                        "note": "Product command already executed; never repeat it to repair logging"}, 5
        return item, result_code([item])
    if command == "validate":
        records, invalid = ([read_json(args.file)], []) if args.file else store.records()
        if args.run_id:
            records = [r for r in records if r["run_id"] == args.run_id]
            if not records:
                raise HistoryError("Run not found", 4)
        items = list(invalid)
        for r in records:
            errors = validate_record(r)
            evidence = store.evidence_status(r) if not errors else []
            items.append({"run_id": r.get("run_id"), "status": "invalid" if errors or any(e["status"] in ("missing", "hash_mismatch", "blocked") for e in evidence) else "valid",
                          "errors": errors, "evidence": evidence})
        return {"items": items, "counts": dict(Counter(i["status"] for i in items))}, result_code(items)
    if command in ("import", "merge"):
        if args.dry_run:
            items = import_files(store, args.source_id, True) if command == "import" else merge_zip(store, args.archive, True)
        else:
            with locked(store.root):
                items = import_files(store, args.source_id) if command == "import" else merge_zip(store, args.archive)
        return {"items": items, "counts": dict(Counter(i["status"] for i in items)), "dry_run": args.dry_run}, result_code(items)
    if command == "report":
        data = report_data(store, args.project)
        with locked(store.root):
            atomic(store.path("reports/latest.md"), markdown_report(data).encode("utf-8"))
        return data if args.json else markdown_report(data), 5 if data["invalid_records"] else 0
    if command == "export":
        with locked(store.root):
            path = export_bundle(store, args.public, args.run_id)
        return {"status": "exported", "path": str(path), "public": args.public}, 0
    if command == "rebuild-index":
        with locked(store.root):
            data = report_data(store)
            target = store.path("index.sqlite")
            fd, temp = tempfile.mkstemp(prefix=".pending-", dir=store.root)
            os.close(fd)
            try:
                with closing(sqlite3.connect(temp)) as database:
                    with database:
                        database.execute("CREATE TABLE runs (run_id TEXT PRIMARY KEY, record_json TEXT NOT NULL)")
                        database.executemany("INSERT INTO runs VALUES (?, ?)", [(r["run_id"], canonical(r).decode()) for r in data["runs"]])
                os.replace(temp, target)
            finally:
                if os.path.exists(temp):
                    os.unlink(temp)
        return {"status": "rebuilt", "count": data["record_count"]}, 5 if data["invalid_records"] else 0
    if command == "sync":
        if config["mode"] != "local_with_sync":
            raise HistoryError("Private sync has not been configured")
        destination = no_links(config["sync_root"])
        try:
            if not destination.is_dir():
                raise OSError("Destination unavailable")
            remote = Store(destination)
            if not remote.enabled():
                raise HistoryError("Destination not enabled", 4)
            with locked(store.root):
                archive = export_bundle(store)
            with locked(remote.root):
                items = merge_zip(remote, archive)
            code = result_code(items)
            status = "synced" if code == 0 else "pending"
        except (OSError, HistoryError, zipfile.BadZipFile):
            items, status, code = [], "pending", 5
        save_json(store.path("sync-state.json"), {"status": status, "checked_at": now(), "items": items})
        return {"status": status, "items": items, "note": "Local records retained; retry sync only"}, code
    if command == "purge":
        if args.run_id != args.confirm_run_id or str(uuid.UUID(args.run_id)) != args.run_id:
            raise HistoryError("Explicit matching run ID required")
        with locked(store.root):
            target = store.path(f"records/{args.run_id}")
            if target.exists():
                # Verify every descendant before native deletion; never follow reparse points.
                for base, dirs, files in os.walk(target, followlinks=False):
                    for name in dirs + files:
                        no_links(Path(base) / name)
                shutil.rmtree(target)
            for archive in store.path("exports").glob("*.zip"):
                with zipfile.ZipFile(no_links(archive)) as package:
                    manifest = json.loads(package.read("manifest.json"))
                if args.run_id in manifest["run_ids"]:
                    archive.unlink(missing_ok=True)
                    store.path("exports/" + archive.stem + ".receipt.json").unlink(missing_ok=True)
            for path in (store.path("index.sqlite"), store.path("reports/latest.md")):
                path.unlink(missing_ok=True)
            for folder in store.path("quarantine").glob("*"):
                payload = no_links(folder / "payload.bin")
                if payload.exists() and args.run_id.encode() in payload.read_bytes():
                    payload.unlink()
                    no_links(folder / "receipt.json").unlink(missing_ok=True)
                    folder.rmdir()
            for receipt in store.path("imports").glob("*/receipt.json"):
                if args.run_id.encode() in no_links(receipt).read_bytes():
                    receipt.unlink()
            for candidate in store.path("imports/candidates").glob("*.json"):
                if read_json(candidate).get("run_id") == args.run_id:
                    no_links(candidate).unlink()
            store.path("sync-state.json").unlink(missing_ok=True)
        return {"status": "purged", "run_id": args.run_id, "limits": "Local records, linked exports, quarantine branches and derived index/report removed. Original sources, sync destinations, backups and third-party copies require separate deletion."}, 0
    raise HistoryError("Unknown command")


def main(argv=None):
    args = parser().parse_args(argv)
    try:
        data, code = execute(args)
    except HistoryError as error:
        data, code = {"status": "error", "message": str(error)}, error.code
    except (OSError, zipfile.BadZipFile, sqlite3.Error):
        data, code = {"status": "blocked", "message": "Filesystem, archive or database unavailable; contents omitted"}, 4
    except (ValueError, TypeError, KeyError):
        data, code = {"status": "invalid", "message": "Malformed input; contents omitted"}, 2
    print(json.dumps(data, ensure_ascii=True, indent=2) if args.json or not isinstance(data, str) else data)
    return code


if __name__ == "__main__":
    sys.exit(main())
