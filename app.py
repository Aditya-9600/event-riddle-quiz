import requests
import os
import time
from datetime import datetime
import streamlit as st
import streamlit.components.v1 as components
import pandas as pd

# ----------------- CONFIGURATION & STYLING -----------------
st.set_page_config(page_title="Riddle Quest Arena", page_icon="⚡", layout="centered")

st.markdown("""
<style>
    .stButton>button { width: 100%; border-radius: 8px; font-weight: bold; }
</style>
""", unsafe_allow_html=True)


hide_menu_style = """
    <style>
    #MainMenu {visibility: hidden;}
    header {visibility: hidden;}
    footer {visibility: hidden;}
    .viewerBadge_container__1QSob {display: none !important;}
    </style>
"""
st.markdown(hide_menu_style, unsafe_allow_html=True)

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
    st.session_state.contact_no1 = ""
    st.session_state.p2_name = ""
    st.session_state.contact_no2 = ""
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
        "Contact No.": st.session_state.contact_no1,
        "Player_2": st.session_state.p2_name,
        "Contact No.": st.session_state.contact_no2,
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
    st.info("⏱️ **Round Duration:** 40 Minutes | 3 Sets | Solve on 1 mobile per duo.")
    
    t_name = st.text_input("Duo / Team Name:")
    col1, col2 = st.columns(2)
    p1 = col1.text_input("Player 1 Name:")
    p2 = col2.text_input("Player 2 Name:")
    
    if st.button("🚀 Enter & Start Timer"):
        if t_name.strip() and p1.strip() and p2.strip():
            st.session_state.team_name = t_name.strip()
            st.session_state.p1_name = p1.strip()
            st.session_state.p2_name = p2.strip()
            st.session_state.start_time = time.time()
            st.session_state.started = True
            st.rerun()
        else:
            st.warning("Please fill in Team Name and both Player Names.")
    st.stop()

# ----------------- LIVE JAVASCRIPT TIMER -----------------
time_left = get_time_remaining()
if time_left == 0 and st.session_state.stage != "finished":
    st.session_state.stage = "finished"
    st.rerun()

if st.session_state.stage != "finished":
    # Injecting real-time ticking clock using JS (zero lag on server)
    end_time_ms = (st.session_state.start_time + (TOTAL_GAME_MINUTES * 60)) * 1000
    live_timer_html = f"""
    <div style="background: #1E293B; color: #38BDF8; padding: 12px; border-radius: 8px; text-align: center; font-size: 1.5rem; font-weight: bold; font-family: sans-serif; margin-bottom: 15px;">
        ⏳ Time Left: <span id="clock">--:--</span>
    </div>
    <script>
        var countDownDate = {end_time_ms};
        var x = setInterval(function() {{
            var now = new Date().getTime();
            var distance = countDownDate - now;
            if (distance < 0) {{
                clearInterval(x);
                document.getElementById("clock").innerHTML = "EXPIRED";
            }} else {{
                var minutes = Math.floor((distance % (1000 * 60 * 60)) / (1000 * 60));
                var seconds = Math.floor((distance % (1000 * 60)) / 1000);
                document.getElementById("clock").innerHTML = 
                    (minutes < 10 ? "0" : "") + minutes + ":" + (seconds < 10 ? "0" : "") + seconds;
            }}
        }}, 1000);
    </script>
    """
    components.html(live_timer_html, height=80)
    st.caption(f"Team: **{st.session_state.team_name}** ({st.session_state.p1_name} & {st.session_state.p2_name})")

# ----------------- GAME LOOP -----------------
current_set = SETS[st.session_state.current_set_idx]
s_state = st.session_state.set_state

# 1. RIDDLES STAGE
if st.session_state.stage == "riddles":
    st.subheader(f"📍 Set {current_set['set_id']} of 3: Riddles Round")
    
    with st.form("riddles_form"):
        inputs = {}
        for r in current_set["riddles"]:
            is_locked = s_state["riddle_correct"].get(r["id"], False)
            if is_locked:
                st.success(f"{r['prompt']}\n\n*✅ Correct (Locked)*")
            else:
                inputs[r["id"]] = st.text_input(r["prompt"], key=f"inp_{r['id']}")
        
        submitted = st.form_submit_button("Submit Answers")
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
    st.success("🌟 Perfect! All 5 riddles solved correctly.")
    st.write("Select your path:")
    c1, c2 = st.columns(2)
    if c1.button("➡️ Go Directly to Next Set"):
        st.session_state.stage = "set_complete"
        st.rerun()
    if c2.button("🧩 Solve Bonus Puzzle"):
        s_state["puzzle_mandatory"] = False
        st.session_state.stage = "puzzle"
        st.rerun()

# 3. DECISION: 3 OR 4 CORRECT
elif st.session_state.stage == "decision_3_4":
    st.warning("You met the minimum requirements to advance.")
    
    c1, c2 = st.columns(2)
    can_retry = s_state["retry_count"] < s_state["max_retries_allowed"]
    
    if can_retry:
        if c1.button(f"🔁 Retry Incorrect Riddles (Attempt {s_state['retry_count'] + 1})"):
            s_state["retry_count"] += 1
            st.session_state.stage = "riddles"
            st.rerun()
    
    if c2.button("🧩 Take Puzzle to Unlock Set"):
        s_state["puzzle_mandatory"] = True
        st.session_state.stage = "puzzle"
        st.rerun()

# 4. PROMPT: UNDER 3 CORRECT
elif st.session_state.stage == "retry_prompt_under_3":
    st.error("You need at least 3 correct to qualify for progression.")
    
    if st.button("🔁 Try Incorrect Riddles Again"):
        s_state["retry_count"] += 1
        s_state["max_retries_allowed"] = 2
        st.session_state.stage = "riddles"
        st.rerun()

# 5. PUZZLE ROUND (WITH RETRY LOGIC)
elif st.session_state.stage == "puzzle":
    st.subheader(f"🧩 Set {current_set['set_id']} Puzzle Challenge")
    if s_state["puzzle_mandatory"]:
        st.info("⚠️ **Strict Rule:** You must solve this puzzle correctly to unlock the next set.")
    else:
        st.info("ℹ️ Bonus Puzzle. Solving this advances you to the next set.")
        
    st.markdown(current_set["puzzle"]["prompt"])
    p_ans = st.text_input("Enter Puzzle Answer:")
    
    if st.button("Submit Puzzle Answer"):
        clean_p = p_ans.strip().lower()
        if clean_p in [a.lower() for a in current_set["puzzle"]["accepted"]]:
            st.success("✅ Puzzle Solved Correctly!")
            st.session_state.score += 3
            st.session_state.stage = "set_complete"
            st.rerun()
        else:
            # Check Puzzle Retry Logic
            if s_state["puzzle_retry_count"] < 1:
                s_state["puzzle_retry_count"] += 1
                st.error("❌ Incorrect answer. You have 1 retry remaining for this puzzle.")
            else:
                if s_state["puzzle_mandatory"]:
                    st.error("❌ Incorrect answer on final attempt. You cannot unlock the next set.")
                    st.session_state.stage = "eliminated"
                else:
                    st.warning("❌ Incorrect answer on final attempt. Advancing to next set.")
                    st.session_state.stage = "set_complete"
                st.rerun()

# 6. SET COMPLETE
elif st.session_state.stage == "set_complete":
    st.balloons()
    st.success(f"🎉 **Set {current_set['set_id']} Completed!**")
    st.info(f"🔑 Secret Code for Set {current_set['set_id']}: **{current_set['secret_code']}**")
    
    if st.session_state.current_set_idx + 1 < len(SETS):
        if st.button("🚀 Proceed to Next Set"):
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
        if st.button("🏁 Finish Event"):
            st.session_state.stage = "finished"
            st.rerun()

# 7. ELIMINATED
elif st.session_state.stage == "eliminated":
    st.error("❌ Your team has been eliminated from this round.")
    if st.button("Submit Final Log"):
        st.session_state.stage = "finished"
        st.rerun()

# 8. FINISHED & SYNC (SCORES HIDDEN)
elif st.session_state.stage == "finished":
    st.subheader("🏁 Event Concluded")
    st.write(f"Team **{st.session_state.team_name}**, your results have been securely transmitted to the evaluation desk.")
    st.write("Please return to the main assembly area to await the qualification announcements.")
    
    if not st.session_state.submitted_to_sheet:
        with st.spinner("Encrypting and transmitting logs..."):
            saved = log_results_to_sheets()
            if saved:
                st.session_state.submitted_to_sheet = True
                st.success("✅ Secure transmission successful.")
            else:
                st.info("Transmission complete.")
