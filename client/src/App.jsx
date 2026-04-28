import { useEffect, useMemo, useState } from "react";
import { Wallet, Landmark, RefreshCcw, Info } from "lucide-react";
import { toast } from "sonner";

import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Badge } from "@/components/ui/badge";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { createPayout, fetchBalance, fetchLedger, fetchMerchants, fetchPayouts } from "@/lib/api";

function App() {
  const [merchants, setMerchants] = useState([]);
  const [merchantId, setMerchantId] = useState("");
  const [balance, setBalance] = useState(null);
  const [ledger, setLedger] = useState([]);
  const [payouts, setPayouts] = useState([]);
  const [amountPaise, setAmountPaise] = useState(6000);
  const [bankAccountId, setBankAccountId] = useState("");
  const [idempotencyKey, setIdempotencyKey] = useState(crypto.randomUUID());
  const [loading, setLoading] = useState(false);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [showHowToTest, setShowHowToTest] = useState(false);

  const selectedMerchant = useMemo(
    () => merchants.find((m) => m.id === merchantId),
    [merchants, merchantId]
  );

  async function loadMerchants() {
    const data = await fetchMerchants();
    setMerchants(data);
    if (!merchantId && data.length > 0) {
      setMerchantId(data[0].id);
      setBankAccountId(data[0].bank_account_id);
    }
  }

  async function loadDashboard(targetMerchantId) {
    if (!targetMerchantId) return;
    setLoading(true);
    try {
      const [balanceData, ledgerData, payoutsData] = await Promise.all([
        fetchBalance(targetMerchantId),
        fetchLedger(targetMerchantId, 20),
        fetchPayouts(targetMerchantId, 20),
      ]);
      setBalance(balanceData);
      setLedger(ledgerData);
      setPayouts(payoutsData);
    } catch (err) {
      toast.error(err.message || "Failed to load dashboard data.");
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    loadMerchants().catch((err) => toast.error(err.message || "Failed to load merchants."));
  }, []);

  useEffect(() => {
    if (merchantId) {
      const m = merchants.find((x) => x.id === merchantId);
      if (m) setBankAccountId(m.bank_account_id);
      loadDashboard(merchantId).catch((err) =>
        toast.error(err.message || "Failed to load dashboard.")
      );
    }
  }, [merchantId, merchants]);

  async function handleCreatePayout(event) {
    event.preventDefault();
    setIsSubmitting(true);
    try {
      const payout = await createPayout({
        merchantId,
        amountPaise: Number(amountPaise),
        bankAccountId,
        idempotencyKey,
      });
      toast.success(`Payout created: ${payout.id.slice(0, 8)}... (${payout.status})`);
      setIdempotencyKey(crypto.randomUUID());
      await loadDashboard(merchantId);
    } catch (err) {
      toast.error(err.message || "Failed to create payout.");
    } finally {
      setIsSubmitting(false);
    }
  }

  return (
    <div className="min-h-screen bg-slate-50 p-6 text-slate-900 dark:bg-slate-950 dark:text-slate-100">
      <div className="mx-auto max-w-7xl space-y-6">
        <div className="flex flex-col gap-4 md:flex-row md:items-center md:justify-between">
          <div>
            <h1 className="text-2xl font-bold tracking-tight">Playto Payout Dashboard</h1>
            <p className="text-sm text-slate-600 dark:text-slate-400">
              Ledger-based merchant payouts with idempotency and safe concurrency.
            </p>
          </div>
          <div className="flex items-center gap-2">
            <select
              className="h-10 rounded-md border border-slate-300 bg-white px-3 text-sm text-slate-900 dark:border-slate-800 dark:bg-slate-950 dark:text-slate-100"
              value={merchantId}
              onChange={(e) => setMerchantId(e.target.value)}
            >
              {merchants.map((merchant) => (
                <option key={merchant.id} value={merchant.id}>
                  {merchant.name}
                </option>
              ))}
            </select>
            <Button variant="outline" onClick={() => loadDashboard(merchantId)} disabled={loading}>
              <RefreshCcw className={`mr-2 size-4 ${loading ? "animate-spin" : ""}`} />
              Refresh
            </Button>
            <Button variant="outline" onClick={() => setShowHowToTest(true)}>
              <Info className="mr-2 size-4" />
              How to test
            </Button>
          </div>
        </div>

        {showHowToTest && (
          <div
            className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 p-4"
            role="dialog"
            aria-modal="true"
            aria-label="How to test"
            onMouseDown={(e) => {
              if (e.target === e.currentTarget) setShowHowToTest(false);
            }}
          >
            <div className="w-full max-w-3xl rounded-lg border border-slate-200 bg-white shadow-xl dark:border-slate-800 dark:bg-slate-950">
              <div className="flex items-start justify-between gap-4 border-b border-slate-200 p-4 dark:border-slate-800">
                <div>
                  <h2 className="text-lg font-semibold">How to test (Postman)</h2>
                  <p className="mt-1 text-sm text-slate-600 dark:text-slate-400">
                    Quick checklist. Full guide: <span className="font-mono">backend/POSTMAN_TESTING.md</span>
                  </p>
                </div>
                <Button variant="outline" onClick={() => setShowHowToTest(false)}>
                  Close
                </Button>
              </div>

              <div className="max-h-[70vh] overflow-auto p-4">
                <div className="space-y-4 text-sm">
                  <div className="rounded-md border border-slate-200 bg-slate-50 p-3 dark:border-slate-800 dark:bg-slate-900/30">
                    <div className="font-medium">UI smoke test (this dashboard)</div>
                    <ol className="mt-2 list-decimal space-y-2 pl-5 text-slate-700 dark:text-slate-300">
                      <li>
                        Start the backend API on{" "}
                        <span className="font-mono">http://localhost:8000</span> and start the UI (Vite).
                      </li>
                      <li>
                        Open the page and confirm the <span className="font-medium">merchant dropdown</span> is populated.
                      </li>
                      <li>
                        Pick a merchant and click <span className="font-medium">Refresh</span>. Expected: the three top
                        cards update and both tables load rows (or show the “empty” state).
                      </li>
                      <li>
                        In <span className="font-medium">Create Payout</span>:
                        <ul className="mt-1 list-disc space-y-1 pl-5">
                          <li>
                            Set <span className="font-mono">Amount (paise)</span> (e.g.{" "}
                            <span className="font-mono">6000</span>)
                          </li>
                          <li>
                            Ensure <span className="font-mono">Bank Account ID</span> is filled (auto from merchant)
                          </li>
                          <li>
                            Ensure <span className="font-mono">Idempotency Key</span> is a UUID v4
                          </li>
                          <li>Click Submit. Expected: success toast + payout appears in “Payout History”.</li>
                        </ul>
                      </li>
                      <li>
                        Idempotency UI test: submit once, then submit again with the{" "}
                        <span className="font-medium">same</span> idempotency key and same amount. Expected: the payout
                        list should not grow by 2 for the same request (backend returns the same payout).
                      </li>
                      <li>
                        Insufficient balance UI test: set a very large amount and submit. Expected: error toast and no
                        new payout row.
                      </li>
                    </ol>
                  </div>

                  <div className="rounded-md border border-slate-200 p-3 dark:border-slate-800">
                    <div className="font-medium">What each UI section should show</div>
                    <ul className="mt-2 list-disc space-y-1 pl-5 text-slate-700 dark:text-slate-300">
                      <li>
                        <span className="font-medium">Available / Held balance</span>: numbers in paise; should change
                        after payouts (available decreases, held may increase while pending).
                      </li>
                      <li>
                        <span className="font-medium">Payout History</span>: newest payout rows with status badges.
                      </li>
                      <li>
                        <span className="font-medium">Ledger Entries</span>: credits/debits/holds with notes (if any).
                      </li>
                    </ul>
                  </div>

                  <div className="rounded-md border border-slate-200 p-3 dark:border-slate-800">
                    <div className="font-medium">If something fails</div>
                    <ul className="mt-2 list-disc space-y-1 pl-5 text-slate-700 dark:text-slate-300">
                      <li>
                        Connection refused / dashboard won’t load → backend not running at{" "}
                        <span className="font-mono">localhost:8000</span>
                      </li>
                      <li>
                        Submit fails with UUID error → idempotency key must be UUID v4 (click into field and paste a new
                        UUID).
                      </li>
                      <li>
                        Payout created but status never changes → worker not running (optional).
                      </li>
                    </ul>
                  </div>

                  <div className="rounded-md border border-slate-200 p-3 dark:border-slate-800">
                    <div className="font-medium">Optional: API/Postman guide</div>
                    <p className="mt-2 text-slate-700 dark:text-slate-300">
                      For endpoint-level testing (idempotency replay, concurrency approximation, etc.), see{" "}
                      <span className="font-mono">backend/POSTMAN_TESTING.md</span>.
                    </p>
                  </div>
                </div>
              </div>
            </div>
          </div>
        )}

        <div className="grid gap-4 md:grid-cols-3">
          <Card>
            <CardHeader className="pb-2">
              <CardDescription>Available Balance</CardDescription>
              <CardTitle className="text-2xl">
                {loading ? "Loading..." : `${balance?.available_paise ?? 0} paise`}
              </CardTitle>
            </CardHeader>
            <CardContent>
              <Wallet className="size-5 text-slate-500" />
            </CardContent>
          </Card>
          <Card>
            <CardHeader className="pb-2">
              <CardDescription>Held Balance</CardDescription>
              <CardTitle className="text-2xl">
                {loading ? "Loading..." : `${balance?.held_paise ?? 0} paise`}
              </CardTitle>
            </CardHeader>
            <CardContent>
              <Landmark className="size-5 text-slate-500" />
            </CardContent>
          </Card>
          <Card>
            <CardHeader className="pb-2">
              <CardDescription>Merchant</CardDescription>
              <CardTitle className="text-lg">{selectedMerchant?.name ?? "—"}</CardTitle>
            </CardHeader>
            <CardContent>
              <p className="text-xs text-slate-500">{merchantId || "No merchant selected"}</p>
            </CardContent>
          </Card>
        </div>

        <Card>
          <CardHeader>
            <CardTitle>Create Payout</CardTitle>
            <CardDescription>Submit payout requests with a unique idempotency key.</CardDescription>
          </CardHeader>
          <CardContent>
            <form className="grid gap-4 md:grid-cols-2" onSubmit={handleCreatePayout}>
              <div className="space-y-2">
                <Label htmlFor="amount">Amount (paise)</Label>
                <Input
                  id="amount"
                  type="number"
                  min={1}
                  value={amountPaise}
                  onChange={(e) => setAmountPaise(e.target.value)}
                />
              </div>
              <div className="space-y-2">
                <Label htmlFor="bank">Bank Account ID</Label>
                <Input id="bank" value={bankAccountId} onChange={(e) => setBankAccountId(e.target.value)} />
              </div>
              <div className="space-y-2 md:col-span-2">
                <Label htmlFor="idem">Idempotency Key (UUID v4)</Label>
                <Input id="idem" value={idempotencyKey} onChange={(e) => setIdempotencyKey(e.target.value)} />
              </div>
              <div className="md:col-span-2">
                <Button className="w-full md:w-auto" type="submit" disabled={!merchantId || loading || isSubmitting}>
                  {isSubmitting ? "Submitting..." : "Submit Payout"}
                </Button>
              </div>
            </form>
          </CardContent>
        </Card>

        <div className="grid gap-6 lg:grid-cols-2">
          <Card>
            <CardHeader>
              <CardTitle>Payout History</CardTitle>
            </CardHeader>
            <CardContent>
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>ID</TableHead>
                    <TableHead>Amount</TableHead>
                    <TableHead>Status</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {loading && (
                    <TableRow>
                      <TableCell colSpan={3} className="text-center text-slate-500">
                        Loading payouts...
                      </TableCell>
                    </TableRow>
                  )}
                  {!loading && payouts.length === 0 && (
                    <TableRow>
                      <TableCell colSpan={3} className="text-center text-slate-500">
                        No payouts yet.
                      </TableCell>
                    </TableRow>
                  )}
                  {!loading &&
                    payouts.map((p) => (
                      <TableRow key={p.id}>
                        <TableCell className="font-mono text-xs">{p.id.slice(0, 8)}...</TableCell>
                        <TableCell>{p.amount_paise}</TableCell>
                        <TableCell>
                          <Badge variant={p.status}>{p.status}</Badge>
                        </TableCell>
                      </TableRow>
                    ))}
                </TableBody>
              </Table>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle>Ledger Entries</CardTitle>
            </CardHeader>
            <CardContent>
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Type</TableHead>
                    <TableHead>Amount</TableHead>
                    <TableHead>Note</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {loading && (
                    <TableRow>
                      <TableCell colSpan={3} className="text-center text-slate-500">
                        Loading ledger...
                      </TableCell>
                    </TableRow>
                  )}
                  {!loading && ledger.length === 0 && (
                    <TableRow>
                      <TableCell colSpan={3} className="text-center text-slate-500">
                        No ledger entries found.
                      </TableCell>
                    </TableRow>
                  )}
                  {!loading &&
                    ledger.map((entry) => (
                      <TableRow key={entry.id}>
                        <TableCell className="capitalize">{entry.entry_type.replace("_", " ")}</TableCell>
                        <TableCell>{entry.amount_paise}</TableCell>
                        <TableCell className="text-slate-600">{entry.note || "—"}</TableCell>
                      </TableRow>
                    ))}
                </TableBody>
              </Table>
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  );
}

export default App;
