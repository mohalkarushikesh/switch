import { useEffect, useRef } from "react";
import MessageBubble from "./MessageBubble.jsx";

export default function ChatWindow({ messages, pending, error }) {
  const endRef = useRef(null);

  useEffect(() => {
    endRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, pending]);

  return (
    <div className="chat">
      {messages.length === 0 && !pending && (
        <div className="chat__empty">
          Start a conversation with your fine-tuned model.
        </div>
      )}

      {messages.map((m, i) => (
        <MessageBubble key={i} role={m.role} content={m.content} />
      ))}

      {pending && (
        <MessageBubble role="assistant" content="Thinking…" />
      )}

      {error && <div className="chat__error">⚠ {error}</div>}

      <div ref={endRef} />
    </div>
  );
}
