// Two small dashboard charts, hand-rolled inline SVG (no chart library):
//   - a status-breakdown donut (paid / needs_review / rejected / failed)
//   - horizontal risk-band bars (low / medium / high)
// Both use reserved STATUS colors and always show a text label + count, so
// identity is never carried by color alone (colorblind-safe by construction).

// status key -> [label, color]. Colors are semantic status hues; the label/count
// beside every mark is the real identity carrier.
const STATUS = {
  paid: ['Paid', 'var(--green)'],
  needs_review: ['Needs review', 'var(--amber)'],
  rejected: ['Rejected', 'var(--red)'],
  failed: ['Failed', 'var(--violet)'],
}

function Donut({ counts, total }) {
  const size = 160
  const stroke = 22
  const r = (size - stroke) / 2
  const C = 2 * Math.PI * r
  const gap = total > 1 ? 2 : 0 // 2px surface gap between segments
  let offset = 0

  return (
    <svg width={size} height={size} viewBox={`0 0 ${size} ${size}`} role="img"
         aria-label="Invoice status breakdown">
      <g transform={`rotate(-90 ${size / 2} ${size / 2})`}>
        {/* recessive track */}
        <circle cx={size / 2} cy={size / 2} r={r} fill="none"
                stroke="var(--panel3)" strokeWidth={stroke} />
        {Object.entries(counts).map(([key, n]) => {
          if (!n) return null
          const frac = n / total
          const len = Math.max(frac * C - gap, 0)
          const seg = (
            <circle key={key} cx={size / 2} cy={size / 2} r={r} fill="none"
                    stroke={STATUS[key]?.[1] || 'var(--muted)'} strokeWidth={stroke}
                    strokeDasharray={`${len} ${C - len}`} strokeDashoffset={-offset}
                    strokeLinecap="butt">
              <title>{`${STATUS[key]?.[0] || key}: ${n} (${Math.round(frac * 100)}%)`}</title>
            </circle>
          )
          offset += frac * C
          return seg
        })}
      </g>
      <text x="50%" y="47%" textAnchor="middle" fill="var(--text)"
            fontSize="26" fontWeight="700">{total}</text>
      <text x="50%" y="60%" textAnchor="middle" fill="var(--muted)" fontSize="11">invoices</text>
    </svg>
  )
}

function RiskBars({ bands }) {
  const rows = [
    ['low', 'Low (0–30)', 'var(--green)', bands.low],
    ['medium', 'Medium (31–74)', 'var(--amber)', bands.medium],
    ['high', 'High (75–100)', 'var(--red)', bands.high],
  ]
  const max = Math.max(1, ...rows.map((r) => r[3]))
  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 10, width: '100%' }}>
      {rows.map(([key, label, color, n]) => (
        <div key={key}>
          <div className="row" style={{ justifyContent: 'space-between', marginBottom: 3 }}>
            <span style={{ fontSize: 12, color: 'var(--muted)' }}>{label}</span>
            <b style={{ fontSize: 12 }}>{n}</b>
          </div>
          {/* recessive track + rounded data-end bar */}
          <div style={{ background: 'var(--panel3)', borderRadius: 4, height: 10 }}>
            <div style={{ width: `${(n / max) * 100}%`, background: color, height: 10, borderRadius: 4 }}
                 title={`${label}: ${n}`} />
          </div>
        </div>
      ))}
    </div>
  )
}

export default function Charts({ records }) {
  const counts = { paid: 0, needs_review: 0, rejected: 0, failed: 0 }
  const bands = { low: 0, medium: 0, high: 0 }
  for (const r of records) {
    if (r.status in counts) counts[r.status] += 1
    const s = r.assessment?.risk_score ?? 0
    bands[s >= 75 ? 'high' : s >= 31 ? 'medium' : 'low'] += 1
  }
  const total = records.length

  return (
    <div className="panel">
      <h2>Portfolio</h2>
      {total === 0 ? (
        <div className="empty">No data yet — submit or load sample invoices.</div>
      ) : (
        <div className="grid2">
          <div>
            <h3>By status</h3>
            <div className="row" style={{ alignItems: 'center', gap: 16 }}>
              <Donut counts={counts} total={total} />
              <div>
                {Object.entries(counts).filter(([, n]) => n).map(([key, n]) => (
                  <div className="row" key={key} style={{ gap: 8, margin: '4px 0' }}>
                    <span style={{ width: 10, height: 10, borderRadius: 3, background: STATUS[key][1], display: 'inline-block' }} />
                    <span style={{ fontSize: 13 }}>{STATUS[key][0]}</span>
                    <b style={{ fontSize: 13 }}>{n}</b>
                  </div>
                ))}
              </div>
            </div>
          </div>
          <div>
            <h3>By risk band</h3>
            <RiskBars bands={bands} />
          </div>
        </div>
      )}
    </div>
  )
}
