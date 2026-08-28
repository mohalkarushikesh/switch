import { useCallback, useEffect, useState } from 'react'
import { api, setApiKey } from './api.js'
import Overview from './components/Overview.jsx'
import StatsBar from './components/StatsBar.jsx'
import SubmitPanel from './components/SubmitPanel.jsx'
import InvoiceTable from './components/InvoiceTable.jsx'
import Attention from './components/Attention.jsx'

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
  const run = (fn) => async (...args) => { await fn(...args); await refresh() }

  const loadSamples = run(async () => { for (const s of SAMPLES) { try { await api.submit(s) } catch { /* dup/auth */ } } })

  return (
    <>
      <header>
        <h1>🛡️ Custodian</h1>
        <span className="pill">Accounts-Payable Agent</span>
        <span className="grow" />
        <input style={{ maxWidth: 240 }} placeholder="API key (if auth on)" value={key} onChange={onKey} />
        <button className="ghost" onClick={loadSamples}>Load samples</button>
        <button className="ghost" onClick={refresh}>Refresh</button>
      </header>

      <main>
        {error && <div className="panel err">Backend error: {error}</div>}
        <Overview />
        <StatsBar stats={stats} health={health} />
        <div className="grid2">
          <SubmitPanel onSubmit={run(api.submit)} onOcr={run(api.submitOcr)} />
          <Attention records={invoices} />
        </div>
        <InvoiceTable records={invoices} onApprove={run(api.approve)} onReject={run(api.reject)} />
      </main>
    </>
  )
}
