import requests
import os
import time
import copy
from datetime import datetime
import streamlit as st
import streamlit.components.v1 as components

# ----------------- CONFIGURATION & STYLING -----------------
st.set_page_config(page_title="Black Out", page_icon="🎮", layout="centered")

# Replace this with the App Script URL generated from your NEW spreadsheet!
GOOGLE_WEBHOOK_URL = "https://script.google.com/macros/s/AKfycbwLnXW4LZfjLfxiMA7RCnRxEikOlN6yiV12PXHN5w1y0Fk43AH8h0qOxlanVg2sJzzD/exec"

# Vibrant Cyberpunk/Neon CSS with Embedded Background Image
vibrant_css = """
    <style>
    /* Hide Default Streamlit Elements */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden !important;}
    [data-testid="stHeader"] {display: none !important;}
    [data-testid="stToolbar"] {display: none !important;}

    /* Animated Tech Background (No download required) */
    .stApp {
        background: linear-gradient(rgba(5, 5, 15, 0.85), rgba(5, 5, 15, 0.85)),
                    url("https://images.unsplash.com/photo-1550751827-4bd374c3f58b?q=80&w=2070") no-repeat center center fixed;
        background-size: cover;
        color: #e0f7fa;
        overflow-x: hidden;
    }

    /* Glassmorphism Containers */
    .stForm, div[data-testid="stVerticalBlock"] > div {
        background: rgba(10, 10, 25, 0.6) !important;
        border: 1px solid rgba(0, 255, 255, 0.2);
        border-radius: 12px;
        padding: 10px;
        box-shadow: 0 4px 30px rgba(0, 0, 0, 0.5);
        backdrop-filter: blur(5px);
    }

    /* Vibrant Glowing Headers */
    h1, h2, h3 {
        background: -webkit-linear-gradient(45deg, #00ffff, #ff00ff);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        text-align: center;
        text-shadow: 0 0 20px rgba(255, 0, 255, 0.5);
        font-weight: 900 !important;
    }

    /* Neon Text Inputs */
    input {
        border-radius: 8px !important;
        border: 1px solid #ff00ff !important;
        background-color: rgba(0, 0, 0, 0.7) !important;
        color: #00ffff !important;
        box-shadow: 0 0 10px rgba(255, 0, 255, 0.2) !important;
        font-weight: bold !important;
        font-size: 1.1rem !important;
    }
    input:focus {
        border: 2px solid #00ffff !important;
        box-shadow: 0 0 20px rgba(0, 255, 255, 0.7) !important;
        outline: none !important;
    }

    /* Vibrant Animated Pushbuttons */
    .stButton > button {
        width: 100%; 
        border-radius: 8px; 
        font-weight: 900;
        letter-spacing: 1px;
        background: linear-gradient(45deg, #090979, #9400d3) !important;
        color: #00ffff !important;
        border: 2px solid #00ffff !important;
        box-shadow: 0 0 15px rgba(148, 0, 211, 0.5) !important;
        transition: all 0.3s ease-in-out !important;
    }
    .stButton > button:hover {
        background: linear-gradient(45deg, #9400d3, #ff00ff) !important;
        color: #ffffff !important;
        border: 2px solid #ff00ff !important;
        box-shadow: 0 0 30px #ff00ff, inset 0 0 10px #00ffff !important;
        transform: translateY(-2px);
    }

    /* Success / Warning Alerts Customization */
    [data-testid="stAlert"] {
        background: rgba(0, 0, 0, 0.8) !important;
        border-left: 4px solid #00ffff !important;
        color: #fff !important;
    }

    /* Energy Divider */
    .energy-divider {
        height: 3px;
        width: 100%;
        background: linear-gradient(90deg, transparent, #00ffff, #ff00ff, #00ffff, transparent);
        box-shadow: 0 0 15px #ff00ff;
        margin: 20px 0;
        animation: pulse-line 2s infinite;
    }

    @keyframes pulse-line {
        0% { opacity: 0.5; }
        50% { opacity: 1; filter: brightness(1.5); }
        100% { opacity: 0.5; }
    }
    </style>
"""
st.markdown(vibrant_css, unsafe_allow_html=True)

def draw_divider():
    st.markdown('<div class="energy-divider"></div>', unsafe_allow_html=True)

# ----------------- SERVER MEMORY FOR REFRESH RESCUE -----------------
@st.cache_resource
def get_server_memory():
    return {}

server_memory = get_server_memory()

def save_team_state():
    if st.session_state.started:
        # Team key is based on Team Name and Player 1 Name since contact numbers are removed
        team_key = f"{st.session_state.team_name.strip().lower()}_{st.session_state.p1_name.strip().lower()}"
        server_memory[team_key] = {
            "team_name": st.session_state.team_name,
            "p1_name": st.session_state.p1_name,
            "p2_name": st.session_state.p2_name,
            "start_time": st.session_state.start_time,
            "current_set_idx": st.session_state.current_set_idx,
            "stage": st.session_state.stage,
            "total_score": st.session_state.total_score,
            "submitted_to_sheet": st.session_state.submitted_to_sheet,
            "set_state": copy.deepcopy(st.session_state.set_state)
        }

# ----------------- GAME DATA -----------------
SETS = [
    {
        "set_id": 1,
        "secret_code": "TEN",
        "riddles": [
            {"id": "r1", "prompt": "1. I have branches, but no fruit, trunk or leaves. What am I?", "accepted": ["bank", "a bank"]},
            {"id": "r2", "prompt": "2. What has to be broken before you can use it?", "accepted": ["egg", "an egg"]},
            {"id": "r3", "prompt": "3. I'm tall when I'm young, and I'm short when I'm old. What am I?", "accepted": ["candle", "a candle"]},
            {"id": "r4", "prompt": "4. What month of the year has 28 days?", "accepted": ["all", "all of them", "every month"]},
            {"id": "r5", "prompt": "5. What can you catch but not throw?", "accepted": ["cold", "a cold"]}
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
            {"id": "r1", "prompt": "1. What begins with an E and ends with an E but only has one letter?", "accepted": ["envelope", "an envelope"]},
            {"id": "r2", "prompt": "2. What can travel around the world while staying in a corner?", "accepted": ["stamp", "a stamp"]},
            {"id": "r3", "prompt": "3. The more of this there is, the less you see. What is it?", "accepted": ["darkness", "dark", "fog"]},
            {"id": "r4", "prompt": "4. What has a head and a tail but no body?", "accepted": ["coin", "a coin"]},
            {"id": "r5", "prompt": "5. Where does today come before yesterday?", "accepted": ["dictionary", "the dictionary"]}
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
            {"id": "r1", "prompt": "1. What has many keys but can't open a single lock?", "accepted": ["piano", "a piano", "keyboard"]},
            {"id": "r2", "prompt": "2. What is full of holes but still holds water?", "accepted": ["sponge", "a sponge"]},
            {"id": "r3", "prompt": "3. What gets wet while drying?", "accepted": ["towel", "a towel"]},
            {"id": "r4", "prompt": "4. What has a neck but no head?", "accepted": ["bottle", "a bottle", "shirt"]},
            {"id": "r5", "prompt": "5. I am not alive, but I grow; I don't have lungs, but I need air. What am I?", "accepted": ["fire", "a fire"]}
        ],
        "puzzle": {
            "prompt": "🧩 **SET 3 PUZZLE**:\nA sundial has the fewest moving parts of any timepiece. Which has the most?",
            "accepted": ["hourglass", "sand timer", "an hourglass"]
        }
    }
]

TOTAL_GAME_MINUTES = 30

# ----------------- SESSION STATE INIT -----------------
if "total_score" not in st.session_state:
    st.session_state.total_score = 0

if "started" not in st.session_state:
    st.session_state.started = False
    st.session_state.team_name = ""
    st.session_state.p1_name = ""
    st.session_state.p2_name = ""
    st.session_state.start_time = 0
    st.session_state.current_set_idx = 0
    st.session_state.stage = "riddles"
    st.session_state.submitted_to_sheet = False
    
    st.session_state.set_state = {
        "riddle_status": {}, 
        "retry_used": False,
        "puzzle_solved": False
    }

def get_time_remaining():
    elapsed = time.time() - st.session_state.start_time
    remaining = (TOTAL_GAME_MINUTES * 60) - elapsed
    return max(0, int(remaining))

def log_results_to_sheets():
    payload = {
        "Timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "Team_Name": st.session_state.team_name,
        "Player_1": st.session_state.p1_name,
        "P1_Contact": "N/A",  # Required to prevent Google Sheets webhook from breaking
        "Player_2": st.session_state.p2_name,
        "P2_Contact": "N/A",  # Required to prevent Google Sheets webhook from breaking
        "Final_Score": st.session_state.total_score,
        "Time_Taken_Sec": int(time.time() - st.session_state.start_time)
       }
    try:
        requests.post(GOOGLE_WEBHOOK_URL, json=payload, timeout=10)
        return True
    except Exception:
        return False

def advance_to_next_set():
    # Calculate score upon leaving the set
    correct_count = sum(1 for v in st.session_state.set_state["riddle_status"].values() if v)
    
    if correct_count == 5:
        st.session_state.total_score += 7
    else:
        st.session_state.total_score += correct_count
        if st.session_state.set_state["puzzle_solved"]:
            st.session_state.total_score += 2

    # Move to next set or end
    if st.session_state.current_set_idx < 2:
        st.session_state.current_set_idx += 1
        st.session_state.stage = "riddles"
        st.session_state.set_state = {
            "riddle_status": {}, 
            "retry_used": False,
            "puzzle_solved": False
        }
    else:
        st.session_state.stage = "final_code_entry"
    save_team_state()


# ----------------- UI SCREEN: REGISTRATION & RECOVERY -----------------
if not st.session_state.started:
    st.markdown("<h1>NEON RIDDLE ARENA</h1>", unsafe_allow_html=True)
    draw_divider()
    st.info("⏱️ **Mission:** 30 Minutes | 3 Nodes | 1 Device per Duo")
    
    t_name = st.text_input("Duo / Team Name:")
    col1, col2 = st.columns(2)
    
    with col1:
        p1 = st.text_input("Player 1 Name:")
    with col2:
        p2 = st.text_input("Player 2 Name:")

    if st.button("🚀 INITIATE SEQUENCE"):
        if t_name.strip() and p1.strip() and p2.strip():
            team_key = f"{t_name.strip().lower()}_{p1.strip().lower()}"
            if team_key in server_memory:
                restored_state = server_memory[team_key]
                for key, value in restored_state.items():
                    st.session_state[key] = value
                st.session_state.started = True
                st.rerun()
            else:
                st.session_state.team_name = t_name.strip()
                st.session_state.p1_name = p1.strip()
                st.session_state.p2_name = p2.strip()
                st.session_state.start_time = time.time()
                st.session_state.started = True
                save_team_state()
                st.rerun()
        else:
            st.warning("⚠️ Access Denied: Fill all credentials.")    
    st.stop()

# ----------------- LIVE JAVASCRIPT TIMER -----------------
time_left = get_time_remaining()
if time_left == 0 and st.session_state.stage != "finished":
    st.session_state.stage = "finished"
    save_team_state()
    st.rerun()

if st.session_state.stage != "finished":
    end_time_ms = (st.session_state.start_time + (TOTAL_GAME_MINUTES * 60)) * 1000
    live_timer_html = f"""
    <div style="background: rgba(0, 0, 0, 0.8); color: #00ffff; padding: 15px; border: 2px solid #ff00ff; border-radius: 8px; text-align: center; font-size: 2.5rem; font-weight: 900; font-family: 'Courier New', monospace; box-shadow: 0 0 25px rgba(0, 255, 255, 0.4); margin-bottom: 5px;">
        ⏱️ <span id="clock">--:--</span>
    </div>
    <script>
        var countDownDate = {end_time_ms};
        var x = setInterval(function() {{
            var now = new Date().getTime();
            var distance = countDownDate - now;
            if (distance < 0) {{
                clearInterval(x);
                document.getElementById("clock").innerHTML = "TIME UP";
                document.getElementById("clock").style.color = "#ff0000";
            }} else {{
                var minutes = Math.floor((distance % (1000 * 60 * 60)) / (1000 * 60));
                var seconds = Math.floor((distance % (1000 * 60)) / 1000);
                document.getElementById("clock").innerHTML = 
                    (minutes < 10 ? "0" : "") + minutes + ":" + (seconds < 10 ? "0" : "") + seconds;
            }}
        }}, 1000);
    </script>
    """
    components.html(live_timer_html, height=110)
    st.caption(f"🛡️ Connected: **{st.session_state.team_name}**")
    draw_divider()

# ----------------- GAME LOOP -----------------
current_set = SETS[st.session_state.current_set_idx]
s_state = st.session_state.set_state

# STAGE 1: RIDDLES
if st.session_state.stage == "riddles":
    st.subheader(f"📍 Set {current_set['set_id']}: Decrypt 5 Nodes")
    
    with st.form("riddles_form"):
        inputs = {}
        for r in current_set["riddles"]:
            is_locked = s_state["riddle_status"].get(r["id"], False)
            if is_locked:
                st.success(f"{r['prompt']}  \n*✅ Verified*")
            else:
                inputs[r["id"]] = st.text_input(r["prompt"], key=f"inp_{r['id']}")
        
        if st.form_submit_button("💥 SUBMIT ANSWERS 💥"):
            for r in current_set["riddles"]:
                r_id = r["id"]
                if not s_state["riddle_status"].get(r_id, False):
                    ans = inputs.get(r_id, "").strip().lower()
                    if ans in [a.lower() for a in r["accepted"]]:
                        s_state["riddle_status"][r_id] = True
                    else:
                        s_state["riddle_status"][r_id] = False
            
            cr = sum(1 for v in s_state["riddle_status"].values() if v)
            
            if cr == 5:
                st.session_state.stage = "eval_5"
            elif cr >= 3:
                st.session_state.stage = "eval_3_4"
            else:
                if s_state["retry_used"]:
                    st.session_state.stage = "eliminated"
                else:
                    st.session_state.stage = "eval_under_3"
            
            save_team_state()
            st.rerun()

# STAGE 2A: EVALUATE 5/5
elif st.session_state.stage == "eval_5":
    st.success("🌟 FLAWLESS! 5/5 Correct. You bypassed the puzzle and earned a massive 7 Points!")
    if st.button("Proceed to Output Data"):
        st.session_state.stage = "show_secret_code"
        save_team_state()
        st.rerun()

# STAGE 2B: EVALUATE 3 OR 4
elif st.session_state.stage == "eval_3_4":
    cr = sum(1 for v in s_state["riddle_status"].values() if v)
    st.warning(f"⚠️ {cr}/5 Correct. Minimum threshold met.")
    
    can_retry = not s_state["retry_used"]
    
    if can_retry:
        c1, c2, c3 = st.columns(3)
        with c1:
            if st.button("🔁 Retry Incorrect"):
                s_state["retry_used"] = True
                st.session_state.stage = "riddles"
                save_team_state()
                st.rerun()
        with c2:
            if st.button("🧩 Unlock Puzzle"):
                st.session_state.stage = "puzzle"
                save_team_state()
                st.rerun()
        with c3:
            if st.button("⏭️ Skip & Next Set"):
                st.session_state.stage = "show_secret_code"
                save_team_state()
                st.rerun()
    else:
        c1, c2 = st.columns(2)
        with c1:
            if st.button("🧩 Unlock Puzzle"):
                st.session_state.stage = "puzzle"
                save_team_state()
                st.rerun()
        with c2:
            if st.button("⏭️ Skip & Next Set"):
                st.session_state.stage = "show_secret_code"
                save_team_state()
                st.rerun()

# STAGE 2C: EVALUATE UNDER 3
elif st.session_state.stage == "eval_under_3":
    cr = sum(1 for v in s_state["riddle_status"].values() if v)
    st.error(f"📉 Signal Lost. Only {cr}/5 correct. You need at least 3 to survive.")
    
    if st.button("🔁 RETRY INCORRECT RIDDLES"):
        s_state["retry_used"] = True
        st.session_state.stage = "riddles"
        save_team_state()
        st.rerun()

# STAGE 3: PUZZLE
elif st.session_state.stage == "puzzle":
    st.subheader(f"🧩 Set {current_set['set_id']} Master Puzzle")
    st.info("⚠️ No retries allowed. Answer carefully.")
        
    st.markdown(current_set["puzzle"]["prompt"])
    p_ans = st.text_input("Enter Execution Code:")
    
    if st.button("💥 EXECUTE PUZZLE 💥"):
        clean_p = p_ans.strip().lower()
        if clean_p in [a.lower() for a in current_set["puzzle"]["accepted"]]:
            st.success("✅ Firewall Bypassed Successfully! +2 Points")
            s_state["puzzle_solved"] = True
        else:
            st.error("❌ Invalid Syntax. Puzzle Failed.")
            s_state["puzzle_solved"] = False
        
        st.session_state.stage = "show_secret_code"
        save_team_state()
        time.sleep(1.5)
        st.rerun()

# STAGE 4: SHOW SECRET CODE
elif st.session_state.stage == "show_secret_code":
    st.balloons()
    st.success(f"⚡ **Grid {current_set['set_id']} Synchronized!**")
    
    st.markdown(
        f"""<div style='text-align:center; padding:20px; border:2px dashed #00ffff; background:rgba(0,0,0,0.5); border-radius:10px;'>
        <h3 style='margin:0; color:#fff;'>SECRET CODE EXTRACTED:</h3>
        <h1 style='margin:0; font-size:4rem; color:#ff00ff; text-shadow:0 0 20px #00ffff;'>{current_set['secret_code']}</h1>
        <p style='margin:0; color:#aaa;'>Write this down immediately.</p>
        </div><br>""", 
        unsafe_allow_html=True
    )
    
    if st.session_state.current_set_idx + 1 < len(SETS):
        if st.button("🚀 ADVANCE TO NEXT SET"):
            advance_to_next_set()
            st.rerun()
    else:
        if st.button("🔒 ACCESS THE FINAL MAINFRAME"):
            advance_to_next_set()
            st.rerun()

# STAGE 5: FINAL CODE ENTRY
elif st.session_state.stage == "final_code_entry":
    st.subheader("🗝️ The Master Override")
    draw_divider()
    st.info("Assemble all 3 encrypted keys sequentially to upload your final score.")
    
    master_input = st.text_input("Enter the Combined Override Code:")
    
    if st.button("💥 TRANSMIT FINAL DATA LOG 💥"):
        correct_master_code = "".join([s["secret_code"].lower() for s in SETS])
        user_clean = master_input.strip().replace(" ", "").lower()
        
        if user_clean == correct_master_code:
            st.session_state.stage = "finished"
            save_team_state()
            st.rerun()
        else:
            st.error("❌ Authentication Failed. Check your keys and rewrite the sequence.")

# STAGE 6: ELIMINATED
elif st.session_state.stage == "eliminated":
    st.error("❌ FATAL ERROR: Your team failed to meet the minimum threshold. You have been eliminated.")
    if st.button("UPLOAD PARTIAL LOGS"):
        st.session_state.stage = "finished"
        save_team_state()
        st.rerun()

# STAGE 7: FINISHED & SYNC
elif st.session_state.stage == "finished":
    st.subheader("🏁 Connection Terminated")
    draw_divider()
    st.write(f"Team **{st.session_state.team_name}**, your telemetry has been securely transmitted.")
    
    if not st.session_state.submitted_to_sheet:
        with st.spinner("Encrypting and syncing logs..."):
            saved = log_results_to_sheets()
            if saved:
                st.session_state.submitted_to_sheet = True
                save_team_state()
                st.success("✅ Secure transmission verified. Handshake complete.")
            else:
                st.info("Transmission failed. Cache saved locally.")
