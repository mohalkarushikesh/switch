// Transient toast notifications (bottom-right). Driven by a list of
// { id, msg, type } items; App auto-dismisses them.
export default function Toasts({ items, onDismiss }) {
  return (
    <div className="toasts">
      {items.map((t) => (
        <div key={t.id} className={`toast ${t.type}`} onClick={() => onDismiss(t.id)}>
          {t.msg}
        </div>
      ))}
    </div>
  )
}
