import streamlit as st
import time

# App title
st.title("Supreme Court Debate Simulator")

# Initialize session state
if "justices" not in st.session_state:
    st.session_state.justices = [
        "Chief Justice John Roberts",
        "Justice Clarence Thomas",
        "Justice Samuel Alito",
        "Justice Sonia Sotomayor",
        "Justice Elena Kagan",
        "Justice Neil Gorsuch",
        "Justice Brett Kavanaugh",
        "Justice Amy Coney Barrett",
        "Justice Ketanji Brown Jackson",
    ]
if "selected_justices" not in st.session_state:
    st.session_state.selected_justices = []
if "debate_topic" not in st.session_state:
    st.session_state.debate_topic = ""
if "transcript" not in st.session_state:
    st.session_state.transcript = []
if "debate_running" not in st.session_state:
    st.session_state.debate_running = False
if "debate_finished" not in st.session_state:
    st.session_state.debate_finished = False

# 1) Select justices
st.subheader("Select participants")
st.session_state.selected_justices = st.multiselect(
    "Choose justices (2-9)",
    options=st.session_state.justices,
    default=st.session_state.selected_justices,
)
if len(st.session_state.selected_justices) < 2:
    st.warning("Select at least 2 justices to start a debate.")

# 2) Enter debate topic
st.subheader("Debate topic")
st.session_state.debate_topic = st.text_input(
    "Enter the debate topic",
    value=st.session_state.debate_topic,
    placeholder="e.g., Constitutional interpretation of a specific clause",
)

# Controls
col1, col2 = st.columns(2)
with col1:
    start_clicked = st.button(
        "Start debate",
        disabled=(len(st.session_state.selected_justices) < 2 or not st.session_state.debate_topic or st.session_state.debate_running),
    )
with col2:
    reset_clicked = st.button("Reset")

if reset_clicked:
    st.session_state.transcript = []
    st.session_state.debate_running = False
    st.session_state.debate_finished = False

# Start debate logic
if start_clicked:
    st.session_state.transcript = [f"Topic: {st.session_state.debate_topic}"]
    st.session_state.debate_running = True
    st.session_state.debate_finished = False

# 3) Streaming transcript window
st.subheader("Live transcript")
transcript_container = st.container()

# Streaming generator
def debate_stream(speakers: list[str] = None):
    # Fallbacks
    speakers = speakers or st.session_state.selected_justices or st.session_state.justices
    # Simple scripted lines
    base_lines = [
        "Opening statement.",
        "Counterpoint with supporting reasoning.",
        "Clarification and legal precedent reference.",
        "Rebuttal focusing on constitutional text and history.",
        "Closing remarks summarizing position.",
    ]
    # Cycle through speakers
    idx = 0
    for line in base_lines:
        speaker = speakers[idx % len(speakers)]
        idx += 1
        yield f"<b>{speaker}:</b> {line}"
    # Indicate end
    yield "__END__"

# Drive streaming
if st.session_state.debate_running and not st.session_state.debate_finished:
    placeholder = st.empty()
    for chunk in debate_stream(st.session_state.selected_justices):
        if chunk == "__END__":
            st.session_state.debate_running = False
            st.session_state.debate_finished = True
            break
        st.session_state.transcript.append(chunk)
        with transcript_container:
            st.markdown(
                """
                <div style="height:280px; overflow-y:auto; border:1px solid #ddd; border-radius:8px; padding:10px;">
                """
                + "<br/>".join(st.session_state.transcript)
                + """
                </div>
                """,
                unsafe_allow_html=True,
            )
        time.sleep(0.2)

# Always render current transcript
with transcript_container:
    st.markdown(
        """
        <div style="height:280px; overflow-y:auto; border:1px solid #ddd; border-radius:8px; padding:10px;">
        """
        + "<br/>".join(st.session_state.transcript)
        + """
        </div>
        """,
        unsafe_allow_html=True,
    )

# 4) Final summary and conclusion window (appears after debate ends)
st.subheader("Summary & Conclusion")
summary_box = st.container()

def generate_summary(topic: str, speakers: list[str], transcript: list[str]) -> str:
    # Very simple heuristic summary (placeholder for real model)
    opening = next((t for t in transcript if "Opening statement" in t), "" )
    closing = next((t for t in transcript if "Closing remarks" in t), "" )
    participants = ", ".join(speakers) if speakers else ", ".join(st.session_state.justices)
    return (
        f"<b>Topic:</b> {topic}<br/>"
        f"<b>Participants:</b> {participants}<br/>"
        f"<b>Highlights:</b> {opening} ... {closing}<br/>"
        f"<b>Conclusion:</b> The debate presented differing interpretations, emphasizing textual analysis, precedent, and judicial philosophy."
    )

if st.session_state.debate_finished:
    with summary_box:
        st.markdown(
            """
            <div style="border:1px solid #ddd; border-radius:8px; padding:10px; background:#f8f9fa;">
            """
            + generate_summary(
                st.session_state.debate_topic,
                st.session_state.selected_justices,
                st.session_state.transcript,
            )
            + """
            </div>
            """,
            unsafe_allow_html=True,
        )
else:
    st.caption("Summary will appear after the debate finishes.")
