// Component render smoke tests for the Custodian web app.
import { render, screen } from '@testing-library/react'
import Overview from './Overview.jsx'
import Pipeline from './Pipeline.jsx'
import StatsBar from './StatsBar.jsx'
import Attention from './Attention.jsx'
import InvoiceTable from './InvoiceTable.jsx'
import Charts from './Charts.jsx'

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
  it('shows totals from stats/health', () => {
    render(<StatsBar stats={{ total_invoices: 3, by_status: { paid: 2, rejected: 1 }, total_paid: 2468 }} health={{ scoring_mode: 'heuristic', model: 'gpt-4o-mini', ledger_balance: 1000000 }} />)
    expect(screen.getByText('Invoices processed')).toBeDefined()
    expect(screen.getByText('3')).toBeDefined()
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
  it('renders a row per invoice with its status', () => {
    render(<InvoiceTable records={[paidRec, rejectedRec]} onApprove={() => {}} onReject={() => {}} />)
    expect(screen.getByText('Processed invoices (2/2)')).toBeDefined()
    expect(screen.getByText('T-1')).toBeDefined()
    expect(screen.getByText('T-2')).toBeDefined()
    // "rejected" appears both as a badge and a filter option — expect >= 1.
    expect(screen.getAllByText('rejected').length).toBeGreaterThan(0)
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
