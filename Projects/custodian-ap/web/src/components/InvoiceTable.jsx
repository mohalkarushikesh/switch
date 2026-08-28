// Invoice list with per-row pipeline viz and an expandable detail drawer
// (risk breakdown, PII, policy verdicts, payment, full audit trail) + actions.
import { useState } from 'react'
import Pipeline from './Pipeline.jsx'
import { money, riskColor, statusLabel } from '../lib/format.js'

function Detail({ rec, onApprove, onReject, onDelete }) {
  const id = rec.invoice.invoice_id
  const del = () => {
    if (window.confirm(`Delete invoice ${id}? This cannot be undone.`)) onDelete(id)
  }
  const a = rec.assessment
  const score = a?.risk_score ?? 0
  return (
    <div style={{ padding: '4px 2px' }}>
      <div className="grid2">
        <div>
          <h3>Risk assessment</h3>
          <div className="row">
            <span className="risk-bar"><span className="risk-fill" style={{ width: `${score}%`, background: riskColor(score) }} /></span>
            <b>{score}</b>/100 <span className="pill">via {a?.source ?? '—'}</span>
          </div>
          <div style={{ color: 'var(--muted)', margin: '6px 0' }}>{a?.rationale}</div>
          <div>{(a?.fraud_flags || []).map((f) => <span className="chip warn" key={f}>{f}</span>)}</div>

          <h3 style={{ marginTop: 12 }}>Data / PII</h3>
          {(rec.redacted_pii || []).length
            ? rec.redacted_pii.map((p) => <span className="chip" key={p}>{p} redacted</span>)
            : <span style={{ color: 'var(--muted)' }}>No PII detected.</span>}
        </div>
        <div>
          <h3>Policy</h3>
          {(rec.policy_violations || []).length
            ? rec.policy_violations.map((v) => (
                <div key={v.code}>
                  <span className={`chip ${v.severity === 'block' ? 'bad' : 'warn'}`}>{v.severity}: {v.code}</span>
                  <span style={{ color: 'var(--muted)', fontSize: 12 }}> {v.message}</span>
                </div>
              ))
            : <span style={{ color: 'var(--muted)' }}>No policy violations.</span>}

          <h3 style={{ marginTop: 12 }}>Decision & payment</h3>
          <div style={{ color: 'var(--muted)', fontSize: 13 }}>{rec.decision?.reason}</div>
          {rec.payment?.paid && <div className="mono" style={{ marginTop: 4 }}>✔ {rec.payment.transaction_id}</div>}
        </div>
      </div>

      <h3 style={{ marginTop: 12 }}>Audit trail</h3>
      <ul className="trail">{(rec.audit_trail || []).map((s, i) => <li key={i}>{s}</li>)}</ul>

      <div className="row" style={{ marginTop: 10, justifyContent: 'space-between' }}>
        <span>
          {rec.status === 'needs_review' && (
            <>
              <button className="ok" onClick={() => onApprove(id)}>Approve & pay</button>{' '}
              <button className="bad" onClick={() => onReject(id)}>Reject</button>
            </>
          )}
        </span>
        <button className="ghost" onClick={del} title="Delete this invoice (admin)">🗑 Delete</button>
      </div>
    </div>
  )
}

const STATUSES = ['all', 'paid', 'needs_review', 'rejected', 'failed']

export default function InvoiceTable({ records, onApprove, onReject, onDelete }) {
  const [open, setOpen] = useState(null)
  const [query, setQuery] = useState('')
  const [status, setStatus] = useState('all')

  const q = query.trim().toLowerCase()
  const filtered = records.filter((r) => {
    if (status !== 'all' && r.status !== status) return false
    if (!q) return true
    return (
      r.invoice.invoice_id.toLowerCase().includes(q) ||
      r.invoice.vendor_name.toLowerCase().includes(q)
    )
  })

  return (
    <div className="panel">
      <div className="row" style={{ justifyContent: 'space-between' }}>
        <h2 style={{ margin: 0 }}>Processed invoices ({filtered.length}/{records.length})</h2>
        <div className="row">
          <input style={{ maxWidth: 220 }} placeholder="Search id or vendor…"
                 value={query} onChange={(e) => setQuery(e.target.value)} />
          <select style={{ width: 'auto' }} value={status} onChange={(e) => setStatus(e.target.value)}>
            {STATUSES.map((s) => <option key={s} value={s}>{s === 'all' ? 'All statuses' : s.replace('_', ' ')}</option>)}
          </select>
        </div>
      </div>
      {records.length === 0 && <div className="empty">No invoices yet — submit one above.</div>}
      {records.length > 0 && filtered.length === 0 && <div className="empty">No invoices match the filter.</div>}
      {filtered.length > 0 && (
        <table>
          <thead>
            <tr><th>Invoice</th><th>Vendor</th><th>Amount</th><th>Pipeline</th><th>Status</th></tr>
          </thead>
          <tbody>
            {filtered.map((rec) => {
              const id = rec.invoice.invoice_id
              const isOpen = open === id
              return (
                <>
                  <tr key={id} className="clickable" onClick={() => setOpen(isOpen ? null : id)}>
                    <td><b>{id}</b></td>
                    <td>{rec.invoice.vendor_name}</td>
                    <td>{money(rec.invoice.amount, rec.invoice.currency)}</td>
                    <td><Pipeline rec={rec} /></td>
                    <td><span className={`badge ${rec.status}`}>{statusLabel(rec.status)}</span></td>
                  </tr>
                  {isOpen && (
                    <tr key={id + '-d'}><td colSpan={5}><Detail rec={rec} onApprove={onApprove} onReject={onReject} onDelete={onDelete} /></td></tr>
                  )}
                </>
              )
            })}
          </tbody>
        </table>
      )}
    </div>
  )
}
