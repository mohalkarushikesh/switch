// Explanatory landing panel — what Custodian is + the six governance layers.

// Exported so the Governance view can render the same six layers without
// duplicating the copy.
export const LAYERS = [
  ['Identity', 'Who is acting, and are they allowed? (API keys / roles here; Keycloak + SPIRE in the full stack)'],
  ['Data', 'PII is scrubbed from invoice text before it reaches an LLM'],
  ['Model', 'LLM calls are gated & routed through one gateway (LiteLLM)'],
  ['Policy', 'Hard rules decide what may happen — ceilings, denylist, duplicates'],
  ['Agent Runtime', 'Agents execute the pipeline: ingest → risk → approval → payment'],
  ['Operations', 'Every action is audited; metrics & notifications make it observable'],
]

export default function Overview() {
  return (
    <div className="panel">
      <h2>What is Custodian?</h2>
      <p style={{ marginTop: 0, color: 'var(--muted)' }}>
        A governed multi-agent accounts-payable system: agents <b>read</b> invoices,{' '}
        <b>score</b> them for fraud/risk, <b>route</b> approvals, and <b>auto-pay</b> the safe
        ones — wrapped in governance layers so every decision is auditable and provable.
      </p>
      <div className="layers">
        {LAYERS.map(([t, d]) => (
          <div className="layer" key={t}>
            <div className="t">{t}</div>
            <div className="d">{d}</div>
          </div>
        ))}
      </div>
    </div>
  )
}
