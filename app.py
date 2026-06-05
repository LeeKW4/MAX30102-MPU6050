import streamlit as st
import pandas as pd
import plotly.express as px
import random

# Set up browser tab titles and widescreen layout
st.set_page_config(page_title="IoT Telemetry Dashboard", layout="wide")

# Initialize short-term memory tracker for database updates
if "last_row_count" not in st.session_state:
    st.session_state.last_row_count = 0
if "is_stalled" not in st.session_state:
    st.session_state.is_stalled = False

# =============================================================================
# DATA ACQUISITION LAYER (WITH CACHE BUSTING)
# =============================================================================
GSHEET_CSV_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vRbL-Zz4Y4a1JyJl3siTKv6gJs3hH86FK4LJk1_ZxgPjXr5JK40HC0YSxN0l990XTTMbprjpTyLA-mv/pub?output=csv"

def load_sensor_data():
    try:
        # Appending a moving random number forces Google to drop its old cache frame
        nocache_url = f"{GSHEET_CSV_URL}&nocache={random.randint(1, 100000)}"
        df = pd.read_csv(nocache_url)
        
        if not df.empty and 'Timestamp' in df.columns:
            # Clean up the timestamps and sort them chronologically
            df['Timestamp'] = pd.to_datetime(df['Timestamp'])
            df = df.sort_values(by='Timestamp').reset_index(drop=True)
        return df
    except Exception as e:
        return pd.DataFrame()

# =============================================================================
# DASHBOARD HEADER INTERFACE
# =============================================================================
st.title("📊 Real-Time IoT Health & Motion Command Center")
st.markdown("This dashboard automatically maintains a rolling window of your latest real-time sensor metrics.")
st.markdown("---")

# =============================================================================
# AUTOMATIC ROLLING ROW-WINDOW FRAGMENT (Updates every 2 seconds)
# =============================================================================
@st.fragment(run_every=2)
def render_live_dashboard():
    raw_df = load_sensor_data()
    
    if not raw_df.empty:
        current_rows = len(raw_df)
        
        # --- UPDATE CHECKER LOGIC ---
        # If the number of rows matches the last check, flag the system as stalled/idle
        if current_rows == st.session_state.last_row_count:
            st.session_state.is_stalled = True
        else:
            st.session_state.is_stalled = False
            st.session_state.last_row_count = current_rows # Update memory with new row count
            
        # Isolate the absolute latest single snapshot row to display on the counters
        latest_reading = raw_df.iloc[-1]
        
        # 1. LIVE HIGHLIGHT METRICS BLOCK (MAX30102 Vitals)
        st.subheader("❤️ Current Biometric Status")
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric(label="Heart Rate (BPM)", value=f"{int(latest_reading['BPM'])} bpm")
        with col2:
            st.metric(label="Blood Oxygen (SpO2)", value=f"{int(latest_reading['SpO2'])} %")
        with col3:
            st.metric(label="Total Logged Packets", value=f"{current_rows} rows")
            
        st.markdown("---")
        
        # ---------------------------------------------------------------------
        # CONDITIONAL RENDER: Freeze reading views if no new data arrived
        # ---------------------------------------------------------------------
        if st.session_state.is_stalled:
            st.info("⏳ **Pipeline Idle:** No new updates detected from the Pico W. Graphs are frozen to save memory.")
            
            # We still show the raw log table below so you can look at historical data frames
            st.markdown("---")
            st.subheader("📋 Last Active Window Database Snapshot")
            rolling_df = raw_df.tail(20).reset_index(drop=True)
            st.dataframe(rolling_df.iloc[::-1], use_container_width=True)
            return # Exit the function here so the graphs don't waste power redrawing empty math
            
        # 2. GRAPHICAL ROLLING VISUALIZATIONS (Only runs if data is actively updating)
        st.subheader("🔄 Live Dynamic Waveforms (Last 20 Packets Rolling Window)")
        rolling_df = raw_df.tail(20).reset_index(drop=True)
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
            
        # 3. RAW ROLLING DATABASE LOGS
        st.markdown("---")
        st.subheader("📋 Active Window Database Stream")
        st.dataframe(rolling_df.iloc[::-1], use_container_width=True)
        
    else:
        st.warning("Database stream temporarily offline. Waiting for fresh Pico W sensor frames...")

# Execute the rolling dashboard instance
render_live_dashboard()
