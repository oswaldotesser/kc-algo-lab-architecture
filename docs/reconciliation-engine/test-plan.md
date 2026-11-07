# Focused test plan

## Existing tests found in the inspected source archive

The archive already contains tests relevant to this case:

- `app/test_bybit_reconciliation.py`: filled order becomes open from REST state; rejected order releases a slot; missing order remains pending; periodic snapshot can close an open signal and queue a journal entry; periodic reconciler records success/error.
- `tests/test_bybit_private_ws.py`: requests pybit automatic reconnect (`restart_on_error=True`, `retries=0`).
- `tests/test_order_submission_journal.py`: submission acknowledgement, definite rejection, unknown outcome, and blocked execution update local status/slot accounting.
- `tests/test_bybit_order_execution.py`: no API calls while safety locks are closed; acknowledgement; rejection; timeout after `place_order` is marked unknown and is not retried.

The original application's test suite was executed on the production VPS environment, where the required dependencies, including `pybit`, are installed. The latest reported run completed with at least 31 passing tests.

The standalone package contains a separate set of isolated policy tests. All 7 standalone tests passed in the local validation run. These tests validate the extracted reconciliation policies independently and do not replace the original application's integration and component tests.

## Minimal acceptance matrix

| Scenario | Expected behavior | Coverage |
|---|---|---|
| REST order lookup finds order in open-orders endpoint | Apply mapped exchange status | Existing integration-style unit test |
| Order absent from open orders but present in history | Return historical order | Add adapter test |
| Order absent from both endpoints | Keep unresolved; do not infer rejection | Existing reconciliation test |
| `place_order` transport timeout | Persist unknown outcome; never resend automatically | Existing executor test |
| Leverage request fails before `place_order` | Definite failure; no order request | Add explicit call-count assertion |
| Position WebSocket event | Record event, then fetch REST snapshot | Add handler test |
| Duplicate identical WebSocket payload | Store once | Add SQLite event-store test |
| Same event semantics but changed payload metadata | Document fingerprint behavior; do not assume deduplication | Add edge-case test |
| Process restart with unresolved submissions | Reconcile bounded candidate set | Add startup recovery test |
| Periodic REST call fails | Record error and allow next scheduled cycle | Existing periodic worker test | next-cycle recovery not explicitly verified
| Concurrent reconciliation calls | No conflicting writes or duplicate side effects | Recommended concurrency test; not currently guaranteed |
| More than REST page limit of positions | Pagination/coverage behavior explicitly verified | Recommended adapter test |

## Additional recommended tests

1. **Order-history fallback:** fake REST adapter returns an empty realtime list and a matching history record.
2. **Stable identity:** ensure `orderLinkId` is preserved from local submission through lookup and WebSocket event mapping.
3. **Event persistence:** send the same canonical payload twice and assert only one `exchange_events` row exists.
4. **Out-of-order events:** apply a late `New` event after `Filled`; decide and enforce a monotonic transition policy if required.
5. **Position attribution:** test two signals with the same symbol and side to expose the current matching limitation.
6. **Single-flight behavior:** overlap periodic and event-triggered reconciliation and verify safe DB transitions.
7. **Pagination:** test exchange responses at and above the configured page size.
8. **Failure injection:** simulate REST timeouts separately for order lookup and position snapshot; assert unresolved state is retained and later retry is possible.


## Additional safety-specific coverage

9. **Protection side effect boundary:** with live execution disabled, the protection-maintenance path must not call set_trading_stop; with it enabled and a qualifying position, assert the expected protection update and subsequent REST verification. This is especially important because the reconciliation service's docstring calls the overall operation read-only, while its implementation delegates to a routine that can amend TP/SL.
