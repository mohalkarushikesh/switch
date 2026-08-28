// Tests for the nav shell and the three views built on the previously unrendered
// /ledger, /policies and /audit endpoints, plus the review queue's bulk actions.
import { render, screen, fireEvent } from '@testing-library/react'
import Nav from './Nav.jsx'
import LedgerView from './LedgerView.jsx'
import Governance from './Governance.jsx'
import Audit from './Audit.jsx'
import ReviewQueue from './ReviewQueue.jsx'

const VIEWS = [
  { id: 'dashboard', label: 'Dashboard', icon: '#' },
  { id: 'queue', label: 'Review queue', icon: '#' },
  { id: 'ledger', label: 'Ledger', icon: '#' },
]

const queuedRec = (id, amount, risk) => ({
  invoice: { invoice_id: id, vendor_name: 'Acme', vendor_account: 'A-123456', amount, currency: 'INR' },
  status: 'needs_review',
  assessment: { risk_score: risk, fraud_flags: [], rationale: 'mid risk', source: 'heuristic' },
  decision: { status: 'needs_review', reason: 'human review', requires_human: true },
  payment: null,
  redacted_pii: [], policy_violations: [], audit_trail: [],
})

describe('Nav', () => {
  it('marks the active section and shows a queue badge', () => {
    render(<Nav views={VIEWS} active="ledger" onNavigate={() => {}} badges={{ queue: 3 }} />)
    expect(screen.getByText('3')).toBeDefined()
    // aria-current, not just styling, identifies the open section.
    expect(screen.getByRole('button', { current: 'page' }).textContent).toContain('Ledger')
  })

  it('navigates on click', () => {
    const seen = []
    render(<Nav views={VIEWS} active="dashboard" onNavigate={(id) => seen.push(id)} />)
    fireEvent.click(screen.getByText('Review queue'))
    expect(seen).toEqual(['queue'])
  })

  it('omits the badge when the count is zero', () => {
    render(<Nav views={VIEWS} active="dashboard" onNavigate={() => {}} badges={{ queue: 0 }} />)
    expect(screen.queryByText('0')).toBeNull()
  })
})

describe('LedgerView', () => {
  const ledger = {
    balance: 900000,
    transactions: [
      { transaction_id: 'TXN-1', invoice_id: 'T-1', vendor_account: 'A-1', amount: 60000, currency: 'INR' },
      { transaction_id: 'TXN-2', invoice_id: 'T-2', vendor_account: 'A-2', amount: 40000, currency: 'INR' },
    ],
  }

  it('derives the opening balance from balance + disbursed', () => {
    render(<LedgerView ledger={ledger} />)
    expect(screen.getByText('Transactions (2/2)')).toBeDefined()
    // 900,000 remaining + 100,000 paid out = 1,000,000 opening.
    expect(screen.getByText(/10,00,000/)).toBeDefined()
    expect(screen.getByText('TXN-1')).toBeDefined()
  })

  it('filters transactions by invoice id', () => {
    render(<LedgerView ledger={ledger} />)
    fireEvent.change(screen.getByPlaceholderText(/Search invoice/), { target: { value: 'T-2' } })
    expect(screen.getByText('Transactions (1/2)')).toBeDefined()
    expect(screen.queryByText('TXN-1')).toBeNull()
    expect(screen.getByText('TXN-2')).toBeDefined()
  })

  it('shows an empty state with no payments', () => {
    render(<LedgerView ledger={{ balance: 1000000, transactions: [] }} />)
    expect(screen.getByText(/No payments released yet/)).toBeDefined()
  })

  it('shows a loading state before the fetch resolves', () => {
    render(<LedgerView ledger={null} />)
    expect(screen.getByText(/Loading ledger/)).toBeDefined()
  })
})

describe('Governance', () => {
  const policies = {
    absolute_ceiling: 250000,
    blocked_vendors: ['shadyvendor ltd'],
    auto_pay_max_risk: 30,
    auto_pay_max_amount: 5000,
    reject_min_risk: 75,
  }

  it('renders the three routing bands derived from the thresholds', () => {
    render(<Governance policies={policies} health={{ scoring_mode: 'heuristic' }} />)
    expect(screen.getByText('Auto-pay')).toBeDefined()
    expect(screen.getByText('Human review')).toBeDefined()
    expect(screen.getByText('Auto-reject')).toBeDefined()
    // Bands are contiguous and derived: 0-30, 31-74, 75-100.
    expect(screen.getByText('0–30')).toBeDefined()
    expect(screen.getByText('31–74')).toBeDefined()
    expect(screen.getByText('75–100')).toBeDefined()
  })

  it('lists blocked vendors and the six governance layers', () => {
    render(<Governance policies={policies} health={{ scoring_mode: 'heuristic' }} />)
    expect(screen.getByText('Blocked vendors (1)')).toBeDefined()
    expect(screen.getByText('shadyvendor ltd')).toBeDefined()
    for (const layer of ['Identity', 'Data', 'Model', 'Policy', 'Agent Runtime', 'Operations']) {
      expect(screen.getByText(layer)).toBeDefined()
    }
  })

  it('shows the provider pill when an LLM is live', () => {
    render(<Governance policies={policies} health={{ scoring_mode: 'llm', provider: 'huggingface' }} />)
    expect(screen.getByText('huggingface')).toBeDefined()
  })
})

describe('Audit', () => {
  const entry = (id, auditId, status, recordedAt) => ({
    audit_id: auditId,
    recorded_at: recordedAt,
    invoice: { invoice_id: id, vendor_name: 'Acme', amount: 1200, currency: 'INR' },
    status,
    assessment: { risk_score: 12, fraud_flags: [], rationale: 'ok', source: 'heuristic' },
    decision: { status: 'approved', reason: 'auto-paid', requires_human: false },
    audit_trail: ['Ingested', 'Risk scored 12'],
  })
  const audit = {
    path: 'sqlite:data/custodian.db#audit_events',
    total: 2,
    entries: [entry('T-1', 1, 'paid', '2026-08-28 10:00:00'), entry('T-2', 2, 'rejected', '2026-08-28 11:00:00')],
  }

  it('lists events newest first and shows the source', () => {
    render(<Audit audit={audit} />)
    expect(screen.getByText('Audit log (2 of 2)')).toBeDefined()
    expect(screen.getByText(/audit_events/)).toBeDefined()
    // API returns oldest-first; the view reverses so T-2 (11:00) is on top.
    const ids = screen.getAllByRole('row').slice(1)
      .map((r) => r.cells[1].querySelector('b').textContent)
    expect(ids).toEqual(['T-2', 'T-1'])
  })

  it('renders the timestamp verbatim rather than shifting it to local time', () => {
    render(<Audit audit={audit} />)
    expect(screen.getByText('2026-08-28 11:00:00')).toBeDefined()
  })

  it('expands an entry to show the trail recorded at that moment', () => {
    render(<Audit audit={audit} />)
    expect(screen.queryByText('Risk scored 12')).toBeNull()
    fireEvent.click(screen.getByText('T-2'))
    expect(screen.getByText('Risk scored 12')).toBeDefined()
  })

  it('filters by status', () => {
    render(<Audit audit={audit} />)
    fireEvent.change(screen.getByPlaceholderText(/Search invoice/), { target: { value: 'rejected' } })
    expect(screen.getByText('Audit log (1 of 2)')).toBeDefined()
  })

  it('shows an empty state with no events', () => {
    render(<Audit audit={{ path: 'x', total: 0, entries: [] }} />)
    expect(screen.getByText(/No audit events yet/)).toBeDefined()
  })
})

describe('ReviewQueue', () => {
  const records = [
    queuedRec('Q-1', 20000, 45),
    queuedRec('Q-2', 30000, 65),
    { ...queuedRec('P-1', 1000, 5), status: 'paid' }, // must not appear
  ]

  it('shows only needs_review invoices, highest risk first', () => {
    render(<ReviewQueue records={records} onApprove={() => {}} onReject={() => {}} />)
    expect(screen.getByText('Review queue (2)')).toBeDefined()
    expect(screen.queryByText('P-1')).toBeNull()
    const ids = screen.getAllByRole('row').slice(1).map((r) => r.cells[1].textContent)
    expect(ids[0]).toContain('Q-2') // risk 65 outranks 45
  })

  it('bulk-approves the selected invoices sequentially', async () => {
    const confirm = vi.spyOn(window, 'confirm').mockReturnValue(true)
    const approved = []
    render(<ReviewQueue records={records}
                        onApprove={(id) => { approved.push(id); return Promise.resolve() }}
                        onReject={() => {}} />)

    fireEvent.click(screen.getByLabelText('Select all queued invoices'))
    expect(screen.getByText('2 selected')).toBeDefined()
    await fireEvent.click(screen.getByText(/Approve & pay selected/))

    expect(approved.sort()).toEqual(['Q-1', 'Q-2'])
    // The confirmation names the count and the total at risk.
    expect(confirm.mock.calls[0][0]).toContain('2 invoice(s)')
    confirm.mockRestore()
  })

  it('does nothing when the confirmation is dismissed', async () => {
    const confirm = vi.spyOn(window, 'confirm').mockReturnValue(false)
    const approved = []
    render(<ReviewQueue records={records}
                        onApprove={(id) => { approved.push(id); return Promise.resolve() }}
                        onReject={() => {}} />)
    fireEvent.click(screen.getByLabelText('Select all queued invoices'))
    await fireEvent.click(screen.getByText(/Approve & pay selected/))
    expect(approved).toEqual([])
    confirm.mockRestore()
  })

  it('shows a clear-queue empty state', () => {
    render(<ReviewQueue records={[records[2]]} onApprove={() => {}} onReject={() => {}} />)
    expect(screen.getByText(/Queue is clear/)).toBeDefined()
  })
})
