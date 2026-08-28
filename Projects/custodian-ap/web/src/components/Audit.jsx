// Audit view — the append-only decision log. Backed by GET /audit, which was
// wired in api.js but rendered nowhere before.
//
// Each entry is a full ProcessedInvoice snapshot at the moment it was recorded,
// so the same invoice appears once per decision (submitted, then approved, ...).
// That history is the point: it's what makes a decision reconstructable.
import { Fragment, useState } from 'react'
import { money, riskColor, statusLabel } from '../lib/format.js'
import Disclosure from './Disclosure.jsx'

const PAGE = 25

// SQLite writes "YYYY-MM-DD HH:MM:SS" (UTC, no zone marker). Render it as-is
// rather than through Date(), which would silently shift it by the local offset.
const timestamp = (value) => (value ? String(value).replace('T', ' ').replace('Z', '') : '—')

export default function Audit({ audit }) {
  const [query, setQuery] = useState('')
  const [shown, setShown] = useState(PAGE)
  const [open, setOpen] = useState(null)

  if (!audit) {
    return (
      <div className="panel">
        <h2>Audit log</h2>
        <div className="empty">Loading audit log…</div>
      </div>
    )
  }

  // The API returns oldest-first; an audit reader wants the latest decision top.
  const entries = [...(audit.entries || [])].reverse()

  const q = query.trim().toLowerCase()
  const filtered = q
    ? entries.filter((e) => {
        const inv = e.invoice || {}
        return (
          String(inv.invoice_id || '').toLowerCase().includes(q) ||
          String(inv.vendor_name || '').toLowerCase().includes(q) ||
          String(e.status || '').toLowerCase().includes(q)
        )
      })
    : entries

  const visible = filtered.slice(0, shown)

  return (
    <div className="panel">
      <div className="row" style={{ justifyContent: 'space-between' }}>
        <h2 style={{ margin: 0 }}>Audit log ({filtered.length}{audit.total ? ` of ${audit.total}` : ''})</h2>
        <input
          style={{ maxWidth: 260 }}
          placeholder="Search invoice, vendor or status…"
          value={query}
          onChange={(e) => { setQuery(e.target.value); setShown(PAGE) }}
        />
      </div>
      <div className="mono" style={{ color: 'var(--muted)', marginBottom: 10 }}>
        source: {audit.path}
      </div>

      {entries.length === 0 && (
        <div className="empty">No audit events yet — submit an invoice to create one.</div>
      )}
      {entries.length > 0 && filtered.length === 0 && (
        <div className="empty">No audit events match the filter.</div>
      )}

      {visible.length > 0 && (
        <table>
          <thead>
            <tr>
              <th>Recorded</th><th>Invoice</th><th>Vendor</th><th>Amount</th><th>Risk</th><th>Status</th>
            </tr>
          </thead>
          <tbody>
            {visible.map((entry, i) => {
              // audit_id is present on the SQLite log; the JSONL log has no id,
              // so fall back to the index for a stable-enough key.
              const key = entry.audit_id ?? `idx-${i}`
              const inv = entry.invoice || {}
              const score = entry.assessment?.risk_score ?? 0
              const isOpen = open === key
              return (
                <Fragment key={key}>
                  <tr className="clickable" onClick={() => setOpen(isOpen ? null : key)}>
                    <td className="mono">{timestamp(entry.recorded_at)}</td>
                    <td>
                      <Disclosure isOpen={isOpen} label={`audit detail for ${inv.invoice_id}`}
                                  onToggle={() => setOpen(isOpen ? null : key)}>
                        <b>{inv.invoice_id}</b>
                      </Disclosure>
                    </td>
                    <td>{inv.vendor_name}</td>
                    <td>{money(inv.amount, inv.currency)}</td>
                    <td>
                      <span className="risk-bar">
                        <span className="risk-fill" style={{ width: `${score}%`, background: riskColor(score) }} />
                      </span>
                      {score}
                    </td>
                    <td><span className={`badge ${entry.status}`}>{statusLabel(entry.status)}</span></td>
                  </tr>
                  {isOpen && (
                    <tr>
                      <td colSpan={6}>
                        <h3>Trail at time of recording</h3>
                        <ul className="trail">
                          {(entry.audit_trail || []).map((step, j) => <li key={j}>{step}</li>)}
                        </ul>
                        {entry.decision?.reason && (
                          <div style={{ color: 'var(--muted)', fontSize: 12, marginTop: 6 }}>
                            Decision: {entry.decision.reason}
                          </div>
                        )}
                      </td>
                    </tr>
                  )}
                </Fragment>
              )
            })}
          </tbody>
        </table>
      )}

      {filtered.length > visible.length && (
        <div style={{ marginTop: 12, textAlign: 'center' }}>
          <button className="ghost" onClick={() => setShown((n) => n + PAGE)}>
            Show {Math.min(PAGE, filtered.length - visible.length)} more
          </button>
        </div>
      )}
    </div>
  )
}
