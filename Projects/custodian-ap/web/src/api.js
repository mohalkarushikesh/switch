// Tiny API client for the Custodian backend. Attaches the API key (if the user
// entered one) as X-API-Key on write requests, so it works whether or not the
// backend has auth enabled.

let apiKey = ''
export const setApiKey = (k) => { apiKey = k || '' }

async function req(method, path, body) {
  const headers = {}
  if (body !== undefined) headers['Content-Type'] = 'application/json'
  if (apiKey && method !== 'GET') headers['X-API-Key'] = apiKey
  const resp = await fetch(path, {
    method,
    headers,
    body: body !== undefined ? JSON.stringify(body) : undefined,
  })
  const text = await resp.text()
  const data = text ? JSON.parse(text) : null
  if (!resp.ok) {
    const detail = data && data.detail ? data.detail : resp.statusText
    throw new Error(`${resp.status}: ${detail}`)
  }
  return data
}

export const api = {
  health: () => req('GET', '/health'),
  stats: () => req('GET', '/stats'),
  ledger: () => req('GET', '/ledger'),
  policies: () => req('GET', '/policies'),
  listInvoices: () => req('GET', '/invoices'),
  getInvoice: (id) => req('GET', `/invoices/${id}`),
  submit: (invoice) => req('POST', '/invoices', invoice),
  submitOcr: (text) => req('POST', '/invoices/ocr', { text }),
  approve: (id) => req('POST', `/invoices/${id}/approve`),
  reject: (id) => req('POST', `/invoices/${id}/reject`),
}
