import json
import re
from pathlib import Path

import streamlit as st

DATA_DIR = Path(__file__).parent / "user_data"
DATA_DIR.mkdir(exist_ok=True)

JOHARI_WORDS = [
    "able", "accepting", "adaptable", "bold", "brave", "calm", "caring", "cheerful",
    "clever", "complex", "confident", "dependable", "dignified", "empathetic", "energetic", "extroverted",
    "friendly", "giving", "happy", "helpful", "idealistic", "independent", "ingenious", "intelligent",
    "introverted", "kind", "knowledgeable", "logical", "loving", "mature", "modest", "nervous",
    "observant", "organized", "patient", "powerful", "proud", "quiet", "reflective", "relaxed",
    "religious", "responsive", "searching", "self-assertive", "self-conscious", "sensible", "sentimental", "shy",
    "silly", "spontaneous", "sympathetic", "tense", "trustworthy", "warm", "wise", "witty",
]


def default_data():
    return {
        "name": "",
        "swot": {"strengths": [], "weaknesses": [], "opportunities": [], "threats": []},
        "johari": {"selected": [], "classification": {}, "blind": [], "unknown": []},
    }


def slugify(name):
    """Turn a display name into a safe filename, e.g. 'Harsh G.' -> 'harsh-g'."""
    slug = re.sub(r"[^a-z0-9]+", "-", name.strip().lower()).strip("-")
    return slug or "guest"


def data_path(slug):
    return DATA_DIR / f"{slug}.json"


def load_data(slug):
    path = data_path(slug)
    if path.exists():
        return json.loads(path.read_text())
    return default_data()


def save_data(slug, data):
    data_path(slug).write_text(json.dumps(data, indent=2))


st.set_page_config(page_title="My SWOT & Johari Window", layout="wide")

# Everyone sharing this deployed link would otherwise read/write the same
# file. Gating on a name (stored per-slug) keeps each visitor's board
# separate without needing real accounts — good enough for a small trusted
# group, not real authentication (anyone who types the same name sees it).
if "user_slug" not in st.session_state:
    st.title("Know Yourself")
    st.caption("A personal SWOT Analysis & Johari Window, built with Streamlit.")
    st.write("Enter your name to start (or re-enter it later to come back to your own board).")
    entered_name = st.text_input("Your name")
    if st.button("Start") and entered_name.strip():
        slug = slugify(entered_name)
        st.session_state.user_slug = slug
        st.session_state.data = load_data(slug)
        st.session_state.data["name"] = entered_name.strip()
        save_data(slug, st.session_state.data)
        st.rerun()
    st.stop()

user_slug = st.session_state.user_slug
data = st.session_state.data


def render_note_list(items, key_prefix, placeholder):
    """Shared add/remove list widget, reused for SWOT quadrants and Johari notes."""
    for idx, item in enumerate(items):
        col_text, col_remove = st.columns([6, 1])
        col_text.write(f"- {item}")
        if col_remove.button("✕", key=f"del_{key_prefix}_{idx}"):
            items.pop(idx)
            save_data(user_slug, data)
            st.rerun()

    # clear_on_submit=True empties the text box after Add is pressed.
    with st.form(key=f"form_{key_prefix}", clear_on_submit=True):
        new_item = st.text_input(
            "add item", key=f"input_{key_prefix}",
            placeholder=placeholder, label_visibility="collapsed",
        )
        if st.form_submit_button("Add") and new_item.strip():
            items.append(new_item.strip())
            save_data(user_slug, data)
            st.rerun()


def render_swot_quadrant(col, key, emoji, title, hint, singular):
    with col, st.container(border=True):
        st.subheader(f"{emoji} {title}")
        st.caption(hint)
        article = "an" if singular[0] in "aeiou" else "a"
        render_note_list(data["swot"][key], f"swot_{key}", f"Add {article} {singular}…")


st.title(f"Know Yourself — {data['name']}" if data["name"] else "Know Yourself")
st.caption("A personal SWOT Analysis & Johari Window, built with Streamlit.")

tab_swot, tab_johari = st.tabs(["SWOT Analysis", "Johari Window"])

with tab_swot:
    st.write(
        "Think honestly about yourself — your skills, habits, circumstances, "
        "and goals. Add as many points as you like to each quadrant."
    )
    row1 = st.columns(2)
    row2 = st.columns(2)
    render_swot_quadrant(row1[0], "strengths", "💪", "Strengths", "What do you do well? What unique skills or advantages do you have?", "strength")
    render_swot_quadrant(row1[1], "weaknesses", "⚠️", "Weaknesses", "Where do you struggle? What holds you back?", "weakness")
    render_swot_quadrant(row2[0], "opportunities", "🚀", "Opportunities", "What's changing around you that you could use?", "opportunity")
    render_swot_quadrant(row2[1], "threats", "🔥", "Threats", "What could hurt you? Risks or things outside your control.", "threat")

with tab_johari:
    st.write(
        "The Johari Window maps self-awareness across four areas. Since this "
        "is a solo exercise, you'll work through it step by step."
    )

    st.subheader("1. Pick words that describe you")
    selected = st.multiselect(
        "Choose as many as genuinely fit — be honest, not aspirational.",
        options=JOHARI_WORDS, default=data["johari"]["selected"],
    )
    if selected != data["johari"]["selected"]:
        data["johari"]["selected"] = selected
        for word in selected:
            data["johari"]["classification"].setdefault(word, "hidden")
        for word in list(data["johari"]["classification"]):
            if word not in selected:
                del data["johari"]["classification"][word]
        save_data(user_slug, data)

    st.subheader("2. Sort your selected traits")
    open_words = st.multiselect(
        "Which of these do people around you already see? (the rest count as Hidden)",
        options=selected,
        default=[w for w in selected if data["johari"]["classification"].get(w) == "open"],
    )
    hidden_words = [w for w in selected if w not in open_words]
    current = {w: ("open" if w in open_words else "hidden") for w in selected}
    if current != {w: data["johari"]["classification"].get(w) for w in selected}:
        data["johari"]["classification"].update(current)
        save_data(user_slug, data)

    st.subheader("3. Blind spot")
    st.caption("Feedback you've received (or suspect) about yourself that surprised you.")
    render_note_list(data["johari"]["blind"], "blind", "e.g. 'I've been told I interrupt when excited'…")

    st.subheader("4. Unknown — room to grow")
    unclaimed = [w for w in JOHARI_WORDS if w not in selected]
    st.caption("Traits you haven't claimed yet: " + (", ".join(unclaimed) if unclaimed else "none — you've claimed them all!"))
    render_note_list(data["johari"]["unknown"], "unknown", "Add a note about unexplored potential…")

    st.subheader("Your Johari Window")
    grid_row1 = st.columns(2)
    grid_row2 = st.columns(2)
    with grid_row1[0], st.container(border=True):
        st.markdown("**Open Area**")
        st.write(", ".join(open_words) or "Nothing yet.")
    with grid_row1[1], st.container(border=True):
        st.markdown("**Blind Spot**")
        st.write(", ".join(data["johari"]["blind"]) or "Nothing yet.")
    with grid_row2[0], st.container(border=True):
        st.markdown("**Hidden Area**")
        st.write(", ".join(hidden_words) or "Nothing yet.")
    with grid_row2[1], st.container(border=True):
        st.markdown("**Unknown**")
        st.write(", ".join(data["johari"]["unknown"]) or "Nothing yet.")

with st.sidebar:
    st.caption(f"Signed in as **{data['name']}**. Data auto-saves under this name only.")
    if st.button("Switch name / start over"):
        del st.session_state["user_slug"]
        del st.session_state["data"]
        st.rerun()
    confirm = st.checkbox("I want to clear all my data")
    if confirm and st.button("Reset everything"):
        st.session_state.data = default_data()
        st.session_state.data["name"] = data["name"]
        save_data(user_slug, st.session_state.data)
        st.rerun()
