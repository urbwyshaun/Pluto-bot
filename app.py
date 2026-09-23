import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go

st.set_page_config(page_title="Pluto FX Bot", layout="wide")
st.title("🔱 Pluto FX - XAUUSD Scanner (Free)")

# --- Fetch XAUUSD data (free from Yahoo) ---
@st.cache_data(ttl=60)
def get_data(tf):
    interval = "60m" if tf=="H1" else "15m"
    df = yf.download("GC=F", period="5d", interval=interval)
    df = df.reset_index()
    return df

h1 = get_data("H1")
m15 = get_data("M15")

# --- Pluto Logic ---
def get_swing(df):
    high = df['High'].max()
    low = df['Low'].min()
    return high, low

h_high, h_low = get_swing(h1.tail(50))
main_618 = h_low + (h_high - h_low) * 0.618

m_high, m_low = get_swing(m15.tail(30))
entry_low = m_low + (m_high - m_low) * 0.236
entry_high = m_low + (m_high - m_low) * 0.382

price = h1['Close'].iloc[-1]

# --- Display ---
st.metric("Current Gold Price", f"${price:.2f}")
col1, col2 = st.columns(2)
col1.metric("Main Fib 61.8% (Target)", f"${main_618:.2f}")
col2.metric("Entry Zone (LTF)", f"${entry_low:.2f} - ${entry_high:.2f}")

# --- Signal ---
if price < main_618:
    st.warning("✅ STEP 1 DONE: Price broke Main 61.8% (Pluto Rule)")
    if entry_low <= price <= entry_high:
        st.success("🔥 ENTRY NOW: Price is in 23.6-38.2% zone! Wait for confirmation candle")
    else:
        st.info(f"Waiting for price to pull back into entry zone")
else:
    st.info("Waiting for break of Main 61.8%...")

# --- Chart ---
fig = go.Figure()
fig.add_trace(go.Candlestick(x=m15['Datetime'], open=m15['Open'], high=m15['High'], low=m15['Low'], close=m15['Close'], name="XAUUSD M15"))
fig.add_hline(y=main_618, line_dash="dash", line_color="red", annotation_text="Main 61.8% TARGET")
fig.add_hrect(y0=entry_low, y1=entry_high, fillcolor="green", opacity=0.2, annotation_text="ENTRY ZONE 23.6-38.2%")
st.plotly_chart(fig, use_container_width=True)

st.caption("Tip: Add this website to Home Screen -> it works like an app")
