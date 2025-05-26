import streamlit as st
import datetime
from openai import OpenAI
from dotenv import load_dotenv
import os
import time
from PIL import Image
import base64
import pytz
import matplotlib.pyplot as plt
import pandas as pd

# Load environment variables
load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# Configuration
ASSISTANT_ID = "asst_urryIMK4661AL0EyIHCVGoM1"
FILE_IDS = {
    "Sunday": "file-32LDPNmrZKYgCcadRna7Mx",
    "Tuesday": "file-Sn7aqSksFneBwCG92hfz1t",
    "Wednesday": "file-SCKkdoKxyDAjbe8sfahW92",
    "Thursday": "file-JFwpbQNMb6UrD4MJ4uV517",
    "Friday": "file-EBjabqhDZ6UXiLLMsHUgYy",
    "Saturday": "file-Gf1K4k5N8ZXXxGVArmDbXK"
}

# Store Options (demo)
STORES = ["C164 Athens", "C1184 Mcdonough", "C1069 Snellville"]

# Get current time in New York timezone
ny_tz = pytz.timezone('America/New_York')
now = datetime.datetime.now(ny_tz)
current_time_str = now.strftime("%I:%M %p")
current_day_str = now.strftime("%A")
formatted_date = now.strftime("%B %d, %Y")

# Initialize session state for chat history
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

# Set page config to default background
st.set_page_config(page_title="LaborBot: Crew Deployment AI", layout="wide")

## --- CSS Styling ---
st.markdown("""
    <style>
        h1, h2, h3, h4, h5, h6, label {
            color: #B30808 !important;
        }
        .logo-container {
            display: flex;
            justify-content: center;
            align-items: center;
            margin-bottom: 10px;
        }
        .stButton>button {
            background-color: black !important;
            color: white !important;
            border: 2px solid #B30808 !important;
            border-radius: 10px !important;
            font-weight: bold !important;
            font-size: 1em !important;
            padding: 0.6em 1.2em !important;
            text-align: center;
            display: inline-block;
            cursor: pointer;
        }
        .stButton>button:hover {
            background-color: #B30808 !important;
            color: white !important;
        }
        .stSelectbox > div {
            background-color: transparent !important;
            border: none !important;
            box-shadow: none !important;
        }
    </style>
""", unsafe_allow_html=True)

# Logo + Title
logo_path = "Raising_Cane's_Chicken_Fingers_logo.svg.png"
try:
    with open(logo_path, "rb") as image_file:
        encoded = base64.b64encode(image_file.read()).decode()
        st.markdown(f"""
            <div class='logo-container'>
                <img src="data:image/png;base64,{encoded}" width="200" />
            </div>
        """, unsafe_allow_html=True)
except FileNotFoundError:
    st.warning("Logo file not found. Proceeding without it.")

st.markdown("<h1 style='text-align: center;'>Raising Cane's LaborBot</h1>", unsafe_allow_html=True)

# --- Input Section ---
st.markdown("<div class='rounded-box'>", unsafe_allow_html=True)
st.write(f"**Today's Date:** {formatted_date}")
st.write(f"📅 **Day:** {current_day_str}")
st.write(f"⏰ **Time:** {current_time_str}")

# Move store selector here
store_selected = st.selectbox("Select Store Location:", STORES, index=0)

# Keep numeric inputs in same block below
current_customers = st.number_input("Current Customer Count", min_value=0, step=1)
current_crew_hours = st.number_input("Current Crew Hours Logged", min_value=0.0, step=0.1)
override_closer_hours = st.number_input("Override Closer Hours (optional)", min_value=0.0, step=0.5, value=6.0)

# Schedule input moved below
employee_data = st.text_area("Paste today's full schedule or currently clocked-in team (optional):", height=250)
st.markdown("</div>", unsafe_allow_html=True)

clocked_in_list = [line.strip() for line in employee_data.split("\n") if line.strip()]

# Chat Interface
st.markdown("### 💬 Ask LaborBot a Question (optional)")
user_query = st.text_input(
    "Type your labor question below:",
    placeholder="e.g., I have a call out in kitchen, how does this affect the shift?",
    key="labor_query_input"
)

# Analyze Button
analyze_button = st.button("🔍 Analyze with LaborBot")

# Run AI Logic
if analyze_button:
    with st.spinner("⏳ Contacting LaborBot and processing..."):
        try:
            file_id = FILE_IDS.get(current_day_str, None)
            if not file_id:
                st.error(f"No PDF available for {current_day_str}.")
            else:
                thread = client.beta.threads.create()

                user_message = (
                    f"Current time: {current_time_str}\n"
                    f"Day: {current_day_str}\n"
                    f"Current customers: {current_customers}\n"
                    f"Current crew hours logged: {current_crew_hours}\n"
                    f"Override closer hours: {override_closer_hours}\n"
                )

                if user_query.strip():
                    user_message += f"Question: {user_query}\n"

                if clocked_in_list:
                    user_message += "\nClocked-in team or schedule:\n" + "\n".join(clocked_in_list)

                client.beta.threads.messages.create(
                    thread_id=thread.id,
                    role="user",
                    content=user_message,
                    file_ids=[file_id]
                )

                run = client.beta.threads.runs.create(
                    thread_id=thread.id,
                    assistant_id=ASSISTANT_ID
                )

                while True:
                    run_status = client.beta.threads.runs.retrieve(thread_id=thread.id, run_id=run.id)
                    if run_status.status == "completed":
                        break
                    time.sleep(2)

                messages = client.beta.threads.messages.list(thread_id=thread.id)
                ai_response = messages.data[0].content[0].text.value

                st.session_state.chat_history.append((user_query if user_query.strip() else "(No question provided)", ai_response))
                st.success("✅ Response received!")

        except Exception as e:
            st.error(f"❌ Error during assistant processing: {e}")

# Display chat history
if st.session_state.chat_history:
    st.subheader("🧠 LaborBot Conversation History")
    for query, response in reversed(st.session_state.chat_history):
        st.markdown(f"**🧍 You:** {query}")
        st.markdown(f"**🤖 LaborBot:** {response}")

