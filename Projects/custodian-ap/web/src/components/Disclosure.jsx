// Keyboard-accessible expand/collapse control for a table row's detail drawer.
//
// The rows in InvoiceTable and Audit were mouse-only: a bare onClick on a <tr>
// takes no focus and ignores Enter/Space. The fix is NOT to put role="button"
// on the <tr> — that overrides its implicit role="row" and breaks the table's
// semantics for a screen reader. Instead the row stays a row (and stays
// clickable for convenience), and this real <button> inside the first cell is
// the actual control: natively focusable, natively Enter/Space-activated, and
// carrying the aria-expanded state.
export default function Disclosure({ isOpen, onToggle, label, children }) {
  return (
    <button
      type="button"
      className="rowtoggle"
      aria-expanded={isOpen}
      aria-label={`${isOpen ? 'Hide' : 'Show'} ${label}`}
      // The parent <tr> also toggles on click; without this the event bubbles
      // and fires the handler twice, collapsing the row as soon as it opens.
      onClick={(event) => { event.stopPropagation(); onToggle() }}
    >
      <span className="caret" aria-hidden="true">{isOpen ? '▾' : '▸'}</span>
      {children}
    </button>
  )
}
