import streamlit as st
import pandas as pd, requests, urllib.parse
import plotly.graph_objects as go

st.set_page_config(page_title="Pluto FAST", layout="wide")
st.title("🔱 Pluto FAST - BUY/SELL + SL/TP")

PHONE = st.secrets.get("WHATSAPP_PHONE", "")
APIKEY = st.secrets.get("WHATSAPP_APIKEY", "")

def send_wa(m):
    try:
        url = f"https://api.callmebot.com/whatsapp.php?phone={PHONE}&text={urllib.parse.quote(m)}&apikey={APIKEY}"
        requests.get(url, timeout=10)
    except: pass

@st.cache_data(ttl=45)
def get_data():
    base = "https://data-api.binance.vision"
    m15 = requests.get(f"{base}/api/v3/klines?symbol=PAXGUSDT&interval=15m&limit=80", timeout=8).json()
    h1 = requests.get(f"{base}/api/v3/klines?symbol=PAXGUSDT&interval=1h&limit=80", timeout=8).json()
    m15_df = pd.DataFrame(m15, columns=['T','O','H','L','C','V','CT','QV','Tr','TB','TQ','I'])
    h1_df = pd.DataFrame(h1, columns=['T','O','H','L','C','V','CT','QV','Tr','TB','TQ','I'])
    for df in [m15_df, h1_df]:
        df['T']=pd.to_datetime(df['T'], unit='ms')
        df[['O','H','L','C']]=df[['O','H','L','C']].astype(float)
    return float(m15_df['C'].iloc[-1]), h1_df, m15_df

try:
    with st.spinner("Loading REAL gold... 3 sec"):
        price,h1,m15 = get_data()
except:
    st.error("Binance slow - tap Retry")
    if st.button("🔄 Retry Fast"):
        st.cache_data.clear()
        st.rerun()
    st.stop()

h_hi=float(h1['H'].max()); h_lo=float(h1['L'].min())
buy_tp=h_lo+(h_hi-h_lo)*0.618
sell_tp=h_hi-(h_hi-h_lo)*0.618
m_hi=float(m15['H'].tail(60).max()); m_lo=float(m15['L'].tail(60).min())
buy_e_low=m_lo+(m_hi-m_lo)*0.236; buy_e_high=m_lo+(m_hi-m_lo)*0.382
sell_e_low=m_lo+(m_hi-m_lo)*0.618; sell_e_high=m_lo+(m_hi-m_lo)*0.764

# SIGNAL
if price < buy_tp and buy_e_low <= price <= buy_e_high:
    sig="BUY"; sl=m_lo-2.5; tp=buy_tp
elif price > sell_tp and sell_e_low <= price <= sell_e_high:
    sig="SELL"; sl=m_hi+2.5; tp=sell_tp
else:
    sig="WAIT"

c1,c2,c3=st.columns(3)
c1.metric("GOLD", f"${price:.2f}"); c2.metric("BUY TP", f"${buy_tp:.2f}"); c3.metric("SELL TP", f"${sell_tp:.2f}")

if sig=="BUY":
    rr=(tp-price)/(price-sl) if price!=sl else 0
    st.success(f"🔥 BUY NOW @ ${price:.2f} | SL ${sl:.2f} | TP ${tp:.2f} | RR 1:{rr:.1f}")
    send_wa(f"🔥 BUY Gold ${price:.2f} SL {sl:.2f} TP {tp:.2f}")
    st.balloons()
elif sig=="SELL":
    rr=(price-tp)/(sl-price) if sl!=price else 0
    st.error(f"🔻 SELL NOW @ ${price:.2f} | SL ${sl:.2f} | TP ${tp:.2f} | RR 1:{rr:.1f}")
    send_wa(f"🔻 SELL Gold ${price:.2f} SL {sl:.2f} TP {tp:.2f}")
else:
    st.info(f"⏳ {sig} - Price ${price:.2f} not in entry yet. BUY zone ${buy_e_low:.1f}-${buy_e_high:.1f}")

fig=go.Figure(data=[go.Candlestick(x=m15['T'], open=m15['O'], high=m15['H'], low=m15['L'], close=m15['C'])])
fig.add_hline(y=buy_tp, line_color="red", line_dash="dash")
fig.add_hrect(y0=buy_e_low, y1=buy_e_high, fillcolor="green", opacity=0.3)
fig.add_hrect(y0=sell_e_low, y1=sell_e_high, fillcolor="red", opacity=0.15)
fig.update_layout(height=480, xaxis_rangeslider_visible=False, template="plotly_dark", margin=dict(l=0,r=0,t=10,b=0))
st.plotly_chart(fig, use_container_width=True)

if st.button("🔄 Refresh Now"):
    st.cache_data.clear()
    st.rerun()
