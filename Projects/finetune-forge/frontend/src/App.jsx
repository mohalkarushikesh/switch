import { useEffect, useState } from "react";
import ChatWindow from "./components/ChatWindow.jsx";
import Composer from "./components/Composer.jsx";
import { fetchHealth, sendChat } from "./api/client.js";

export default function App() {
  const [messages, setMessages] = useState([]);
  const [pending, setPending] = useState(false);
  const [error, setError] = useState(null);
  const [health, setHealth] = useState(null);

  useEffect(() => {
    fetchHealth()
      .then(setHealth)
      .catch(() => setHealth({ status: "unreachable" }));
  }, []);

  async function handleSend(text) {
    setError(null);
    const next = [...messages, { role: "user", content: text }];
    setMessages(next);
    setPending(true);
    try {
      const { reply } = await sendChat(next);
      setMessages((cur) => [...cur, { role: "assistant", content: reply }]);
    } catch (err) {
      setError(err.message);
    } finally {
      setPending(false);
    }
  }

  function reset() {
    setMessages([]);
    setError(null);
  }

  return (
    <div className="app">
      <header className="app__header">
        <div>
          <h1 className="app__title">FineTune Forge</h1>
          <p className="app__subtitle">React · FastAPI · fine-tuned LLM</p>
        </div>
        <div className="app__status">
          {health && (
            <span
              className={`badge badge--${
                health.status === "ok" ? "ok" : "down"
              }`}
              title={health.model || ""}
            >
              {health.status === "ok"
                ? `${health.provider} · ${health.model}`
                : "backend unreachable"}
            </span>
          )}
          <button className="app__reset" onClick={reset} disabled={!messages.length}>
            Clear
          </button>
        </div>
      </header>

      <main className="app__main">
        <ChatWindow messages={messages} pending={pending} error={error} />
      </main>

      <footer className="app__footer">
        <Composer onSend={handleSend} disabled={pending} />
      </footer>
    </div>
  );
}
