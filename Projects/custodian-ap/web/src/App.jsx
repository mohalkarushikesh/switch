import { useCallback, useEffect, useRef, useState } from 'react'
import { api, setApiKey } from './api.js'
import Overview from './components/Overview.jsx'
import StatsBar from './components/StatsBar.jsx'
import SubmitPanel from './components/SubmitPanel.jsx'
import InvoiceTable from './components/InvoiceTable.jsx'
import Attention from './components/Attention.jsx'
import Charts from './components/Charts.jsx'
import Toasts from './components/Toasts.jsx'

const SAMPLES = [
  { invoice_id: 'INV-001', vendor_name: 'Acme Office Supplies', vendor_account: 'ACME-CHK-889201', amount: 1240.5, issue_date: '2026-08-10', due_date: '2026-09-10', line_items: ['Paper', 'Ink'], memo: 'Monthly office supply order.' },
  { invoice_id: 'INV-002', vendor_name: 'Skyline Construction Co', vendor_account: 'SKY-CHK-4410233', amount: 48250, issue_date: '2026-08-01', due_date: '2026-08-31', line_items: ['Phase 2 work'], memo: 'Progress payment 2 of 4.' },
  { invoice_id: 'INV-003', vendor_name: 'QuickPay Global Ltd', vendor_account: 'X12', amount: 75000, issue_date: '2026-08-25', due_date: '2026-08-26', line_items: [], memo: 'URGENT: wire now, changed bank details.' },
  { invoice_id: 'INV-004', vendor_name: 'Bright Cleaning Services', vendor_account: 'BRIGHT-CHK-77120', amount: 3000, issue_date: '2026-08-20', due_date: '2026-08-05', line_items: ['Weekly cleaning'], memo: 'Standard monthly cleaning.' },
]

export default function App() {
  const [health, setHealth] = useState(null)
  const [stats, setStats] = useState(null)
  const [invoices, setInvoices] = useState([])
  const [key, setKey] = useState('')
  const [error, setError] = useState('')
  const [toasts, setToasts] = useState([])
  const toastId = useRef(0)
  const [theme, setTheme] = useState(() => localStorage.getItem('custodian-theme') || 'dark')

  useEffect(() => {
    document.documentElement.setAttribute('data-theme', theme)
    localStorage.setItem('custodian-theme', theme)
  }, [theme])

  const pushToast = useCallback((msg, type = 'ok') => {
    const id = ++toastId.current
    setToasts((ts) => [...ts, { id, msg, type }])
    setTimeout(() => setToasts((ts) => ts.filter((t) => t.id !== id)), 3500)
  }, [])
  const dismiss = (id) => setToasts((ts) => ts.filter((t) => t.id !== id))

  const refresh = useCallback(async () => {
    try {
      const [h, s, inv] = await Promise.all([api.health(), api.stats(), api.listInvoices()])
      setHealth(h); setStats(s); setInvoices(inv); setError('')
    } catch (e) {
      setError(String(e.message || e))
    }
  }, [])

  useEffect(() => {
    refresh()
    const t = setInterval(refresh, 8000) // light polling so the view stays fresh
    return () => clearInterval(t)
  }, [refresh])

  const onKey = (e) => { setKey(e.target.value); setApiKey(e.target.value) }

  // Wrap an API call: refresh + toast on completion, error toast on failure.
  // `msg` may be a string or a fn(result)->string. A rejected/failed outcome is
  // toasted as "bad" so a duplicate/blocked submission is obvious.
  const run = (fn, msg) => async (...args) => {
    try {
      const r = await fn(...args)
      await refresh()
      if (msg) {
        const text = typeof msg === 'function' ? msg(r) : msg
        const bad = r && (r.status === 'rejected' || r.status === 'failed')
        pushToast(text, bad ? 'bad' : 'ok')
      }
      return r
    } catch (e) {
      pushToast(String(e.message || e), 'bad')
      throw e
    }
  }

  // Human-readable outcome for a processed-invoice result.
  const outcome = (r) => {
    const dup = (r.policy_violations || []).some((v) => v.code === 'duplicate_invoice')
    return `${r.invoice.invoice_id} → ${(r.status || '').replace('_', ' ')}${dup ? ' (duplicate)' : ''}`
  }

  const loadSamples = run(async () => {
    for (const s of SAMPLES) { try { await api.submit(s) } catch { /* dup/auth */ } }
  }, 'Sample invoices loaded')

  const deleteAll = () => {
    if (invoices.length === 0) return
    if (window.confirm(`Delete all ${invoices.length} invoices and reset the ledger? This cannot be undone.`)) {
      run(api.removeAll, 'All invoices deleted')()
    }
  }

  return (
    <>
      <header>
        <h1>🛡️ Custodian</h1>
        <span className="pill">Accounts-Payable Agent</span>
        <span className="grow" />
        <input style={{ maxWidth: 240 }} placeholder="API key (if auth on)" value={key} onChange={onKey} />
        <button className="ghost" onClick={loadSamples}>Load samples</button>
        <button className="ghost" onClick={refresh}>Refresh</button>
        <button className="bad" onClick={deleteAll} disabled={invoices.length === 0}
                title="Delete all invoices (admin)">Delete all</button>
        <button className="ghost" onClick={() => setTheme((t) => (t === 'dark' ? 'light' : 'dark'))}>
          {theme === 'dark' ? '☀️ Light' : '🌙 Dark'}
        </button>
      </header>

      <main>
        {error && <div className="panel err">Backend error: {error}</div>}
        <Overview />
        <StatsBar stats={stats} health={health} />
        <Charts records={invoices} />
        <div className="grid2">
          <SubmitPanel onSubmit={run(api.submit, outcome)} onOcr={run(api.submitOcr, outcome)} />
          <Attention records={invoices} />
        </div>
        <InvoiceTable
          records={invoices}
          onApprove={run(api.approve, 'Invoice approved & paid')}
          onReject={run(api.reject, 'Invoice rejected')}
          onDelete={run(api.remove, 'Invoice deleted')}
        />
      </main>

      <Toasts items={toasts} onDismiss={dismiss} />
    </>
  )
}
