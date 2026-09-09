export default function MessageBubble({ role, content }) {
  return (
    <div className={`bubble bubble--${role}`}>
      <span className="bubble__role">{role}</span>
      <div className="bubble__content">{content}</div>
    </div>
  );
}
