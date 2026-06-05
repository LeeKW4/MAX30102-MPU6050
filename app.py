import streamlit as st
import pandas as pd
import plotly.express as px
import time

# Set up browser tab titles and widescreen layout
st.set_page_config(page_title="IoT Telemetry Dashboard", layout="wide")

# =============================================================================
# DATA ACQUISITION LAYER
# =============================================================================
# Paste your published Comma-separated values (.csv) link here
GSHEET_CSV_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vRbL-Zz4Y4a1JyJl3siTKv6gJs3hH86FK4LJk1_ZxgPjXr5JK40HC0YSxN0l990XTTMbprjpTyLA-mv/pub?output=csv"

def load_sensor_data():
    try:
        # Pull down the latest live rows from your Google Sheets database
        df = pd.read_csv(GSHEET_CSV_URL)
        # Convert timestamp strings into real pandas datetime objects for clean charting
        if 'Timestamp' in df.columns:
            df['Timestamp'] = pd.to_datetime(df['Timestamp'])
        return df
    except Exception as e:
        st.error(f"Failed to connect to spreadsheet database: {e}")
        return pd.DataFrame()

# =============================================================================
# DASHBOARD HEADER INTERFACE
# =============================================================================
st.title("📊 Real-Time IoT Health & Motion Command Center")
st.markdown("This dashboard pulls live data frames directly from the Raspberry Pi Pico W telemetry pipeline.")

# Create an automatic browser auto-refresh switch
auto_refresh = st.sidebar.checkbox("Enable Live 2s Auto-Refresh", value=True)
if auto_refresh:
    # Forces Streamlit to re-run the entire script every 2 seconds
    time.sleep(2)
    st.rerun()

# Load the fresh data profile frame
df = load_sensor_data()

if not df.empty:
    # Isolate the absolute latest row in the spreadsheet to display real-time values
    latest_reading = df.iloc[-1]
    
    # =============================================================================
    # 1. LIVE HIGHLIGHT METRICS BLOCK (MAX30102 Vitals)
    # =============================================================================
    st.subheader("❤️ Current Biometric Status")
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric(label="Heart Rate (BPM)", value=f"{int(latest_reading['BPM'])} bpm")
    with col2:
        st.metric(label="Blood Oxygen (SpO2)", value=f"{int(latest_reading['SpO2'])} %")
    with col3:
        st.metric(label="Total Database Records", value=f"{len(df)} rows")
        
    st.markdown("---")
    
    # =============================================================================
    # 2. GRAPHICAL TIME-SERIES VISUALIZATIONS (MPU6050 Motion)
    # =============================================================================
    st.subheader("🔄 Real-Time Kinematic Waveforms")
    
    # Limit visualization to the last 50 data frames so the charts remain clean and responsive
    plot_df = df.tail(50)
    
    chart_col1, chart_col2 = st.columns(2)
    
    with chart_col1:
        st.markdown("**Accelerometer Magnitude Profile (G-Force)**")
        # Generate an interactive line chart combining X, Y, and Z axes
        fig_accel = px.line(plot_df, x='Timestamp', y=['AX', 'AY', 'AZ'], 
                            labels={'value': 'Acceleration (G)', 'variable': 'Axis'})
        st.plotly_chart(fig_accel, use_container_width=True)
        
    with chart_col2:
        st.markdown("**Gyroscope Angular Velocity Profile (°/s)**")
        # Generate an interactive line chart combining rotational velocity components
        fig_gyro = px.line(plot_df, x='Timestamp', y=['GX', 'GY', 'GZ'], 
                           labels={'value': 'Rotation (°/s)', 'variable': 'Axis'})
        st.plotly_chart(fig_gyro, use_container_width=True)
        
    # =============================================================================
    # 3. RAW DATABASE LOGS
    # =============================================================================
    st.markdown("---")
    st.subheader("📋 Raw Database Log Stream")
    # Show reverse historical order so the newest logs appear right at the top
    st.dataframe(df.iloc[::-1], use_container_width=True)

else:
    st.warning("Database currently empty. Ensure your Pico W is actively sending sensor data packets.")