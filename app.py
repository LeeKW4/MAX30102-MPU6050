import streamlit as st
import pandas as pd
import plotly.express as px
import random

# Set up browser tab titles and widescreen layout
st.set_page_config(page_title="IoT Telemetry Dashboard", layout="wide")

# =============================================================================
# DATA ACQUISITION LAYER
# =============================================================================
# Updated with your new Google Sheets CSV link
GSHEET_CSV_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vRbL-Zz4Y4a1JyJl3siTKv6gJs3hH86FK4LJk1_ZxgPjXr5JK40HC0YSxN0l990XTTMbprjpTyLA-mv/pub?output=csv"

def load_sensor_data():
    try:
        # Appending a random number forces Google to skip its cache and provide the newest row
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
# HIGH-SPEED LIVE STREAMING FRAGMENT (Updates continually every 1 second)
# =============================================================================
@st.fragment(run_every=1)
def render_live_dashboard():
    raw_df = load_sensor_data()
    
    if not raw_df.empty:
        # Keep exactly the last 20 rows for a smooth rolling window
        active_df = raw_df.tail(20).reset_index(drop=True)
        latest_reading = active_df.iloc[-1]
        current_rows = len(raw_df)
        
        # 1. LIVE HIGHLIGHT METRICS & STATUS BANNER
        col_title, col_status = st.columns([3, 1])
        with col_title:
            st.subheader("❤️ Current Biometric Status")
        with col_status:
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
