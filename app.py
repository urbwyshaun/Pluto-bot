import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import requests, urllib.parse

st.set_page_config(page_title="Pluto FX REAL", layout="wide")
st.title("🔱 Pluto FX - REAL GOLD")

PHONE = st.secrets.get("WHATSAPP_PHONE", "")
APIKEY = st.secrets.get("WHATSAPP_APIKEY", "")

def send_whatsapp(msg):
    try:
        text = urllib.parse.quote(msg)
        url = f"https://api.callmebot.com/whatsapp.php?phone={PHONE}&text={text}&apikey={APIKEY}"
        r = requests.get(url, timeout=15)
        return "api" in r.text.lower() or r.status_code==200
    except Exception as e:
        st.error(f"WA error: {e}")
        return False

@st.cache_data(ttl=60)
def get_paxg():
    endpoints = ["https://data-api.binance.vision","https://api.binance.com","https://api1.binance.com"]
    for base in endpoints:
        try:
            r1 = requests.get(f"{base}/api/v3/klines?symbol=PAXGUSDT&interval=15m&limit=100", timeout=10).json()
            r2 = requests.get(f"{base}/api/v3/klines?symbol=PAXGUSDT&interval=1h&limit=100", timeout=10).json()
            if isinstance(r1, list) and len(r1)>10:
                m15 = pd.DataFrame(r1, columns=['Time','Open','High','Low','Close','Vol','CT','QV','Tr','TB','TQ','I'])
                m15['Time']=pd.to_datetime(m15['Time'], unit='ms')
                m15[['Open','High','Low','Close']]=m15[['Open','High','Low','Close']].astype(float)
                h1 = pd.DataFrame(r2, columns=['Time','Open','High','Low','Close','Vol','CT','QV','Tr','TB','TQ','I'])
                h1['Time']=pd.to_datetime(h1['Time'], unit='ms')
                h1[['Open','High','Low','Close']]=h1[['Open','High','Low','Close']].astype(float)
                price=float(m15['Close'].iloc[-1])
                return price,h1,m15
        except: continue
    r = requests.get("https://api.gold-api.com/price/XAU", timeout=10).json()
    price=float(r['price'])
    return price, pd.DataFrame(), pd.DataFrame()

try:
    price,h1,m15 = get_paxg()
    if m15.empty: raise Exception("No candles")
except:
    st.error("Loading... tap Refresh")
    if st.button("🔄 Retry Now"):
        st.cache_data.clear()
        st.rerun()
    st.stop()

h_high=float(h1['High'].max()); h_low=float(h1['Low'].min())
main_618=h_low+(h_high-h_low)*0.618
m_high=float(m15['High'].tail(80).max()); m_low=float(m15['Low'].tail(80).min())
entry_low=m_low+(m_high-m_low)*0.236
entry_high=m_low+(m_high-m_low)*0.382

c1,c2,c3=st.columns(3)
c1.metric("GOLD", f"${price:,.2f}"); c2.metric("Main 61.8%", f"${main_618:,.2f}"); c3.metric("Entry", f"${entry_low:.2f}-{entry_high:.2f}")

if price < main_618 and entry_low <= price <= entry_high:
    st.warning("🔥 ENTRY NOW!"); st.balloons()
    send_whatsapp(f"🔥 PLUTO ENTRY: Gold ${price:.2f} Zone {entry_low:.1f}-{entry_high:.1f}")
elif price < main_618:
    st.success("✅ Break Done")
else:
    st.info("Waiting for break...")

fig=go.Figure(data=[go.Candlestick(x=m15['Time'], open=m15['Open'], high=m15['High'], low=m15['Low'], close=m15['Close'])])
fig.add_hline(y=main_618, line_dash="dash", line_color="red", annotation_text="61.8%")
fig.add_hrect(y0=entry_low, y1=entry_high, fillcolor="green", opacity=0.25)
fig.update_layout(height=500, xaxis_rangeslider_visible=False, template="plotly_dark")
st.plotly_chart(fig, use_container_width=True)

st.divider()
col1,col2 = st.columns(2)
with col1:
    if st.button("🔄 Refresh Price"):
        st.cache_data.clear()
        st.rerun()
with col2:
    if st.button("📲 Test WhatsApp Now"):
        ok = send_whatsapp(f"✅ PLUTO TEST OK! Gold ${price:.2f} - Your bot is LIVE")
        if ok:
            st.success(f"Message sent to {PHONE}! Check WhatsApp")
        else:
            st.error("Failed - Check Secrets saved")
