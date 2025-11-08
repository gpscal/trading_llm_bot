import streamlit as st
import requests
import time
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots

st.title("Trading LLM Bot Dashboard")

# Initialize session state
if 'auto_refresh' not in st.session_state:
    st.session_state.auto_refresh = False
if 'last_price_history' not in st.session_state:
    st.session_state.last_price_history = []
if 'chart_key' not in st.session_state:
    st.session_state.chart_key = 0

# Profiles Panel
st.subheader("Profiles")
profiles_col1, profiles_col2 = st.columns(2)
with profiles_col1:
    profile_name = st.text_input("Profile Name", key="profile_name")
    api_key = st.text_input("Kraken API Key", type="password")
    api_secret = st.text_input("Kraken API Secret", type="password")
    slack_webhook_url = st.text_input("Slack Webhook URL", type="password")
    telegram_bot_token = st.text_input("Telegram Bot Token", type="password")
    telegram_chat_id = st.text_input("Telegram Chat ID", type="password")
    if st.button("Save Profile"):
        if not profile_name:
            st.error("Please provide a profile name.")
        else:
            payload = {
                'name': profile_name,
                'api_key': api_key or None,
                'api_secret': api_secret or None,
                'slack_webhook_url': slack_webhook_url or None,
                'telegram_bot_token': telegram_bot_token or None,
                'telegram_chat_id': telegram_chat_id or None
            }
            try:
                r = requests.post("http://localhost:5000/save_profile", json=payload, timeout=10)
                if r.status_code == 200:
                    st.success("Profile saved.")
                else:
                    st.error(f"Save failed: {r.text}")
            except Exception as e:
                st.error(f"Error: {e}")

with profiles_col2:
    try:
        resp = requests.get("http://localhost:5000/profiles", timeout=10)
        profiles = resp.json() if resp.status_code == 200 else {}
    except Exception:
        profiles = {}
    profile_names = sorted(list(profiles.keys()))
    selected_profile = st.selectbox("Select Profile", options=[""] + profile_names)
    if selected_profile:
        st.json(profiles.get(selected_profile, {}))
        if st.button("Apply Profile"):
            try:
                r = requests.post("http://localhost:5000/apply_profile", json={'name': selected_profile}, timeout=10)
                if r.status_code == 200:
                    st.success("Profile applied. New credentials active.")
                else:
                    st.error(f"Apply failed: {r.text}")
            except Exception as e:
                st.error(f"Error: {e}")

# Control Panel
st.subheader("Control Panel")
col1, col2, col3, col4 = st.columns(4)

with col1:
    initial_usdt = st.number_input("Initial USDT", value=1000.0, key="usdt_input")

with col2:
    initial_sol = st.number_input("Initial SOL", value=10.0, key="sol_input")

with col3:
    if st.button("Start Simulation", key="start_sim"):
        try:
            response = requests.post("http://localhost:5000/start_simulation",
                                   json={"initial_usdt": initial_usdt, "initial_sol": initial_sol})
            if response.status_code == 200:
                st.success("Simulation started!")
                st.session_state.auto_refresh = True
            else:
                st.error(f"Failed to start simulation: {response.json()}")
        except Exception as e:
            st.error(f"Error: {e}")

with col4:
    if st.button("Start Live Trading", key="start_live"):
        try:
            response = requests.post("http://localhost:5000/start_live")
            if response.status_code == 200:
                st.success("Live trading started!")
                st.session_state.auto_refresh = True
            else:
                st.error(f"Failed to start live trading: {response.json()}")
        except Exception as e:
            st.error(f"Error: {e}")

# Stop button and auto-refresh toggle
col5, col6 = st.columns(2)
with col5:
    if st.button("Stop", key="stop"):
        try:
            response = requests.post("http://localhost:5000/stop")
            if response.status_code == 200:
                st.success("Stopped!")
                st.session_state.auto_refresh = False
            else:
                st.error(f"Failed to stop: {response.json()}")
        except Exception as e:
            st.error(f"Error: {e}")

with col6:
    auto_refresh = st.checkbox("Auto-refresh", value=st.session_state.auto_refresh, key="auto_refresh_checkbox")
    st.session_state.auto_refresh = auto_refresh

# Manual refresh button
if st.button("Refresh Now", key="manual_refresh"):
    pass  # This will trigger a rerun

# Function to fetch status
@st.cache_data(ttl=30)  # Cache for 30 seconds
def fetch_status():
    try:
        response = requests.get("http://localhost:5000/get_status", timeout=5)
        return response.json()
    except Exception as e:
        st.error(f"Error fetching status: {e}")
        return None

# Display sections
st.subheader("Current Status")
status_placeholder = st.empty()

st.subheader("Current Balance")
balance_placeholder = st.empty()

st.subheader("BTC Indicators")
btc_indicators_placeholder = st.empty()

st.subheader("SOL Indicators")
sol_indicators_placeholder = st.empty()

st.subheader("Recent Logs")
logs_placeholder = st.empty()

st.subheader("SOL Price Chart")
chart_placeholder = st.empty()

st.subheader("Equity Curve (USD)")
equity_placeholder = st.empty()

st.subheader("Drawdown (%)")
drawdown_placeholder = st.empty()

# Main update function
def update_display():
    status = fetch_status()
    if not status:
        return

    # Display status
    status_text = f"Running: {status.get('running', False)}\nMode: {status.get('mode', 'None')}"
    status_placeholder.text(status_text)

    # Display balance
    balance = status.get('balance', {})
    if balance:
        balance_text = f"USDT: {balance.get('usdt', 0):.2f}\nSOL: {balance.get('sol', 0):.4f}\nSOL Price: {balance.get('sol_price', 0):.2f}"
        balance_placeholder.text(balance_text)
    else:
        balance_placeholder.text("Balance not available yet.")

    # Display indicators
    indicators = status.get('indicators', {})
    if 'btc' in indicators and indicators['btc']:
        btc_data = []
        for key, value in indicators['btc'].items():
            if isinstance(value, list):
                btc_data.append(f"{key}: {', '.join([f'{v:.2f}' if isinstance(v, (int, float)) else str(v) for v in value])}")
            else:
                btc_data.append(f"{key}: {value:.4f}" if isinstance(value, (int, float)) else f"{key}: {value}")
        btc_indicators_placeholder.text("\n".join(btc_data))
    else:
        btc_indicators_placeholder.text("BTC indicators loading or not available yet.")

    if 'sol' in indicators and indicators['sol']:
        sol_data = []
        for key, value in indicators['sol'].items():
            if isinstance(value, list):
                sol_data.append(f"{key}: {', '.join([f'{v:.4f}' if isinstance(v, (int, float)) else str(v) for v in value])}")
            else:
                sol_data.append(f"{key}: {value:.4f}" if isinstance(value, (int, float)) else f"{key}: {value}")
        sol_indicators_placeholder.text("\n".join(sol_data))
    else:
        sol_indicators_placeholder.text("SOL indicators loading or not available yet.")

    # Display logs
    logs = status.get('logs', [])
    if logs:
        recent_logs = logs[-20:]
        formatted_logs = "\n".join([f"• {log.replace(chr(10), ' | ')}" for log in recent_logs])
        logs_placeholder.markdown(f"```\n{formatted_logs}\n```")
    else:
        logs_placeholder.text("No logs yet. Start simulation to generate data.")

    # Update chart only if data changed
    current_price_history = status.get('price_history', [])
    if current_price_history != st.session_state.last_price_history and current_price_history:
        st.session_state.last_price_history = current_price_history.copy()
        st.session_state.chart_key += 1

        df = pd.DataFrame(current_price_history)
        fig = px.line(df, x='time', y='price', title='SOL Price')
        chart_placeholder.plotly_chart(fig, key=f"sol_price_chart_{st.session_state.chart_key}")
    elif not current_price_history:
        chart_placeholder.text("Price history not available yet.")

    # Equity curve
    equity_history = status.get('equity_history', [])
    if equity_history:
        eq_df = pd.DataFrame(equity_history)
        eq_fig = px.line(eq_df, x='time', y='equity', title='Total Equity (USD)')
        equity_placeholder.plotly_chart(eq_fig, key=f"equity_chart_{st.session_state.chart_key}")
    else:
        equity_placeholder.text("Equity history not available yet.")

    # Drawdown curve
    drawdown_history = status.get('drawdown_history', [])
    if drawdown_history:
        dd_df = pd.DataFrame(drawdown_history)
        dd_fig = px.line(dd_df, x='time', y='drawdown_pct', title='Drawdown (%)')
        drawdown_placeholder.plotly_chart(dd_fig, key=f"drawdown_chart_{st.session_state.chart_key}")
    else:
        drawdown_placeholder.text("Drawdown history not available yet.")

    # TradingView-style indicator charts
    st.subheader("TradingView-style Indicator Charts")
    tv_tabs = st.tabs(["SOL", "BTC"])

    def render_tv_chart(asset: str):
        ih = status.get('indicator_history', {}).get(asset, [])
        if not ih:
            st.info(f"No indicator history for {asset} yet.")
            return
        df = pd.DataFrame(ih)
        # Select price series
        if asset == 'sol':
            price_series = status.get('price_history', [])
        else:
            price_series = status.get('btc_price_history', [])
        price_df = pd.DataFrame(price_series)

        fig = make_subplots(rows=4, cols=1, shared_xaxes=True,
                            row_heights=[0.45, 0.2, 0.2, 0.15],
                            vertical_spacing=0.02,
                            subplot_titles=("Price with MA & Bollinger Bands", "RSI (14)", "MACD", "Stochastic"))

        # Row 1: Price + MA + BB
        if not price_df.empty:
            fig.add_trace(go.Scatter(x=price_df['time'], y=price_df['price'], name=f"{asset.upper()} Price", line=dict(color='#1f77b4')), row=1, col=1)
        if 'moving_avg' in df:
            fig.add_trace(go.Scatter(x=df['time'], y=df['moving_avg'], name='MA', line=dict(color='#ff7f0e')), row=1, col=1)
        if 'bb_upper' in df and 'bb_lower' in df:
            fig.add_trace(go.Scatter(x=df['time'], y=df['bb_upper'], name='BB Upper', line=dict(color='#2ca02c', width=1), opacity=0.6), row=1, col=1)
            fig.add_trace(go.Scatter(x=df['time'], y=df['bb_lower'], name='BB Lower', line=dict(color='#d62728', width=1), opacity=0.6), row=1, col=1)

        # Row 2: RSI
        if 'rsi' in df:
            fig.add_trace(go.Scatter(x=df['time'], y=df['rsi'], name='RSI', line=dict(color='#9467bd')), row=2, col=1)
            fig.add_hline(y=70, line=dict(color='red', dash='dot'), row=2, col=1)
            fig.add_hline(y=30, line=dict(color='green', dash='dot'), row=2, col=1)

        # Row 3: MACD and Signal
        if 'macd' in df and 'macd_signal' in df:
            fig.add_trace(go.Scatter(x=df['time'], y=df['macd'], name='MACD', line=dict(color='#8c564b')), row=3, col=1)
            fig.add_trace(go.Scatter(x=df['time'], y=df['macd_signal'], name='Signal', line=dict(color='#7f7f7f')), row=3, col=1)

        # Row 4: Stochastic
        if 'stoch' in df:
            fig.add_trace(go.Scatter(x=df['time'], y=df['stoch'], name='%K', line=dict(color='#17becf')), row=4, col=1)
            fig.add_hline(y=80, line=dict(color='red', dash='dot'), row=4, col=1)
            fig.add_hline(y=20, line=dict(color='green', dash='dot'), row=4, col=1)

        fig.update_layout(height=800, showlegend=True, margin=dict(l=40, r=20, t=40, b=40))
        st.plotly_chart(fig, use_container_width=True)

    with tv_tabs[0]:
        render_tv_chart('sol')
    with tv_tabs[1]:
        render_tv_chart('btc')

# Initial display
update_display()

# Auto-refresh logic
if st.session_state.auto_refresh:
    time.sleep(5)
    st.rerun()
