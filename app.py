import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go

st.set_page_config(page_title="Pluto FX Bot", layout="wide")
st.title("🔱 Pluto FX - XAUUSD Free Bot")
st.caption("Main H1 61.8% + M15 Entry Zone (No PC needed)")

# --- Functions ---
@st.cache_data(ttl=120)
def get_data(period, interval):
    df = yf.download("GC=F", period=period, interval=interval, auto_adjust=True)
    if df.empty:
        return pd.DataFrame()
    # Fix columns if multi-index
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.get_level_values(0)
    df = df.reset_index()
    return df

# Load
with st.spinner("Loading Gold data..."):
    h1 = get_data("5d", "60m")
    m15 = get_data("5d", "15m")

if h1.empty or m15.empty:
    st.error("Data feed busy. Tap 'Rerun' at bottom. Yahoo limits free data sometimes.")
    st.stop()

# Fix column names
def clean(df):
    # Ensure names are standard
    for col in ['Open','High','Low','Close']:
        if col not in df.columns:
            # try lowercase
            for c in df.columns:
                if c.lower() == col.lower():
                    df[col] = df[c]
    return df

h1 = clean(h1)
m15 = clean(m15)

# Calculate levels
h_high = float(h1['High'].tail(50).max())
h_low = float(h1['Low'].tail(50).min())
main_618 = h_low + (h_high - h_low) * 0.618

m_high = float(m15['High'].tail(40).max())
m_low = float(m15['Low'].tail(40).min())
range_m = m_high - m_low
entry_low = m_low + range_m * 0.236
entry_high = m_low + range_m * 0.382

price = float(h1['Close'].iloc[-1])

# Metrics
c1, c2, c3 = st.columns(3)
c1.metric("Gold Now", f"${price:,.2f}")
c2.metric("Main H1 61.8% Target", f"${main_618:,.2f}")
c3.metric("M15 Entry Zone", f"${entry_low:,.1f} - {entry_high:,.1f}")

# Signals
if price < main_618:
    st.success("✅ STEP 1 DONE: Price BROKE Main H1 61.8%")
    if entry_low <= price <= entry_high:
        st.warning("🔥🔥 ENTRY NOW in 23.6-38.2% Zone - Look for bullish engulfing!")
        st.balloons()
    else:
        st.info(f"⏳ Waiting for pullback into Entry Zone.")
else:
    st.info("⏳ Waiting for Break of Main H1 61.8%... No trade yet.")

# Chart
fig = go.Figure(data=[go.Candlestick(
    x=m15.iloc[-100:]['Datetime'] if 'Datetime' in m15.columns else m15.iloc[-100:].index,
    open=m15['Open'].tail(100),
    high=m15['High'].tail(100),
    low=m15['Low'].tail(100),
    close=m15['Close'].tail(100),
    name="Gold M15"
)])
fig.add_hline(y=main_618, line_dash="dash", line_color="red", annotation_text="Main 61.8%")
fig.add_hrect(y0=entry_low, y1=entry_high, fillcolor="green", opacity=0.15)
fig.update_layout(height=500, xaxis_rangeslider_visible=False)
st.plotly_chart(fig, use_container_width=True)

if st.button("🔄 Refresh Price"):
    st.cache_data.clear()
    st.rerun()
