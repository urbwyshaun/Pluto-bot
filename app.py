import streamlit as st
import pandas as pd, requests, urllib.parse
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from datetime import datetime
import pytz

st.set_page_config(page_title="Pluto FINAL ALL", layout="wide")
st.title("🔱 Pluto FINAL - MT5 + WhatsApp + Live P/L + Journal")

PHONE = st.secrets.get("WHATSAPP_PHONE", "")
APIKEY = st.secrets.get("WHATSAPP_APIKEY", "")
def send_wa(m):
    try:
        requests.get(f"https://api.callmebot.com/whatsapp.php?phone={PHONE}&text={urllib.parse.quote(m)}&apikey={APIKEY}", timeout=8)
    except: pass

if 'trades' not in st.session_state: st.session_state.trades=[]
if 'active_trade' not in st.session_state: st.session_state.active_trade=None

st.sidebar.header("💰 Account")
balance = st.sidebar.number_input("Balance $", value=50.0, step=5.0)
risk_pct = st.sidebar.slider("Risk %", 1.0, 5.0, 2.0)

sast = pytz.timezone('Africa/Johannesburg')
now_sast = datetime.now(sast)
is_active = 10 <= now_sast.hour <= 23

@st.cache_data(ttl=20)
def get_data():
    base="https://data-api.binance.vision"
    m15=requests.get(f"{base}/api/v3/klines?symbol=PAXGUSDT&interval=15m&limit=120", timeout=7).json()
    h1=requests.get(f"{base}/api/v3/klines?symbol=PAXGUSDT&interval=1h&limit=120", timeout=7).json()
    def to_df(d):
        df=pd.DataFrame(d, columns=['T','O','H','L','C','V','CT','QV','Tr','TB','TQ','I'])
        df['T']=pd.to_datetime(df['T'], unit='ms')
        df[['O','H','L','C','V']]=df[['O','H','L','C','V']].astype(float)
        df['EMA50']=df['C'].ewm(span=50).mean(); df['EMA200']=df['C'].ewm(span=200).mean()
        return df
    return to_df(m15), to_df(h1)

m15,h1=get_data(); price=float(m15['C'].iloc[-1]); df=m15

h_hi=float(h1['H'].max()); h_lo=float(h1['L'].min()); diff=h_hi-h_lo
fibs={"0% TOP":h_hi,"23.6%":h_lo+diff*0.764,"38.2% BUY TP":h_lo+diff*0.618,"50%":h_lo+diff*0.5,"61.8% SELL TP":h_lo+diff*0.382,"78.6%":h_lo+diff*0.236,"100% BOT":h_lo}
buy_tp=fibs["38.2% BUY TP"]; sell_tp=fibs["61.8% SELL TP"]
m_hi=float(df['H'].tail(60).max()); m_lo=float(df['L'].tail(60).min())
buy_low=m_lo+(m_hi-m_lo)*0.236; buy_high=m_lo+(m_hi-m_lo)*0.382
sell_low=m_lo+(m_hi-m_lo)*0.618; sell_high=m_lo+(m_hi-m_lo)*0.764

def calc_rr(e,sl,tp,buy): return (tp-e)/(e-sl) if buy and e!=sl else (e-tp)/(sl-e) if sl!=e else 0
rr_buy=calc_rr(price,m_lo-1.5,buy_tp,True) if buy_low<=price<=buy_high else 0
rr_sell=calc_rr(price,m_hi+1.5,sell_tp,False) if sell_low<=price<=sell_high else 0

if price<buy_tp and buy_low<=price<=buy_high and rr_buy>=2.0: sig="BUY"; sl=m_lo-1.5; tp=buy_tp; rr=rr_buy
elif price>sell_tp and sell_low<=price<=sell_high and rr_sell>=2.0: sig="SELL"; sl=m_hi+1.5; tp=sell_tp; rr=rr_sell
else: sig="WAIT"; sl=0; tp=0; rr=0

risk_money=balance*(risk_pct/100); lot=max(0.01, round((risk_money/abs(price-sl)/100) if sig!="WAIT" and price!=sl else 0.01,2))

# --- LIVE LOGIC (NEW but not removing old) ---
if sig in ["BUY","SELL"] and st.session_state.active_trade is None and is_active:
    st.session_state.active_trade={"type":sig,"entry":price,"sl":sl,"tp":tp,"lot":lot,"time":now_sast.strftime("%H:%M %d/%m"),"rr":rr}
    send_wa(f"🔥 NEW {sig} @ ${price:.2f} LOT {lot} SL {sl:.2f} TP {tp:.2f}")

pnl_live="None"
if st.session_state.active_trade:
    at=st.session_state.active_trade
    run = (price-at['entry'])*(at['lot']/0.01) if at['type']=="BUY" else (at['entry']-price)*(at['lot']/0.01)
    pnl_live = f"{'🟢 +$' if run>0 else '🔴 $'}{run:.2f}"
    # Auto close check
    closed=False
    if at['type']=="BUY":
        if price>=at['tp']: at.update({"result":"WIN","pnl":(at['tp']-at['entry'])*(at['lot']/0.01),"close_price":at['tp'],"close_time":now_sast.strftime("%H:%M")}); closed=True
        elif price<=at['sl']: at.update({"result":"LOSS","pnl":(at['sl']-at['entry'])*(at['lot']/0.01),"close_price":at['sl'],"close_time":now_sast.strftime("%H:%M")}); closed=True
    else:
        if price<=at['tp']: at.update({"result":"WIN","pnl":(at['entry']-at['tp'])*(at['lot']/0.01),"close_price":at['tp'],"close_time":now_sast.strftime("%H:%M")}); closed=True
        elif price>=at['sl']: at.update({"result":"LOSS","pnl":(at['entry']-at['sl'])*(at['lot']/0.01),"close_price":at['sl'],"close_time":now_sast.strftime("%H:%M")}); closed=True
    if closed:
        st.session_state.trades.append(at); 
        send_wa(f"{'✅ WIN' if at['result']=='WIN' else '❌ LOSS'} {at['type']} {at['pnl']:.2f}")
        st.session_state.active_trade=None

# TOP BAR
c1,c2,c3,c4=st.columns(4)
c1.metric("GOLD", f"${price:.2f}"); c2.metric("LIVE P/L", pnl_live); c3.metric("LOT", lot); c4.metric("Session", "ACTIVE ✅" if is_active else "SLEEP 💤")

if st.session_state.active_trade:
    at=st.session_state.active_trade
    st.warning(f"📈 LIVE {at['type']} | Entry ${at['entry']:.2f} -> Now ${price:.2f} | {pnl_live} | SL ${at['sl']:.2f} TP ${at['tp']:.2f} RR 1:{at['rr']:.1f}")
    st.code(f"{at['type']} XAUUSD {at['lot']} lot\nEntry {at['entry']:.2f}\nSL {at['sl']:.2f}\nTP {at['tp']:.2f}\nRR 1:{at['rr']:.1f}\nRunning {pnl_live}", language="text")
    st.markdown(f"<button onclick=\"navigator.clipboard.writeText('{at['type']} {at['lot']} SL {at['sl']:.2f} TP {at['tp']:.2f}')\" style='width:100%;padding:12px;background:#00ff88;color:black;border-radius:8px;font-weight:bold;'>📋 COPY FOR DERIV</button>", unsafe_allow_html=True)
    st.link_button("🚀 OPEN DERIV MT5", "https://mt5.deriv.com/", use_container_width=True)
elif sig=="BUY": st.success(f"🔥 BUY SIGNAL ${price:.2f} RR 1:{rr:.1f}")
elif sig=="SELL": st.error(f"🔻 SELL SIGNAL ${price:.2f} RR 1:{rr:.1f}")
else: st.info(f"⏳ WAIT | BUY {buy_low:.1f}-{buy_high:.1f} RR {rr_buy:.1f} | SELL {sell_low:.1f}-{sell_high:.1f} RR {rr_sell:.1f}")

# CHART - OLD MT5 FULL KEPT
fig=make_subplots(rows=2, cols=1, shared_xaxes=True, vertical_spacing=0.03, row_heights=[0.8,0.2])
fig.add_trace(go.Candlestick(x=df['T'], open=df['O'], high=df['H'], low=df['L'], close=df['C'], name="XAUUSD"), row=1, col=1)
fig.add_trace(go.Scatter(x=df['T'], y=df['EMA50'], line=dict(color='orange',width=1), name="EMA50"), row=1, col=1)
fig.add_trace(go.Scatter(x=df['T'], y=df['EMA200'], line=dict(color='cyan',width=1.5), name="EMA200"), row=1, col=1)
for label,lvl in fibs.items():
    col="yellow" if "TP" in label else "gray"
    fig.add_hline(y=lvl, line_dash="dot", line_color=col, annotation_text=f"{label} {lvl:.1f}", annotation_position="right", row=1, col=1)
fig.add_hrect(y0=buy_low, y1=buy_high, fillcolor="green", opacity=0.2, line_width=0, row=1, col=1)
fig.add_hrect(y0=sell_low, y1=sell_high, fillcolor="red", opacity=0.15, line_width=0, row=1, col=1)
if st.session_state.active_trade:
    at=st.session_state.active_trade
    fig.add_hline(y=at['entry'], line_color="white", line_width=2, row=1, col=1)
    fig.add_hline(y=at['sl'], line_color="red", line_dash="dash", row=1, col=1)
    fig.add_hline(y=at['tp'], line_color="green", line_dash="dash", row=1, col=1)
fig.add_trace(go.Bar(x=df['T'], y=df['V'], marker_color='gray', name="Vol"), row=2, col=1)
fig.update_layout(height=650, template="plotly_dark", xaxis_rangeslider_visible=False, margin=dict(l=0,r=0,t=10,b=0))
st.plotly_chart(fig, use_container_width=True, config={'scrollZoom': True})

# JOURNAL - NEW
if st.session_state.trades:
    df_t=pd.DataFrame(st.session_state.trades)
    wins=len(df_t[df_t['result']=="WIN"]); total=len(df_t); pnl_total=df_t['pnl'].sum()
    st.divider(); st.subheader(f"📊 YOUR 5 TP CHALLENGE: {wins}/{total} WINS | {wins/5*100:.0f}% to GOAL | Total ${pnl_total:.2f}")
    st.progress(min(wins/5,1.0))
    st.dataframe(df_t[['time','type','entry','close_price','pnl','result','rr','lot']], use_container_width=True)
else:
    st.caption("No closed trades yet - your first BUY is still running, will auto-log when TP/SL hits")

col1,col2=st.columns(2)
with col1:
    if st.button("🔄 Refresh", use_container_width=True): st.cache_data.clear(); st.rerun()
with col2:
    if st.button("📲 Test WhatsApp", use_container_width=True): send_wa(f"✅ FINAL TEST ${price:.2f} Live {pnl_live}"); st.success("Sent!")

st.markdown("<script>setTimeout(()=>{window.location.reload()}, 15000);</script>", unsafe_allow_html=True)
import streamlit as st
import pandas as pd, requests, urllib.parse
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from datetime import datetime
import pytz

st.set_page_config(page_title="Pluto MT5 Tabs", layout="wide")
st.markdown("""
<style>
.stTabs [data-baseweb="tab-list"] { gap: 10px; }
.stTabs [data-baseweb="tab"] { height: 50px; padding: 10px 30px; font-weight: bold; }
</style>
""", unsafe_allow_html=True)

PHONE = st.secrets.get("WHATSAPP_PHONE", "")
APIKEY = st.secrets.get("WHATSAPP_APIKEY", "")
def send_wa(m):
    try: requests.get(f"https://api.callmebot.com/whatsapp.php?phone={PHONE}&text={urllib.parse.quote(m)}&apikey={APIKEY}", timeout=8)
    except: pass

if 'trades' not in st.session_state: st.session_state.trades=[]
if 'active_trade' not in st.session_state: st.session_state.active_trade=None

st.sidebar.header("💰 Account")
balance = st.sidebar.number_input("Balance $", value=50.0)
risk_pct = st.sidebar.slider("Risk %", 1.0, 5.0, 2.0)

sast = pytz.timezone('Africa/Johannesburg')
now_sast = datetime.now(sast)
is_active = 10 <= now_sast.hour <= 23

@st.cache_data(ttl=20)
def get_data():
    base="https://data-api.binance.vision"
    m15=requests.get(f"{base}/api/v3/klines?symbol=PAXGUSDT&interval=15m&limit=120", timeout=7).json()
    h1=requests.get(f"{base}/api/v3/klines?symbol=PAXGUSDT&interval=1h&limit=120", timeout=7).json()
    def to_df(d):
        df=pd.DataFrame(d, columns=['T','O','H','L','C','V','CT','QV','Tr','TB','TQ','I'])
        df['T']=pd.to_datetime(df['T'], unit='ms')
        df[['O','H','L','C','V']]=df[['O','H','L','C','V']].astype(float)
        df['EMA50']=df['C'].ewm(span=50).mean(); df['EMA200']=df['C'].ewm(span=200).mean()
        return df
    return to_df(m15), to_df(h1)

m15,h1=get_data(); price=float(m15['C'].iloc[-1]); df=m15
h_hi=float(h1['H'].max()); h_lo=float(h1['L'].min()); diff=h_hi-h_lo
fibs={"0% TOP":h_hi,"23.6%":h_lo+diff*0.764,"38.2% BUY TP":h_lo+diff*0.618,"50%":h_lo+diff*0.5,"61.8% SELL TP":h_lo+diff*0.382,"78.6%":h_lo+diff*0.236,"100% BOT":h_lo}
buy_tp=fibs["38.2% BUY TP"]; sell_tp=fibs["61.8% SELL TP"]
m_hi=float(df['H'].tail(60).max()); m_lo=float(df['L'].tail(60).min())
buy_low=m_lo+(m_hi-m_lo)*0.236; buy_high=m_lo+(m_hi-m_lo)*0.382
sell_low=m_lo+(m_hi-m_lo)*0.618; sell_high=m_lo+(m_hi-m_lo)*0.764

def calc_rr(e,sl,tp,buy): return (tp-e)/(e-sl) if buy and e!=sl else (e-tp)/(sl-e) if sl!=e else 0
rr_buy=calc_rr(price,m_lo-1.5,buy_tp,True) if buy_low<=price<=buy_high else 0
rr_sell=calc_rr(price,m_hi+1.5,sell_tp,False) if sell_low<=price<=sell_high else 0
if price<buy_tp and buy_low<=price<=buy_high and rr_buy>=2.0: sig="BUY"; sl=m_lo-1.5; tp=buy_tp; rr=rr_buy
elif price>sell_tp and sell_low<=price<=sell_high and rr_sell>=2.0: sig="SELL"; sl=m_hi+1.5; tp=sell_tp; rr=rr_sell
else: sig="WAIT"; sl=0; tp=0; rr=0
risk_money=balance*(risk_pct/100); lot=max(0.01, round((risk_money/abs(price-sl)/100) if sig!="WAIT" and price!=sl else 0.01,2))

# LIVE LOGIC
if sig in ["BUY","SELL"] and st.session_state.active_trade is None and is_active:
    st.session_state.active_trade={"type":sig,"entry":price,"sl":sl,"tp":tp,"lot":lot,"time":now_sast.strftime("%H:%M %d/%m"),"rr":rr}
    send_wa(f"🔥 NEW {sig} @ ${price:.2f} LOT {lot}")

pnl_live="None"; run=0
if st.session_state.active_trade:
    at=st.session_state.active_trade
    run = (price-at['entry'])*(at['lot']/0.01) if at['type']=="BUY" else (at['entry']-price)*(at['lot']/0.01)
    pnl_live = f"{'🟢 +$' if run>0 else '🔴 $'}{run:.2f}"
    closed=False
    if at['type']=="BUY":
        if price>=at['tp']: at.update({"result":"WIN","pnl":(at['tp']-at['entry'])*(at['lot']/0.01),"close_price":at['tp'],"close_time":now_sast.strftime("%H:%M")}); closed=True
        elif price<=at['sl']: at.update({"result":"LOSS","pnl":(at['sl']-at['entry'])*(at['lot']/0.01),"close_price":at['sl'],"close_time":now_sast.strftime("%H:%M")}); closed=True
    else:
        if price<=at['tp']: at.update({"result":"WIN","pnl":(at['entry']-at['tp'])*(at['lot']/0.01),"close_price":at['tp'],"close_time":now_sast.strftime("%H:%M")}); closed=True
        elif price>=at['sl']: at.update({"result":"LOSS","pnl":(at['entry']-at['sl'])*(at['lot']/0.01),"close_price":at['sl'],"close_time":now_sast.strftime("%H:%M")}); closed=True
    if closed:
        st.session_state.trades.append(at); send_wa(f"{'✅ WIN' if at['result']=='WIN' else '❌ LOSS'} {at['type']} {at['pnl']:.2f}")
        st.session_state.active_trade=None

# TOP INFO BAR ALWAYS VISIBLE
c1,c2,c3,c4=st.columns(4)
c1.metric("GOLD", f"${price:.2f}"); c2.metric("LIVE P/L", pnl_live); c3.metric("Session", "ACTIVE ✅" if is_active else "SLEEP 💤"); c4.metric("Signal", sig)

# === 3 TABS LIKE MT5 ===
tab1, tab2, tab3 = st.tabs(["📈 CHART (MT5)", "📊 TRADE PROGRESS", "📓 JOURNAL - 5 TP"])

with tab1:
    st.subheader("MT5 Chart - Use 2 fingers to zoom, drag to pan")
    fig=make_subplots(rows=2, cols=1, shared_xaxes=True, vertical_spacing=0.03, row_heights=[0.8,0.2])
    fig.add_trace(go.Candlestick(x=df['T'], open=df['O'], high=df['H'], low=df['L'], close=df['C'], name="XAU"), row=1, col=1)
    fig.add_trace(go.Scatter(x=df['T'], y=df['EMA50'], line=dict(color='orange',width=1), name="EMA50"), row=1, col=1)
    fig.add_trace(go.Scatter(x=df['T'], y=df['EMA200'], line=dict(color='cyan',width=1.5), name="EMA200"), row=1, col=1)
    for label,lvl in fibs.items():
        col="yellow" if "TP" in label else "gray"
        fig.add_hline(y=lvl, line_dash="dot", line_color=col, annotation_text=f"{label} {lvl:.1f}", annotation_position="right", row=1, col=1)
    fig.add_hrect(y0=buy_low, y1=buy_high, fillcolor="green", opacity=0.25, line_width=0, row=1, col=1)
    fig.add_hrect(y0=sell_low, y1=sell_high, fillcolor="red", opacity=0.15, line_width=0, row=1, col=1)
    if st.session_state.active_trade:
        at=st.session_state.active_trade
        fig.add_hline(y=at['entry'], line_color="white", line_width=2, annotation_text=f"ENTRY {at['entry']:.1f}", row=1, col=1)
        fig.add_hline(y=at['sl'], line_color="red", line_dash="dash", annotation_text="SL", row=1, col=1)
        fig.add_hline(y=at['tp'], line_color="green", line_dash="dash", annotation_text="TP", row=1, col=1)
    fig.add_trace(go.Bar(x=df['T'], y=df['V'], marker_color='gray', name="Vol"), row=2, col=1)
    fig.update_layout(height=700, template="plotly_dark", xaxis_rangeslider_visible=False, dragmode='pan', margin=dict(l=0,r=0,t=20,b=0))
    # THIS ENABLES ZOOM/PAN CONTROLS
    st.plotly_chart(fig, use_container_width=True, config={
        'scrollZoom': True, 'displayModeBar': True, 'displaylogo': False,
        'modeBarButtonsToAdd': ['drawline','drawrect','eraseshape']
    })
    st.caption("🔍 Pinch with 2 fingers to zoom | Drag 1 finger to move | Double tap to reset | Use toolbar on top-right to draw")

with tab2:
    if st.session_state.active_trade:
        at=st.session_state.active_trade
        st.success(f"### 📈 LIVE {at['type']} RUNNING")
        colA,colB=st.columns(2)
        colA.metric("Entry", f"${at['entry']:.2f}"); colA.metric("Current", f"${price:.2f}")
        colB.metric("Running P/L", pnl_live, delta=f"{run:.2f}"); colB.metric("RR", f"1:{at['rr']:.1f}")
        st.divider()
        st.code(f"{at['type']} XAUUSD {at['lot']} lot\nEntry: {at['entry']:.2f}\nSL: {at['sl']:.2f}\nTP: {at['tp']:.2f}\nRunning: {pnl_live}", language="text")
        st.markdown(f"<button onclick=\"navigator.clipboard.writeText('{at['type']} XAUUSD {at['lot']} SL {at['sl']:.2f} TP {at['tp']:.2f}')\" style='width:100%;padding:15px;background:#00ff88;color:black;border-radius:10px;font-weight:bold;font-size:16px;'>📋 COPY FOR DERIV MT5</button>", unsafe_allow_html=True)
        st.link_button("🚀 OPEN DERIV MT5", "https://mt5.deriv.com/", use_container_width=True)
        st.progress(min(max((price-at['entry'])/(at['tp']-at['entry']) if at['type']=="BUY" else (at['entry']-price)/(at['entry']-at['tp']),0),1) if at['tp']!=at['entry'] else 0)
        st.caption("Bar shows progress to TP")
    else:
        if sig=="WAIT": st.info(f"⏳ No active trade. Waiting for price to enter zone.\n\nBUY Zone {buy_low:.1f}-{buy_high:.1f} RR {rr_buy:.1f}\nSELL Zone {sell_low:.1f}-{sell_high:.1f} RR {rr_sell:.1f}")
        else: st.warning(f"🔥 {sig} SIGNAL READY @ ${price:.2f} - Will start on next refresh if session ACTIVE")

with tab3:
    if st.session_state.trades:
        df_t=pd.DataFrame(st.session_state.trades)
        wins=len(df_t[df_t['result']=="WIN"]); total=len(df_t); pnl_total=df_t['pnl'].sum()
        st.subheader(f"🏆 {wins}/{total} WINS | ${pnl_total:.2f} Total | {wins/5*100:.0f}% to 5 TP")
        st.progress(min(wins/5,1.0))
        c1,c2,c3=st.columns(3)
        c1.metric("Wins", wins); c2.metric("Loss", total-wins); c3.metric("Win Rate", f"{wins/total*100:.0f}%")
        st.dataframe(df_t[['time','type','entry','close_price','pnl','result','rr','lot']], use_container_width=True)
        if st.button("🗑️ Clear Journal", use_container_width=True): st.session_state.trades=[]; st.rerun()
    else:
        st.info("No closed trades yet. Your challenge starts when first trade hits TP/SL.\n\nGoal: 5 TP = Validation ✅")
        st.image("https://i.imgur.com/8QJ4sQl.png") if False else None

col1,col2=st.columns(2)
with col1:
    if st.button("🔄 Refresh All", use_container_width=True): st.cache_data.clear(); st.rerun()
with col2:
    if st.button("📲 Test WA", use_container_width=True): send_wa(f"✅ TABS TEST ${price:.2f} {pnl_live}"); st.success("Sent!")

st.markdown("<script>setTimeout(()=>{window.location.reload()}, 15000);</script>", unsafe_allow_html=True)
