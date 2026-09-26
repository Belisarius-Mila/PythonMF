"""Explicit, identical-copy recovery only. No merge, deletion or epoch rotation."""
from __future__ import annotations

import hashlib
import json

from camino.api.v1 import _body, _positive, _uuid
from camino.domain.codec import exact_object
from camino.domain.model import ContractError
from camino.domain.revision_store import StoreConflict


def complete_recovery(store, media, raw: bytes) -> dict:
    proof = exact_object(_body(raw), {
        "contract_version", "server_id", "epoch", "device_id", "cursor",
        "operations", "moments", "assets",
    })
    if type(proof["contract_version"]) is not int or proof["contract_version"] != 1:
        raise ContractError("unsupported recovery contract")
    for key in ("server_id", "epoch", "device_id"):
        _uuid(proof[key])
    _positive(proof["cursor"], "cursor")
    for key in ("operations", "moments", "assets"):
        if not isinstance(proof[key], list):
            raise ContractError("recovery inventory must be an array")

    def mismatch():
        # No private IDs, payloads or differences in public errors/logs.
        raise StoreConflict("recovery_mismatch", "copies differ; preserve both and review")

    # Same lock order as media finalization: media first, then metadata.
    # The write reservation fences epoch, cursor, conflicts and privacy changes.
    with media._lock, store._connection() as db:
        db.execute("BEGIN IMMEDIATE")
        try:
            meta = store._meta(db)
            if any(proof[k] != meta[k] for k in ("server_id", "epoch", "cursor")):
                mismatch()
            if proof["device_id"] != meta["writer_device_id"]:
                mismatch()
            if meta["exports_blocked"] and not meta["reconciliation_required"]:
                mismatch()
            if db.execute("SELECT 1 FROM conflict_candidates LIMIT 1").fetchone():
                mismatch()
            rows = db.execute("SELECT id,device_sequence,request_sha256,request_body "
                              "FROM accepted_operations ORDER BY device_sequence").fetchall()
            if len(rows) != proof["cursor"] or len(rows) != len(proof["operations"]):
                mismatch()
            for sequence, (row, entry) in enumerate(zip(rows, proof["operations"]), 1):
                entry = exact_object(entry, {"id", "sequence", "sha256"})
                if (type(entry["sequence"]) is not int or entry != {
                    "id": row["id"], "sequence": sequence, "sha256": row["request_sha256"],
                } or row["device_sequence"] != sequence or
                    hashlib.sha256(row["request_body"]).hexdigest() != row["request_sha256"]):
                    mismatch()

            def indexed(entries, fields):
                result = {}
                for entry in entries:
                    entry = exact_object(entry, fields)
                    _uuid(entry["id"])
                    if entry["id"] in result:
                        mismatch()
                    result[entry["id"]] = entry
                return result

            moments = indexed(proof["moments"], {"id", "revision", "privacy"})
            expected = {}
            for row in db.execute("SELECT id,revision,body FROM moments"):
                body = json.loads(row["body"])
                expected[row["id"]] = {"id": row["id"], "revision": row["revision"],
                                       "privacy": body["privacy"]}
            if moments != expected or any(type(m["revision"]) is not int for m in moments.values()):
                mismatch()
            assets = indexed(proof["assets"], {"id", "byte_count", "sha256"})
            manifests = {r["id"]: json.loads(r["body"]) for r in db.execute("SELECT id,body FROM assets")}
            if set(assets) != set(manifests):
                mismatch()
            # Include receipts without a matching manifest: no hidden orphan accepted as complete.
            with media._open() as media_db:
                verified = {r[0] for r in media_db.execute("SELECT asset_id FROM verified_assets")}
            if verified != set(assets):
                mismatch()
            for identifier, entry in assets.items():
                manifest = manifests[identifier]
                if type(entry["byte_count"]) is not int or entry != {
                    "id": identifier, "byte_count": manifest["byte_count"], "sha256": manifest["sha256"],
                }:
                    mismatch()
                receipt = media._verified_receipt(identifier)  # Rehash actual immutable bytes.
                if receipt is None or any(receipt[k] != entry[k] for k in ("byte_count", "sha256")):
                    mismatch()
            db.execute("UPDATE meta SET exports_blocked=0,reconciliation_required=0 WHERE singleton=1")
            db.commit()
            return {"contract_version": 1, "server_id": meta["server_id"], "epoch": meta["epoch"],
                    "cursor": meta["cursor"], "request_sha256": hashlib.sha256(raw).hexdigest(),
                    "exports_blocked": False, "reconciliation_required": False}
        except Exception:
            db.rollback()
            raise
