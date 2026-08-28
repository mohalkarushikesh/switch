// Component render smoke tests for the Custodian web app.
import { render, screen, fireEvent } from '@testing-library/react'
import Overview from './Overview.jsx'
import Pipeline from './Pipeline.jsx'
import StatsBar from './StatsBar.jsx'
import Attention from './Attention.jsx'
import InvoiceTable from './InvoiceTable.jsx'
import Charts from './Charts.jsx'
import { toCsv } from '../lib/csv.js'

const paidRec = {
  invoice: { invoice_id: 'T-1', vendor_name: 'Acme', vendor_account: 'A-123456', amount: 1234, currency: 'INR' },
  status: 'paid',
  assessment: { risk_score: 0, fraud_flags: [], rationale: 'ok', source: 'heuristic' },
  decision: { status: 'approved', reason: 'ok', requires_human: false },
  payment: { paid: true, transaction_id: 'TXN-1', reason: 'paid' },
  redacted_pii: [], policy_violations: [], audit_trail: ['Ingested', 'Risk scored'],
}
const rejectedRec = {
  ...paidRec,
  invoice: { ...paidRec.invoice, invoice_id: 'T-2', amount: 90000 },
  status: 'rejected',
  assessment: { risk_score: 100, fraud_flags: ['very large amount'], rationale: 'bad', source: 'heuristic' },
  decision: { status: 'rejected', reason: 'too risky', requires_human: false },
  payment: { paid: false, transaction_id: null, reason: 'not approved' },
}

describe('Overview', () => {
  it('explains the system and lists the six governance layers', () => {
    render(<Overview />)
    expect(screen.getByText('What is Custodian?')).toBeDefined()
    for (const layer of ['Identity', 'Data', 'Model', 'Policy', 'Agent Runtime', 'Operations']) {
      expect(screen.getByText(layer)).toBeDefined()
    }
  })
})

describe('Pipeline', () => {
  it('renders all six stages for a record', () => {
    render(<Pipeline rec={paidRec} />)
    for (const stage of ['Ingest', 'PII', 'Risk', 'Approval', 'Policy', 'Payment']) {
      expect(screen.getByText(stage)).toBeDefined()
    }
  })
})

describe('StatsBar', () => {
  const stats = { total_invoices: 3, by_status: { paid: 2, rejected: 1 }, total_paid: 2468 }

  it('shows totals from stats/health', () => {
    render(<StatsBar stats={stats} health={{ scoring_mode: 'heuristic', model: 'gpt-4o-mini', ledger_balance: 1000000 }} />)
    expect(screen.getByText('Invoices processed')).toBeDefined()
    expect(screen.getByText('3')).toBeDefined()
  })

  it('names the provider and strips its prefix from the model when an LLM is live', () => {
    render(<StatsBar stats={stats} health={{
      scoring_mode: 'llm', provider: 'huggingface',
      model: 'huggingface/meta-llama/Llama-3.1-8B-Instruct', ledger_balance: 1000000,
    }} />)
    expect(screen.getByText('Hugging Face')).toBeDefined()
    expect(screen.getByText('meta-llama/Llama-3.1-8B-Instruct')).toBeDefined()
    expect(screen.queryByText('heuristic rules')).toBeNull()
  })

  it('falls back to the heuristic pill when no LLM is configured', () => {
    render(<StatsBar stats={stats} health={{ scoring_mode: 'heuristic', model: 'gpt-4o-mini', llm_disabled: true, ledger_balance: 1000000 }} />)
    expect(screen.getByText('heuristic rules')).toBeDefined()
  })
})

describe('Attention', () => {
  it('lists only flagged (rejected / high-risk) invoices', () => {
    render(<Attention records={[paidRec, rejectedRec]} />)
    expect(screen.getByText('Needs attention (1)')).toBeDefined()
    expect(screen.getByText('T-2')).toBeDefined()
    expect(screen.queryByText('T-1')).toBeNull()
  })
})

describe('InvoiceTable', () => {
  // Read the id from its <b>, not the whole cell — the cell also holds the
  // disclosure button's caret glyph.
  const ids = () => screen.getAllByRole('row').slice(1).map((r) => r.cells[0].querySelector('b').textContent)

  it('renders a row per invoice with its status', () => {
    render(<InvoiceTable records={[paidRec, rejectedRec]} onApprove={() => {}} onReject={() => {}} />)
    expect(screen.getByText('Processed invoices (2/2)')).toBeDefined()
    expect(screen.getByText('T-1')).toBeDefined()
    expect(screen.getByText('T-2')).toBeDefined()
    // "rejected" appears both as a badge and a filter option — expect >= 1.
    expect(screen.getAllByText('rejected').length).toBeGreaterThan(0)
  })

  it('sorts by amount ascending then descending', () => {
    // T-1 is 1234, T-2 is 90000; incoming order is newest-first (T-1, T-2).
    render(<InvoiceTable records={[paidRec, rejectedRec]} onApprove={() => {}} onReject={() => {}} />)
    fireEvent.click(screen.getByLabelText('Sort by amount'))
    expect(ids()).toEqual(['T-1', 'T-2'])
    fireEvent.click(screen.getByLabelText('Sort by amount'))
    expect(ids()).toEqual(['T-2', 'T-1'])
  })

  it('filters by risk band', () => {
    // T-1 scores 0 (low), T-2 scores 100 (high).
    render(<InvoiceTable records={[paidRec, rejectedRec]} onApprove={() => {}} onReject={() => {}} />)
    fireEvent.change(screen.getByLabelText('Filter by risk band'), { target: { value: 'high' } })
    expect(screen.getByText('Processed invoices (1/2)')).toBeDefined()
    expect(ids()).toEqual(['T-2'])
  })

  it('exposes the detail drawer as a real, keyboard-operable button', () => {
    render(<InvoiceTable records={[paidRec]} onApprove={() => {}} onReject={() => {}} />)
    const toggle = screen.getByRole('button', { name: 'Show details for T-1' })
    expect(toggle.getAttribute('aria-expanded')).toBe('false')
    // A native <button> gets Enter/Space activation for free, so clicking it is
    // an honest proxy; what matters is that it IS a button, not a bare <tr>.
    fireEvent.click(toggle)
    expect(screen.getByText('Risk assessment')).toBeDefined()
    expect(screen.getByRole('button', { name: 'Hide details for T-1' })
                 .getAttribute('aria-expanded')).toBe('true')
  })

  it('keeps rows as table rows so table semantics survive', () => {
    render(<InvoiceTable records={[paidRec, rejectedRec]} onApprove={() => {}} onReject={() => {}} />)
    // Regression guard: role="button" on a <tr> would override role="row".
    expect(screen.getAllByRole('row').length).toBe(3) // header + 2 data rows
  })
})

describe('Charts', () => {
  it('summarizes status counts and risk bands', () => {
    render(<Charts records={[paidRec, rejectedRec]} />)
    expect(screen.getByText('Portfolio')).toBeDefined()
    expect(screen.getByText('By status')).toBeDefined()
    expect(screen.getByText('By risk band')).toBeDefined()
    // two invoices total shown in the donut center
    expect(screen.getByText('2')).toBeDefined()
  })

  it('shows an empty state with no records', () => {
    render(<Charts records={[]} />)
    expect(screen.getByText(/No data yet/)).toBeDefined()
  })
})

describe('CSV export', () => {
  it('produces a header row and one row per invoice', () => {
    const csv = toCsv([paidRec, rejectedRec])
    const lines = csv.split('\n')
    expect(lines[0]).toContain('invoice_id')
    expect(lines).toHaveLength(3) // header + 2 rows
    expect(lines[1]).toContain('T-1')
    expect(lines[2]).toContain('T-2')
  })
})
