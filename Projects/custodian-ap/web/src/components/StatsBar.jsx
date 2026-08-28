// Stat tiles derived from /stats + /health.
import { money } from '../lib/format.js'

export default function StatsBar({ stats, health }) {
  const by = stats?.by_status || {}
  return (
    <div className="panel">
      <h2>At a glance</h2>
      <div className="tiles">
        <div className="tile">
          <div className="k">Invoices processed</div>
          <div className="v">{stats?.total_invoices ?? '—'}</div>
        </div>
        <div className="tile">
          <div className="k">Auto-paid</div>
          <div className="v" style={{ color: 'var(--green)' }}>{by.paid ?? 0}</div>
        </div>
        <div className="tile">
          <div className="k">Needs review / rejected</div>
          <div className="v" style={{ color: 'var(--amber)' }}>
            {(by.needs_review ?? 0)} / <span style={{ color: 'var(--red)' }}>{by.rejected ?? 0}</span>
          </div>
        </div>
        <div className="tile">
          <div className="k">Ledger balance</div>
          <div className="v">{money(health?.ledger_balance)}</div>
        </div>
      </div>
      <div className="row" style={{ marginTop: 12 }}>
        <span className="pill">Scoring: <b>{health?.scoring_mode ?? '…'}</b></span>
        <span className="pill">Model: <b>{health?.model ?? '…'}</b></span>
        <span className="pill">Total auto-paid: <b>{money(stats?.total_paid)}</b></span>
      </div>
    </div>
  )
}
