# app.py
import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import time

# Page config
st.set_page_config(
    page_title="AEGIS Poultry Monitoring",
    page_icon="🐔",
    layout="wide"
)

# Custom CSS for styling
st.markdown("""
<style>
    .main-header {
        font-size: 3rem;
        color: #1f77b4;
        text-align: center;
        margin-bottom: 2rem;
    }
    .metric-card {
        background-color: #f0f2f6;
        padding: 1rem;
        border-radius: 0.5rem;
        border-left: 4px solid #1f77b4;
        margin-bottom: 1rem;
    }
    .alert {
        background-color: #ff4b4b;
        color: white;
        padding: 1rem;
        border-radius: 0.5rem;
        margin: 1rem 0;
    }
</style>
""", unsafe_allow_html=True)

# Header
st.markdown('<h1 class="main-header">AEGIS 🛡️ Poultry Health Monitoring</h1>', unsafe_allow_html=True)

# Sidebar for controls
with st.sidebar:
    st.header("Farm Controls")
    farm_size = st.slider("Number of Birds", 1000, 10000, 5000)
    alert_threshold = st.slider("Alert Threshold (%)", 80, 95, 90)
    st.divider()
    st.write("**Last Updated:**")
    st.write(datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    if st.button("🔄 Refresh Data"):
        st.rerun()

# Generate realistic fake data
@st.cache_data(ttl=60)  # Cache for 1 minute
def generate_data():
    now = datetime.now()
    hours = 24
    timestamps = [now - timedelta(hours=x) for x in range(hours, 0, -1)]
    
    # Base values with some noise
    base_water = 50 + np.random.normal(0, 5, hours)
    base_activity = 70 + np.random.normal(0, 8, hours)
    base_temp = 22 + np.random.normal(0, 1, hours)
    
    # Create a gradual anomaly in the last 6 hours
    anomaly_start = -6
    base_water[anomaly_start:] *= 0.8  # 20% drop
    base_activity[anomaly_start:] *= 0.7  # 30% drop
    base_temp[anomaly_start:] += 1.5  # Temperature rise
    
    df = pd.DataFrame({
        'timestamp': timestamps,
        'water_consumption': np.maximum(0, base_water),  # No negative values
        'activity_index': np.maximum(0, base_activity),
        'temperature': base_temp
    })
    
    return df

df = generate_data()
latest = df.iloc[-1]

# Calculate health score (simple average of normalized metrics)
water_norm = latest['water_consumption'] / 50  # 50 is normal baseline
activity_norm = latest['activity_index'] / 70   # 70 is normal baseline
temp_norm = 1 - (abs(latest['temperature'] - 22) / 5)  # 22°C is ideal

health_score = (water_norm + activity_norm + temp_norm) / 3 * 100

# Metrics columns
col1, col2, col3, col4 = st.columns(4)

with col1:
    st.markdown('<div class="metric-card">', unsafe_allow_html=True)
    st.metric("Water Consumption", f"{latest['water_consumption']:.1f} L/hr", 
              delta="-20% from normal" if latest['water_consumption'] < 40 else None)
    st.markdown('</div>', unsafe_allow_html=True)

with col2:
    st.markdown('<div class="metric-card">', unsafe_allow_html=True)
    st.metric("Activity Index", f"{latest['activity_index']:.1f}%", 
              delta="-30% from normal" if latest['activity_index'] < 50 else None)
    st.markdown('</div>', unsafe_allow_html=True)

with col3:
    st.markdown('<div class="metric-card">', unsafe_allow_html=True)
    st.metric("Temperature", f"{latest['temperature']:.1f}°C", 
              delta="+1.5°C" if latest['temperature'] > 23 else None)
    st.markdown('</div>', unsafe_allow_html=True)

with col4:
    st.markdown('<div class="metric-card">', unsafe_allow_html=True)
    st.metric("Health Score", f"{health_score:.1f}%", 
              delta="Critical" if health_score < alert_threshold else "Normal",
              delta_color="inverse" if health_score < alert_threshold else "normal")
    st.markdown('</div>', unsafe_allow_html=True)

# Alert system
if health_score < alert_threshold:
    st.markdown(f"""
    <div class="alert">
        <h3>🚨 CRITICAL ALERT</h3>
        <p>Flock health score has dropped to {health_score:.1f}%. This indicates a potential disease outbreak.</p>
        <p><strong>Recommended actions:</strong></p>
        <ul>
            <li>Isolate affected birds immediately</li>
            <li>Check water supply lines</li>
            <li>Contact veterinarian for inspection</li>
            <li>Increase monitoring frequency</li>
        </ul>
    </div>
    """, unsafe_allow_html=True)

# Charts
fig = make_subplots(rows=2, cols=2, 
                   subplot_titles=('Water Consumption', 'Activity Index', 
                                  'Temperature', 'Health Score Trend'),
                   vertical_spacing=0.15)

# Water consumption
fig.add_trace(go.Scatter(x=df['timestamp'], y=df['water_consumption'], 
                         name='Water', line=dict(color='blue')), row=1, col=1)
fig.add_hline(y=40, line_dash="dash", line_color="red", row=1, col=1)

# Activity index
fig.add_trace(go.Scatter(x=df['timestamp'], y=df['activity_index'], 
                         name='Activity', line=dict(color='green')), row=1, col=2)
fig.add_hline(y=50, line_dash="dash", line_color="red", row=1, col=2)

# Temperature
fig.add_trace(go.Scatter(x=df['timestamp'], y=df['temperature'], 
                         name='Temperature', line=dict(color='orange')), row=2, col=1)
fig.add_hline(y=23.5, line_dash="dash", line_color="red", row=2, col=1)

# Health score trend
health_scores = (df['water_consumption']/50 + df['activity_index']/70 + 
                 (1 - (abs(df['temperature'] - 22)/5))) / 3 * 100
fig.add_trace(go.Scatter(x=df['timestamp'], y=health_scores, 
                         name='Health Score', line=dict(color='red')), row=2, col=2)
fig.add_hline(y=alert_threshold, line_dash="dash", line_color="red", row=2, col=2)

fig.update_layout(height=600, showlegend=False)
st.plotly_chart(fig, use_container_width=True)

# Raw data section
with st.expander("View Raw Sensor Data"):
    st.dataframe(df.style.format({
        'water_consumption': '{:.1f}',
        'activity_index': '{:.1f}',
        'temperature': '{:.1f}'
    }), use_container_width=True)

# Footer
st.divider()
st.caption("AEGIS Poultry Monitoring System • Early Warning Detection Prototype • Not for clinical use")