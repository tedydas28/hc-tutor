import streamlit as st
import requests

# ── Page config ──────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="HC Teaching Assistant",
    page_icon="🎓",
    layout="centered"
)

# ── Backend URL ───────────────────────────────────────────────────────────────
# Change this to your Render URL when deployed
BACKEND_URL = "http://127.0.0.1:8000"

# ── Styling ───────────────────────────────────────────────────────────────────
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600&family=Outfit:wght@500;700&display=swap');

    html, body, [class*="css"] {
        font-family: 'Inter', sans-serif;
    }

    /* Hide Streamlit default chrome */
    #MainMenu, footer, header { visibility: hidden; }

    /* Page background */
    .stApp {
        background-color: #f8fafc;
        background-image:
            radial-gradient(at 40% 20%, hsla(250,100%,74%,0.12) 0px, transparent 50%),
            radial-gradient(at 80% 0%, hsla(189,100%,56%,0.12) 0px, transparent 50%),
            radial-gradient(at 0% 50%, hsla(340,100%,76%,0.12) 0px, transparent 50%);
    }

    /* Header */
    .hc-header {
        text-align: center;
        padding: 1.5rem 0 1rem 0;
        font-family: 'Outfit', sans-serif;
        font-size: 1.8rem;
        font-weight: 700;
        color: #0f172a;
    }

    .hc-header span {
        background: linear-gradient(135deg, #6366f1, #8b5cf6);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
    }

    .hc-subheader {
        text-align: center;
        color: #64748b;
        font-size: 0.95rem;
        margin-bottom: 2rem;
    }

    /* Chat bubbles */
    .bubble-user {
        background: linear-gradient(135deg, #6366f1, #8b5cf6);
        color: white;
        padding: 1rem 1.25rem;
        border-radius: 18px;
        border-bottom-right-radius: 4px;
        margin: 0.5rem 0 0.5rem 20%;
        line-height: 1.6;
        font-size: 0.95rem;
        box-shadow: 0 4px 15px rgba(99,102,241,0.2);
    }

    .bubble-bot {
        background: white;
        color: #0f172a;
        padding: 1rem 1.25rem;
        border-radius: 18px;
        border-bottom-left-radius: 4px;
        margin: 0.5rem 20% 0.5rem 0;
        line-height: 1.6;
        font-size: 0.95rem;
        border: 1px solid rgba(226,232,240,0.8);
        box-shadow: 0 4px 15px rgba(0,0,0,0.03);
    }

    .sender-label {
        font-size: 0.72rem;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.5px;
        color: #94a3b8;
        margin-bottom: 4px;
        padding: 0 4px;
    }

    .sender-label.user-label { text-align: right; }

    .hc-tag-badge {
        display: inline-block;
        background: rgba(255,255,255,0.25);
        border-radius: 20px;
        padding: 2px 10px;
        font-size: 0.8rem;
        font-weight: 600;
        margin-bottom: 6px;
    }

    /* Input styling */
    .stTextInput input {
        border-radius: 16px !important;
        border: 2px solid transparent !important;
        background: rgba(241,245,249,0.8) !important;
        color: black !important;
        font-family: 'Inter', sans-serif !important;
        padding: 0.8rem 1rem !important;
        transition: all 0.3s ease !important;
    }

    .stTextInput input:focus {
        border-color: #6366f1 !important;
        background: white !important;
        color: black !important;
        box-shadow: 0 0 0 4px rgba(99,102,241,0.15) !important;
    }

    .stTextArea textarea {
        border-radius: 16px !important;
        border: 2px solid transparent !important;
        background: rgba(241,245,249,0.8) !important;
        color: black !important;
        font-family: 'Inter', sans-serif !important;
        transition: all 0.3s ease !important;
        min-height: 120px !important;
    }

    .stTextArea textarea:focus {
        border-color: #6366f1 !important;
        background: white !important;
        color: black !important;
        box-shadow: 0 0 0 4px rgba(99,102,241,0.15) !important;
    }

    /* Button */
    .stButton button {
        background: linear-gradient(135deg, #6366f1, #8b5cf6) !important;
        color: white !important;
        border: none !important;
        border-radius: 16px !important;
        font-family: 'Inter', sans-serif !important;
        font-weight: 600 !important;
        font-size: 1rem !important;
        padding: 0.6rem 2rem !important;
        width: 100% !important;
        box-shadow: 0 4px 15px rgba(99,102,241,0.3) !important;
        transition: all 0.2s ease !important;
    }

    .stButton button:hover {
        box-shadow: 0 8px 25px rgba(99,102,241,0.4) !important;
        transform: translateY(-2px) !important;
    }

    /* Divider */
    hr {
        border: none;
        border-top: 1px solid #e2e8f0;
        margin: 1rem 0;
    }
</style>
""", unsafe_allow_html=True)

# ── Header ────────────────────────────────────────────────────────────────────
st.markdown("""
<div class="hc-header">
    🎓 <span>HC Teaching Assistant</span>
</div>
<div class="hc-subheader">
    Minerva University · HC Footnote Feedback
</div>
""", unsafe_allow_html=True)

# ── Session state ─────────────────────────────────────────────────────────────
if "messages" not in st.session_state:
    st.session_state.messages = [
        {
            "role": "bot",
            "text": (
                "👋 **Welcome to the HC Footnote Feedback Bot!**\n\n"
                "I'm here to help you strengthen your HC application and ensure "
                "it aligns with Minerva's requirements.\n\n"
                "**Here's how to use me:**\n"
                "1. Enter the HC tag (e.g., *#organization*)\n"
                "2. Paste your footnote text and assignment context\n"
                "3. Hit **Analyze** — feedback comes back in a few seconds.\n\n"
                "Let's get started! ✨"
            ),
            "hc_tag": None
        }
    ]

# ── Chat history ──────────────────────────────────────────────────────────────
chat_area = st.container()

with chat_area:
    for msg in st.session_state.messages:
        if msg["role"] == "user":
            st.markdown('<div class="sender-label user-label">You</div>', unsafe_allow_html=True)
            tag_html = f'<div class="hc-tag-badge">#{msg["hc_tag"]}</div><br>' if msg.get("hc_tag") else ""
            st.markdown(
                f'<div class="bubble-user">{tag_html}{msg["text"]}</div>',
                unsafe_allow_html=True
            )
        else:
            st.markdown('<div class="sender-label">HC Tutor</div>', unsafe_allow_html=True)
            st.markdown(
                f'<div class="bubble-bot">{msg["text"]}</div>',
                unsafe_allow_html=True
            )

st.markdown("<hr>", unsafe_allow_html=True)

# ── Input form ────────────────────────────────────────────────────────────────
hc_tag = st.text_input(
    "HC Tag",
    placeholder="Which HC are you footnoting? (e.g., organization)",
    label_visibility="collapsed"
)

footnote = st.text_area(
    "Footnote",
    placeholder="Paste your assignment text and footnote here...",
    label_visibility="collapsed"
)

analyze_clicked = st.button("✈️  Analyze", use_container_width=True)

# ── On submit ─────────────────────────────────────────────────────────────────
if analyze_clicked:
    if not hc_tag.strip():
        st.warning("Please enter an HC tag before submitting.")
    elif not footnote.strip():
        st.warning("Please paste your footnote text before submitting.")
    else:
        # Add user message
        st.session_state.messages.append({
            "role": "user",
            "text": footnote.strip(),
            "hc_tag": hc_tag.strip()
        })

        # Call backend
        with st.spinner("Processing feedback..."):
            try:
                response = requests.post(
                    f"{BACKEND_URL}/grade",
                    json={
                        "student_work": footnote.strip(),
                        "hc_filename": hc_tag.strip()
                    },
                    timeout=60
                )
                data = response.json()
                feedback = data.get("feedback", f"Something went wrong — raw response: {data}")

            except requests.exceptions.ConnectionError:
                feedback = "Could not connect to the backend. Make sure the server is running."
            except Exception as e:
                feedback = f"Error: {str(e)}"

        # Add bot response
        st.session_state.messages.append({
            "role": "bot",
            "text": feedback,
            "hc_tag": None
        })

        st.rerun()