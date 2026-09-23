import streamlit as st
import pandas as pd, requests, urllib.parse
import plotly.graph_objects as go
from plotly.subplots import make_subplots

st.set_page_config(page_title="Pluto MT5 CHART", layout="wide")
st.title("🔱 Pluto GOLD - MT5 FULL CHART + FIB")

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
df = m15 # chart = 15m for swing

h_hi=float(h1['H'].max()); h_lo=float(h1['L'].min())
diff = h_hi - h_lo
fibs = {
    "0% (TOP)": h_hi,
    "23.6%": h_lo + diff*0.764,
    "38.2%": h_lo + diff*0.618,
    "50%": h_lo + diff*0.5,
    "61.8% GOLDEN": h_lo + diff*0.382,
    "78.6%": h_lo + diff*0.236,
    "100% (BOTTOM)": h_lo,
}
buy_tp = fibs["38.2%"]
sell_tp = fibs["61.8% GOLDEN"]
m_hi=float(df['H'].tail(60).max()); m_lo=float(df['L'].tail(60).min())
buy_low=m_lo+(m_hi-m_lo)*0.236; buy_high=m_lo+(m_hi-m_lo)*0.382
sell_low=m_lo+(m_hi-m_lo)*0.618; sell_high=m_lo+(m_hi-m_lo)*0.764

st.metric("GOLD LIVE", f"${price:.2f}")

# --- MT5 STYLE CHART ---
fig = make_subplots(rows=2, cols=1, shared_xaxes=True, vertical_spacing=0.02, row_heights=[0.8,0.2])

fig.add_trace(go.Candlestick(x=df['T'], open=df['O'], high=df['H'], low=df['L'], close=df['C'], name="XAUUSD"), row=1, col=1)
fig.add_trace(go.Scatter(x=df['T'], y=df['EMA50'], line=dict(color='orange', width=1), name="EMA 50"), row=1, col=1)
fig.add_trace(go.Scatter(x=df['T'], y=df['EMA200'], line=dict(color='blue', width=1.5), name="EMA 200"), row=1, col=1)

# FIB LINES like MT5
colors = {"0% (TOP)":"#ffffff","23.6%":"#ffeb3b","38.2%":"#00ff00","50%":"#00bcd4","61.8% GOLDEN":"#ff9800","78.6%":"#f44336","100% (BOTTOM)":"#ffffff"}
for label, level in fibs.items():
    fig.add_hline(y=level, line_dash="dot", line_color=colors[label], annotation_text=f"{label} ${level:.1f}", annotation_position="right", row=1, col=1)

fig.add_hrect(y0=buy_low, y1=buy_high, fillcolor="green", opacity=0.2, line_width=0, annotation_text="BUY ZONE", row=1, col=1)
fig.add_hrect(y0=sell_low, y1=sell_high, fillcolor="red", opacity=0.15, line_width=0, annotation_text="SELL ZONE", row=1, col=1)

# Volume like MT5
fig.add_trace(go.Bar(x=df['T'], y=df['V'], name="Volume", marker_color='gray'), row=2, col=1)

fig.update_layout(height=700, template="plotly_dark", xaxis_rangeslider_visible=False, showlegend=True, margin=dict(l=0,r=0,t=20,b=0), dragmode='pan')
fig.update_yaxes(title_text="Price", row=1, col=1)
fig.update_yaxes(title_text="Vol", row=2, col=1)
st.plotly_chart(fig, use_container_width=True, config={'scrollZoom': True, 'displayModeBar': True})

# SIGNALS
st.divider()
if buy_low <= price <= buy_high:
    st.success(f"🔥 BUY SIGNAL @ ${price:.2f} -> TP ${buy_tp:.2f} | SL ${m_lo-1.5:.2f}")
elif sell_low <= price <= sell_high:
    st.error(f"🔻 SELL SIGNAL @ ${price:.2f} -> TP ${sell_tp:.2f} | SL ${m_hi+1.5:.2f}")
else:
    st.info(f"⏳ WAIT | Price ${price:.2f} | BUY {buy_low:.1f}-{buy_high:.1f} | SELL {sell_low:.1f}-{sell_high:.1f}")

if st.button("🔄 Refresh Chart"): st.cache_data.clear(); st.rerun()

st.markdown("<script>setTimeout(()=>{window.location.reload()}, 30000);</script>", unsafe_allow_html=True)
