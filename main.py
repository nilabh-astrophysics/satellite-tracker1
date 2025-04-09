# 🌍 Satellite Ground Track Tracker - Professional Streamlit App

import streamlit as st
import numpy as np
import pandas as pd
from skyfield.api import load, EarthSatellite, wgs84
import plotly.express as px
from datetime import datetime, timedelta
import pytz

# --- Configuration ---
st.set_page_config(page_title="Satellite Ground Track Tracker", layout="wide")

# --- Title & Intro ---
st.markdown("""
# 🛰️ Satellite Ground Track Tracker
Visualize the orbital trajectory of satellites in real-time using Two-Line Element (TLE) data. Perfect for space mission planning, education, or competitive hackathons.
""")

# --- Sidebar Inputs ---
st.sidebar.header("🔧 Satellite Simulation Settings")

# Option to use custom TLE or pick from list
use_custom_tle = st.sidebar.checkbox("✏️ Enter Custom TLE", value=False)

if use_custom_tle:
    st.sidebar.markdown("Enter your custom Two-Line Element (TLE) data:")
    tle_name = st.sidebar.text_input("Satellite Name", "CUSTOM_SAT")
    tle_line1 = st.sidebar.text_input("TLE Line 1", "1 25544U 98067A   21275.51847222  .00002182  00000-0  45426-4 0  9992")
    tle_line2 = st.sidebar.text_input("TLE Line 2", "2 25544  51.6442 200.0463 0003707 133.5601  38.8325 15.48815429299184")
    try:
        satellite = EarthSatellite(tle_line1, tle_line2, tle_name)
        selected_satellite_name = tle_name
    except Exception as e:
        st.sidebar.error(f"Error parsing TLE: {e}")
        st.stop()
else:
    with st.spinner("Fetching latest satellite data..."):
        tle_url = 'https://celestrak.org/NORAD/elements/stations.txt'
        tle_lines = load.tle_file(tle_url)
        by_name = {sat.name: sat for sat in tle_lines}
        satellite_names = sorted(by_name.keys())
    selected_satellite_name = st.sidebar.selectbox("🌐 Select Satellite", satellite_names)
    satellite = by_name[selected_satellite_name]

# Simulation Controls
duration_minutes = st.sidebar.slider("🕒 Duration (minutes)", 30, 240, 90, 10)
time_step = st.sidebar.slider("⏱️ Time Step (seconds)", 10, 120, 30, 10)

# Local Timezone Selection
timezone_list = ['UTC', 'Asia/Kolkata', 'US/Eastern', 'Europe/London']
selected_tz = st.sidebar.selectbox("🌍 Display Timezone", timezone_list)
tz = pytz.timezone(selected_tz)

# --- Compute Satellite Position ---
ts = load.timescale()
start_time = datetime.now(pytz.utc)
minutes = np.arange(0, duration_minutes * 60, time_step)
observation_times = ts.utc(start_time.year, start_time.month, start_time.day,
                            start_time.hour, start_time.minute, minutes)

lats, lons, altitudes, timestamps = [], [], [], []
for t in observation_times:
    subpoint = satellite.at(t).subpoint()
    lats.append(subpoint.latitude.degrees)
    lons.append(subpoint.longitude.degrees)
    altitudes.append(subpoint.elevation.km)
    local_time = datetime.strptime(t.utc_iso(), "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=pytz.utc).astimezone(tz)
    timestamps.append(local_time.strftime('%Y-%m-%d %H:%M:%S'))

# --- DataFrame ---
df = pd.DataFrame({
    'Timestamp': timestamps,
    'Latitude': lats,
    'Longitude': lons,
    'Altitude (km)': altitudes
})

# --- Plotting ---
st.subheader(f"🗺️ Ground Track for: {selected_satellite_name}")
fig = px.scatter_geo(
    df,
    lat='Latitude',
    lon='Longitude',
    color='Altitude (km)',
    hover_data=['Timestamp'],
    projection="natural earth",
    title=f"Orbital Path Simulation ({selected_satellite_name})"
)
fig.update_traces(marker=dict(size=5))
fig.update_layout(margin={"r":0,"t":50,"l":0,"b":0}, height=600)

st.plotly_chart(fig, use_container_width=True)

# --- Extra Visual ---
st.markdown("""
### 📌 Current Simulation Info:
- **Satellite:** {0}
- **Start Time (UTC):** {1}
- **Duration:** {2} minutes
- **Time Step:** {3} seconds
""".format(selected_satellite_name, start_time.strftime('%Y-%m-%d %H:%M:%S'), duration_minutes, time_step))

# --- Data Table ---
with st.expander("📊 Show Raw Telemetry Data"):
    st.dataframe(df, use_container_width=True)

# --- Download Option ---
csv = df.to_csv(index=False).encode('utf-8')
st.download_button(
    label="📥 Download as CSV",
    data=csv,
    file_name=f"{selected_satellite_name.replace(' ', '_').lower()}_ground_track.csv",
    mime='text/csv'
)

# --- Footer ---
st.markdown("""
---
🚀 Created for hackathons and space tech demos. Built with ❤️ by combining real-time orbital mechanics (Skyfield), Python, and Streamlit.
""")
