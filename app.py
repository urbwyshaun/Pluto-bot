import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import requests, urllib.parse

st.set_page_config(page_title="Pluto FX REAL", layout="wide")
st.title("🔱 Pluto FX - REAL GOLD (Binance PAXG = XAUUSD)")

PHONE = st.secrets.get("WHATSAPP_PHONE", "")
APIKEY = st.secrets.get("WHATSAPP_APIKEY", "")

def send_whatsapp(msg):
    if not PHONE or not APIKEY: return False
    try:
        text = urllib.parse.quote(msg)
        url = f"https://api.callmebot.com/whatsapp.php?phone={PHONE}&text={text}&apikey={APIKEY}"
        requests.get(url, timeout=10)
        return True
    except: return False

@st.cache_data(ttl=60)
def get_paxg():
    # Binance PAXGUSDT = Real Gold Price - No API key, never blocked
    url_m15 = "https://api.binance.com/api/v3/klines?symbol=PAXGUSDT&interval=15m&limit=100"
    url_h1 = "https://api.binance.com/api/v3/klines?symbol=PAXGUSDT&interval=1h&limit=100"
    
    r1 = requests.get(url_m15, timeout=10).json()
    r2 = requests.get(url_h1, timeout=10).json()
    
    # [open time, open, high, low, close...]
    m15 = pd.DataFrame(r1, columns=['Time','Open','High','Low','Close','Vol','CT','QV','Tr','TB','TQ','I'])
    m15['Time'] = pd.to_datetime(m15['Time'], unit='ms')
    m15[['Open','High','Low','Close']] = m15[['Open','High','Low','Close']].astype(float)
    
    h1 = pd.DataFrame(r2, columns=['Time','Open','High','Low','Close','Vol','CT','QV','Tr','TB','TQ','I'])
    h1['Time'] = pd.to_datetime(h1['Time'], unit='ms')
    h1[['Open','High','Low','Close']] = h1[['Open','High','Low','Close']].astype(float)
    
    price = float(m15['Close'].iloc[-1])
    return price, h1, m15

try:
    price, h1, m15 = get_paxg()
except Exception as e:
    st.error(f"Binance busy: {e}")
    if st.button("🔄 Retry"):
        st.cache_data.clear()
        st.rerun()
    st.stop()

h_high = float(h1['High'].max())
h_low = float(h1['Low'].min())
main_618 = h_low + (h_high - h_low) * 0.618

m_high = float(m15['High'].tail(80).max())
m_low = float(m15['Low'].tail(80).min())
entry_low = m_low + (m_high - m_low) * 0.236
entry_high = m_low + (m_high - m_low) * 0.382

c1,c2,c3 = st.columns(3)
c1.metric("REAL GOLD (PAXG)", f"${price:,.2f}")
c2.metric("Main 61.8%", f"${main_618:,.2f}")
c3.metric("Entry Zone", f"${entry_low:,.2f} - {entry_high:,.2f}")

st.caption(f"✅ 100% REAL candles | PAXGUSDT = XAUUSD | Last candle: {m15['Time'].iloc[-1]} | Source: Binance")

is_break = price < main_618
in_entry = entry_low <= price <= entry_high

if is_break and in_entry:
    st.warning("🔥 REAL ENTRY NOW - Check Exness M15!")
    st.balloons()
    send_whatsapp(f"🔥 PLUTO REAL: Gold ${price:.2f} IN ENTRY ZONE {entry_low:.1f}-{entry_high:.1f}")
elif is_break:
    st.success(f"✅ Main Break Done (Price ${price:.2f} < 61.8% ${main_618:.2f})")
else:
    st.info(f"⏳ Waiting for break below ${main_618:.2f}")

fig = go.Figure(data=[go.Candlestick(
    x=m15['Time'], open=m15['Open'], high=m15['High'], low=m15['Low'], close=m15['Close'], name="PAXG=Gold"
)])
fig.add_hline(y=main_618, line_dash="dash", line_color="red", annotation_text="Main 61.8% Break Level")
fig.add_hrect(y0=entry_low, y1=entry_high, fillcolor="green", opacity=0.25, annotation_text="Entry")
fig.update_layout(height=550, xaxis_rangeslider_visible=False, template="plotly_dark")
st.plotly_chart(fig, use_container_width=True)

col1, col2 = st.columns(2)
with col1:
    if st.button("🔄 Refresh Real Gold"):
        st.cache_data.clear()
        st.rerun()
with col2:
    if st.button("📲 Test WhatsApp"):
        send_whatsapp(f"✅ REAL GOLD ${price:.2f} Bot working!")
        st.success("WhatsApp sent!")
