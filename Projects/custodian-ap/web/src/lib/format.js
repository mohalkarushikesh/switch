// Small shared formatting/derivation helpers.

export const money = (n, currency = 'INR') =>
  (n ?? 0).toLocaleString('en-IN', { style: 'currency', currency })

// Risk band -> color. Mirrors the backend's routing thresholds.
export const riskColor = (score) =>
  score >= 75 ? 'var(--red)' : score >= 31 ? 'var(--amber)' : 'var(--green)'

export const statusLabel = (s) => (s || '').replace(/_/g, ' ')

// An invoice "needs attention" if it was rejected or scored high-risk (>= 70),
// matching the backend's notification criteria.
export const needsAttention = (rec) => {
  const risk = rec.assessment?.risk_score ?? 0
  return rec.status === 'rejected' || risk >= 70
}
