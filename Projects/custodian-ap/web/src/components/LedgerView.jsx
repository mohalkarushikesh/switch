// Ledger view — balance and the payment rail's transaction history.
// Backed by GET /ledger, which was wired in api.js but rendered nowhere before.
import { useState } from 'react'
import { money } from '../lib/format.js'

export default function LedgerView({ ledger }) {
  const [query, setQuery] = useState('')

  if (!ledger) {
    return (
      <div className="panel">
        <h2>Ledger</h2>
        <div className="empty">Loading ledger…</div>
      </div>
    )
  }

  const txns = ledger.transactions || []
  // The API exposes the current balance and the transactions drawn against it,
  // so the opening balance is derived rather than fetched.
  const disbursed = txns.reduce((sum, t) => sum + (t.amount || 0), 0)
  const opening = (ledger.balance || 0) + disbursed

  const q = query.trim().toLowerCase()
  const filtered = q
    ? txns.filter(
        (t) =>
          String(t.invoice_id || '').toLowerCase().includes(q) ||
          String(t.transaction_id || '').toLowerCase().includes(q) ||
          String(t.vendor_account || '').toLowerCase().includes(q),
      )
    : txns

  return (
    <>
      <div className="panel">
        <h2>Ledger</h2>
        <div className="tiles">
          <div className="tile">
            <div className="k">Available balance</div>
            <div className="v">{money(ledger.balance)}</div>
          </div>
          <div className="tile">
            <div className="k">Opening balance</div>
            <div className="v">{money(opening)}</div>
          </div>
          <div className="tile">
            <div className="k">Total disbursed</div>
            <div className="v" style={{ color: 'var(--amber)' }}>{money(disbursed)}</div>
          </div>
          <div className="tile">
            <div className="k">Transactions</div>
            <div className="v">{txns.length}</div>
          </div>
        </div>
        {/* Share of the opening balance already paid out. */}
        {opening > 0 && (
          <div style={{ marginTop: 14 }}>
            <div className="row" style={{ justifyContent: 'space-between', marginBottom: 4 }}>
              <span style={{ fontSize: 12, color: 'var(--muted)' }}>Disbursed against opening balance</span>
              <b style={{ fontSize: 12 }}>{Math.round((disbursed / opening) * 100)}%</b>
            </div>
            <div style={{ background: 'var(--panel3)', borderRadius: 4, height: 10 }}>
              <div style={{
                width: `${Math.min(100, (disbursed / opening) * 100)}%`,
                background: 'var(--amber)', height: 10, borderRadius: 4,
              }} />
            </div>
          </div>
        )}
      </div>

      <div className="panel">
        <div className="row" style={{ justifyContent: 'space-between' }}>
          <h2 style={{ margin: 0 }}>Transactions ({filtered.length}/{txns.length})</h2>
          <input
            style={{ maxWidth: 260 }}
            placeholder="Search invoice, txn or account…"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
          />
        </div>
        {txns.length === 0 && (
          <div className="empty">No payments released yet. Auto-paid invoices appear here.</div>
        )}
        {txns.length > 0 && filtered.length === 0 && (
          <div className="empty">No transactions match the filter.</div>
        )}
        {filtered.length > 0 && (
          <table>
            <thead>
              <tr>
                <th>Transaction</th><th>Invoice</th><th>Vendor account</th><th>Amount</th>
              </tr>
            </thead>
            <tbody>
              {filtered.map((t) => (
                <tr key={t.transaction_id}>
                  <td className="mono">{t.transaction_id}</td>
                  <td><b>{t.invoice_id}</b></td>
                  <td className="mono">{t.vendor_account}</td>
                  <td>{money(t.amount, t.currency)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>
    </>
  )
}
