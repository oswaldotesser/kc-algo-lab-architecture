from reference.reconciliation_policy import (
    classify_submission_transport_error,
    event_fingerprint,
    is_reconciliation_candidate,
    is_terminal_reconciliation_status,
    map_exchange_order_status,
    should_resubmit_order_after_transport_error,
    status_from_position_snapshot,
)


def test_only_submitted_and_unknown_states_are_candidates():
    assert is_reconciliation_candidate("order_submitted")
    assert is_reconciliation_candidate("submission_unknown")
    assert not is_reconciliation_candidate("open")
    assert not is_reconciliation_candidate("rejected")


def test_terminal_states_stop_bounded_reconciliation_worker():
    assert is_terminal_reconciliation_status("open")
    assert is_terminal_reconciliation_status("closed")
    assert is_terminal_reconciliation_status("rejected")
    assert not is_terminal_reconciliation_status("submission_unknown")


def test_exchange_order_status_mapping():
    assert map_exchange_order_status("Filled") == "filled"
    assert map_exchange_order_status("PartiallyFilled") == "partially_filled"
    assert map_exchange_order_status("Rejected") == "rejected"
    assert map_exchange_order_status("SomeFutureStatus") is None


def test_position_snapshot_opens_or_closes_filled_signal():
    assert status_from_position_snapshot("filled", True) == "open"
    assert status_from_position_snapshot("open", False) == "closed"
    assert status_from_position_snapshot("submission_unknown", False) == "submission_unknown"


def test_ambiguous_place_order_error_is_not_retried():
    assert classify_submission_transport_error("place_order") == "submission_unknown"
    assert should_resubmit_order_after_transport_error("place_order") is False


def test_pre_submission_leverage_error_is_definite_but_not_resubmitted():
    assert classify_submission_transport_error("set_leverage") == "submission_failed"
    assert should_resubmit_order_after_transport_error("set_leverage") is False


def test_event_fingerprint_is_stable_for_key_order():
    first = {"topic": "order", "data": [{"orderId": "demo-1", "orderStatus": "Filled"}]}
    second = {"data": [{"orderStatus": "Filled", "orderId": "demo-1"}], "topic": "order"}
    assert event_fingerprint(first) == event_fingerprint(second)
