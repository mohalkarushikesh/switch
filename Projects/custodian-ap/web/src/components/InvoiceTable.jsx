// Invoice list with per-row pipeline viz and an expandable detail drawer
// (risk breakdown, PII, policy verdicts, payment, full audit trail) + actions.
import { Fragment, useState } from 'react'
import Pipeline from './Pipeline.jsx'
import { money, riskColor, statusLabel } from '../lib/format.js'
import Disclosure from './Disclosure.jsx'
import { downloadCsv } from '../lib/csv.js'

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

// Risk bands match the backend's routing thresholds (see Governance view).
const RISK_BANDS = {
  all: () => true,
  low: (s) => s <= 30,
  medium: (s) => s >= 31 && s <= 74,
  high: (s) => s >= 75,
}
const BAND_LABELS = { all: 'All risk', low: 'Low (0–30)', medium: 'Medium (31–74)', high: 'High (75–100)' }

// Sortable columns -> the value each one sorts on. Sorting is client-side
// because the full list is already loaded; refetching to reorder would add a
// round-trip and a loading state for nothing.
const SORTERS = {
  invoice: (r) => r.invoice.invoice_id,
  vendor: (r) => r.invoice.vendor_name,
  amount: (r) => r.invoice.amount,
  risk: (r) => r.assessment?.risk_score ?? 0,
  status: (r) => r.status,
}

export default function InvoiceTable({ records, onApprove, onReject, onDelete }) {
  const [open, setOpen] = useState(null)
  const [query, setQuery] = useState('')
  const [status, setStatus] = useState('all')
  const [band, setBand] = useState('all')
  const [sort, setSort] = useState({ key: null, dir: 'asc' })

  const q = query.trim().toLowerCase()
  const matched = records.filter((r) => {
    if (status !== 'all' && r.status !== status) return false
    if (!RISK_BANDS[band](r.assessment?.risk_score ?? 0)) return false
    if (!q) return true
    return (
      r.invoice.invoice_id.toLowerCase().includes(q) ||
      r.invoice.vendor_name.toLowerCase().includes(q)
    )
  })

  // No sort selected keeps the backend's newest-first ordering.
  const filtered = sort.key
    ? [...matched].sort((a, b) => {
        const get = SORTERS[sort.key]
        const [x, y] = [get(a), get(b)]
        const cmp = typeof x === 'number' ? x - y : String(x).localeCompare(String(y))
        return sort.dir === 'asc' ? cmp : -cmp
      })
    : matched

  // Click cycles asc -> desc on the same column; a new column starts at asc.
  const toggleSort = (key) =>
    setSort((prev) => ({ key, dir: prev.key === key && prev.dir === 'asc' ? 'desc' : 'asc' }))

  const Th = ({ id, children }) => (
    <th>
      <button type="button" className="sortbtn" onClick={() => toggleSort(id)}
              aria-label={`Sort by ${id}`}
              aria-sort={sort.key === id ? (sort.dir === 'asc' ? 'ascending' : 'descending') : 'none'}>
        {children}
        <span className="sortarrow" aria-hidden="true">
          {sort.key === id ? (sort.dir === 'asc' ? '▲' : '▼') : ''}
        </span>
      </button>
    </th>
  )

  return (
    <div className="panel">
      <div className="row" style={{ justifyContent: 'space-between' }}>
        <h2 style={{ margin: 0 }}>Processed invoices ({filtered.length}/{records.length})</h2>
        <div className="row">
          <input style={{ maxWidth: 220 }} placeholder="Search id or vendor…"
                 value={query} onChange={(e) => setQuery(e.target.value)} />
          <select style={{ width: 'auto' }} value={status} onChange={(e) => setStatus(e.target.value)}
                  aria-label="Filter by status">
            {STATUSES.map((s) => <option key={s} value={s}>{s === 'all' ? 'All statuses' : s.replace('_', ' ')}</option>)}
          </select>
          <select style={{ width: 'auto' }} value={band} onChange={(e) => setBand(e.target.value)}
                  aria-label="Filter by risk band">
            {Object.keys(RISK_BANDS).map((b) => <option key={b} value={b}>{BAND_LABELS[b]}</option>)}
          </select>
          <button className="ghost" disabled={records.length === 0}
                  onClick={() => downloadCsv(records)} title="Export all as CSV">⬇ CSV</button>
        </div>
      </div>
      {records.length === 0 && <div className="empty">No invoices yet — submit one above.</div>}
      {records.length > 0 && filtered.length === 0 && <div className="empty">No invoices match the filter.</div>}
      {filtered.length > 0 && (
        <table>
          <thead>
            <tr>
              <Th id="invoice">Invoice</Th>
              <Th id="vendor">Vendor</Th>
              <Th id="amount">Amount</Th>
              <Th id="risk">Risk</Th>
              <th>Pipeline</th>
              <Th id="status">Status</Th>
            </tr>
          </thead>
          <tbody>
            {filtered.map((rec) => {
              const id = rec.invoice.invoice_id
              const isOpen = open === id
              const score = rec.assessment?.risk_score ?? 0
              return (
                // The key belongs on the Fragment: a row and its detail row are
                // one list item, so keying the inner <tr>s left the item itself
                // unkeyed and row identity unstable across re-renders.
                <Fragment key={id}>
                  <tr className="clickable" onClick={() => setOpen(isOpen ? null : id)}>
                    <td>
                      <Disclosure isOpen={isOpen} label={`details for ${id}`}
                                  onToggle={() => setOpen(isOpen ? null : id)}>
                        <b>{id}</b>
                      </Disclosure>
                    </td>
                    <td>{rec.invoice.vendor_name}</td>
                    <td>{money(rec.invoice.amount, rec.invoice.currency)}</td>
                    <td style={{ whiteSpace: 'nowrap' }}>
                      <span className="risk-bar">
                        <span className="risk-fill" style={{ width: `${score}%`, background: riskColor(score) }} />
                      </span>
                      {score}
                    </td>
                    <td><Pipeline rec={rec} /></td>
                    <td><span className={`badge ${rec.status}`}>{statusLabel(rec.status)}</span></td>
                  </tr>
                  {isOpen && (
                    <tr><td colSpan={6}><Detail rec={rec} onApprove={onApprove} onReject={onReject} onDelete={onDelete} /></td></tr>
                  )}
                </Fragment>
              )
            })}
          </tbody>
        </table>
      )}
    </div>
  )
}
