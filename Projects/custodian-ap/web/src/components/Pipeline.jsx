// Visualizes one invoice's journey through the pipeline stages.

function stagesFor(rec) {
  const risk = rec.assessment?.risk_score ?? 0
  const dstatus = rec.decision?.status
  const violations = rec.policy_violations || []
  const hasBlock = violations.some((v) => v.severity === 'block')
  const hasFlag = violations.some((v) => v.severity === 'flag')

  const riskState = risk >= 75 ? 'bad' : risk >= 31 ? 'warn' : 'done'
  const approvalState =
    dstatus === 'approved' ? 'done' : dstatus === 'rejected' ? 'bad' : 'warn'
  const policyState = hasBlock ? 'bad' : hasFlag ? 'warn' : 'done'
  const payState = rec.payment?.paid ? 'done' : rec.status === 'failed' ? 'bad' : 'skip'

  return [
    { name: 'Ingest', state: 'done' },
    { name: 'PII', state: (rec.redacted_pii || []).length ? 'warn' : 'done' },
    { name: 'Risk', state: riskState },
    { name: 'Approval', state: approvalState },
    { name: 'Policy', state: policyState },
    { name: 'Payment', state: payState },
  ]
}

export default function Pipeline({ rec }) {
  const stages = stagesFor(rec)
  return (
    <div className="pipe">
      {stages.map((s, i) => (
        <span className="stage" key={s.name}>
          <span className={`dot ${s.state}`} title={s.state} />
          <span className="name">{s.name}</span>
          {i < stages.length - 1 && <span className="arrow">→</span>}
        </span>
      ))}
    </div>
  )
}
