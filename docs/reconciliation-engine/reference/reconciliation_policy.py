"""Small, dependency-free policy extraction for the reconciliation case study.

This module documents selected decisions from the inspected application. It is
not imported by, nor a replacement for, the original KC Algo Lab service.
"""

from __future__ import annotations

import hashlib
import json
from typing import Any

PENDING_RECONCILIATION_STATUSES = frozenset(
    {"order_submitted", "submission_unknown"}
)
TERMINAL_RECONCILIATION_STATUSES = frozenset(
    {"open", "closed", "rejected", "cancelled", "deactivated"}
)
ORDER_EVENT_STATUS_MAP = {
    "New": "order_submitted",
    "PartiallyFilled": "partially_filled",
    "Filled": "filled",
    "Cancelled": "cancelled",
    "Rejected": "rejected",
    "Deactivated": "deactivated",
}


def is_reconciliation_candidate(status: str) -> bool:
    """Only submitted/unknown submissions enter the per-order recovery path."""
    return status in PENDING_RECONCILIATION_STATUSES


def is_terminal_reconciliation_status(status: str) -> bool:
    """Whether the bounded per-order worker can stop retrying reconciliation."""
    return status in TERMINAL_RECONCILIATION_STATUSES


def map_exchange_order_status(exchange_status: str) -> str | None:
    """Translate a known Bybit order status into the local lifecycle vocabulary."""
    return ORDER_EVENT_STATUS_MAP.get(exchange_status)


def status_from_position_snapshot(current_status: str, has_matching_position: bool) -> str:
    """Mirror the inspected position-to-signal transition rule.

    A present symbol/side position means open. An absent position closes a
    previously filled/open signal; other unresolved states remain unchanged.
    """
    if has_matching_position:
        return "open"
    if current_status in {"filled", "open"}:
        return "closed"
    return current_status


def classify_submission_transport_error(stage: str) -> str:
    """Return the safe local outcome after a transport error at a given stage.

    An error before place_order is a definite submission failure. An error
    during place_order is ambiguous because the exchange may have accepted it.
    The policy never authorizes automatic order resubmission.
    """
    if stage == "place_order":
        return "submission_unknown"
    if stage == "set_leverage":
        return "submission_failed"
    raise ValueError(f"Unsupported submission stage: {stage}")


def should_resubmit_order_after_transport_error(stage: str) -> bool:
    """Conservative policy: never automatically repeat a possibly sent order."""
    classify_submission_transport_error(stage)  # validate the stage
    return False


def event_fingerprint(message: dict[str, Any]) -> str:
    """Fingerprint canonical JSON as the source event store does."""
    payload = json.dumps(message, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()
