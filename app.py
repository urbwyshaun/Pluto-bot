import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import requests, urllib.parse
from streamlit_autorefresh import st_autorefresh

st.set_page_config(page_title="Pluto FX PRO", layout="wide")

# Auto refresh every 60 seconds
st_autorefresh(interval=60 * 1000, key="goldrefresh")

st.title("🔱 Pluto FX PRO - Auto BUY/SELL + SL/TP")

PHONE = st.secrets.get("WHATSAPP_PHONE", "")
APIKEY = st.secrets.get("WHATSAPP_APIKEY", "")

def send_whatsapp(msg):
    try:
        text = urllib.parse.quote(msg)
        url = f"https://api.callmebot.com/whatsapp.php?phone={PHONE}&text={text}&apikey={APIKEY}"
        requests.get(url, timeout=10)
        return True
    except: return False

@st.cache_data(ttl=50)
def get_paxg():
    for base in ["https://data-api.binance.vision","https://api.binance.com"]:
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
                return float(m15['Close'].iloc[-1]), h1, m15
        except: continue
    return 0, pd.DataFrame(), pd.DataFrame()

price,h1,m15 = get_paxg()
if price==0 or m15.empty:
    st.error("Loading... auto retrying in 60s")
    st.stop()

# LEVELS
h_high=float(h1['High'].max()); h_low=float(h1['Low'].min())
main_buy_level = h_low + (h_high - h_low)*0.618  # Price must be below this to BUY
main_sell_level = h_high - (h_high - h_low)*0.618  # Price must be above this to SELL

m_high=float(m15['High'].tail(80).max()); m_low=float(m15['Low'].tail(80).min())
entry_buy_low = m_low + (m_high-m_low)*0.236
entry_buy_high = m_low + (m_high-m_low)*0.382
entry_sell_low = m_low + (m_high-m_low)*0.618
entry_sell_high = m_low + (m_high-m_low)*0.764

# LOGIC
signal = "WAIT"
sl=tp=0
if price < main_buy_level and entry_buy_low <= price <= entry_buy_high:
    signal = "BUY"
    sl = m_low - 3.0  # 3 dollars below low
    tp = main_buy_level
elif price > main_sell_level and entry_sell_low <= price <= entry_sell_high:
    signal = "SELL"
    sl = m_high + 3.0
    tp = main_sell_level
elif price < main_buy_level:
    signal = "BREAK DONE - WAITING FOR ENTRY"
else:
    signal = "WAITING FOR MAIN BREAK"

# UI
c1,c2,c3,c4 = st.columns(4)
c1.metric("GOLD LIVE", f"${price:,.2f}")
c2.metric("Main BUY < ", f"${main_buy_level:,.2f}")
c3.metric("Main SELL > ", f"${main_sell_level:,.2f}")
c4.metric("Auto-Refresh", "ON 60s")

if signal=="BUY":
    st.success(f"🔥 {signal} SIGNAL NOW!")
    st.balloons()
    risk = price - sl
    reward = tp - price
    rr = reward/risk if risk!=0 else 0
    st.markdown(f"""
    ### ✅ TAKE BUY ON EXNESS M15 NOW
    **Entry Price:** ${price:,.2f}
    **Stop Loss:** ${sl:,.2f} (Below low + buffer)
    **Take Profit:** ${tp:,.2f} (Main 61.8%)
    **Risk:** ${risk:,.2f} | **Reward:** ${reward:,.2f} | **RR:** 1:{rr:.1f}
    """)
    send_whatsapp(f"🔥 PLUTO BUY NOW! Entry ${price:.2f} SL ${sl:.2f} TP ${tp:.2f} RR 1:{rr:.1f}")
    
elif signal=="SELL":
    st.error(f"🔥 {signal} SIGNAL NOW!")
    risk = sl - price
    reward = price - tp
    rr = reward/risk if risk!=0 else 0
    st.markdown(f"""
    ### 🔻 TAKE SELL ON EXNESS M15 NOW
    **Entry Price:** ${price:,.2f}
    **Stop Loss:** ${sl:,.2f}
    **Take Profit:** ${tp:,.2f}
    **RR:** 1:{rr:.1f}
    """)
    send_whatsapp(f"🔻 PLUTO SELL NOW! Entry ${price:.2f} SL ${sl:.2f} TP ${tp:.2f}")

else:
    st.info(f"⏳ {signal} | Gold ${price:.2f}")

fig=go.Figure(data=[go.Candlestick(x=m15['Time'], open=m15['Open'], high=m15['High'], low=m15['Low'], close=m15['Close'])])
fig.add_hline(y=main_buy_level, line_dash="dash", line_color="red", annotation_text="BUY TP / Main 61.8%")
fig.add_hline(y=main_sell_level, line_dash="dash", line_color="orange", annotation_text="SELL TP")
fig.add_hrect(y0=entry_buy_low, y1=entry_buy_high, fillcolor="green", opacity=0.25, annotation_text="BUY ENTRY")
fig.add_hrect(y0=entry_sell_low, y1=entry_sell_high, fillcolor="red", opacity=0.15, annotation_text="SELL ENTRY")
fig.update_layout(height=550, xaxis_rangeslider_visible=False, template="plotly_dark")
st.plotly_chart(fig, use_container_width=True)

if st.button("📲 Test WhatsApp Alert"):
    send_whatsapp(f"✅ PRO BOT TEST - Gold ${price:.2f} Auto refresh ON. You will get BUY/SELL with SL/TP!")
    st.success("Sent!")

st.caption("Auto refreshes every 60 seconds. Keep tab open during London (10am-1pm) and NY (3pm-6pm) CAT.")
