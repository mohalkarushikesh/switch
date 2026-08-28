// Tiny API client for the Custodian backend. Attaches the API key (if the user
// entered one) as X-API-Key on every request, so it works whether or not the
// backend has auth enabled.

let apiKey = ''
export const setApiKey = (k) => { apiKey = k || '' }

async function req(method, path, body) {
  const headers = {}
  if (body !== undefined) headers['Content-Type'] = 'application/json'
  // Sent on reads too, not just writes: /invoices, /ledger and /audit now
  // require a key when the backend has auth enabled, because they return full
  // invoice snapshots including vendor account numbers.
  if (apiKey) headers['X-API-Key'] = apiKey
  const resp = await fetch(path, {
    method,
    headers,
    body: body !== undefined ? JSON.stringify(body) : undefined,
  })
  const text = await resp.text()
  const data = text ? JSON.parse(text) : null
  if (!resp.ok) {
    throw new Error(`${resp.status}: ${formatDetail(data, resp.statusText)}`)
  }
  return data
}

// FastAPI returns validation errors as an array of {loc, msg, type} objects;
// render them readably instead of "[object Object]".
function formatDetail(data, fallback) {
  const detail = data && data.detail !== undefined ? data.detail : fallback
  if (Array.isArray(detail)) {
    return detail
      .map((e) => {
        const field = Array.isArray(e.loc) ? e.loc.slice(1).join('.') : ''
        return field ? `${field}: ${e.msg}` : e.msg
      })
      .join('; ')
  }
  if (detail && typeof detail === 'object') return JSON.stringify(detail)
  return String(detail)
}

export const api = {
  health: () => req('GET', '/health'),
  stats: () => req('GET', '/stats'),
  ledger: () => req('GET', '/ledger'),
  policies: () => req('GET', '/policies'),
  audit: (limit) => req('GET', limit ? `/audit?limit=${limit}` : '/audit'),
  listInvoices: () => req('GET', '/invoices'),
  getInvoice: (id) => req('GET', `/invoices/${id}`),
  submit: (invoice) => req('POST', '/invoices', invoice),
  submitBatch: (invoices) => req('POST', '/invoices/batch', invoices),
  submitOcr: (text) => req('POST', '/invoices/ocr', { text }),
  approve: (id) => req('POST', `/invoices/${id}/approve`),
  reject: (id) => req('POST', `/invoices/${id}/reject`),
  remove: (id) => req('DELETE', `/invoices/${id}`),
  removeAll: () => req('DELETE', '/invoices'),
}
