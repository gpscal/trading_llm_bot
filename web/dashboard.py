import streamlit as st
import requests
import time
import pandas as pd
import plotly.express as px

st.title("SolBot Dashboard")

# Start Simulation
initial_usdt = st.number_input("Initial USDT", value=1000.0)
initial_sol = st.number_input("Initial SOL", value=10.0)
if st.button("Start Simulation"):
    response = requests.post("http://localhost:5000/start_simulation", json={"initial_usdt": initial_usdt, "initial_sol": initial_sol})
    st.write(response.json())

# Start Live Trading
if st.button("Start Live Trading"):
    response = requests.post("http://localhost:5000/start_live")
    st.write(response.json())

# Stop
if st.button("Stop"):
    response = requests.post("http://localhost:5000/stop")
    st.write(response.json())

# Status Display
st.subheader("Current Status")
status_placeholder = st.empty()

# Logs
st.subheader("Recent Logs")
logs_placeholder = st.empty()

# Chart
st.subheader("SOL Price Chart")
chart_placeholder = st.empty()

# Polling loop for updates
while True:
    try:
        status = requests.get("http://localhost:5000/get_status").json()
        status_placeholder.json(status)
        
        logs = "\n".join(status.get('logs', []))
        logs_placeholder.text(logs)
        
        # Example chart - assumes 'price_history' in state as list of dicts [{'time': ..., 'price': ...}]
        if 'price_history' in status:
            df = pd.DataFrame(status['price_history'])
            fig = px.line(df, x='time', y='price', title='SOL Price')
            chart_placeholder.plotly_chart(fig)
        
        time.sleep(5)  # Update every 5 seconds
    except:
        time.sleep(5)
