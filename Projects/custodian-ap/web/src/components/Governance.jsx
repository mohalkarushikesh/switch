// Governance view — the active policy configuration that decides every
// invoice's fate. Backed by GET /policies, which was wired in api.js but
// rendered nowhere before, so these thresholds were invisible in the UI.
import { money } from '../lib/format.js'
import { LAYERS } from './Overview.jsx'

// The routing bands, derived from the thresholds the backend reports. Mirrors
// agents/approval.py: auto-pay at/below max risk, reject at/above min risk,
// everything between goes to a human.
function bandsFor(policies) {
  const autoMax = policies.auto_pay_max_risk
  const rejectMin = policies.reject_min_risk
  return [
    {
      key: 'auto',
      label: 'Auto-pay',
      range: `0–${autoMax}`,
      color: 'var(--green)',
      width: autoMax + 1,
      detail: `Paid without a human, provided the amount is at or below ${money(policies.auto_pay_max_amount)}.`,
    },
    {
      key: 'review',
      label: 'Human review',
      range: `${autoMax + 1}–${rejectMin - 1}`,
      color: 'var(--amber)',
      width: Math.max(0, rejectMin - autoMax - 1),
      detail: 'Queued for a reviewer to approve or reject.',
    },
    {
      key: 'reject',
      label: 'Auto-reject',
      range: `${rejectMin}–100`,
      color: 'var(--red)',
      width: Math.max(0, 101 - rejectMin),
      detail: 'Rejected outright; no payment is attempted.',
    },
  ]
}

function RiskRuler({ policies }) {
  const bands = bandsFor(policies).filter((b) => b.width > 0)
  return (
    <>
      {/* Proportional ruler across the 0-100 risk scale. Each segment carries
          its own text label, so the bands never rely on colour alone. */}
      <div className="ruler" role="img"
           aria-label={bands.map((b) => `${b.label}: risk ${b.range}`).join('; ')}>
        {bands.map((b) => (
          <div key={b.key} className="ruler-seg" style={{ flex: b.width, background: b.color }}>
            <span>{b.range}</span>
          </div>
        ))}
      </div>
      <div style={{ marginTop: 10 }}>
        {bands.map((b) => (
          <div key={b.key} className="row" style={{ gap: 8, alignItems: 'flex-start', margin: '6px 0' }}>
            <span style={{
              width: 10, height: 10, borderRadius: 3, background: b.color,
              display: 'inline-block', marginTop: 4, flex: '0 0 auto',
            }} />
            <span>
              <b>{b.label}</b> <span className="mono" style={{ color: 'var(--muted)' }}>risk {b.range}</span>
              <div style={{ color: 'var(--muted)', fontSize: 12 }}>{b.detail}</div>
            </span>
          </div>
        ))}
      </div>
    </>
  )
}

export default function Governance({ policies, health }) {
  if (!policies) {
    return (
      <div className="panel">
        <h2>Governance</h2>
        <div className="empty">Loading policy configuration…</div>
      </div>
    )
  }

  const blocked = policies.blocked_vendors || []

  return (
    <>
      <div className="panel">
        <h2>Approval routing</h2>
        <RiskRuler policies={policies} />
      </div>

      <div className="grid2">
        <div className="panel">
          <h2>Hard limits</h2>
          <table>
            <tbody>
              <tr>
                <td>Absolute ceiling</td>
                <td><b>{money(policies.absolute_ceiling)}</b></td>
              </tr>
              <tr>
                <td>Auto-pay amount cap</td>
                <td><b>{money(policies.auto_pay_max_amount)}</b></td>
              </tr>
              <tr>
                <td>Auto-pay max risk</td>
                <td><b>{policies.auto_pay_max_risk}</b>/100</td>
              </tr>
              <tr>
                <td>Auto-reject min risk</td>
                <td><b>{policies.reject_min_risk}</b>/100</td>
              </tr>
            </tbody>
          </table>
          <div style={{ color: 'var(--muted)', fontSize: 12, marginTop: 8 }}>
            Any invoice above the absolute ceiling is blocked by policy regardless of its
            risk score — a hard rule that overrides the model's judgement.
          </div>
        </div>

        <div className="panel">
          <h2>Blocked vendors ({blocked.length})</h2>
          {blocked.length === 0 ? (
            <div className="empty">
              No vendor denylist configured. Set <span className="mono">CUSTODIAN_BLOCKED_VENDORS</span>.
            </div>
          ) : (
            <div>{blocked.map((v) => <span className="chip bad" key={v}>{v}</span>)}</div>
          )}

          <h3 style={{ marginTop: 16 }}>Model layer</h3>
          <div className="row">
            <span className="pill">Scoring: <b>{health?.scoring_mode ?? '…'}</b></span>
            {health?.provider && <span className="pill">Provider: <b>{health.provider}</b></span>}
          </div>
          <div style={{ color: 'var(--muted)', fontSize: 12, marginTop: 8 }}>
            Risk scores come from {health?.scoring_mode === 'llm'
              ? 'an LLM routed through LiteLLM'
              : 'the transparent rule-based heuristic'}.
          </div>
        </div>
      </div>

      <div className="panel">
        <h2>Governance layers</h2>
        <div className="layers">
          {LAYERS.map(([title, detail]) => (
            <div className="layer" key={title}>
              <div className="t">{title}</div>
              <div className="d">{detail}</div>
            </div>
          ))}
        </div>
      </div>
    </>
  )
}
