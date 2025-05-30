import streamlit as st
import datetime
import time
import pytz
import os  # ✅ Required to access environment variables
from openai import OpenAI
from dotenv import load_dotenv

# === Load environment variables from .env file ===
load_dotenv()
openai_api_key = os.getenv("OPENAI_API_KEY")

if not openai_api_key:
    st.error("❌ OPENAI_API_KEY not found in .env file.")
else:
    client = OpenAI(api_key=openai_api_key)

# === Constants ===
ASSISTANT_ID = "asst_urryIMK4661AL0EyIHCVGoM1"  # Replace with your actual Assistant ID
NY_TZ = pytz.timezone('America/New_York')
COLOR_PRIMARY = "#B30808"

# === Session State ===
if 'thread_id' not in st.session_state:
    st.session_state.thread_id = None
if 'analysis_data' not in st.session_state:
    st.session_state.analysis_data = None


def main():
    st.set_page_config(
        page_title="LaborBot: Crew Deployment AI", 
        layout="centered",
        page_icon="🍗"
    )
    
    # Custom CSS
    st.markdown(f"""
        <style>
            .stButton>button {{
                background-color: {COLOR_PRIMARY} !important;
                color: white !important;
                border: none !important;
            }}
            .stTextInput>div>div>input {{
                border: 1px solid {COLOR_PRIMARY} !important;
            }}
        </style>
    """, unsafe_allow_html=True)
    
    # Header
    st.title("🍗 Raising Cane's LaborBot")
    st.caption("AI-Powered Crew Deployment System")
    
    # Input Section
    with st.form("labor_inputs"):
        current_day = st.selectbox(
            "Day of Week",
            options=["Sunday", "Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"],
            index=datetime.datetime.now(NY_TZ).weekday()
        )
        
        col1, col2 = st.columns(2)
        with col1:
            current_time = st.time_input("Current Time")
            current_customers = st.number_input("Current Customer Count", min_value=0, value=100)
        with col2:
            override_hours = st.number_input("Closer Hours Override", min_value=0.0, value=6.0, step=0.5)
            current_crew_hours = st.number_input("Current Crew Hours", min_value=0.0, value=45.5, step=0.5)
        
        submitted = st.form_submit_button("🚀 Generate Labor Analysis", type="primary")
    
    # Analysis Section
    if submitted:
        with st.spinner("Consulting with LaborBot..."):
            try:
                # Create a new thread if one doesn't exist
                if not st.session_state.thread_id:
                    thread = client.beta.threads.create()
                    st.session_state.thread_id = thread.id
                
                # Create message with user inputs
                message = client.beta.threads.messages.create(
                    thread_id=st.session_state.thread_id,
                    role="user",
                    content=f"""
                    Current Time: {current_time.strftime('%I:%M %p')}
                    Current Customers: {current_customers}
                    Crew Hours: {current_crew_hours}
                    Closer Hours Override: {override_hours}
                    Day: {current_day}
                    """
                )
                
                # Run the Assistant
                run = client.beta.threads.runs.create(
                    thread_id=st.session_state.thread_id,
                    assistant_id=ASSISTANT_ID
                )
                
                # Poll for completion
                while True:
                    run_status = client.beta.threads.runs.retrieve(
                        thread_id=st.session_state.thread_id,
                        run_id=run.id
                    )
                    if run_status.status == "completed":
                        break
                    time.sleep(1)
                
                # Get the response
                messages = client.beta.threads.messages.list(
                    thread_id=st.session_state.thread_id
                )
                
                # Display the latest message
                st.session_state.analysis_data = messages.data[0].content[0].text.value
                st.markdown(st.session_state.analysis_data)
                
            except Exception as e:
                st.error(f"Error consulting LaborBot: {str(e)}")


