// Review queue — the reviewer's workspace: everything the pipeline routed to a
// human, with multi-select so a batch can be cleared in one pass instead of
// expanding each row in the main table.
import { useState } from 'react'
import { money, riskColor } from '../lib/format.js'
import Pipeline from './Pipeline.jsx'

export default function ReviewQueue({ records, onApprove, onReject }) {
  const [selected, setSelected] = useState(() => new Set())
  const [busy, setBusy] = useState(false)

  const queue = records.filter((r) => r.status === 'needs_review')
  // Highest risk first — the riskiest item is the one a reviewer should see.
  const sorted = [...queue].sort(
    (a, b) => (b.assessment?.risk_score ?? 0) - (a.assessment?.risk_score ?? 0),
  )

  // Selections are kept only for ids still in the queue: acting on an invoice
  // removes it, and a stale id would otherwise inflate the count and get
  // re-submitted on the next bulk action (a 409 from the backend).
  const live = new Set(sorted.map((r) => r.invoice.invoice_id))
  const chosen = [...selected].filter((id) => live.has(id))
  const allChosen = sorted.length > 0 && chosen.length === sorted.length

  const toggle = (id) => setSelected((prev) => {
    const next = new Set(prev)
    if (next.has(id)) next.delete(id)
    else next.add(id)
    return next
  })

  const toggleAll = () =>
    setSelected(allChosen ? new Set() : new Set(sorted.map((r) => r.invoice.invoice_id)))

  // Sequential, not Promise.all: each approval draws down the same ledger, so
  // firing them concurrently would race on the balance. A failure mid-way stops
  // the run rather than pressing on blindly.
  async function bulk(action, verb) {
    const ids = chosen
    if (ids.length === 0) return
    const total = money(
      sorted.filter((r) => ids.includes(r.invoice.invoice_id))
            .reduce((sum, r) => sum + r.invoice.amount, 0),
    )
    const confirmMsg = verb === 'approve'
      ? `Approve and pay ${ids.length} invoice(s) totalling ${total}? This releases real payments against the ledger.`
      : `Reject ${ids.length} invoice(s) totalling ${total}?`
    if (!window.confirm(confirmMsg)) return

    setBusy(true)
    try {
      for (const id of ids) await action(id)
      setSelected(new Set())
    } finally {
      setBusy(false)
    }
  }

  return (
    <div className="panel">
      <div className="row" style={{ justifyContent: 'space-between' }}>
        <h2 style={{ margin: 0 }}>Review queue ({sorted.length})</h2>
        {sorted.length > 0 && (
          <div className="row">
            <span style={{ fontSize: 12, color: 'var(--muted)' }}>
              {chosen.length} selected
            </span>
            <button className="ok" disabled={busy || chosen.length === 0}
                    onClick={() => bulk(onApprove, 'approve')}>
              Approve &amp; pay selected
            </button>
            <button className="bad" disabled={busy || chosen.length === 0}
                    onClick={() => bulk(onReject, 'reject')}>
              Reject selected
            </button>
          </div>
        )}
      </div>

      {sorted.length === 0 ? (
        <div className="empty">
          Queue is clear — nothing is waiting on a human. 🎉
        </div>
      ) : (
        <table>
          <thead>
            <tr>
              <th style={{ width: 32 }}>
                <input type="checkbox" style={{ width: 'auto' }} checked={allChosen}
                       onChange={toggleAll} aria-label="Select all queued invoices" />
              </th>
              <th>Invoice</th><th>Vendor</th><th>Amount</th><th>Risk</th><th>Pipeline</th><th />
            </tr>
          </thead>
          <tbody>
            {sorted.map((rec) => {
              const id = rec.invoice.invoice_id
              const score = rec.assessment?.risk_score ?? 0
              return (
                <tr key={id}>
                  <td>
                    <input type="checkbox" style={{ width: 'auto' }}
                           checked={selected.has(id)} onChange={() => toggle(id)}
                           aria-label={`Select ${id}`} />
                  </td>
                  <td>
                    <b>{id}</b>
                    {(rec.policy_violations || []).map((v) => (
                      <div key={v.code}>
                        <span className={`chip ${v.severity === 'block' ? 'bad' : 'warn'}`}>{v.code}</span>
                      </div>
                    ))}
                  </td>
                  <td>{rec.invoice.vendor_name}</td>
                  <td>{money(rec.invoice.amount, rec.invoice.currency)}</td>
                  <td>
                    <span className="risk-bar">
                      <span className="risk-fill" style={{ width: `${score}%`, background: riskColor(score) }} />
                    </span>
                    <b>{score}</b>
                    <div style={{ color: 'var(--muted)', fontSize: 11, maxWidth: 260 }}>
                      {rec.assessment?.rationale}
                    </div>
                  </td>
                  <td><Pipeline rec={rec} /></td>
                  <td style={{ whiteSpace: 'nowrap' }}>
                    <button className="ok" disabled={busy} onClick={() => onApprove(id)}>Approve</button>{' '}
                    <button className="bad" disabled={busy} onClick={() => onReject(id)}>Reject</button>
                  </td>
                </tr>
              )
            })}
          </tbody>
        </table>
      )}
    </div>
  )
}
