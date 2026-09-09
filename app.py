import requests
import os
import time
from datetime import datetime
import streamlit as st
import streamlit.components.v1 as components
import pandas as pd

# ----------------- CONFIGURATION & STYLING -----------------
st.set_page_config(page_title="Riddle Quest Arena", page_icon="⚡", layout="centered")

# High-Voltage Electrical CSS Theme
electric_css = """
    <style>
    /* Hide Default Streamlit Elements */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden !important;}
    [data-testid="stHeader"] {display: none !important;}
    [data-testid="stToolbar"] {display: none !important;}

    /* Core Background - Dark Circuit Board Vibe */
    .stApp {
        background: radial-gradient(circle at 50% 10%, #081121 0%, #010308 100%);
        color: #e0f7fa;
    }

    /* Neon Flickering Headers */
    h1, h2, h3 {
        color: #00ffff !important;
        text-shadow: 0 0 5px #00ffff, 0 0 15px #00ffff, 0 0 30px #0077ff;
        animation: electric-flicker 2s infinite alternate;
        text-align: center;
    }

    /* Glowing Text Inputs */
    input {
        border-radius: 6px !important;
        border: 1px solid #00a8cc !important;
        background-color: rgba(2, 12, 27, 0.8) !important;
        color: #00ffff !important;
        box-shadow: 0 0 10px rgba(0, 168, 204, 0.3) !important;
        font-family: 'Courier New', Courier, monospace !important;
        font-weight: bold !important;
    }
    input:focus {
        border: 1px solid #fffb00 !important;
        box-shadow: 0 0 20px rgba(255, 251, 0, 0.7) !important;
        outline: none !important;
    }

    /* High-Voltage Pushbuttons */
    .stButton > button {
        width: 100%; 
        border-radius: 8px; 
        font-weight: 800;
        letter-spacing: 1px;
        background: linear-gradient(90deg, #001f3f, #005f73) !important;
        color: #00ffff !important;
        border: 2px solid #00ffff !important;
        box-shadow: 0 0 15px rgba(0, 255, 255, 0.4), inset 0 0 8px rgba(0, 255, 255, 0.2) !important;
        transition: all 0.3s ease-in-out !important;
    }
    .stButton > button:hover {
        background: linear-gradient(90deg, #005f73, #0a9396) !important;
        color: #fffb00 !important;
        border: 2px solid #fffb00 !important;
        box-shadow: 0 0 25px #00ffff, 0 0 45px #fffb00 !important;
        transform: scale(1.02);
    }

    /* Plasma Arc Divider */
    .plasma-divider {
        height: 3px;
        width: 100%;
        background: linear-gradient(90deg, transparent, #00ffff, #fffb00, #00ffff, transparent);
        box-shadow: 0 0 15px #00ffff, 0 0 30px #fffb00;
        margin: 20px 0;
        animation: plasma-surge 1.5s infinite ease-in-out;
    }

    /* Keyframe Animations */
    @keyframes electric-flicker {
        0%, 19%, 21%, 23%, 25%, 54%, 56%, 100% { opacity: 1; text-shadow: 0 0 10px #00ffff, 0 0 25px #0077ff; }
        20%, 24%, 55% { opacity: 0.4; text-shadow: none; }
    }
    @keyframes plasma-surge {
        0% { filter: brightness(1); }
        50% { filter: brightness(1.8); }
        100% { filter: brightness(1); }
    }
    </style>
"""
st.markdown(electric_css, unsafe_allow_html=True)

def electric_line():
    st.markdown('<div class="plasma-divider"></div>', unsafe_allow_html=True)


# ----------------- GAME DATA -----------------
SETS = [
    {
        "set_id": 1,
        "secret_code": "TEN",
        "riddles": [
            {"id": "r1", "prompt": "1.", "accepted": ["bank", "a bank"]},
            {"id": "r2", "prompt": "2.", "accepted": ["egg", "an egg"]},
            {"id": "r3", "prompt": "3.", "accepted": ["candle", "a candle"]},
            {"id": "r4", "prompt": "4.", "accepted": ["all", "all of them", "all months", "every month"]},
            {"id": "r5", "prompt": "5.", "accepted": ["cold", "a cold"]}
        ],
        "puzzle": {
            "prompt": "🧩 **SET 1 PUZZLE**:\nIf 1=3, 2=3, 3=5, 4=4, 5=4, what does 6 equal?",
            "accepted": ["3", "three"]
        }
    },
    {
        "set_id": 2,
        "secret_code": "YEAR",
        "riddles": [
            {"id": "r1", "prompt": "1.", "accepted": ["envelope", "an envelope"]},
            {"id": "r2", "prompt": "2.", "accepted": ["stamp", "a stamp", "postage stamp"]},
            {"id": "r3", "prompt": "3.", "accepted": ["footsteps", "steps", "footprints"]},
            {"id": "r4", "prompt": "4.", "accepted": ["coin", "a coin"]},
            {"id": "r5", "prompt": "5.", "accepted": ["dictionary", "the dictionary", "in dictionary"]}
        ],
        "puzzle": {
            "prompt": "🧩 **SET 2 PUZZLE**:\nI add 5 to 9 and get 2. The answer is correct, but how?",
            "accepted": ["clock", "time", "on a clock", "watch"]
        }
    },
    {
        "set_id": 3,
        "secret_code": "CYCLE",
        "riddles": [
            {"id": "r1", "prompt": "1.", "accepted": ["piano", "a piano", "keyboard"]},
            {"id": "r2", "prompt": "2.", "accepted": ["sponge", "a sponge"]},
            {"id": "r3", "prompt": "3.", "accepted": ["towel", "a towel"]},
            {"id": "r4", "prompt": "4.", "accepted": ["bottle", "a bottle", "shirt"]},
            {"id": "r5", "prompt": "5.", "accepted": ["fire", "a fire"]}
        ],
        "puzzle": {
            "prompt": "🧩 **SET 3 PUZZLE**:\nA sundial has the fewest moving parts of any timepiece. Which has the most?",
            "accepted": ["hourglass", "sand timer", "an hourglass"]
        }
    }
]

TOTAL_GAME_MINUTES = 40

# ----------------- SESSION STATE -----------------
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

def get_time_remaining():
    elapsed = time.time() - st.session_state.start_time
    remaining = (TOTAL_GAME_MINUTES * 60) - elapsed
    return max(0, int(remaining))

def log_results_to_sheets():
    url = "https://script.google.com/macros/s/AKfycbwLnXW4LZfjLfxiMA7RCnRxEikOlN6yiV12PXHN5w1y0Fk43AH8h0qOxlanVg2sJzzD/exec"
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
        requests.post(url, json=payload, timeout=10)
        return True
    except Exception:
        return False

# ----------------- UI SCREEN: REGISTRATION -----------------
if not st.session_state.started:
    st.title("⚡ Duo Riddle & Puzzle Arena")
    electric_line()
    st.info("⏱️ **Circuit Duration:** 40 Minutes | 3 Sets | Solve on 1 mobile per duo.")
    
    t_name = st.text_input("Duo / Team Name:")
    col1, col2 = st.columns(2)
    
    with col1:
        p1 = st.text_input("Player 1 Name:")
        p1_contact = st.text_input("Player 1 Contact Number:")
        
    with col2:
        p2 = st.text_input("Player 2 Name:")
        p2_contact = st.text_input("Player 2 Contact Number:")

    if st.button("🔌 Connect to Grid & Start Timer"):
        if t_name.strip() and p1.strip() and p2.strip() and p1_contact.strip() and p2_contact.strip():
            st.session_state.team_name = t_name.strip()
            st.session_state.p1_name = p1.strip()
            st.session_state.p1_contact = p1_contact.strip()
            st.session_state.p2_name = p2.strip()
            st.session_state.p2_contact = p2_contact.strip()
            st.session_state.start_time = time.time()
            st.session_state.started = True
            st.rerun()
        else:
            st.warning("⚠️ INCOMPLETE CIRCUIT: Please fill in Team Name, Player Names, and Contact Numbers.")    
    st.stop()

# ----------------- LIVE JAVASCRIPT TIMER -----------------
time_left = get_time_remaining()
if time_left == 0 and st.session_state.stage != "finished":
    st.session_state.stage = "finished"
    st.rerun()

if st.session_state.stage != "finished":
    # Multimeter-style glowing timer overlay
    end_time_ms = (st.session_state.start_time + (TOTAL_GAME_MINUTES * 60)) * 1000
    live_timer_html = f"""
    <div style="background: rgba(0, 30, 60, 0.9); color: #00ffff; padding: 15px; border: 2px solid #00ffff; border-radius: 8px; text-align: center; font-size: 2rem; font-weight: bold; font-family: 'Courier New', monospace; box-shadow: 0 0 20px #00ffff, inset 0 0 15px rgba(0, 255, 255, 0.5); margin-bottom: 5px; text-shadow: 0 0 8px #00ffff;">
        ⚡ SYSTEM POWER: <span id="clock">--:--</span> ⚡
    </div>
    <script>
        var countDownDate = {end_time_ms};
        var x = setInterval(function() {{
            var now = new Date().getTime();
            var distance = countDownDate - now;
            if (distance < 0) {{
                clearInterval(x);
                document.getElementById("clock").innerHTML = "POWER DEPLETED";
                document.getElementById("clock").style.color = "#ff0044";
            }} else {{
                var minutes = Math.floor((distance % (1000 * 60 * 60)) / (1000 * 60));
                var seconds = Math.floor((distance % (1000 * 60)) / 1000);
                document.getElementById("clock").innerHTML = 
                    (minutes < 10 ? "0" : "") + minutes + ":" + (seconds < 10 ? "0" : "") + seconds;
            }}
        }}, 1000);
    </script>
    """
    components.html(live_timer_html, height=100)
    st.caption(f"📡 Transmission from Team: **{st.session_state.team_name}** ({st.session_state.p1_name} & {st.session_state.p2_name})")
    electric_line()

# ----------------- GAME LOOP -----------------
current_set = SETS[st.session_state.current_set_idx]
s_state = st.session_state.set_state

# 1. RIDDLES STAGE
if st.session_state.stage == "riddles":
    st.subheader(f"📍 Set {current_set['set_id']} of 3: Decrypt the Node")
    
    with st.form("riddles_form"):
        inputs = {}
        for r in current_set["riddles"]:
            is_locked = s_state["riddle_correct"].get(r["id"], False)
            if is_locked:
                st.success(f"{r['prompt']}\n\n*✅ Verified (Signal Locked)*")
            else:
                inputs[r["id"]] = st.text_input(r["prompt"], key=f"inp_{r['id']}")
        
        submitted = st.form_submit_button("Transmit Answers")
        if submitted:
            for r in current_set["riddles"]:
                r_id = r["id"]
                if not s_state["riddle_correct"].get(r_id, False):
                    ans = inputs.get(r_id, "").strip().lower()
                    if ans in [a.lower() for a in r["accepted"]]:
                        s_state["riddle_correct"][r_id] = True
                        st.session_state.score += 1
                    else:
                        s_state["riddle_correct"][r_id] = False
            
            correct_count = sum(1 for v in s_state["riddle_correct"].values() if v)
            
            if correct_count == 5:
                st.session_state.stage = "decision_5"
            elif correct_count >= 3:
                st.session_state.stage = "decision_3_4"
            else:
                if s_state["retry_count"] < s_state["max_retries_allowed"]:
                    st.session_state.stage = "retry_prompt_under_3"
                else:
                    st.session_state.stage = "eliminated"
            st.rerun()

# 2. DECISION: 5/5 CORRECT
elif st.session_state.stage == "decision_5":
    st.success("🌟 Maximum Output! All 5 frequencies matched.")
    st.write("Select your routing path:")
    c1, c2 = st.columns(2)
    if c1.button("➡️ Bypass to Next Set"):
        st.session_state.stage = "set_complete"
        st.rerun()
    if c2.button("🧩 Overclock Bonus Puzzle"):
        s_state["puzzle_mandatory"] = False
        st.session_state.stage = "puzzle"
        st.rerun()

# 3. DECISION: 3 OR 4 CORRECT
elif st.session_state.stage == "decision_3_4":
    st.warning("⚠️ Partial Connection: Minimum thresholds met.")
    
    c1, c2 = st.columns(2)
    can_retry = s_state["retry_count"] < s_state["max_retries_allowed"]
    
    if can_retry:
        if c1.button(f"🔁 Recalibrate Incorrect (Attempt {s_state['retry_count'] + 1})"):
            s_state["retry_count"] += 1
            st.session_state.stage = "riddles"
            st.rerun()
    
    if c2.button("🧩 Override Firewall via Puzzle"):
        s_state["puzzle_mandatory"] = True
        st.session_state.stage = "puzzle"
        st.rerun()

# 4. PROMPT: UNDER 3 CORRECT
elif st.session_state.stage == "retry_prompt_under_3":
    st.error("📉 Signal Lost. You need at least 3 correct nodes to advance.")
    
    if st.button("🔁 Reconnect and Try Again"):
        s_state["retry_count"] += 1
        s_state["max_retries_allowed"] = 2
        st.session_state.stage = "riddles"
        st.rerun()

# 5. PUZZLE ROUND (WITH RETRY LOGIC)
elif st.session_state.stage == "puzzle":
    st.subheader(f"🧩 Set {current_set['set_id']} Logic Gate")
    if s_state["puzzle_mandatory"]:
        st.info("⚠️ **Strict Rule:** You must bypass this logic gate correctly to unlock the next set.")
    else:
        st.info("ℹ️ Bonus Circuit. Solving this pushes you to the next grid.")
        
    st.markdown(current_set["puzzle"]["prompt"])
    p_ans = st.text_input("Enter Execution Code:")
    
    if st.button("Execute Puzzle Logic"):
        clean_p = p_ans.strip().lower()
        if clean_p in [a.lower() for a in current_set["puzzle"]["accepted"]]:
            st.success("✅ Firewall Bypassed Successfully!")
            st.session_state.score += 3
            st.session_state.stage = "set_complete"
            st.rerun()
        else:
            if s_state["puzzle_retry_count"] < 1:
                s_state["puzzle_retry_count"] += 1
                st.error("❌ Invalid Syntax. 1 retry remaining before lockout.")
            else:
                if s_state["puzzle_mandatory"]:
                    st.error("❌ Fatal Error. You are permanently locked out of the next set.")
                    st.session_state.stage = "eliminated"
                else:
                    st.warning("❌ Process Terminated. Re-routing to next set.")
                    st.session_state.stage = "set_complete"
                st.rerun()

# 6. SET COMPLETE
elif st.session_state.stage == "set_complete":
    st.balloons()
    st.success(f"⚡ **Grid {current_set['set_id']} Synchronized!**")
    st.info(f"🔑 Encrypted Key for Set {current_set['set_id']}: **{current_set['secret_code']}**")
    
    if st.session_state.current_set_idx + 1 < len(SETS):
        if st.button("🚀 Jump to Next Sector"):
            st.session_state.current_set_idx += 1
            st.session_state.stage = "riddles"
            st.session_state.set_state = {
                "riddle_correct": {},
                "retry_count": 0,
                "max_retries_allowed": 1,
                "puzzle_mandatory": False,
                "puzzle_retry_count": 0
            }
            st.rerun()
    else:
        if st.button("🔒 Access the Mainframe"):
            st.session_state.stage = "final_code_entry"
            st.rerun()

# 7. FINAL CODE ENTRY
elif st.session_state.stage == "final_code_entry":
    st.subheader("🗝️ The Master Override")
    electric_line()
    st.info("Assemble all 3 encrypted keys sequentially to trigger the final network submission.")
    
    master_input = st.text_input("Enter the Combined Override Code:")
    
    if st.button("Transmit Final Data Log"):
        correct_master_code = "".join([s["secret_code"].lower() for s in SETS])
        user_clean = master_input.strip().replace(" ", "").lower()
        
        if user_clean == correct_master_code:
            st.session_state.stage = "finished"
            st.rerun()
        else:
            st.error("❌ Authentication Failed. Check your keys and rewrite the sequence.")

# 8. ELIMINATED
elif st.session_state.stage == "eliminated":
    st.error("❌ CIRCUIT OVERLOAD: Your team has been disconnected from the server.")
    if st.button("Upload Partial Telemetry"):
        st.session_state.stage = "finished"
        st.rerun()

# 9. FINISHED & SYNC (SCORES HIDDEN)
elif st.session_state.stage == "finished":
    st.subheader("🏁 Connection Terminated")
    electric_line()
    st.write(f"Team **{st.session_state.team_name}**, your telemetry has been securely transmitted to the evaluation core.")
    st.write("Please return to the main assembly area while we decode the network qualifications.")
    
    if not st.session_state.submitted_to_sheet:
        with st.spinner("Encrypting and syncing logs to the mainframe..."):
            saved = log_results_to_sheets()
            if saved:
                st.session_state.submitted_to_sheet = True
                st.success("✅ Secure transmission verified. Handshake complete.")
            else:
                st.info("Transmission complete. Cache saved locally.")
