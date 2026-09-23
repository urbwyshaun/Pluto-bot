import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
import time

st.set_page_config(page_title="Pluto FX Bot", layout="wide")
st.title("🔱 Pluto FX - XAUUSD")
st.caption("Free bot | Main H1 61.8% + M15 Entry Zone")

@st.cache_data(ttl=90)
def get_data(interval):
    # Try 2 tickers - one always works
    for ticker in ["XAUUSD=X", "GC=F"]:
        try:
            df = yf.download(ticker, period="5d", interval=interval, auto_adjust=True, progress=False)
            if not df.empty and len(df) > 20:
                if isinstance(df.columns, pd.MultiIndex):
                    df.columns = df.columns.get_level_values(0)
                df = df.reset_index()
                return df
        except:
            time.sleep(1)
            continue
    return pd.DataFrame()

h1 = get_data("60m")
m15 = get_data("15m")

if h1.empty or m15.empty:
    st.error("Yahoo is slow right now. Wait 30 seconds then tap Rerun below.")
    if st.button("🔄 Rerun Now"):
        st.cache_data.clear()
        st.rerun()
    st.stop()

h_high = float(h1['High'].tail(50).max())
h_low = float(h1['Low'].tail(50).min())
main_618 = h_low + (h_high - h_low) * 0.618

m_high = float(m15['High'].tail(40).max())
m_low = float(m15['Low'].tail(40).min())
entry_low = m_low + (m_high - m_low) * 0.236
entry_high = m_low + (m_high - m_low) * 0.382

price = float(h1['Close'].iloc[-1])

c1, c2, c3 = st.columns(3)
c1.metric("Gold Now", f"${price:,.2f}")
c2.metric("Main 61.8% Target", f"${main_618:,.2f}")
c3.metric("Entry Zone", f"${entry_low:,.1f}-{entry_high:,.1f}")

if price < main_618:
    st.success("✅ Break of Main 61.8% confirmed")
    if entry_low <= price <= entry_high:
        st.warning("🔥 ENTRY ZONE NOW - Wait for bullish candle!")
        st.balloons()
    else:
        st.info("Waiting for pullback to 23.6-38.2% zone")
else:
    st.info("Waiting for break of Main 61.8%...")

# Chart
x_col = 'Datetime' if 'Datetime' in m15.columns else ('Date' if 'Date' in m15.columns else m15.columns[0])
fig = go.Figure(data=[go.Candlestick(
    x=m15.tail(100)[x_col],
    open=m15['Open'].tail(100),
    high=m15['High'].tail(100),
    low=m15['Low'].tail(100),
    close=m15['Close'].tail(100)
)])
fig.add_hline(y=main_618, line_dash="dash", line_color="red")
fig.add_hrect(y0=entry_low, y1=entry_high, fillcolor="green", opacity=0.2)
fig.update_layout(height=450, xaxis_rangeslider_visible=False)
st.plotly_chart(fig, use_container_width=True)

if st.button("🔄 Refresh"):
    st.cache_data.clear()
    st.rerun()
