import { useCallback, useEffect, useMemo, useRef, useState } from 'react'
import { api, setApiKey } from './api.js'
import { useHashRoute } from './lib/useHashRoute.js'
import Nav from './components/Nav.jsx'
import Overview from './components/Overview.jsx'
import StatsBar from './components/StatsBar.jsx'
import SubmitPanel from './components/SubmitPanel.jsx'
import InvoiceTable from './components/InvoiceTable.jsx'
import Attention from './components/Attention.jsx'
import Charts from './components/Charts.jsx'
import Toasts from './components/Toasts.jsx'
import ReviewQueue from './components/ReviewQueue.jsx'
import LedgerView from './components/LedgerView.jsx'
import Governance from './components/Governance.jsx'
import Audit from './components/Audit.jsx'

const VIEWS = [
  { id: 'dashboard', label: 'Dashboard', icon: '▦' },
  { id: 'queue', label: 'Review queue', icon: '⏳' },
  { id: 'ledger', label: 'Ledger', icon: '₹' },
  { id: 'governance', label: 'Governance', icon: '🛡' },
  { id: 'audit', label: 'Audit', icon: '📜' },
]
// Module-level so its identity is stable across renders (useHashRoute deps).
const VIEW_IDS = VIEWS.map((v) => v.id)

const POLL_MS = 8000
// The audit log is append-only and every entry embeds a full invoice snapshot,
// so cap what the dashboard pulls rather than growing the payload forever.
const AUDIT_LIMIT = 200

// Sample memos/line items deliberately embed PII (emails + phone numbers) so the
// Data-governance layer has something to redact — the "redacted_pii" chips in
// each invoice's detail drawer prove PII never reaches the LLM.
const SAMPLES = [
  { invoice_id: 'INV-001', vendor_name: 'Acme Office Supplies', vendor_account: 'ACME-CHK-889201', amount: 1240.5, issue_date: '2026-08-10', due_date: '2026-09-10', line_items: ['Paper', 'Ink — reorder: supplies@acme-office.com'], memo: 'Monthly office supply order. Queries: ap@acme-office.com or +91 98765 43210.' },
  { invoice_id: 'INV-002', vendor_name: 'Skyline Construction Co', vendor_account: 'SKY-CHK-4410233', amount: 48250, issue_date: '2026-08-01', due_date: '2026-08-31', line_items: ['Phase 2 work — foreman +91 90012 34567'], memo: 'Progress payment 2 of 4. Site lead: rakesh@skyline-build.in, +91 90000 12345.' },
  { invoice_id: 'INV-003', vendor_name: 'QuickPay Global Ltd', vendor_account: 'X12', amount: 75000, issue_date: '2026-08-25', due_date: '2026-08-26', line_items: ['Consulting — invoices to billing@quickpay-global.co'], memo: 'URGENT: wire now, changed bank details. Confirm to finance@quickpay-global.co or +91 98111 22333.' },
  { invoice_id: 'INV-004', vendor_name: 'Bright Cleaning Services', vendor_account: 'BRIGHT-CHK-77120', amount: 3000, issue_date: '2026-08-20', due_date: '2026-08-05', line_items: ['Weekly cleaning — supervisor priya@brightclean.in'], memo: 'Standard monthly cleaning. Billing: billing@brightclean.in, 022-4455-6677.' },
]

export default function App() {
  const [route, navigate] = useHashRoute(VIEW_IDS, 'dashboard')

  const [health, setHealth] = useState(null)
  const [stats, setStats] = useState(null)
  const [invoices, setInvoices] = useState([])
  // Per-view data, fetched only while its section is open.
  const [ledger, setLedger] = useState(null)
  const [policies, setPolicies] = useState(null)
  const [audit, setAudit] = useState(null)

  const [key, setKey] = useState('')
  const [error, setError] = useState('')
  const [toasts, setToasts] = useState([])
  const toastId = useRef(0)
  const [live, setLive] = useState(true)
  const [updatedAt, setUpdatedAt] = useState(null)
  // Light is the default (USWDS government-interface convention); a returning
  // user's explicit choice still wins.
  const [theme, setTheme] = useState(() => localStorage.getItem('custodian-theme') || 'light')

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
      setHealth(h); setStats(s); setInvoices(inv)
      // Only the open section's extra endpoint is polled, so switching views
      // costs one request instead of every view paying for all of them.
      if (route === 'ledger') setLedger(await api.ledger())
      if (route === 'governance') setPolicies(await api.policies())
      if (route === 'audit') setAudit(await api.audit(AUDIT_LIMIT))
      setError('')
      setUpdatedAt(new Date())
    } catch (e) {
      setError(String(e.message || e))
    }
  }, [route])

  // Refetches on mount, on every view change, and while live polling is on.
  useEffect(() => {
    refresh()
    if (!live) return
    const t = setInterval(refresh, POLL_MS)
    return () => clearInterval(t)
  }, [refresh, live])

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

  // One /invoices/batch call rather than four sequential submits.
  const loadSamples = run(() => api.submitBatch(SAMPLES), 'Sample invoices loaded')

  const deleteAll = () => {
    if (invoices.length === 0) return
    if (window.confirm(`Delete all ${invoices.length} invoices and reset the ledger? This cannot be undone.`)) {
      run(api.removeAll, 'All invoices deleted')()
    }
  }

  const approve = run(api.approve, 'Invoice approved & paid')
  const reject = run(api.reject, 'Invoice rejected')

  // Flip risk scoring between the live LLM and the offline heuristic at runtime.
  const toggleScoring = () => {
    const next = health?.scoring_mode === 'llm' ? 'heuristic' : 'llm'
    const msg = next === 'llm' ? 'Scoring: live LLM' : 'Scoring: offline heuristic'
    run(api.setScoringMode, msg)(next)
  }

  const queueCount = useMemo(
    () => invoices.filter((r) => r.status === 'needs_review').length,
    [invoices],
  )

  return (
    <>
      <header>
        <h1>🛡️ Custodian</h1>
        <span className="pill">Accounts-Payable Agent</span>
        <span className="grow" />
        <input style={{ maxWidth: 200 }} placeholder="API key (if auth on)" value={key} onChange={onKey} />
        <button className="ghost" onClick={loadSamples}>Load samples</button>
        <button
          className="ghost"
          onClick={toggleScoring}
          disabled={!health?.llm_available}
          title={
            health?.llm_available
              ? 'Toggle risk scoring between the live LLM and the offline heuristic'
              : 'No LLM key configured (or disabled) — heuristic only'
          }
        >
          {health?.scoring_mode === 'llm' ? '🤖 Scoring: LLM' : '🧮 Scoring: Heuristic'}
        </button>
        <button className={live ? 'ghost' : ''} onClick={() => setLive((v) => !v)}
                title={live ? `Auto-refreshing every ${POLL_MS / 1000}s — click to pause` : 'Paused — click to resume auto-refresh'}>
          {live ? '⏸ Live' : '▶ Paused'}
        </button>
        <button className="ghost" onClick={refresh}>Refresh</button>
        <button className="bad" onClick={deleteAll} disabled={invoices.length === 0}
                title="Delete all invoices (admin)">Delete all</button>
        <button className="ghost" onClick={() => setTheme((t) => (t === 'dark' ? 'light' : 'dark'))}>
          {theme === 'dark' ? '☀️ Light' : '🌙 Dark'}
        </button>
      </header>

      <div className="shell">
        <Nav views={VIEWS} active={route} onNavigate={navigate} badges={{ queue: queueCount }} />

        <main>
          {error && <div className="panel err">Backend error: {error}</div>}

          {route === 'dashboard' && (
            <>
              <Overview />
              <StatsBar stats={stats} health={health} />
              <Charts records={invoices} />
              <div className="grid2">
                <SubmitPanel onSubmit={run(api.submit, outcome)} onOcr={run(api.submitOcr, outcome)} />
                <Attention records={invoices} />
              </div>
              <InvoiceTable
                records={invoices}
                onApprove={approve}
                onReject={reject}
                onDelete={run(api.remove, 'Invoice deleted')}
              />
            </>
          )}

          {route === 'queue' && (
            <ReviewQueue records={invoices} onApprove={approve} onReject={reject} />
          )}
          {route === 'ledger' && <LedgerView ledger={ledger} />}
          {route === 'governance' && <Governance policies={policies} health={health} />}
          {route === 'audit' && <Audit audit={audit} onClear={run(api.clearAudit, 'Audit log cleared')} />}

          <div className="updated">
            {updatedAt
              ? `Updated ${updatedAt.toLocaleTimeString()}${live ? '' : ' · auto-refresh paused'}`
              : 'Loading…'}
          </div>
        </main>
      </div>

      <Toasts items={toasts} onDismiss={dismiss} />
    </>
  )
}
