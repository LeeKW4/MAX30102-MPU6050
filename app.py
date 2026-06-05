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
        # Appending a random number trick forces Google to bypass its 5-minute cache
        nocache_url = f"{GSHEET_CSV_URL}&nocache={random.randint(1, 100000)}"
        df = pd.read_csv(nocache_url)
        if 'Timestamp' in df.columns:
            df['Timestamp'] = pd.to_datetime(df['Timestamp'])
        return df
    except Exception as e:
        return pd.DataFrame()

# =============================================================================
# DASHBOARD HEADER INTERFACE
# =============================================================================
st.title("📊 Real-Time IoT Health & Motion Command Center")
st.markdown("This dashboard pulls live data frames directly from the Raspberry Pi Pico W telemetry pipeline.")
st.markdown("---")

# =============================================================================
# AUTOMATIC BACKGROUND STREAMING FRAGMENT
# =============================================================================
# run_every=2 tells Streamlit to automatically re-execute this block every 2 seconds smoothly
@st.fragment(run_every=2)
def render_live_dashboard():
    df = load_sensor_data()
    
    if not df.empty:
        # Isolate the absolute latest row in the spreadsheet
        latest_reading = df.iloc[-1]
        
        # 1. LIVE HIGHLIGHT METRICS BLOCK (MAX30102 Vitals)
        st.subheader("❤️ Current Biometric Status")
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric(label="Heart Rate (BPM)", value=f"{int(latest_reading['BPM'])} bpm")
        with col2:
            st.metric(label="Blood Oxygen (SpO2)", value=f"{int(latest_reading['SpO2'])} %")
        with col3:
            st.metric(label="Total Database Records", value=f"{len(df)} rows")
            
        st.markdown("---")
        
        # 2. GRAPHICAL TIME-SERIES VISUALIZATIONS (MPU6050 Motion)
        st.subheader("🔄 Real-Time Kinematic Waveforms")
        plot_df = df.tail(50)
        
        chart_col1, chart_col2 = st.columns(2)
        
        with chart_col1:
            st.markdown("**Accelerometer Magnitude Profile (G-Force)**")
            fig_accel = px.line(plot_df, x='Timestamp', y=['AX', 'AY', 'AZ'], 
                                labels={'value': 'Acceleration (G)', 'variable': 'Axis'})
            st.plotly_chart(fig_accel, use_container_width=True)
            
        with chart_col2:
            st.markdown("**Gyroscope Angular Velocity Profile (°/s)**")
            fig_gyro = px.line(plot_df, x='Timestamp', y=['GX', 'GY', 'GZ'], 
                               labels={'value': 'Rotation (°/s)', 'variable': 'Axis'})
            st.plotly_chart(fig_gyro, use_container_width=True)
            
        # 3. RAW DATABASE LOGS
        st.markdown("---")
        st.subheader("📋 Raw Database Log Stream")
        st.dataframe(df.iloc[::-1], use_container_width=True)
        
    else:
        st.warning("Database currently empty or waiting for spreadsheet connection...")

# Execute the live update fragment
render_live_dashboard()
