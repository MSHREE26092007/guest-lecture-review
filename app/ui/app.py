"""Streamlit prototype - minimal: upload -> review -> scorecard."""
import os, time, requests, streamlit as st
st.set_page_config(page_title="Guest Lecture Review Agent", layout="wide")
BASE_URL = os.getenv("API_BASE_URL", "https://guest-lecture-review.vercel.app")
API_BASE = BASE_URL

def api(url, method="GET", files=None):
    try:
        if method == "GET":
            r = requests.get(url, timeout=30)
        else:
            r = requests.post(url, files=files, timeout=60) if files else requests.post(url, timeout=60)
        r.raise_for_status()
        return r.json() if r.text else {}
    except Exception as exc:
        st.error(f"API error: {exc}")
        return {}

if "submission_id" not in st.session_state:
    st.session_state.submission_id = None
if "pipeline_done" not in st.session_state:
    st.session_state.pipeline_done = False

st.title("📄 Guest Lecture Document Review Agent")
st.caption("Upload a .docx or .PDF and get validated scorecard with format, structure, completeness, and grammar feedback.")

col1, col2 = st.columns([1, 1.2])

with col1:
    st.subheader("📤 Upload Report")
    uploaded_file = st.file_uploader("Choose a DOCX or PDF file", type=["docx", "pdf"])
    if st.button("Run Review", disabled=st.session_state.pipeline_done) and uploaded_file:
        with st.spinner("Uploading..."):
            res = api(f"{API_BASE}/upload", method="POST", files={"file": (uploaded_file.name, uploaded_file.getvalue(), uploaded_file.type)})
        if res.get("submission_id"):
            st.session_state.submission_id = res["submission_id"]
            st.session_state.pipeline_done = False
            # trigger review immediately (sync, runs pipeline)
            with st.spinner("Running review pipeline..."):
                api(f"{API_BASE}/review/{res['submission_id']}", method="POST")
            st.rerun()
        else:
            st.error("Upload failed")
    if st.session_state.submission_id:
        st.info(f"Submission ID: {st.session_state.submission_id}")
    if st.session_state.pipeline_done:
        if st.button("Run Again"):
            st.session_state.submission_id = None
            st.session_state.pipeline_done = False
            st.rerun()

with col2:
    st.subheader("🔎 Results")
    if not st.session_state.submission_id:
        st.info("Upload a document to start.")
    else:
        sid = st.session_state.submission_id
        # poll status 15s max, fast
        final = None
        for _ in range(15):
            s = api(f"{API_BASE}/status/{sid}")
            if not s:
                break
            cols = st.columns(6)
            labels = [("Template", s.get("template_status")), ("Formatting", s.get("formatting_status")), ("Completeness", s.get("completeness_status")), ("Semantic", s.get("semantic_status")), ("Grammar", s.get("grammar_status")), ("Policy", s.get("policy_status"))]
            for c, (lbl, stt) in zip(cols, labels):
                c.metric(lbl, "✅" if stt == "done" else "⏳")
            if s.get("final_report"):
                final = s
                st.session_state.pipeline_done = True
                break
            if s.get("status") == "failed":
                st.error(s.get("error", "failed"))
                break
            time.sleep(1)
        if st.session_state.pipeline_done or final:
            r = api(f"{API_BASE}/report/{sid}")
            if r:
                score = float(r["overall_score"]); mx = float(r["overall_max"])
                st.metric("Overall Score", f"{score:.1f}/{mx:.1f} ({score/mx*100:.0f}%)")
                st.caption(f"Grade: **{r['grade']}**")
                st.divider()
                st.markdown("**Per-criterion breakdown:**")
                for c in r["criteria"]:
                    sc = float(c["score"]) if isinstance(c["score"], str) else c["score"]
                    st.write(f"- **{c['label']}**: {sc:.1f}/{c['max_score']:.1f} ({c['mode']}) — {c.get('detail','')}")
                if r["missing_items"]:
                    st.warning("⚠️ Missing required fields:")
                    for m in r["missing_items"]:
                        st.write(f"- {m}")
                if r["formatting_errors"]:
                    st.error("🛠️ Formatting errors:")
                    for fe in r["formatting_errors"]:
                        st.write(f"- {fe.get('label','?')}: expected {fe.get('expected')} actual {fe.get('actual')}")
                if r["suggestions"]:
                    st.info("💡 Suggestions:")
                    for s in r["suggestions"]:
                        st.write(f"- **{s['title']}**: {s['detail']}")
