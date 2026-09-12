import unittest
from costs import cny_display, normalize_cost, set_cost, summarize


class CostAccountingTests(unittest.TestCase):
    def row(self, request, status="succeeded"):
        return {"request_id": request, "ledger_id": request, "stage": request, "status": status}

    def test_conversion_is_idempotent_and_retains_provider_evidence(self):
        a = set_cost(self.row("a"), "USD", estimated_amount="1.23")
        self.assertEqual(a["estimated_amount"], "8.61")
        self.assertEqual(a["currency"], "CNY")
        self.assertEqual(a["cost_display"], "¥8.61")
        self.assertEqual(normalize_cost(normalize_cost(a)), a)
        self.assertEqual(a["source_cost"]["estimated_amount"], "1.23")

    def test_failed_cost_counts_and_unknown_is_not_zero(self):
        charged = set_cost(self.row("failed", "failed"), "USD", amount="0.10")
        unknown = set_cost(self.row("unknown", "failed"), "USD")
        yuan = set_cost(self.row("yuan"), "CNY", amount="0.50")
        out = summarize([charged, unknown, yuan])
        self.assertEqual(out["display"], "¥1.20")
        self.assertEqual(out["failed_known_display"], "¥0.70")
        self.assertEqual(out["pending_attempts"], ["unknown"])

    def test_estimate_replaced_without_duplicate_or_rounding_each_row(self):
        estimated = set_cost(self.row("same"), "USD", estimated_amount="1")
        confirmed = set_cost(self.row("same"), "USD", amount="0.5")
        self.assertEqual(summarize([confirmed, estimated, confirmed])["display"], "¥3.50")
        rows = [set_cost(self.row(str(i)), "USD", amount="0.0007") for i in range(2)]
        self.assertEqual(summarize(rows)["display"], "¥0.01")
        self.assertEqual(cny_display("1.005"), "¥1.01")


if __name__ == "__main__":
    unittest.main()
