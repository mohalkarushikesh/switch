// Export processed invoices to a CSV file, client-side (no backend needed).

const COLUMNS = [
  ['invoice_id', (r) => r.invoice.invoice_id],
  ['vendor', (r) => r.invoice.vendor_name],
  ['amount', (r) => r.invoice.amount],
  ['currency', (r) => r.invoice.currency],
  ['status', (r) => r.status],
  ['risk_score', (r) => r.assessment?.risk_score ?? ''],
  ['source', (r) => r.assessment?.source ?? ''],
  ['decision', (r) => r.decision?.reason ?? ''],
]

const cell = (v) => `"${String(v).replace(/"/g, '""')}"`

export function toCsv(records) {
  const header = COLUMNS.map(([name]) => name).join(',')
  const rows = records.map((r) => COLUMNS.map(([, fn]) => cell(fn(r))).join(','))
  return [header, ...rows].join('\n')
}

export function downloadCsv(records, filename = 'custodian-invoices.csv') {
  const blob = new Blob([toCsv(records)], { type: 'text/csv;charset=utf-8' })
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = filename
  a.click()
  URL.revokeObjectURL(url)
}
