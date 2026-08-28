// Submit invoices either as a structured form or as OCR-style text.
import { useState } from 'react'

// Fresh, unique id each time so repeated submits aren't blocked as duplicates.
const genId = () => 'INV-' + Date.now().toString().slice(-6)

const BLANK = {
  vendor_name: 'New Vendor Co', vendor_account: 'NVC-CHK-100200',
  amount: 2500, issue_date: '2026-08-15', due_date: '2026-09-15',
  line_items: 'Consulting, Support', memo: 'Q3 services',
}

const SAMPLE_OCR = `Invoice Number: OCR-500
Vendor: Globex Corp
Account: GLBX-CHK-4521
Invoice Date: 2026-08-14
Due Date: 2026-09-14
- Cloud hosting (August)
- Support retainer
Total: ₹4,200.00
Memo: Monthly services`

export default function SubmitPanel({ onSubmit, onOcr }) {
  const [tab, setTab] = useState('form')
  const [form, setForm] = useState(() => ({ ...BLANK, invoice_id: genId() }))
  const [ocr, setOcr] = useState(SAMPLE_OCR)
  const [busy, setBusy] = useState(false)
  const [err, setErr] = useState('')

  const set = (k) => (e) => setForm({ ...form, [k]: e.target.value })

  async function go(fn, freshId = false) {
    setBusy(true); setErr('')
    try {
      await fn()
      // After a successful form submit, roll to a new unique id for the next one.
      if (freshId) setForm((f) => ({ ...f, invoice_id: genId() }))
    } catch (e) {
      setErr(String(e.message || e))
    } finally {
      setBusy(false)
    }
  }

  const submitForm = () =>
    go(() =>
      onSubmit({
        ...form,
        amount: parseFloat(form.amount),
        line_items: String(form.line_items).split(',').map((s) => s.trim()).filter(Boolean),
      }),
      true,
    )

  return (
    <div className="panel">
      <h2>Submit an invoice</h2>
      <div className="tabbar">
        <button className={tab === 'form' ? 'active' : ''} onClick={() => setTab('form')}>Form</button>
        <button className={tab === 'ocr' ? 'active' : ''} onClick={() => setTab('ocr')}>OCR text</button>
      </div>

      {tab === 'form' ? (
        <div className="grid2">
          <div><label>Invoice ID</label><input value={form.invoice_id} onChange={set('invoice_id')} /></div>
          <div><label>Vendor</label><input value={form.vendor_name} onChange={set('vendor_name')} /></div>
          <div><label>Vendor account</label><input value={form.vendor_account} onChange={set('vendor_account')} /></div>
          <div><label>Amount (INR)</label><input type="number" value={form.amount} onChange={set('amount')} /></div>
          <div><label>Issue date</label><input value={form.issue_date} onChange={set('issue_date')} /></div>
          <div><label>Due date</label><input value={form.due_date} onChange={set('due_date')} /></div>
          <div style={{ gridColumn: '1 / -1' }}><label>Line items (comma separated)</label><input value={form.line_items} onChange={set('line_items')} /></div>
          <div style={{ gridColumn: '1 / -1' }}><label>Memo</label><input value={form.memo} onChange={set('memo')} /></div>
        </div>
      ) : (
        <div>
          <label>Paste OCR output (as a Tesseract/vision model would produce)</label>
          <textarea value={ocr} onChange={(e) => setOcr(e.target.value)} className="mono" />
        </div>
      )}

      <div className="row" style={{ marginTop: 12 }}>
        {tab === 'form' ? (
          <button disabled={busy} onClick={submitForm}>Run through pipeline</button>
        ) : (
          <button disabled={busy} onClick={() => go(() => onOcr(ocr))}>Extract & run</button>
        )}
        {err && <span className="err">{err}</span>}
      </div>
    </div>
  )
}
