"""Streamlit UI for the Kubernetes SRE copilot.

Talks to the FastAPI service over HTTP rather than importing the pipeline, so the
UI cannot accidentally hold its own copy of the graph state - the approval gate
depends on both sides sharing one checkpointer.

    streamlit run ui/streamlit_app.py
"""

from __future__ import annotations

import os

import httpx
import streamlit as st

API_BASE = os.environ.get("RAG_API_BASE", "http://127.0.0.1:8000")
TIMEOUT = httpx.Timeout(300.0, connect=10.0)

EXAMPLES = [
    "Why is my pod stuck in CrashLoopBackOff with exit code 137?",
    "Our ingress started returning 502s right after a deploy. Where do I look?",
    "How many sev1 incidents did production clusters have since June 2026?",
    "Which services had the most failed deployments this quarter?",
    "What does the change control policy require before draining nodes?",
]

st.set_page_config(page_title="K8s SRE Copilot", page_icon="⎈", layout="wide")


def api_post(path: str, payload: dict) -> dict:
    response = httpx.post(f"{API_BASE}{path}", json=payload, timeout=TIMEOUT)
    response.raise_for_status()
    return response.json()


def api_get(path: str) -> dict:
    response = httpx.get(f"{API_BASE}{path}", timeout=TIMEOUT)
    response.raise_for_status()
    return response.json()


# ------------------------------------------------------------------- sidebar

with st.sidebar:
    st.title("⎈ SRE Copilot")
    st.caption("Enterprise Advanced RAG on LangGraph")

    try:
        health = api_get("/health")
        badge = "🟢" if health["status"] == "ok" else "🟠"
        st.markdown(f"{badge} **API** `{health['status']}`")
        st.markdown(f"**Indexed chunks** {health['indexed_chunks']}")
        st.markdown(f"**Model** `{health['model']}`")
        st.markdown(f"**Cache** {health['cache']}")
        st.markdown(f"**SQL** {health['sql_dialect']}")
        with st.expander("Pipeline layers"):
            for name, enabled in health["features"].items():
                st.markdown(f"{'✅' if enabled else '⬜'} {name}")
    except Exception as exc:
        st.error(f"API unreachable at {API_BASE}\n\n{exc}")
        st.caption("Start it with `rag-api` (or `uvicorn advanced_rag.api.main:app`).")

    st.divider()
    st.subheader("Try one")
    for example in EXAMPLES:
        if st.button(example, use_container_width=True):
            st.session_state["pending_question"] = example
            st.rerun()

    st.divider()
    if st.button("Clear answer cache", use_container_width=True):
        api_post("/cache/clear", {})
        st.success("Cache cleared")


# --------------------------------------------------------------------- state

st.session_state.setdefault("history", [])
st.session_state.setdefault("awaiting", None)

tab_chat, tab_retrieval = st.tabs(["Ask", "Retrieval lab"])


# ----------------------------------------------------------------- rendering


def render_trace(trace: list[dict]) -> None:
    if not trace:
        return
    total = sum(step["elapsed_ms"] for step in trace)
    with st.expander(f"Pipeline trace - {len(trace)} steps, {total} ms"):
        for step in trace:
            st.markdown(f"**{step['node']}** · `{step['elapsed_ms']} ms` — {step['detail']}")


ICONS = {"allow": "✅", "redact": "✂️", "block": "⛔", "skip": "⚠️"}


def render_guardrails(outcomes: list[dict]) -> None:
    if not outcomes:
        return
    blocked = [o for o in outcomes if o["action"] == "block"]
    skipped = [o for o in outcomes if o["action"] == "skip"]

    if blocked:
        label = "Guardrails - BLOCKED"
    else:
        ran = len(outcomes) - len(skipped)
        label = f"Guardrails - {ran} of {len(outcomes)} layers ran"
        if skipped:
            # Never summarise a failed-open layer as a pass: the request got less
            # scrutiny than the layer count suggests, and the reader must know.
            label += f", {len(skipped)} SKIPPED"

    with st.expander(label, expanded=bool(blocked or skipped)):
        if skipped:
            st.warning(
                f"{len(skipped)} layer(s) could not run and failed open: "
                + ", ".join(o["layer"] for o in skipped)
                + ". This answer received less checking than a full pass."
            )
        for outcome in outcomes:
            icon = ICONS.get(outcome["action"], "•")
            detail = f" — {outcome['detail']}" if outcome["detail"] else ""
            st.markdown(f"{icon} **{outcome['layer']}**{detail}")


def render_citations(citations: list[dict]) -> None:
    if not citations:
        return
    with st.expander(f"Sources ({len(citations)})"):
        for index, citation in enumerate(citations, start=1):
            where = citation["title"] or citation["source"]
            section = f" › {citation['section']}" if citation["section"] else ""
            st.markdown(
                f"**[{index}]** {where}{section}  \n"
                f"`{citation['source']}` · score {citation['score']:.3f}"
            )


def render_answer(payload: dict) -> None:
    if payload.get("blocked"):
        st.error(payload["answer"])
    else:
        st.markdown(payload["answer"])

    meta = [
        f"route `{payload['route']}`",
        f"{payload['latency_ms']} ms",
        f"{payload['input_tokens']}→{payload['output_tokens']} tokens",
    ]
    if payload.get("cached"):
        meta.append(f"**cache hit ({payload['cache_kind']})**")
    st.caption(" · ".join(meta))

    render_citations(payload.get("citations") or [])
    render_guardrails(payload.get("guardrails") or [])
    render_trace(payload.get("trace") or [])

    sql = payload.get("sql")
    if sql and sql.get("rows"):
        with st.expander(f"Query result ({sql['row_count']} rows)", expanded=True):
            st.code(sql["sql"], language="sql")
            st.dataframe(
                [dict(zip(sql["columns"], row, strict=False)) for row in sql["rows"]],
                use_container_width=True,
            )


# ------------------------------------------------------------------ ask tab

with tab_chat:
    for entry in st.session_state["history"]:
        with st.chat_message("user"):
            st.markdown(entry["question"])
        with st.chat_message("assistant"):
            render_answer(entry["payload"])

    awaiting = st.session_state["awaiting"]
    if awaiting:
        st.warning("This question needs a database query. It will not run until you approve it.")
        st.code(awaiting["sql"]["sql"] or "(no query)", language="sql")
        if awaiting["sql"].get("rationale"):
            st.caption(awaiting["sql"]["rationale"])

        approve_col, reject_col = st.columns(2)
        decision = None
        if approve_col.button("✅ Approve and run", use_container_width=True, type="primary"):
            decision = True
        if reject_col.button("⛔ Reject", use_container_width=True):
            decision = False

        if decision is not None:
            with st.spinner("Running the approved query..."):
                payload = api_post(
                    "/approve", {"thread_id": awaiting["thread_id"], "approved": decision}
                )
            st.session_state["history"].append(
                {"question": awaiting["question"], "payload": payload}
            )
            st.session_state["awaiting"] = None
            st.rerun()

    # A sidebar example button parks its text in session state for this run.
    typed = st.chat_input("Ask about the clusters, an incident, or a runbook...") or (
        st.session_state.pop("pending_question", None)
    )
    if typed and not awaiting:
        with st.spinner("Running the pipeline..."):
            payload = api_post("/ask", {"question": typed})
        if payload.get("awaiting_approval"):
            st.session_state["awaiting"] = {
                "thread_id": payload["thread_id"],
                "question": typed,
                "sql": payload.get("sql") or {"sql": "", "rationale": ""},
            }
        else:
            st.session_state["history"].append({"question": typed, "payload": payload})
        st.rerun()


# ------------------------------------------------------- retrieval lab tab

with tab_retrieval:
    st.subheader("Retrieval lab")
    st.caption(
        "Compare retrieval strategies without generation - this is the fastest way "
        "to see what hybrid search, HyDE and reranking each contribute."
    )

    query = st.text_input("Query", value="pod killed with exit code 137")
    controls = st.columns(4)
    mode = controls[0].selectbox("Mode", ["hybrid", "dense", "sparse"])
    fusion = controls[1].selectbox("Fusion", ["weighted", "rrf"], disabled=mode != "hybrid")
    use_hyde = controls[2].checkbox("HyDE", value=False)
    rerank = controls[3].checkbox("Rerank", value=True)
    top_k = st.slider("Candidates (top_k)", 5, 50, 20)

    if st.button("Retrieve", type="primary"):
        with st.spinner("Retrieving..."):
            result = api_post(
                "/retrieve",
                {
                    "query": query,
                    "mode": mode,
                    "fusion": fusion,
                    "use_hyde": use_hyde,
                    "rerank": rerank,
                    "top_k": top_k,
                },
            )
        if result.get("hyde_document"):
            with st.expander("Generated HyDE passage (embedded, never shown to users)"):
                st.write(result["hyde_document"])

        # Which score actually determined this order? Showing the rerank score
        # first when it did not drive the sort makes a correct list look broken.
        authoritative = result.get("rerank_is_authoritative", False)
        sorted_by = "rerank" if authoritative else "retrieval"
        st.markdown(f"**{len(result['results'])} results** — ordered by `{sorted_by}` score")
        if result.get("reranked") and not authoritative:
            st.info(
                "No cross-encoder is available, so the reranker is **score-only**: the "
                "`rerank` column below is a lexical-overlap signal shown for comparison, "
                "and deliberately does *not* reorder the list. Measured, letting it "
                "reorder dropped precision@5 from 0.76 to 0.64."
            )

        for index, hit in enumerate(result["results"], start=1):
            rerank_score = hit["rerank_score"]
            retrieval = f"retrieval **{hit['retrieval_score']:.3f}**"
            if rerank_score is None:
                score_text = retrieval
            elif authoritative:
                score_text = (
                    f"rerank **{rerank_score:.3f}** · "
                    f"retrieval {hit['retrieval_score']:.3f}"
                )
            else:
                score_text = f"{retrieval} · rerank {rerank_score:.3f} (not used for ordering)"
            with st.expander(f"{index}. {hit['source']} › {hit['section']} — {score_text}"):
                st.text(hit["text"])
