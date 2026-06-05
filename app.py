import streamlit as st
import pandas as pd
import plotly.express as px
import random

# Set up browser tab titles and widescreen layout
st.set_page_config(page_title="IoT Telemetry Dashboard", layout="wide")

# =============================================================================
# DATA ACQUISITION LAYER (WITH CACHE BUSTING)
# =============================================================================
GSHEET_CSV_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vVvZ2qyY_IQ5xPzPEAbXuT_YYWZUhuLqmRWIZEW66H8qvSiglRBz4YdLrKaUn68nA4/pub?gid=0&single=true&output=csv"

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
# AUTOMATIC ROLLING TIME-WINDOW FRAGMENT (Updates every 2 seconds)
# =============================================================================
@st.fragment(run_every=2)
def render_live_dashboard():
    raw_df = load_sensor_data()
    
    if not raw_df.empty:
        # ---------------------------------------------------------------------
        # AUTOMATIC MEMORY PURGE: Keep only the latest 30 seconds of live data
        # ---------------------------------------------------------------------
        latest_time = raw_df['Timestamp'].max()
        time_threshold = latest_time - pd.Timedelta(seconds=30)
        
        # Filter dataframe to drop old values outside the active time window
        rolling_df = raw_df[raw_df['Timestamp'] >= time_threshold].reset_index(drop=True)
        
        # Fallback: If 30 seconds calculation drops too many frames, keep the last 20 uploaded rows
        if len(rolling_df) < 5:
            rolling_df = raw_df.tail(20).reset_index(drop=True)
            
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
            st.metric(label="Active Rolling Buffer", value=f"{len(rolling_df)} data packets")
            
        st.markdown("---")
        
        # 2. GRAPHICAL ROLLING TIME-SERIES VISUALIZATIONS (MPU6050 & MAX30102)
        st.subheader("🔄 Live Dynamic Waveforms (30s Rolling Window)")
        chart_col1, chart_col2 = st.columns(2)
        
        with chart_col1:
            st.markdown("**MPU6050 Accelerometer Profile (G-Force)**")
            fig_accel = px.line(rolling_df, x='Timestamp', y=['AX', 'AY', 'AZ'], 
                                labels={'value': 'Acceleration (G)', 'variable': 'Axis'})
            # Tighten the padding margins so the charts look clean as they shift
            fig_accel.update_layout(margin=dict(l=20, r=20, t=20, b=20))
            st.plotly_chart(fig_accel, use_container_width=True)
            
        with chart_col2:
            st.markdown("**MPU6050 Gyroscope Angular Velocity Profile (°/s)**")
            fig_gyro = px.line(rolling_df, x='Timestamp', y=['GX', 'GY', 'GZ'], 
                               labels={'value': 'Rotation (°/s)', 'variable': 'Axis'})
            fig_gyro.update_layout(margin=dict(l=20, r=20, t=20, b=20))
            st.plotly_chart(fig_gyro, use_container_width=True)
            
        # 3. RAW ROLLING DATABASE LOGS (Newest rows always sit at the top)
        st.markdown("---")
        st.subheader("📋 Active Window Database Stream")
        st.dataframe(rolling_df.iloc[::-1], use_container_width=True)
        
    else:
        st.warning("Database stream temporarily offline. Waiting for fresh Pico W sensor frames...")

# Execute the rolling dashboard instance
render_live_dashboard()
