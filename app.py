import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import pytz
import time
import requests

# ================= PAGE CONFIG =================
st.set_page_config(
    page_title="Price Action Scanner – Rajkumar",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;700&family=Syne:wght@700;800&display=swap');
    html, body, [class*="css"] { font-family: 'JetBrains Mono', monospace; background-color: #0a0e1a; color: #e2e8f0; }
    .main { background-color: #0a0e1a; }
    .block-container { padding-top: 1.5rem; }
    h1, h2, h3 { font-family: 'Syne', sans-serif; }
    .signal-buy  { background: linear-gradient(135deg,#0d2b1a,#0a1f12); border:1px solid #00ff88; border-radius:10px; padding:14px 18px; margin:6px 0; box-shadow:0 0 12px rgba(0,255,136,0.15); }
    .signal-sell { background: linear-gradient(135deg,#2b0d0d,#1f0a0a); border:1px solid #ff4466; border-radius:10px; padding:14px 18px; margin:6px 0; box-shadow:0 0 12px rgba(255,68,102,0.15); }
    .badge-buy   { color:#00ff88; font-weight:700; font-size:1.1em; }
    .badge-sell  { color:#ff4466; font-weight:700; font-size:1.1em; }
    .score-bar-wrap { background:#1e2535; border-radius:6px; height:8px; margin-top:6px; }
    .kpi-box     { background:#111827; border:1px solid #1e2d3d; border-radius:12px; padding:18px 22px; text-align:center; }
    .kpi-val     { font-size:2em; font-weight:800; font-family:'Syne',sans-serif; }
    .kpi-label   { font-size:0.75em; color:#64748b; margin-top:4px; }
    .bt-win      { background:linear-gradient(135deg,#0d2b1a,#0a1f12); border:1px solid #00ff88; border-radius:8px; padding:10px 14px; margin:4px 0; }
    .bt-loss     { background:linear-gradient(135deg,#2b0d0d,#1f0a0a); border:1px solid #ff4466; border-radius:8px; padding:10px 14px; margin:4px 0; }
    .bt-open     { background:#111827; border:1px solid #475569; border-radius:8px; padding:10px 14px; margin:4px 0; }
    .stButton>button { background:linear-gradient(135deg,#1a56db,#0e3d9c); color:white; border:none; border-radius:8px; font-family:'JetBrains Mono',monospace; font-weight:700; padding:0.5rem 1.5rem; width:100%; }
    .stButton>button:hover { background:linear-gradient(135deg,#2563eb,#1a4fc4); }
    .sidebar-title { font-family:'Syne',sans-serif; font-size:1.3em; font-weight:800; color:#60a5fa; margin-bottom:1rem; }
    div[data-testid="stSidebarContent"] { background-color:#0d1117; }
</style>
""", unsafe_allow_html=True)

# ================= HEADER =================
st.markdown("<h1 style='font-family:Syne,sans-serif;font-size:2.2em;margin-bottom:0'>⚡ Price Action Scanner</h1>", unsafe_allow_html=True)
st.markdown("<p style='color:#64748b;margin-top:0;font-size:0.85em'>Pure candle structure · Telegram Alerts · 30-Day Backtest · 1:2 R:R</p>", unsafe_allow_html=True)
st.markdown("---")

IST = pytz.timezone("Asia/Kolkata")

# ================= SIDEBAR =================
st.sidebar.markdown("<div class='sidebar-title'>⚙️ Scanner Settings</div>", unsafe_allow_html=True)
run_button   = st.sidebar.button("🚀 Run Scanner")
auto_refresh = st.sidebar.checkbox("Auto Refresh (5 min)", value=False)
min_score    = st.sidebar.slider("Minimum Signal Score", 0, 10, 5)
show_sells   = st.sidebar.checkbox("Show SELL signals too", value=True)
tf_choice    = st.sidebar.radio("Intraday Timeframe", ["5m", "15m"], index=0)

st.sidebar.markdown("---")
st.sidebar.markdown("<div style='color:#60a5fa;font-weight:700;margin-bottom:6px'>📲 Telegram Alerts</div>", unsafe_allow_html=True)
tg_token   = st.sidebar.text_input("Bot Token", type="password", placeholder="123456:ABC-xyz...")
tg_chat_id = st.sidebar.text_input("Chat ID", placeholder="-100123456789")
tg_enabled = st.sidebar.checkbox("Enable Alerts (Score ≥ 7 + Vol Spike)", value=False)

st.sidebar.markdown("---")
st.sidebar.markdown("<small style='color:#475569'>Signals: Engulfing · Hammer · ORB · Structure · Inside/Outside Bar · R-Factor · Volume</small>", unsafe_allow_html=True)

# ================= STOCK LIST =================
STOCK_LIST = [
    'IDEA.NS','BSE.NS','INDUSTOWER.NS','RBLBANK.NS','GLENMARK.NS','KFINTECH.NS','NATIONALUM.NS','EICHERMOT.NS','ASTRAL.NS','M&M.NS','VEDL.NS','ASHOKLEY.NS',
    'VOLTAS.NS','CHOLAFIN.NS','BIOCON.NS','CAMS.NS','ANGELONE.NS','EXIDEIND.NS','MARUTI.NS','UNOMINDA.NS','IRFC.NS','NMDC.NS','SAIL.NS','NYKAA.NS','ABCAPITAL.NS','TVSMOTOR.NS',
    'POWERGRID.NS','AMBER.NS','DRREDDY.NS','LTF.NS','RELIANCE.NS','PNBHOUSING.NS','NAUKRI.NS','SHRIRAMFIN.NS','PHOENIXLTD.NS','PFC.NS','PAYTM.NS','KAYNES.NS','INOXWIND.NS',
    'IREDA.NS','CANBK.NS','CDSL.NS','NUVAMA.NS','ETERNAL.NS','MAXHEALTH.NS','TATAPOWER.NS','PPLPHARMA.NS','BDL.NS','BHARTIARTL.NS','SBILIFE.NS',
    'AUROPHARMA.NS','SUZLON.NS','LAURUSLABS.NS','RVNL.NS','YESBANK.NS','MFSL.NS','SONACOMS.NS','SUNPHARMA.NS','OIL.NS','HDFCLIFE.NS','SAMMAANCAP.NS','KPITTECH.NS','HINDALCO.NS',
    'IIFL.NS','BAJAJFINSV.NS','ALKEM.NS','BHEL.NS','HINDZINC.NS','HUDCO.NS','BANDHANBNK.NS','AXISBANK.NS','TATASTEEL.NS','RECLTD.NS','IDFCFIRSTB.NS','NBCC.NS','BHARATFORG.NS','360ONE.NS',
    'ASIANPAINT.NS','BOSCHLTD.NS','TATAELXSI.NS','MUTHOOTFIN.NS','IRCTC.NS','UNIONBANK.NS','BANKINDIA.NS','FEDERALBNK.NS','SHREECEM.NS','TITAGARH.NS','JSWENERGY.NS','PNB.NS','COALINDIA.NS',
    'BAJFINANCE.NS','MOTHERSON.NS','JINDALSTEL.NS','INDUSINDBK.NS','JUBLFOOD.NS','LUPIN.NS','HEROMOTOCO.NS','HDFCBANK.NS','ZYDUSLIFE.NS','BAJAJ-AUTO.NS','MANAPPURAM.NS','BANKBARODA.NS',
    'TATACONSUM.NS','CONCOR.NS','ADANIENT.NS','DALBHARAT.NS','JSWSTEEL.NS','HDFCAMC.NS','CUMMINSIND.NS','DIXON.NS','ADANIGREEN.NS',
    'INDIANB.NS','KALYANKJIL.NS','INDHOTEL.NS','TRENT.NS','LICHSGFIN.NS','IOC.NS','BLUESTARCO.NS','CROMPTON.NS','LICI.NS','BRITANNIA.NS','BPCL.NS','HAVELLS.NS','PGEL.NS',
    'OFSS.NS','AMBUJACEM.NS','ICICIBANK.NS','TIINDIA.NS','GRASIM.NS','FORTIS.NS','SBICARD.NS','HFCL.NS','KOTAKBANK.NS','HINDPETRO.NS','SUPREMEIND.NS','LTIM.NS','AUBANK.NS',
    'ADANIENSOL.NS','NESTLEIND.NS','DLF.NS','SBIN.NS','NHPC.NS','MAZDOCK.NS','NCC.NS','ULTRACEMCO.NS','POLYCAB.NS','DELHIVERY.NS','GAIL.NS','NTPC.NS','INDIGO.NS','PETRONET.NS',
    'BEL.NS','ADANIPORTS.NS','APLAPOLLO.NS','IEX.NS','MCX.NS','ICICIPRULI.NS','CGPOWER.NS','WIPRO.NS','TORNTPHARM.NS','TATACHEM.NS','TATATECH.NS','ONGC.NS','GMRAIRPORT.NS','TITAN.NS',
    'MANKIND.NS','UNITDSPR.NS','HAL.NS','DMART.NS','PIDILITIND.NS','PAGEIND.NS','ABB.NS','MARICO.NS','UPL.NS','SOLARINDS.NS','LT.NS','DABUR.NS','GODREJCP.NS','PATANJALI.NS',
    'APOLLOHOSP.NS','HINDUNILVR.NS','INFY.NS','SYNGENE.NS','SRF.NS','LODHA.NS','CYIENT.NS','TECHM.NS','TCS.NS','CIPLA.NS','ICICIGI.NS','COLPAL.NS','HCLTECH.NS','IGL.NS',
    'OBEROIRLTY.NS','COFORGE.NS','DIVISLAB.NS','GODREJPROP.NS','PIIND.NS','ITC.NS','SIEMENS.NS','KEI.NS','MPHASIS.NS','POLICYBZR.NS','TORNTPOWER.NS','PRESTIGE.NS','PERSISTENT.NS','VBL.NS'
]

# ================= TELEGRAM =================
def send_telegram(token, chat_id, message):
    try:
        url     = f"https://api.telegram.org/bot{token}/sendMessage"
        payload = {"chat_id": chat_id, "text": message, "parse_mode": "HTML"}
        resp    = requests.post(url, data=payload, timeout=5)
        return resp.status_code == 200
    except Exception:
        return False

# ================= PRICE ACTION FUNCTIONS =================
def is_bullish_engulfing(prev, curr):
    return (prev["Close"] < prev["Open"] and curr["Close"] > curr["Open"]
            and curr["Open"] <= prev["Close"] and curr["Close"] >= prev["Open"])

def is_bearish_engulfing(prev, curr):
    return (prev["Close"] > prev["Open"] and curr["Close"] < curr["Open"]
            and curr["Open"] >= prev["Close"] and curr["Close"] <= prev["Open"])

def is_hammer(candle):
    body        = abs(candle["Close"] - candle["Open"])
    total_range = candle["High"] - candle["Low"]
    if total_range == 0 or body == 0:
        return False, False
    lower_wick = min(candle["Open"], candle["Close"]) - candle["Low"]
    upper_wick = candle["High"] - max(candle["Open"], candle["Close"])
    return (lower_wick >= 2 * body and upper_wick <= body,
            upper_wick >= 2 * body and lower_wick <= body)

def is_inside_bar(prev, curr):
    return curr["High"] <= prev["High"] and curr["Low"] >= prev["Low"]

def is_outside_bar(prev, curr):
    return curr["High"] > prev["High"] and curr["Low"] < prev["Low"]

def is_strong_candle(candle):
    body        = abs(candle["Close"] - candle["Open"])
    total_range = candle["High"] - candle["Low"]
    if total_range == 0:
        return False, False
    ratio = body / total_range
    return (ratio >= 0.70 and candle["Close"] > candle["Open"],
            ratio >= 0.70 and candle["Close"] < candle["Open"])

def detect_market_structure(df):
    highs = df["High"].values
    lows  = df["Low"].values
    n     = len(highs)
    if n < 6:
        return "Unclear"
    rh = highs[n-6:n];  rl = lows[n-6:n]
    hh = rh[-1] > max(rh[:-1]);  hl = rl[-1] > min(rl[:-1])
    lh = rh[-1] < max(rh[:-1]);  ll = rl[-1] < min(rl[:-1])
    if hh and hl:    return "Uptrend"
    elif lh and ll:  return "Downtrend"
    return "Sideways"

def detect_support_resistance(daily_df, current_price, tolerance=0.005):
    levels = []
    for i in range(2, len(daily_df) - 2):
        if daily_df["High"].iloc[i] >= max(daily_df["High"].iloc[i-2:i+3]):
            levels.append(daily_df["High"].iloc[i])
        if daily_df["Low"].iloc[i] <= min(daily_df["Low"].iloc[i-2:i+3]):
            levels.append(daily_df["Low"].iloc[i])
    near = any(abs(current_price - l) / current_price <= tolerance for l in levels)
    return near, levels

# ================= SHARED SCORE ENGINE =================
def compute_score(curr, prev, intraday_window, daily_sub, prev_day, today_day):
    current_price    = curr["Close"]
    price_change_pct = (current_price - prev_day["Close"]) / prev_day["Close"] * 100 if prev_day["Close"] else 0

    avg_range = (daily_sub["High"] - daily_sub["Low"]).tail(10).mean()
    r_factor  = abs(today_day["Close"] - prev_day["Close"]) / avg_range if avg_range else 0

    avg_vol   = intraday_window["Volume"].mean()
    vol_ratio = curr["Volume"] / avg_vol if avg_vol else 0
    vol_spike = vol_ratio >= 2.0

    first_c        = intraday_window.iloc[0]
    orb_high_break = current_price > first_c["High"]
    orb_low_break  = current_price < first_c["Low"]
    prev_high_break= current_price > prev_day["High"]
    prev_low_break = current_price < prev_day["Low"]

    bull_engulf          = is_bullish_engulfing(prev, curr)
    bear_engulf          = is_bearish_engulfing(prev, curr)
    hammer, shoot_star   = is_hammer(curr)
    inside_bar           = is_inside_bar(prev, curr)
    outside_bar          = is_outside_bar(prev, curr)
    strong_bull, strong_bear = is_strong_candle(curr)
    structure            = detect_market_structure(intraday_window)
    near_sr, _           = detect_support_resistance(daily_sub, current_price)

    bull_score = bear_score = 0
    bull_reasons = []; bear_reasons = []

    if bull_engulf:     bull_score += 2;   bull_reasons.append("Bullish Engulfing")
    if bear_engulf:     bear_score += 2;   bear_reasons.append("Bearish Engulfing")
    if hammer:          bull_score += 1.5; bull_reasons.append("Hammer")
    if shoot_star:      bear_score += 1.5; bear_reasons.append("Shooting Star")
    if strong_bull:     bull_score += 1.5; bull_reasons.append("Strong Bull Candle")
    if strong_bear:     bear_score += 1.5; bear_reasons.append("Strong Bear Candle")
    if orb_high_break:  bull_score += 1.5; bull_reasons.append("ORB High Break")
    if orb_low_break:   bear_score += 1.5; bear_reasons.append("ORB Low Break")
    if prev_high_break: bull_score += 1.5; bull_reasons.append("Prev Day High Break")
    if prev_low_break:  bear_score += 1.5; bear_reasons.append("Prev Day Low Break")

    if structure == "Uptrend":   bull_score += 1; bull_reasons.append("Uptrend Structure")
    if structure == "Downtrend": bear_score += 1; bear_reasons.append("Downtrend Structure")

    if outside_bar:
        if price_change_pct > 0: bull_score += 0.5; bull_reasons.append("Outside Bar ↑")
        else:                    bear_score += 0.5; bear_reasons.append("Outside Bar ↓")

    if r_factor >= 0.5:
        if bull_score >= bear_score: bull_score += 1; bull_reasons.append(f"R-Factor {round(r_factor,2)}")
        else:                        bear_score += 1; bear_reasons.append(f"R-Factor {round(r_factor,2)}")

    if vol_spike:
        if bull_score >= bear_score: bull_score += 1; bull_reasons.append("Volume Spike ✔")
        else:                        bear_score += 1; bear_reasons.append("Volume Spike ✔")

    if near_sr:
        if bull_score >= bear_score: bull_score += 0.5; bull_reasons.append("Near S/R Level")
        else:                        bear_score += 0.5; bear_reasons.append("Near S/R Level")

    bull_score = round(min(bull_score, 10), 1)
    bear_score = round(min(bear_score, 10), 1)

    if bull_score >= bear_score:
        final_score, signal, reasons = bull_score, "BUY",  bull_reasons
    else:
        final_score, signal, reasons = bear_score, "SELL", bear_reasons

    if final_score < 2:
        signal = "NEUTRAL"

    return {
        "signal": signal, "score": final_score, "reasons": reasons,
        "r_factor": round(r_factor, 2), "vol_ratio": round(vol_ratio, 2),
        "vol_spike": vol_spike, "structure": structure,
        "price_change_pct": round(price_change_pct, 2),
        "inside_bar": inside_bar, "outside_bar": outside_bar,
    }

# ================= LIVE ANALYZE =================
def analyze_stock(symbol, timeframe="5m"):
    try:
        ticker   = yf.Ticker(symbol)
        daily    = ticker.history(period="30d")
        if daily.empty or len(daily) < 10:
            return None

        intraday = ticker.history(period="1d", interval=timeframe)
        if intraday.empty or len(intraday) < 5:
            return None

        intraday = intraday.reset_index()
        if intraday["Datetime"].dt.tz is not None:
            intraday["Datetime"] = intraday["Datetime"].dt.tz_convert(IST)

        curr      = intraday.iloc[-1]
        prev      = intraday.iloc[-2]
        prev_day  = daily.iloc[-2]
        today_day = daily.iloc[-1]

        sc = compute_score(curr, prev, intraday, daily, prev_day, today_day)

        daily["TR"] = np.maximum(daily["High"] - daily["Low"],
            np.maximum(abs(daily["High"] - daily["Close"].shift()),
                       abs(daily["Low"]  - daily["Close"].shift())))
        atr    = daily["TR"].tail(14).mean()
        cp     = curr["Close"]
        sl     = round(cp - 1.5 * atr, 2) if sc["signal"] == "BUY" else round(cp + 1.5 * atr, 2)
        target = round(cp + 3.0 * atr, 2) if sc["signal"] == "BUY" else round(cp - 3.0 * atr, 2)

        return {
            "Stock":       symbol.replace(".NS", ""),
            "Symbol":      symbol,
            "Price":       round(cp, 2),
            "Change %":    sc["price_change_pct"],
            "Signal":      sc["signal"],
            "Score":       sc["score"],
            "R-Factor":    sc["r_factor"],
            "Reasons":     " · ".join(sc["reasons"]) if sc["reasons"] else "—",
            "Structure":   sc["structure"],
            "Vol Ratio":   sc["vol_ratio"],
            "Vol Spike":   sc["vol_spike"],
            "Inside Bar":  "✅" if sc["inside_bar"]  else "",
            "Outside Bar": "✅" if sc["outside_bar"] else "",
            "Stop Loss":   sl,
            "Target":      target,
        }
    except Exception:
        return None

# ================= SCANNER =================
@st.cache_data(ttl=300)
def run_scanner(timeframe):
    results = []
    for stock in STOCK_LIST:
        res = analyze_stock(stock, timeframe)
        if res:
            results.append(res)
        time.sleep(0.25)
    return pd.DataFrame(results)

# ================= BACKTEST ENGINE =================
def backtest_stock(symbol, timeframe="5m", rr_ratio=2.0, min_bt_score=5):
    try:
        ticker = yf.Ticker(symbol)
        daily  = ticker.history(period="60d")
        if daily.empty or len(daily) < 15:
            return []

        # yfinance allows max ~60 days for 5m/15m data
        end   = datetime.now(IST)
        start = end - timedelta(days=35)
        intraday = ticker.history(
            start=start.strftime("%Y-%m-%d"),
            end=end.strftime("%Y-%m-%d"),
            interval=timeframe
        )
        if intraday.empty:
            return []

        intraday = intraday.reset_index()
        if intraday["Datetime"].dt.tz is not None:
            intraday["Datetime"] = intraday["Datetime"].dt.tz_convert(IST)
        intraday["Date"] = intraday["Datetime"].dt.date

        trading_days = sorted(intraday["Date"].unique())
        trades = []

        for day in trading_days:
            day_df = intraday[intraday["Date"] == day].reset_index(drop=True)
            if len(day_df) < 6:
                continue

            # Get prev/today daily rows
            prev_daily_rows  = daily[daily.index.date < day]
            today_daily_rows = daily[daily.index.date == day]
            if len(prev_daily_rows) < 2:
                continue
            prev_day  = prev_daily_rows.iloc[-1]
            today_day = today_daily_rows.iloc[-1] if not today_daily_rows.empty else prev_day

            # ATR from daily
            daily_sub = daily[daily.index.date <= day].tail(20).copy()
            daily_sub["TR"] = np.maximum(
                daily_sub["High"] - daily_sub["Low"],
                np.maximum(abs(daily_sub["High"] - daily_sub["Close"].shift()),
                           abs(daily_sub["Low"]  - daily_sub["Close"].shift()))
            )
            atr = daily_sub["TR"].tail(14).mean()
            if not atr or np.isnan(atr) or atr == 0:
                continue

            # Scan candles — one trade per day on first qualifying signal
            for idx in range(2, len(day_df) - 1):
                curr   = day_df.iloc[idx]
                prev   = day_df.iloc[idx - 1]
                window = day_df.iloc[:idx + 1]

                sc = compute_score(curr, prev, window, daily_sub, prev_day, today_day)

                if sc["score"] < min_bt_score or sc["signal"] == "NEUTRAL":
                    continue

                entry = curr["Close"]
                sig   = sc["signal"]
                sl     = round(entry - 1.5 * atr, 2)       if sig == "BUY"  else round(entry + 1.5 * atr, 2)
                target = round(entry + rr_ratio * 1.5 * atr, 2) if sig == "BUY"  else round(entry - rr_ratio * 1.5 * atr, 2)

                # Scan future candles same day
                result = "Open"
                for _, fc in day_df.iloc[idx + 1:].iterrows():
                    if sig == "BUY":
                        if fc["High"] >= target: result = "WIN";  break
                        if fc["Low"]  <= sl:     result = "LOSS"; break
                    else:
                        if fc["Low"]  <= target: result = "WIN";  break
                        if fc["High"] >= sl:     result = "LOSS"; break

                trades.append({
                    "Date":        str(day),
                    "Time":        curr["Datetime"].strftime("%H:%M"),
                    "Signal":      sig,
                    "Score":       sc["score"],
                    "Entry":       round(entry, 2),
                    "SL":          sl,
                    "Target":      target,
                    "ATR":         round(atr, 2),
                    "Reasons":     " · ".join(sc["reasons"]) if sc["reasons"] else "—",
                    "Result":      result,
                })
                break  # one trade per day only

        return trades
    except Exception:
        return []

# =====================================================================
#                         MAIN UI
# =====================================================================
main_tab, bt_tab = st.tabs(["📡 Live Scanner", "📊 Backtest (30 Days)"])

# ==================== LIVE SCANNER ====================
with main_tab:
    if run_button or auto_refresh:
        with st.spinner("⚡ Scanning price action across all stocks..."):
            df = run_scanner(tf_choice)

        if df.empty:
            st.warning("No data returned. Try again during market hours.")
        else:
            df = df[df["Score"] >= min_score]
            if not show_sells:
                df = df[df["Signal"] != "SELL"]

            df_buy  = df[df["Signal"] == "BUY"].sort_values("Score", ascending=False)
            df_sell = df[df["Signal"] == "SELL"].sort_values("Score", ascending=False)
            df_all  = df.sort_values("Score", ascending=False)

            # ---- Telegram ----
            if tg_enabled and tg_token and tg_chat_id:
                alert_df = df[(df["Score"] >= 7) & (df["Vol Spike"] == True)]
                sent = 0
                for _, row in alert_df.iterrows():
                    arrow = "🟢 BUY" if row["Signal"] == "BUY" else "🔴 SELL"
                    msg = (
                        f"<b>⚡ Price Action Alert</b>\n\n"
                        f"<b>{row['Stock']}</b>  {arrow}\n"
                        f"💰 Price: ₹{row['Price']}  ({row['Change %']:+.2f}%)\n"
                        f"🎯 Score: {row['Score']}/10\n"
                        f"📈 R-Factor: {row['R-Factor']}  Vol×: {row['Vol Ratio']}\n"
                        f"🛑 SL: ₹{row['Stop Loss']}  🎯 TGT: ₹{row['Target']}\n"
                        f"📌 {row['Reasons']}\n"
                        f"🕐 {datetime.now(IST).strftime('%H:%M:%S IST')}"
                    )
                    if send_telegram(tg_token, tg_chat_id, msg):
                        sent += 1
                if sent:
                    st.success(f"📲 {sent} Telegram alert(s) sent!")

            # ---- KPIs ----
            k1, k2, k3, k4, k5 = st.columns(5)
            def kpi(col, val, label, color="#60a5fa"):
                col.markdown(f"<div class='kpi-box'><div class='kpi-val' style='color:{color}'>{val}</div><div class='kpi-label'>{label}</div></div>", unsafe_allow_html=True)
            kpi(k1, len(df),      "Scanned",   "#60a5fa")
            kpi(k2, len(df_buy),  "BUY",       "#00ff88")
            kpi(k3, len(df_sell), "SELL",      "#ff4466")
            kpi(k4, df_buy.iloc[0]["Stock"]  if not df_buy.empty  else "—", "Top BUY",  "#00ff88")
            kpi(k5, df_sell.iloc[0]["Stock"] if not df_sell.empty else "—", "Top SELL", "#ff4466")
            st.markdown("<br>", unsafe_allow_html=True)

            def render_cards(frame, sig_type):
                if frame.empty:
                    st.info(f"No {sig_type} signals with score ≥ {min_score}")
                    return
                for _, row in frame.iterrows():
                    css = "signal-buy" if sig_type == "BUY" else "signal-sell"
                    bcls= "badge-buy"  if sig_type == "BUY" else "badge-sell"
                    arr = "▲" if sig_type == "BUY" else "▼"
                    cc  = "#00ff88" if row["Change %"] >= 0 else "#ff4466"
                    bc  = "#00ff88" if sig_type == "BUY"    else "#ff4466"
                    sp  = int(row["Score"] * 10)
                    st.markdown(f"""
                    <div class='{css}'>
                      <div style='display:flex;justify-content:space-between;align-items:center'>
                        <div>
                          <span style='font-size:1.2em;font-weight:800;font-family:Syne,sans-serif'>{row['Stock']}</span>&nbsp;&nbsp;
                          <span class='{bcls}'>{arr} {sig_type}</span>&nbsp;
                          <span style='color:#94a3b8;font-size:0.82em'>{row['Structure']}</span>
                        </div>
                        <div style='text-align:right'>
                          <span style='font-size:1.3em;font-weight:700'>₹{row['Price']}</span>&nbsp;
                          <span style='color:{cc};font-size:0.9em'>{row['Change %']:+.2f}%</span>
                        </div>
                      </div>
                      <div style='margin:8px 0 4px 0;color:#94a3b8;font-size:0.8em'>{row['Reasons']}</div>
                      <div style='display:flex;justify-content:space-between;align-items:center;margin-top:6px'>
                        <div>
                          <span style='color:#64748b;font-size:0.75em'>SL </span><span style='color:#fbbf24;font-weight:700'>₹{row['Stop Loss']}</span>&nbsp;&nbsp;
                          <span style='color:#64748b;font-size:0.75em'>TGT </span><span style='color:#34d399;font-weight:700'>₹{row['Target']}</span>&nbsp;&nbsp;
                          <span style='color:#64748b;font-size:0.75em'>Vol×</span><span style='color:#e2e8f0'>{row['Vol Ratio']}</span>&nbsp;&nbsp;
                          <span style='color:#64748b;font-size:0.75em'>R-Fac</span><span style='color:#c084fc;font-weight:700'>{row['R-Factor']}</span>
                        </div>
                        <div style='font-size:0.78em;color:#64748b'>Score <b style='color:{bc}'>{row['Score']}/10</b></div>
                      </div>
                      <div class='score-bar-wrap'><div style='width:{sp}%;background:{bc};height:8px;border-radius:6px'></div></div>
                    </div>""", unsafe_allow_html=True)

            t1, t2, t3 = st.tabs(["🟢 BUY", "🔴 SELL", "📋 All"])
            with t1:
                st.markdown(f"### 🟢 BUY Signals &nbsp;<span style='color:#64748b;font-size:0.7em'>{len(df_buy)} stocks</span>", unsafe_allow_html=True)
                render_cards(df_buy, "BUY")
            with t2:
                st.markdown(f"### 🔴 SELL Signals &nbsp;<span style='color:#64748b;font-size:0.7em'>{len(df_sell)} stocks</span>", unsafe_allow_html=True)
                render_cards(df_sell, "SELL")
            with t3:
                def csig(v):
                    if v=="BUY":  return "color:#00ff88;font-weight:bold"
                    if v=="SELL": return "color:#ff4466;font-weight:bold"
                    return "color:#94a3b8"
                styled = df_all.drop(columns=["Symbol","Vol Spike"], errors="ignore").style\
                    .applymap(csig, subset=["Signal"])\
                    .background_gradient(subset=["Score"], cmap="RdYlGn", vmin=0, vmax=10)\
                    .format({"Price":"₹{:.2f}","Stop Loss":"₹{:.2f}","Target":"₹{:.2f}","Change %":"{:+.2f}%"})
                st.dataframe(styled, use_container_width=True, height=600)

            st.markdown(f"<p style='color:#334155;font-size:0.75em;text-align:right'>Scanned: {datetime.now(IST).strftime('%d %b %Y, %H:%M:%S IST')} · {tf_choice}</p>", unsafe_allow_html=True)
    else:
        st.info("👈 Configure settings in the sidebar and click **🚀 Run Scanner** to begin.")
        st.markdown("---")

        st.markdown("### ⚡ How to Use This Tool")
        c1, c2 = st.columns(2)
        with c1:
            st.markdown("""
**📡 Live Scanner**
1. Set **Timeframe** → 5m or 15m
2. Set **Minimum Score** → 5 or higher recommended
3. Click **🚀 Run Scanner**
4. Check **BUY / SELL tabs** for signals
5. Each card shows: Price, SL, Target, R-Factor, Vol, Reasons
            """)
        with c2:
            st.markdown("""
**📊 Backtest Tab**
1. Select any stock from the dropdown
2. Choose timeframe (5m / 15m)
3. Set minimum score filter
4. Click **🔍 Run Backtest**
5. See 30-day WIN/LOSS log with 1:2 R:R results
            """)

        st.markdown("---")
        st.markdown("### 📌 Signal Types Detected")
        col1, col2, col3 = st.columns(3)
        with col1:
            st.success("🕯️ Bullish Engulfing\n\n🔨 Hammer\n\n💪 Strong Bull Candle")
        with col2:
            st.error("🕯️ Bearish Engulfing\n\n⭐ Shooting Star\n\n💪 Strong Bear Candle")
        with col3:
            st.warning("📊 ORB Breakout\n\n📏 Prev Day Break\n\n🔁 Inside / Outside Bar")

        st.markdown("---")
        m1, m2, m3, m4 = st.columns(4)
        m1.metric("Stocks Monitored", "150+")
        m2.metric("Signal Types", "10")
        m3.metric("R:R Ratio", "1 : 2")
        m4.metric("Timeframes", "5m / 15m")

# ==================== BACKTEST TAB ====================
with bt_tab:
    st.markdown("### 📊 30-Day Backtest — 1:2 Risk:Reward")
    st.markdown("<p style='color:#64748b;font-size:0.85em'>Pick a stock · Detects price action signals on historical candles · Checks if 1:2 R:R target hit before SL · One trade per day</p>", unsafe_allow_html=True)

    ca, cb, cc = st.columns([2, 1, 1])
    with ca:
        bt_symbol    = st.selectbox("Select Stock", [s.replace(".NS","") for s in STOCK_LIST])
    with cb:
        bt_tf        = st.radio("Timeframe", ["5m","15m"], key="bt_tf")
    with cc:
        bt_min_score = st.slider("Min Score to Trade", 3, 9, 5, key="bt_score")

    if st.button("🔍 Run Backtest", key="run_bt"):
        full_sym = bt_symbol + ".NS"
        with st.spinner(f"⏳ Running 30-day backtest on {bt_symbol} ({bt_tf})..."):
            trades = backtest_stock(full_sym, bt_tf, rr_ratio=2.0, min_bt_score=bt_min_score)

        if not trades:
            st.warning("No trades found. Try lowering Min Score or the stock may lack intraday history.")
        else:
            tdf    = pd.DataFrame(trades)
            wins   = len(tdf[tdf["Result"] == "WIN"])
            losses = len(tdf[tdf["Result"] == "LOSS"])
            opens  = len(tdf[tdf["Result"] == "Open"])
            closed = wins + losses
            wr     = round(wins / closed * 100, 1) if closed else 0
            ev     = round(((wins * 2) - losses) / closed, 2) if closed else 0

            # ---- KPIs ----
            st.markdown(f"#### {bt_symbol} · {bt_tf} · Last 30 Days")
            m1,m2,m3,m4,m5,m6 = st.columns(6)
            def mkpi(col, val, label, color):
                col.markdown(f"<div class='kpi-box'><div class='kpi-val' style='color:{color}'>{val}</div><div class='kpi-label'>{label}</div></div>", unsafe_allow_html=True)
            mkpi(m1, len(tdf),    "Total Signals", "#60a5fa")
            mkpi(m2, wins,        "WIN ✅",          "#00ff88")
            mkpi(m3, losses,      "LOSS ❌",          "#ff4466")
            mkpi(m4, opens,       "Open ⏳",          "#fbbf24")
            mkpi(m5, f"{wr}%",    "Win Rate",        "#00ff88" if wr >= 50 else "#ff4466")
            mkpi(m6, f"{ev}R",    "Exp Value/Trade", "#00ff88" if ev > 0   else "#ff4466")

            st.markdown("<br>", unsafe_allow_html=True)

            if ev > 0:
                st.success(f"✅ Positive edge! For every ₹100 risked → avg return ₹{round(ev*100)} over 30 days on {bt_symbol}.")
            else:
                st.error(f"❌ Negative edge. Lost ₹{abs(round(ev*100))} per ₹100 risked on avg. Try raising the Min Score filter.")

            st.markdown("---")
            st.markdown("#### 📋 Trade-by-Trade Log")

            for _, t in tdf.iterrows():
                css  = "bt-win"  if t["Result"]=="WIN"  else ("bt-loss" if t["Result"]=="LOSS" else "bt-open")
                icon = "✅ WIN"  if t["Result"]=="WIN"  else ("❌ LOSS"  if t["Result"]=="LOSS" else "⏳ Open")
                sc   = "#00ff88" if t["Signal"]=="BUY"  else "#ff4466"
                st.markdown(f"""
                <div class='{css}'>
                  <div style='display:flex;justify-content:space-between'>
                    <div>
                      <span style='color:{sc};font-weight:700'>{t['Signal']}</span>
                      &nbsp;·&nbsp;<span style='color:#94a3b8;font-size:0.85em'>{t['Date']} @ {t['Time']}</span>
                      &nbsp;·&nbsp;<span style='color:#60a5fa;font-size:0.82em'>Score {t['Score']}/10</span>
                    </div>
                    <div style='font-weight:800;font-size:1.1em'>{icon}</div>
                  </div>
                  <div style='margin-top:5px;font-size:0.8em;color:#94a3b8'>{t['Reasons']}</div>
                  <div style='margin-top:6px;font-size:0.85em'>
                    <span style='color:#64748b'>Entry </span><b>₹{t['Entry']}</b>&nbsp;&nbsp;
                    <span style='color:#64748b'>SL </span><span style='color:#fbbf24'>₹{t['SL']}</span>&nbsp;&nbsp;
                    <span style='color:#64748b'>TGT </span><span style='color:#34d399'>₹{t['Target']}</span>&nbsp;&nbsp;
                    <span style='color:#64748b'>ATR </span><span style='color:#c084fc'>₹{t['ATR']}</span>
                  </div>
                </div>""", unsafe_allow_html=True)

# ===== AUTO REFRESH =====
if auto_refresh:
    time.sleep(300)
    st.rerun()