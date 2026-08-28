// Stat tiles derived from /stats + /health.
import { money } from '../lib/format.js'

// Backend provider id -> display name. Unknown ids fall through as-is so a
// newly supported provider still renders something sensible.
const PROVIDERS = { openai: 'OpenAI', groq: 'Groq', huggingface: 'Hugging Face' }

// Model ids are namespaced by provider ("huggingface/meta-llama/Llama-3.1-8B-Instruct");
// the prefix is already shown as the provider pill, so drop it from the model pill.
const shortModel = (model = '') => {
  const i = model.indexOf('/')
  return i === -1 ? model : model.slice(i + 1)
}

// Why are we on the heuristic scorer? Distinguishes the deliberate kill-switch
// from a simply-absent credential, so the fix is obvious from the dashboard.
const heuristicReason = (health) =>
  health?.llm_disabled
    ? 'CUSTODIAN_DISABLE_LLM is set — LLM calls are switched off'
    : 'No API key for the configured model’s provider. Set OPENAI_API_KEY, GROQ_API_KEY, or HUGGINGFACE_API_KEY.'

export default function StatsBar({ stats, health }) {
  const by = stats?.by_status || {}
  return (
    <div className="panel">
      <h2>At a glance</h2>
      <div className="tiles">
        <div className="tile">
          <div className="k">Invoices processed</div>
          <div className="v">{stats?.total_invoices ?? '—'}</div>
        </div>
        <div className="tile">
          <div className="k">Auto-paid</div>
          <div className="v" style={{ color: 'var(--green)' }}>{by.paid ?? 0}</div>
        </div>
        <div className="tile">
          <div className="k">Needs review / rejected</div>
          <div className="v" style={{ color: 'var(--amber)' }}>
            {(by.needs_review ?? 0)} / <span style={{ color: 'var(--red)' }}>{by.rejected ?? 0}</span>
          </div>
        </div>
        <div className="tile">
          <div className="k">Ledger balance</div>
          <div className="v">{money(health?.ledger_balance)}</div>
        </div>
      </div>
      <div className="row" style={{ marginTop: 12 }}>
        <span className="pill">Scoring: <b>{health?.scoring_mode ?? '…'}</b></span>
        {/* Only show the provider/model when actually scoring via an LLM; otherwise
            the rules engine is what's running (so "gpt-4o-mini" isn't misleading). */}
        {health?.scoring_mode === 'llm' ? (
          <>
            <span className="pill">
              Provider: <b>{PROVIDERS[health.provider] ?? health.provider}</b>
            </span>
            <span className="pill">Model: <b>{shortModel(health.model)}</b></span>
          </>
        ) : (
          <span className="pill" title={heuristicReason(health)}>
            Engine: <b>heuristic rules</b>
          </span>
        )}
        <span className="pill">Total auto-paid: <b>{money(stats?.total_paid)}</b></span>
      </div>
    </div>
  )
}
