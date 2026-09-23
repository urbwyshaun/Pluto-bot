import streamlit as st
import pandas as pd, requests, urllib.parse
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from datetime import datetime
import pytz

st.set_page_config(page_title="Pluto MT5 ULTRA", layout="wide")
st.title("🔱 Pluto MT5 ULTRA - Chart + WhatsApp")

PHONE = st.secrets.get("WHATSAPP_PHONE", "")
APIKEY = st.secrets.get("WHATSAPP_APIKEY", "")

def send_wa(m):
    try:
        url = f"https://api.callmebot.com/whatsapp.php?phone={PHONE}&text={urllib.parse.quote(m)}&apikey={APIKEY}"
        requests.get(url, timeout=8)
        return True
    except: return False

# ACCOUNT
st.sidebar.header("💰 Account")
balance = st.sidebar.number_input("Balance $", value=50.0, step=5.0)
risk_pct = st.sidebar.slider("Risk %", 1.0, 5.0, 2.0)

# TIME
sast = pytz.timezone('Africa/Johannesburg')
now_sast = datetime.now(sast)
is_active = 10 <= now_sast.hour <= 23

@st.cache_data(ttl=30)
def get_data():
    base = "https://data-api.binance.vision"
    m15 = requests.get(f"{base}/api/v3/klines?symbol=PAXGUSDT&interval=15m&limit=120", timeout=7).json()
    h1 = requests.get(f"{base}/api/v3/klines?symbol=PAXGUSDT&interval=1h&limit=120", timeout=7).json()
    def to_df(d):
        df=pd.DataFrame(d, columns=['T','O','H','L','C','V','CT','QV','Tr','TB','TQ','I'])
        df['T']=pd.to_datetime(df['T'], unit='ms')
        df[['O','H','L','C','V']]=df[['O','H','L','C','V']].astype(float)
        df['EMA50']=df['C'].ewm(span=50).mean()
        df['EMA200']=df['C'].ewm(span=200).mean()
        return df
    return to_df(m15), to_df(h1)

m15,h1 = get_data()
price = float(m15['C'].iloc[-1])
df = m15

h_hi=float(h1['H'].max()); h_lo=float(h1['L'].min()); diff=h_hi-h_lo
fibs = {"0% TOP": h_hi,"23.6%": h_lo+diff*0.764,"38.2%": h_lo+diff*0.618,"50%": h_lo+diff*0.5,"61.8% GOLDEN": h_lo+diff*0.382,"78.6%": h_lo+diff*0.236,"100% BOT": h_lo}
buy_tp=fibs["38.2%"]; sell_tp=fibs["61.8% GOLDEN"]
m_hi=float(df['H'].tail(60).max()); m_lo=float(df['L'].tail(60).min())
buy_low=m_lo+(m_hi-m_lo)*0.236; buy_high=m_lo+(m_hi-m_lo)*0.382
sell_low=m_lo+(m_hi-m_lo)*0.618; sell_high=m_lo+(m_hi-m_lo)*0.764

def calc_rr(entry, sl, tp, is_buy):
    return (tp-entry)/(entry-sl) if is_buy and entry!=sl else (entry-tp)/(sl-entry) if sl!=entry else 0

rr_buy = calc_rr(price, m_lo-1.5, buy_tp, True) if buy_low <= price <= buy_high else 0
rr_sell = calc_rr(price, m_hi+1.5, sell_tp, False) if sell_low <= price <= sell_high else 0

if price < buy_tp and buy_low <= price <= buy_high and rr_buy>=2.0:
    sig="BUY"; sl=m_lo-1.5; tp=buy_tp; rr=rr_buy
elif price > sell_tp and sell_low <= price <= sell_high and rr_sell>=2.0:
    sig="SELL"; sl=m_hi+1.5; tp=sell_tp; rr=rr_sell
else:
    sig="WAIT"; sl=0; tp=0; rr=0

sl_dist = abs(price-sl) if sig!="WAIT" else 1.5
risk_money = balance*(risk_pct/100)
lot_raw = risk_money/sl_dist/100 if sl_dist>0 else 0.01
lot = max(0.01, round(lot_raw,2))

c1,c2,c3=st.columns(3)
c1.metric("GOLD", f"${price:.2f}"); c2.metric("Session", f"{'ACTIVE ✅' if is_active else 'SLEEP 💤'}"); c3.metric("LOT", f"{lot}")

# SIGNALS + WHATSAPP
if sig=="BUY" and is_active:
    st.success(f"🔥 BUY NOW @ ${price:.2f} RR 1:{rr:.1f} LOT {lot} SL {sl:.2f} TP {tp:.2f}")
    if send_wa(f"🔥 BUY Gold ${price:.2f} LOT {lot} SL {sl:.2f} TP {tp:.2f} RR 1:{rr:.1f}"): st.toast("WhatsApp Sent!")
    st.balloons(); st.audio("https://actions.google.com/sounds/v1/alarms/beep_short.ogg")
    st.code(f"Deriv BUY {lot} lot\nSL {sl:.2f}\nTP {tp:.2f}", language="text")
    st.markdown(f"""<button onclick="navigator.clipboard.writeText('BUY {lot} SL {sl:.2f} TP {tp:.2f}')" style="width:100%;padding:12px;background:#00ff88;color:black;border-radius:8px;font-weight:bold;">📋 COPY FOR DERIV</button>""", unsafe_allow_html=True)
    st.link_button("🚀 OPEN DERIV", "https://mt5.deriv.com/", use_container_width=True)
elif sig=="SELL" and is_active:
    st.error(f"🔻 SELL NOW @ ${price:.2f} RR 1:{rr:.1f} LOT {lot} SL {sl:.2f} TP {tp:.2f}")
    if send_wa(f"🔻 SELL Gold ${price:.2f} LOT {lot} SL {sl:.2f} TP {tp:.2f} RR 1:{rr:.1f}"): st.toast("WhatsApp Sent!")
    st.audio("https://actions.google.com/sounds/v1/alarms/beep_short.ogg")
    st.code(f"Deriv SELL {lot} lot\nSL {sl:.2f}\nTP {tp:.2f}", language="text")
    st.markdown(f"""<button onclick="navigator.clipboard.writeText('SELL {lot} SL {sl:.2f} TP {tp:.2f}')" style="width:100%;padding:12px;background:#ff4444;color:white;border-radius:8px;font-weight:bold;">📋 COPY FOR DERIV</button>""", unsafe_allow_html=True)
    st.link_button("🚀 OPEN DERIV", "https://mt5.deriv.com/", use_container_width=True)
else:
    st.info(f"⏳ WAIT - BUY {buy_low:.1f}-{buy_high:.1f} RR {rr_buy:.1f} | SELL {sell_low:.1f}-{sell_high:.1f} RR {rr_sell:.1f}")

# FULL CHART
fig = make_subplots(rows=2, cols=1, shared_xaxes=True, vertical_spacing=0.02, row_heights=[0.8,0.2])
fig.add_trace(go.Candlestick(x=df['T'], open=df['O'], high=df['H'], low=df['L'], close=df['C'], name="XAUUSD"), row=1, col=1)
fig.add_trace(go.Scatter(x=df['T'], y=df['EMA50'], line=dict(color='orange', width=1), name="EMA50"), row=1, col=1)
fig.add_trace(go.Scatter(x=df['T'], y=df['EMA200'], line=dict(color='cyan', width=1.5), name="EMA200"), row=1, col=1)
for label, lvl in fibs.items():
    fig.add_hline(y=lvl, line_dash="dot", line_color="yellow" if "61.8" in label or "38.2" in label else "gray", annotation_text=f"{label} {lvl:.1f}", annotation_position="right", row=1, col=1)
fig.add_hrect(y0=buy_low, y1=buy_high, fillcolor="green", opacity=0.25, line_width=0, row=1, col=1)
fig.add_hrect(y0=sell_low, y1=sell_high, fillcolor="red", opacity=0.2, line_width=0, row=1, col=1)
fig.add_trace(go.Bar(x=df['T'], y=df['V'], marker_color='gray', name="Vol"), row=2, col=1)
fig.update_layout(height=650, template="plotly_dark", xaxis_rangeslider_visible=False, margin=dict(l=0,r=0,t=10,b=0))
st.plotly_chart(fig, use_container_width=True, config={'scrollZoom': True})

col1,col2=st.columns(2)
with col1:
    if st.button("🔄 Refresh", use_container_width=True): st.cache_data.clear(); st.rerun()
with col2:
    if st.button("📲 Test WhatsApp", use_container_width=True):
        ok=send_wa(f"✅ Pluto MT5 TEST Gold ${price:.2f} Lot {lot}")
        st.success("WhatsApp Sent!" if ok else "Check Secrets PHONE/APIKEY")
