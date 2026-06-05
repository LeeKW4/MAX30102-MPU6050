import streamlit as st
import pandas as pd
import plotly.express as px
import random
import time

# Set up browser tab titles and widescreen layout
st.set_page_config(page_title="IoT Telemetry Dashboard", layout="wide")

# Initialize persistent memory registers for state tracking
if "last_row_count" not in st.session_state:
    st.session_state.last_row_count = 0
if "miss_count" not in st.session_state:
    st.session_state.miss_count = 0
if "is_sleeping" not in st.session_state:
    st.session_state.is_sleeping = False
if "cached_df" not in st.session_state:
    st.session_state.cached_df = pd.DataFrame()

# =============================================================================
# DATA ACQUISITION LAYER (WITH CACHE BUSTING)
# =============================================================================
GSHEET_CSV_URL = "hhttps://docs.google.com/spreadsheets/d/e/2PACX-1vRbL-Zz4Y4a1JyJl3siTKv6gJs3hH86FK4LJk1_ZxgPjXr5JK40HC0YSxN0l990XTTMbprjpTyLA-mv/pub?output=csv"

def load_sensor_data():
    try:
        # Appending a moving random number forces Google to drop its old cache frame
        nocache_url = f"{GSHEET_CSV_URL}&nocache={random.randint(1, 100000)}"
        df = pd.read_csv(nocache_url)
        
        if not df.empty and 'Timestamp' in df.columns:
            df['Timestamp'] = pd.to_datetime(df['Timestamp'])
        return df
    except Exception as e:
        return pd.DataFrame()

# =============================================================================
# DASHBOARD HEADER INTERFACE
# =============================================================================
st.title("📊 Real-Time IoT Health & Motion Command Center")
st.markdown("This dashboard features an automated smart-sleep engine to protect memory bandwidth when the hardware is idle.")
st.markdown("---")

# =============================================================================
# AUTOMATIC ROLLING ROW-WINDOW FRAGMENT (Smart Dynamic Cadence)
# =============================================================================
# We run the check loop every 2 seconds normally. If sleeping, it shifts gears safely.
refresh_rate = 5 if st.session_state.is_sleeping else 2

@st.fragment(run_every=refresh_rate)
def render_live_dashboard():
    # 1. Fetch fresh data matrix from the sheet gateway
    raw_df = load_sensor_data()
    
    if not raw_df.empty:
        current_rows = len(raw_df)
        
        # --- SMART SLEEP ENGINE LOGIC EVALUATION ---
        if current_rows == st.session_state.last_row_count:
            # Data hasn't changed. Advance the miss counter strike register
            st.session_state.miss_count += 1
            if st.session_state.miss_count >= 2:
                st.session_state.is_sleeping = True
        else:
            # WAKE UP SEQUENCE: Fresh data packet confirmed! Reset counters
            st.session_state.is_sleeping = False
            st.session_state.miss_count = 0
            st.session_state.last_row_count = current_rows
            st.session_state.cached_df = raw_df.copy() # Store fresh snapshot in state storage

        # Always read calculations from memory when deep sleep is active to keep graphs stable
        active_df = st.session_state.cached_df if st.session_state.is_sleeping else raw_df
        latest_reading = active_df.iloc[-1]
        
        # 2. METRICS DISPLAY COUNTERS BLOCK
        st.subheader("❤️ Current Biometric Status")
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric(label="Heart Rate (BPM)", value=f"{int(latest_reading['BPM'])} bpm")
        with col2:
            st.metric(label="Blood Oxygen (SpO2)", value=f"{int(latest_reading['SpO2'])} %")
        with col3:
            st.metric(label="Total Logged Packets", value=f"{len(active_df)} rows")
            
        st.markdown("---")
        
        # 3. PIPELINE STATUS ANNOUNCEMENTS
        if st.session_state.is_sleeping:
            st.warning(f"🛑 **Dashboard Suspended (No Updates for 2 Cycles):** Network pooling paused. Waiting for your Pico W to transmit a new entry before waking up...")
        else:
            st.success(f"🟢 **Pipeline Active:** Live streaming data packets smoothly. (Miss Counter: {st.session_state.miss_count}/2)")

        # 4. GRAPHICAL ROLLING VISUALIZATIONS
        st.subheader("🔄 Live Dynamic Waveforms (Last 20 Packets Rolling Window)")
        rolling_df = active_df.tail(20)
        chart_col1, chart_col2 = st.columns(2)
        
        with chart_col1:
            st.markdown("**MPU6050 Accelerometer Profile (G-Force)**")
            fig_accel = px.line(rolling_df, x='Timestamp', y=['AX', 'AY', 'AZ'], 
                                labels={'value': 'Acceleration (G)', 'variable': 'Axis'})
            fig_accel.update_layout(margin=dict(l=20, r=20, t=20, b=20))
            st.plotly_chart(fig_accel, use_container_width=True)
            
        with chart_col2:
            st.markdown("**MPU6050 Gyroscope Angular Velocity Profile (°/s)**")
            fig_gyro = px.line(rolling_df, x='Timestamp', y=['GX', 'GY', 'GZ'], 
                               labels={'value': 'Rotation (°/s)', 'variable': 'Axis'})
            fig_gyro.update_layout(margin=dict(l=20, r=20, t=20, b=20))
            st.plotly_chart(fig_gyro, use_container_width=True)
            
        # 5. RAW ROLLING DATABASE LOGS
        st.markdown("---")
        st.subheader("📋 Active Window Database Stream")
        st.dataframe(rolling_df.iloc[::-1], use_container_width=True)
        
    else:
        st.warning("Database stream temporarily offline. Waiting for fresh Pico W sensor frames...")

# Execute the smart-sleep tracking instance
render_live_dashboard()
