// "Needs attention" feed — mirrors what the backend notifies on
// (rejected or high-risk invoices).
import { needsAttention, money } from '../lib/format.js'

export default function Attention({ records }) {
  const flagged = records.filter(needsAttention)
  return (
    <div className="panel">
      <h2>Needs attention ({flagged.length})</h2>
      {flagged.length === 0 && <div className="empty">Nothing flagged. 🎉</div>}
      {flagged.map((rec) => {
        const risk = rec.assessment?.risk_score ?? 0
        const events = []
        if (rec.status === 'rejected') events.push('rejected')
        if (risk >= 70) events.push('high-risk')
        return (
          <div key={rec.invoice.invoice_id} style={{ padding: '8px 0', borderBottom: '1px solid var(--border)' }}>
            <div className="row" style={{ justifyContent: 'space-between' }}>
              <b>{rec.invoice.invoice_id}</b>
              <span>{events.map((e) => <span className="chip bad" key={e}>{e}</span>)}</span>
            </div>
            <div style={{ color: 'var(--muted)', fontSize: 12 }}>
              {rec.invoice.vendor_name} · {money(rec.invoice.amount)} · risk {risk}
            </div>
          </div>
        )
      })}
    </div>
  )
}
