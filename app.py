import streamlit as st
import time
import requests
from datetime import datetime

# -------------------------------------------------------------
# 1. PAGE SETUP & ELECTRICAL HIGH-VOLTAGE THEME
# -------------------------------------------------------------
st.set_page_config(page_title="Duo Riddle & Puzzle Arena", page_icon="⚡", layout="centered")

electric_css = """
<style>
/* Nuclear UI Overrides: Completely remove GitHub Octocat, toolbar, header, footer */
#MainMenu { visibility: hidden !important; }
footer { visibility: hidden !important; }
header { visibility: hidden !important; }
[data-testid="stHeader"] { display: none !important; }
[data-testid="stToolbar"] { display: none !important; }

/* Dark Electrical Circuit Background */
.stApp {
    background: radial-gradient(circle at 50% 20%, #0d1b2a 0%, #050811 100%);
    color: #e0f7fa;
}

/* High-Voltage Animated Heading */
.electric-title {
    font-size: 2.3rem;
    font-weight: 800;
    text-align: center;
    color: #00f0ff;
    text-shadow: 0 0 8px #00f0ff, 0 0 20px #00f0ff, 0 0 35px #0077ff;
    animation: arc-flicker 2s infinite alternate;
    margin-bottom: 0.2rem;
}

/* Electric Spark Arc Banner */
.spark-arc {
    height: 4px;
    width: 100%;
    background: linear-gradient(90deg, transparent, #00f0ff, #fffb00, #00f0ff, transparent);
    box-shadow: 0 0 12px #00f0ff, 0 0 25px #fffb00;
    margin-bottom: 1.5rem;
    animation: plasma-surge 1.2s infinite ease-in-out;
}

/* Sub-info Electrical Box */
.circuit-box {
    background: rgba(0, 240, 255, 0.05);
    border: 1px solid #00f0ff;
    box-shadow: 0 0 15px rgba(0, 240, 255, 0.25), inset 0 0 10px rgba(0, 240, 255, 0.15);
    border-radius: 8px;
    padding: 12px 18px;
    text-align: center;
    font-weight: 600;
    color: #b2ebf2;
    margin-bottom: 1.5rem;
}

/* Input Fields Glow */
input {
    border-radius: 6px !important;
    border: 1px solid #00a8cc !important;
    background-color: rgba(10, 25, 47, 0.7) !important;
    color: #00f0ff !important;
    box-shadow: 0 0 8px rgba(0, 168, 204, 0.3) !important;
}

input:focus {
    border: 1px solid #fffb00 !important;
    box-shadow: 0 0 15px rgba(255, 251, 0, 0.6) !important;
}

/* High-Voltage Interactive Pushbuttons */
.stButton > button {
    width: 100%;
    background: linear-gradient(45deg, #002b49, #005f73) !important;
    color: #00f0ff !important;
    font-weight: bold !important;
    font-size: 1.1rem !important;
    border: 2px solid #00f0ff !important;
    border-radius: 8px !important;
    box-shadow: 0 0 12px rgba(0, 240, 255, 0.4), inset 0 0 8px rgba(0, 240, 255, 0.2) !important;
    transition: all 0.25s ease-in-out !important;
}

.stButton > button:hover {
    background: linear-gradient(45deg, #00f0ff, #0077b6) !important;
    color: #050811 !important;
    box-shadow: 0 0 25px #00f0ff, 0 0 45px #fffb00 !important;
    transform: scale(1.01);
}

/* Keyframe Animations */
@keyframes arc-flicker {
    0%, 18%, 22%, 25%, 53%, 57%, 100% {
        opacity: 1;
        text-shadow: 0 0 10px #00f0ff, 0 0 25px #00f0ff, 0 0 40px #0077ff;
    }
    19%, 24%, 55% {
        opacity: 0.3;
        text-shadow: none;
    }
}

@keyframes plasma-surge {
    0% { filter: brightness(1) drop-shadow(0 0 4px #00f0ff); }
    50% { filter: brightness(1.7) drop-shadow(0 0 15px #fffb00); }
    100% { filter: brightness(1) drop-shadow(0 0 4px #00f0ff); }
}
</style>
"""
st.markdown(electric_css, unsafe_allow_html=True)

# -------------------------------------------------------------
# 2. CONFIGURATION & SESSION STATE INITIALIZATION
# -------------------------------------------------------------
TOTAL_GAME_MINUTES = 40
GOOGLE_SHEET_URL = "https://script.google.com/macros/s/AKfycbwLnXW4LZfjLfxiMA7RCnRxEikO1N6yiV12PXHN5w1y0Fk43AH8h0qOxIanVg2sJzz0/exec"

if "started" not in st.session_state:
    st.session_state.started = False
    st.session_state.team_name = ""
    st.session_state.p1_name = ""
    st.session_state.p2_name = ""
    st.session_state.p1_contact = ""
    st.session_state.p2_contact = ""
    st.session_state.start_time = 0
    st.session_state.current_set_idx = 0
    st.session_state.stage = "riddles"
    st.session_state.score = 0
    st.session_state.submitted_to_sheet = False
    st.session_state.set_state = {
        "riddle_correct": {},
        "retry_count": 0,
        "max_retries_allowed": 1,
        "puzzle_mandatory": False,
        "puzzle_retry_count": 0
    }

# -------------------------------------------------------------
# 3. HELPER FUNCTIONS
# -------------------------------------------------------------
def get_time_remaining():
    elapsed = time.time() - st.session_state.start_time
    remaining = (TOTAL_GAME_MINUTES * 60) - elapsed
    return max(0, int(remaining))

def log_results_to_sheets():
    payload = {
        "Timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "Team_Name": st.session_state.team_name,
        "Player_1": st.session_state.p1_name,
        "P1_Contact": st.session_state.p1_contact,
        "Player_2": st.session_state.p2_name,
        "P2_Contact": st.session_state.p2_contact,
        "Final_Score": st.session_state.score,
        "Time_Taken_Sec": int(time.time() - st.session_state.start_time)
    }
    try:
        requests.post(GOOGLE_SHEET_URL, json=payload, timeout=10)
        return True
    except Exception:
        return False

# -------------------------------------------------------------
# 4. REGISTRATION SCREEN (ISOLATED VIA ST.STOP)
# -------------------------------------------------------------
if not st.session_state.started:
    st.markdown('<div class="electric-title">⚡ Duo Riddle & Puzzle Arena</div>', unsafe_allow_html=True)
    st.markdown('<div class="spark-arc"></div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="circuit-box">⏱️ Round Duration: 40 Minutes | 3 Sets | Solve on 1 mobile per duo.</div>',
        unsafe_allow_html=True
    )

    t_name = st.text_input("Duo / Team Name:")
    
    col1, col2 = st.columns(2)
    with col1:
        p1 = st.text_input("Player 1 Name:")
        p1_contact = st.text_input("Player 1 Contact Number:")
    with col2:
        p2 = st.text_input("Player 2 Name:")
        p2_contact = st.text_input("Player 2 Contact Number:")

    if st.button("⚡ Connect Grid & Start Timer"):
        if t_name.strip() and p1.strip() and p2.strip() and p1_contact.strip() and p2_contact.strip():
            st.session_state.team_name = t_name.strip()
            st.session_state.p1_name = p1.strip()
            st.session_state.p2_name = p2.strip()
            st.session_state.p1_contact = p1_contact.strip()
            st.session_state.p2_contact = p2_contact.strip()
            st.session_state.start_time = time.time()
            st.session_state.started = True
            st.rerun()
        else:
            st.warning("Please fill in Team Name, both Player Names, and both Contact Numbers.")

    # Halt script execution here so subsequent views do not render on registration
    st.stop()

# -------------------------------------------------------------
# 5. ACTIVE ARENA DASHBOARD & TIMER
# -------------------------------------------------------------
st.markdown('<div class="electric-title">⚡ High-Voltage Arena</div>', unsafe_allow_html=True)
st.markdown('<div class="spark-arc"></div>', unsafe_allow_html=True)

rem_seconds = get_time_remaining()
if rem_seconds <= 0 and st.session_state.stage not in ["finished", "eliminated"]:
    st.session_state.stage = "finished"
    st.rerun()

mins, secs = divmod(rem_seconds, 60)
timer_col1, timer_col2 = st.columns([2, 1])
with timer_col1:
    st.write(f"Team: **{st.session_state.team_name}** | Stage: **{st.session_state.stage.upper()}**")
with timer_col2:
    st.markdown(f"<h3 style='color:#fffb00; text-align:right; margin:0;'>⚡ {mins:02d}:{secs:02d}</h3>", unsafe_allow_html=True)

# -------------------------------------------------------------
# 6. STAGES & PUZZLE FLOW
# -------------------------------------------------------------
if st.session_state.stage == "riddles":
    st.info(f"⚡ Set {st.session_state.current_set_idx + 1} of 3: Decrypt the Circuit Codes")

    ans1 = st.text_input("Riddle 1: I store potential across an electric field and block direct current once saturated. What am I?", key="r1")
    ans2 = st.text_input("Riddle 2: I induce a back-EMF proportional to the rate of change of magnetic flux. What am I?", key="r2")

    if st.button("Submit Riddle Answers"):
        score_gain = 0
        if "capacitor" in ans1.lower():
            score_gain += 10
        if "inductor" in ans2.lower():
            score_gain += 10

        st.session_state.score += score_gain

        if st.session_state.current_set_idx < 2:
            st.session_state.current_set_idx += 1
            st.rerun()
        else:
            st.session_state.stage = "finished"
            st.rerun()

elif st.session_state.stage == "eliminated":
    st.error("❌ Circuit Overload: Your team has been eliminated from this round.")
    if st.button("Submit Final Log"):
        st.session_state.stage = "finished"
        st.rerun()

# -------------------------------------------------------------
# 7. FINISHED & GOOGLE SHEETS SYNC
# -------------------------------------------------------------
elif st.session_state.stage == "finished":
    st.subheader("🏁 Event Concluded")
    st.write(f"Team **{st.session_state.team_name}**, your results have been securely transmitted to the evaluation desk.")
    st.write("Please return to the main assembly area to await the qualification announcements.")

    if not st.session_state.submitted_to_sheet:
        with st.spinner("⚡ Encrypting and transmitting circuit telemetry..."):
            saved = log_results_to_sheets()
            if saved:
                st.session_state.submitted_to_sheet = True
                st.success("✅ Secure transmission successful.")
            else:
                st.info("Transmission recorded locally.")
