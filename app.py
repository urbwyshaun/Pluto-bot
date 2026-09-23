import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import requests, urllib.parse, time

st.set_page_config(page_title="Pluto FX REAL", layout="wide")
st.title("🔱 Pluto FX - 100% REAL XAUUSD")

PHONE = st.secrets.get("WHATSAPP_PHONE", "")
APIKEY = st.secrets.get("WHATSAPP_APIKEY", "")

def send_whatsapp(msg):
    if not PHONE or not APIKEY: return False
    try:
        text = urllib.parse.quote(msg)
        url = f"https://api.callmebot.com/whatsapp.php?phone={PHONE}&text={text}&apikey={APIKEY}"
        r = requests.get(url, timeout=10)
        return True
    except: return False

@st.cache_data(ttl=120)
def get_real_xau():
    try:
        # DIRECT YAHOO API - bypasses block
        url = "https://query1.finance.yahoo.com/v8/finance/chart/XAUUSD=X?range=5d&interval=15m"
        headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
        r = requests.get(url, headers=headers, timeout=15).json()
        result = r['chart']['result'][0]
        timestamps = result['timestamp']
        ohlc = result['indicators']['quote'][0]

        df = pd.DataFrame({
            'Time': pd.to_datetime(timestamps, unit='s'),
            'Open': ohlc['open'],
            'High': ohlc['high'],
            'Low': ohlc['low'],
            'Close': ohlc['close'],
            'Volume': ohlc['volume']
        }).dropna()

        # Resample to get H1 from M15
        df.set_index('Time', inplace=True)
        h1 = df.resample('1H').agg({'Open':'first','High':'max','Low':'min','Close':'last'}).dropna().reset_index()
        df = df.reset_index()

        live_price = float(df['Close'].iloc[-1])
        return live_price, h1, df
    except Exception as e:
        # Fallback to Gold API price if Yahoo still blocks
        try:
            r = requests.get("https://api.gold-api.com/price/XAU", timeout=10).json()
            price = float(r['price'])
            return price, pd.DataFrame(), pd.DataFrame()
        except:
            return 0, pd.DataFrame(), pd.DataFrame()

price, h1, m15 = get_real_xau()

if price == 0 or m15.empty:
    st.error("Yahoo still cooling down (60 sec). Tap Refresh.")
    if st.button("🔄 Refresh Real Data"):
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
c1.metric("REAL Gold", f"${price:,.2f}")
c2.metric("Main 61.8%", f"${main_618:,.2f}")
c3.metric("Entry", f"${entry_low:,.2f}-{entry_high:,.2f}")

st.caption(f"Data: {len(m15)} real M15 candles from Yahoo | Last: {m15['Time'].iloc[-1]}")

if price < main_618 and entry_low <= price <= entry_high:
    st.warning("🔥 REAL ENTRY NOW!")
    st.balloons()
    send_whatsapp(f"🔥 REAL PLUTO: Gold ${price:.2f} IN ENTRY ZONE!")
elif price < main_618:
    st.success("✅ Main Break Done (REAL)")
else:
    st.info("Waiting for break...")

fig = go.Figure(data=[go.Candlestick(
    x=m15['Time'], open=m15['Open'], high=m15['High'], low=m15['Low'], close=m15['Close']
)])
fig.add_hline(y=main_618, line_dash="dash", line_color="red", annotation_text="Main 61.8%")
fig.add_hrect(y0=entry_low, y1=entry_high, fillcolor="green", opacity=0.2)
fig.update_layout(height=500, xaxis_rangeslider_visible=False)
st.plotly_chart(fig, use_container_width=True)

if st.button("🔄 Refresh Real"):
    st.cache_data.clear()
    st.rerun()

if st.button("📲 Test WhatsApp Real"):
    send_whatsapp(f"✅ REAL data connected! Gold ${price:.2f}")
    st.success("Sent!")
