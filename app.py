import streamlit as st
import pandas as pd
import plotly.express as px
import random

# Set up browser tab titles and widescreen layout
st.set_page_config(page_title="IoT Telemetry Dashboard", layout="wide")

# =============================================================================
# UI TRICK: Hide the Streamlit "Running..." animation in the top right corner
# This makes the 1-second refresh completely invisible to the user!
# =============================================================================
st.markdown("""
    <style>
        .stApp [data-testid="stToolbar"] { display: none; }
    </style>
""", unsafe_allow_html=True)

# Initialize persistent memory to hold our "Screenshot"
if "last_row_count" not in st.session_state:
    st.session_state.last_row_count = 0
if "screenshot_df" not in st.session_state:
    st.session_state.screenshot_df = pd.DataFrame()

# =============================================================================
# DATA ACQUISITION LAYER
# =============================================================================
GSHEET_CSV_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vRbL-Zz4Y4a1JyJl3siTKv6gJs3hH86FK4LJk1_ZxgPjXr5JK40HC0YSxN0l990XTTMbprjpTyLA-mv/pub?output=csv"

def load_sensor_data():
    try:
        nocache_url = f"{GSHEET_CSV_URL}&nocache={random.randint(1, 100000)}"
        df = pd.read_csv(nocache_url)
        if not df.empty and 'Timestamp' in df.columns:
            df['Timestamp'] = pd.to_datetime(df['Timestamp'])
        return df
    except Exception as e:
        return pd.DataFrame()

st.title("📊 Real-Time IoT Health & Motion Command Center")
st.markdown("---")

# =============================================================================
# HIGH-SPEED BACKGROUND CHECKER (Runs exactly every 1 second)
# =============================================================================
@st.fragment(run_every=1)
def render_live_dashboard():
    raw_df = load_sensor_data()
    
    if not raw_df.empty:
        current_rows = len(raw_df)
        
        # ---------------------------------------------------------------------
        # SCREENSHOT LOGIC: Does the row count match our memory?
        # ---------------------------------------------------------------------
        if current_rows > st.session_state.last_row_count:
            # NEW DATA: Update our memory and grab the newest 20 rows
            st.session_state.last_row_count = current_rows
            st.session_state.screenshot_df = raw_df.tail(20).reset_index(drop=True)
            is_frozen = False
        else:
            # NO NEW DATA: Lock the visual state
            is_frozen = True
            
        # Fallback just in case the app restarts mid-stream
        if st.session_state.screenshot_df.empty:
            st.session_state.screenshot_df = raw_df.tail(20).reset_index(drop=True)

        # Always build the charts using our locked memory dataframe
        active_df = st.session_state.screenshot_df
        latest_reading = active_df.iloc[-1]
        
        # 1. LIVE HIGHLIGHT METRICS & DYNAMIC STATUS BANNER
        col_title, col_status = st.columns([3, 1])
        with col_title:
            st.subheader("❤️ Current Biometric Status")
        with col_status:
            if is_frozen:
                st.error("📸 **SCREENSHOT MODE (FROZEN)**")
            else:
                st.success("🟢 **LIVE STREAMING**")
                
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric(label="Heart Rate (BPM)", value=f"{int(latest_reading['BPM'])} bpm")
        with col2:
            st.metric(label="Blood Oxygen (SpO2)", value=f"{int(latest_reading['SpO2'])} %")
        with col3:
            st.metric(label="Total Logged Packets", value=f"{current_rows} rows")
            
        st.markdown("---")

        # 2. GRAPHICAL VISUALIZATIONS
        st.subheader("🔄 Dynamic Waveforms (Last 20 Packets)")
        chart_col1, chart_col2 = st.columns(2)
        
        with chart_col1:
            st.markdown("**MPU6050 Accelerometer Profile (G-Force)**")
            fig_accel = px.line(active_df, x='Timestamp', y=['AX', 'AY', 'AZ'], 
                                labels={'value': 'Acceleration (G)', 'variable': 'Axis'})
            fig_accel.update_layout(margin=dict(l=20, r=20, t=20, b=20))
            st.plotly_chart(fig_accel, use_container_width=True)
            
        with chart_col2:
            st.markdown("**MPU6050 Gyroscope Angular Velocity Profile (°/s)**")
            fig_gyro = px.line(active_df, x='Timestamp', y=['GX', 'GY', 'GZ'], 
                               labels={'value': 'Rotation (°/s)', 'variable': 'Axis'})
            fig_gyro.update_layout(margin=dict(l=20, r=20, t=20, b=20))
            st.plotly_chart(fig_gyro, use_container_width=True)
            
        # 3. RAW DATABASE LOGS
        st.markdown("---")
        st.subheader("📋 Active Window Database Stream")
        st.dataframe(active_df.iloc[::-1], use_container_width=True)
        
    else:
        st.warning("Database stream temporarily offline. Waiting for fresh Pico W sensor frames...")

# Execute the dashboard instance
render_live_dashboard()
