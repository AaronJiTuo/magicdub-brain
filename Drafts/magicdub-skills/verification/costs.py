"""Canonical CNY accounting, with original provider amounts retained as evidence."""
from __future__ import annotations

from copy import deepcopy
from decimal import Decimal, ROUND_HALF_UP

USD_TO_CNY = Decimal("7")
FX_POLICY = "fixed_usd_cny_7"


def cny_display(value):
    return "¥" + str(Decimal(str(value)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP))


def set_cost(attempt, currency, *, amount=None, estimated_amount=None, basis=None):
    if currency not in ("USD", "CNY"):
        raise ValueError(f"Unsupported provider currency: {currency}")
    rate = USD_TO_CNY if currency == "USD" else Decimal(1)
    source = {"currency": currency, "amount": str(amount) if amount is not None else None,
              "estimated_amount": str(estimated_amount) if estimated_amount is not None else None,
              "estimate_basis": basis}
    attempt.update(currency="CNY", fx_policy=FX_POLICY, source_cost=source, fx_rate=str(rate),
                   amount=str(Decimal(str(amount))*rate) if amount is not None else None,
                   estimated_amount=str(Decimal(str(estimated_amount))*rate) if estimated_amount is not None else None,
                   cost_status="confirmed" if amount is not None else "estimated" if estimated_amount is not None else "pending")
    value = attempt["amount"] if amount is not None else attempt["estimated_amount"]
    attempt["cost_display"] = cny_display(value) if value is not None else "待核实"
    if basis is not None:
        attempt["estimate_basis"] = basis
    return attempt


def normalize_cost(attempt):
    a = deepcopy(attempt)
    if "source_cost" in a:
        source = a["source_cost"]
    else:
        source = {"currency": a.get("currency", "USD"),
                  "amount": a.get("amount") if a.get("cost_status") == "confirmed" else None,
                  "estimated_amount": a.get("estimated_amount") if a.get("cost_status") == "estimated" else None,
                  "estimate_basis": a.get("estimate_basis")}
    return set_cost(a, source["currency"], amount=source.get("amount"),
                    estimated_amount=source.get("estimated_amount"), basis=source.get("estimate_basis"))


def summarize(attempts):
    # Copies or repeated reads of the same request are not new charges. Reconciled
    # amounts supersede estimates; a failed charged attempt still contributes.
    ranks = {"pending": 0, "estimated": 1, "confirmed": 2}
    unique = {}
    for raw in attempts:
        a = normalize_cost(raw)
        key = a.get("request_id") or a.get("ledger_id")
        if not key:
            raise ValueError("An unsubmitted attempt needs a stable ledger_id")
        prior = unique.get(key)
        if prior is None or ranks[a["cost_status"]] >= ranks[prior["cost_status"]]:
            unique[key] = a
    rows = list(unique.values())
    confirmed = sum((Decimal(a["amount"]) for a in rows if a["cost_status"] == "confirmed"), Decimal(0))
    estimated = sum((Decimal(a["estimated_amount"]) for a in rows if a["cost_status"] == "estimated"), Decimal(0))
    failed_states = {"failed", "submission_unknown", "submission_rejected", "FAILED", "CANCELLED"}
    failed = [a for a in rows if a.get("status") in failed_states]
    failed_known = sum((Decimal(a["amount"] if a["cost_status"] == "confirmed" else a["estimated_amount"])
                        for a in failed if a["cost_status"] != "pending"), Decimal(0))
    fields = ("ledger_id", "stage", "endpoint", "request_id", "status", "cost_status", "currency",
              "amount", "estimated_amount", "cost_display", "fx_policy", "fx_rate", "source_cost", "usage_disposition")
    return {"schema_version": 2, "currency": "CNY", "fx_policy": FX_POLICY, "usd_to_cny": str(USD_TO_CNY),
            "confirmed": {"CNY": str(confirmed)}, "estimated": {"CNY": str(estimated)},
            "known_total": {"CNY": str(confirmed+estimated)}, "display": cny_display(confirmed+estimated),
            "failed_known_total": {"CNY": str(failed_known)}, "failed_known_display": cny_display(failed_known),
            "pending_attempts": [a["ledger_id"] for a in rows if a["cost_status"] == "pending"],
            "unreconciled_attempts": [a["ledger_id"] for a in rows if a["cost_status"] != "confirmed"],
            "failed_attempts": [a["ledger_id"] for a in failed], "request_count": len(rows),
            "host_agent_cost": "unmeasured and excluded", "rounding": "sum exact Decimal amounts, round display only (half up)",
            "attempts": [{k: a.get(k) for k in fields} for a in rows]}
