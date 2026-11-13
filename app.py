import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import pandas_ta as ta
from streamlit_autorefresh import st_autorefresh
from scanner import load_indices
from gaussian import gaussian_channel
from gaussian import (
    add_confirmed_signals,
    add_stock_confirmed_signals,
    add_5m_breakout_signals
)
from gaussian import apply_pivot_filter
from candle_patterns import detect_candle_patterns
from market_data_manager import update_all_1m_data
from plyer import notification
import winsound


STOCK_LIST = [
    "BANKNIFTY",
    "MARUTI.NS",
    "RELIANCE.NS",
    "APOLLOHOSP.NS",
    "NTPC.NS",
    "HEROMOTOCO.NS",
    "POWERGRID.NS",
    "M&M.NS",
    "ONGC.NS",
    "COALINDIA.NS",
    "BAJAJ-AUTO.NS",
    "BAJAJFINSV.NS",
    "KOTAKBANK.NS",
    "TITAN.NS",
    "EICHERMOT.NS",
    "UPL.NS",
    "NESTLEIND.NS",
    "LT.NS",
    "BRITANNIA.NS",
    "BAJFINANCE.NS",
    "HDFCBANK.NS",
    "INDUSINDBK.NS",
    "ASIANPAINT.NS",
    "HINDUNILVR.NS",
    "BHARTIARTL.NS",
    "WIPRO.NS",
    "TCS.NS",
    "ULTRACEMCO.NS",
    "ITC.NS",
    "ADANIENT.NS",
    "SBILIFE.NS",
    "HCLTECH.NS",
    "ADANIPORTS.NS",
    "HDFCLIFE.NS",
    "BPCL.NS",
    "INFY.NS",
    "CIPLA.NS",
    "DRREDDY.NS",
    "TATACONSUM.NS",
    "AXISBANK.NS",
    "SBIN.NS",
    "JSWSTEEL.NS",
    "ICICIBANK.NS",
    "HINDALCO.NS",
    "DIVISLAB.NS",
    "GRASIM.NS",
    "SUNPHARMA.NS",
    "TATASTEEL.NS",
    "TECHM.NS"
]


def send_windows_notification(message):

    try:
        winsound.Beep(1500, 500)
        winsound.Beep(1500, 500)
        notification.notify(
            title="🚨 Gaussian Signal",
            message=message,
            app_name="Gaussian Dashboard",
            timeout=10
        )
    except Exception as e:
        print("Notification Error:", e)

def get_market_holidays(df):

    all_days = pd.date_range(
        start=df.index.min().date(),
        end=df.index.max().date(),
        freq="D"
    )

    trading_days = set(
        pd.to_datetime(df.index.date)
    )

    holiday_days = [
        d.strftime("%Y-%m-%d")
        for d in all_days
        if (
            d.weekday() < 5
            and pd.Timestamp(d) not in trading_days
        )
    ]

    return holiday_days

st.set_page_config(
    page_title="Gaussian Dashboard",
    layout="wide"
)

st.markdown("""
<style>
.block-container{
    padding-top:0rem;
    padding-left:1rem;
    padding-right:1rem;
    padding-bottom:0rem;
}
</style>
""", unsafe_allow_html=True)

if "today_mode" not in st.session_state:
    st.session_state.today_mode = True

if "last_signal" not in st.session_state:
    st.session_state.last_signal = ""

if st.session_state.today_mode:

    refresh_count = st_autorefresh(
        interval= 10 * 1000,
        key="refresh"
    )

else:

    refresh_count = st_autorefresh(
        interval=3000 * 1000,
        key="history_refresh"
    )

head1, head2, head3, head4, head5 = st.columns(
    [5, 2, 2, 1, 2]
)

with head1:
    st.markdown(
        f"""
        <div style="
            font-size:22px;
            font-weight:600;
            padding-top:0px;
            white-space:nowrap;
        ">
        📈 Gaussian Index Dashboard |
        🔄 {refresh_count}
        </div>
        """,
        unsafe_allow_html=True
    )

with head2:

    if st.button(
        "📥 Stock Market Data",
        use_container_width=True
    ):

        with st.spinner(
            "Updating 1 Minute Database..."
        ):

            update_all_1m_data()

        st.success(
            "Database Updated Successfully"
        )

with head3:

    selected_stock = st.selectbox(
        "Stock",
        STOCK_LIST,
        index=0,
        label_visibility="collapsed"
    )


with head4:
    today = st.checkbox(
        "Today",
        value=st.session_state.today_mode,
        key="today_toggle"
    )
    st.session_state.today_mode = today

with head5:
    selected_date = st.date_input(
        "Select Date",
        value=pd.Timestamp.today(),
        label_visibility="collapsed"
    )

import os

def load_stock_from_folder(stock_symbol):

    file_name = (
        stock_symbol
        .replace("^", "")
        .replace(".", "_")
    ) + ".csv"

    csv_path = os.path.join(
        r"C:\Users\ChetanPatil3\OneDrive - EPAM\Stock_Market_Data",
        file_name
    )

    if not os.path.exists(csv_path):
        return None

    df = pd.read_csv(csv_path)

    df["Datetime"] = pd.to_datetime(
        df["Datetime"]
    )

    df.set_index(
        "Datetime",
        inplace=True
    )

    df.index = pd.to_datetime(
        df.index
    ).tz_localize(None)

    return df

if st.session_state.today_mode:
    data_period = "5d"
else:
    data_period = "60d"
nifty, banknifty = load_indices(data_period)

selected_stock_df = None

if (
    not st.session_state.today_mode
    and selected_stock != "BANKNIFTY"
):

    selected_stock_df = load_stock_from_folder(
        selected_stock
    )

    if selected_stock_df is None:

        st.error(
            f"{selected_stock} CSV not found"
        )

        st.stop()

if selected_stock_df is not None:

    stock_1m = selected_stock_df.copy()

    stock_5m = (
        stock_1m
        .resample("5min")
        .agg({
            "Open":"first",
            "High":"max",
            "Low":"min",
            "Close":"last",
            "Volume":"sum"
        })
        .dropna()
    )

def load_index_from_folder(symbol):

    file_name = (
        symbol
        .replace("^", "")
        .replace(".", "_")
    ) + ".csv"

    csv_path = os.path.join(
        r"C:\Users\ChetanPatil3\OneDrive - EPAM\Stock_Market_Data",
        file_name
    )

    if not os.path.exists(csv_path):
        return None

    df = pd.read_csv(csv_path)

    df["Datetime"] = pd.to_datetime(df["Datetime"])

    df.set_index(
        "Datetime",
        inplace=True
    )

    df.index = df.index.tz_localize(None)

    return df

if st.session_state.today_mode:

    nifty_1m, banknifty_1m = load_indices(
        period="7d",
        interval="1m"
    )

else:

    nifty_1m = load_index_from_folder("^NSEI")
    banknifty_1m = load_index_from_folder("^NSEBANK")



nifty_1m.index = pd.to_datetime(
    nifty_1m.index
).tz_localize(None)

banknifty_1m.index = pd.to_datetime(
    banknifty_1m.index
).tz_localize(None)
nifty.index = pd.to_datetime(nifty.index).tz_localize(None)
banknifty.index = pd.to_datetime(banknifty.index).tz_localize(None)
if nifty is None:
    st.error("Nifty download failed")
    st.stop()

if banknifty is None:
    st.error("BankNifty download failed")
    st.stop()

nifty = gaussian_channel(nifty)
banknifty = gaussian_channel(banknifty)
nifty_1m = gaussian_channel(nifty_1m)
banknifty_1m = gaussian_channel(banknifty_1m)
nifty_1m = detect_candle_patterns(nifty_1m)
banknifty_1m = detect_candle_patterns(banknifty_1m)
# 1 Minute EMA
nifty_1m["EMA44"] = ta.ema(nifty_1m["Close"], length=44)
nifty_1m["EMA200"] = ta.ema(nifty_1m["Close"], length=200)

banknifty_1m["EMA44"] = ta.ema(banknifty_1m["Close"], length=44)
banknifty_1m["EMA200"] = ta.ema(banknifty_1m["Close"], length=200)

if selected_stock_df is not None:

    stock_5m = gaussian_channel(stock_5m)

    stock_1m = gaussian_channel(stock_1m)
    stock_1m = detect_candle_patterns(stock_1m)

    stock_1m["EMA44"] = ta.ema(
        stock_1m["Close"],
        length=44
    )

    stock_1m["EMA200"] = ta.ema(
        stock_1m["Close"],
        length=200
    )

    stock_5m["BUY"] = False
    stock_5m["SELL"] = False

    stock_1m["BUY"] = False
    stock_1m["SELL"] = False

    # ==========================================
    # STOCK : 5m -> 1m
    # ==========================================

    stock_5m_curve = (
        stock_5m[["SMAX", "SMIN"]]
        .resample("1min")
        .interpolate(method="linear")
    )

    stock_1m["SMAX_5M"] = (
        stock_5m_curve["SMAX"]
        .reindex(stock_1m.index)
        .ffill()
    )

    stock_1m["SMIN_5M"] = (
        stock_5m_curve["SMIN"]
        .reindex(stock_1m.index)
        .ffill()
    )

    stock_1m = add_5m_breakout_signals(
        stock_1m
    )


    # ==========================================
    # STOCK : 1m -> 5m
    # ==========================================

    stock_1m_curve = (
        stock_1m[["SMAX", "SMIN"]]
        .resample("5min")
        .last()
    )

    stock_5m["SMAX_1M"] = stock_1m_curve["SMAX"]

    stock_5m["SMIN_1M"] = stock_1m_curve["SMIN"]

    stock_5m[["SMAX_1M","SMIN_1M"]] = (
        stock_5m[["SMAX_1M","SMIN_1M"]]
        .interpolate(method="linear")
    )

# ==========================================
# NIFTY : 5m Channel -> 1m Smooth Projection
# ==========================================

nifty_5m_curve = (
    nifty[["SMAX", "SMIN"]]
    .resample("1min")
    .interpolate(method="linear")
)

nifty_1m["SMAX_5M"] = (
    nifty_5m_curve["SMAX"]
    .reindex(nifty_1m.index)
    .ffill()
)

nifty_1m["SMIN_5M"] = (
    nifty_5m_curve["SMIN"]
    .reindex(nifty_1m.index)
    .ffill()
)

nifty_1m = add_5m_breakout_signals(
    nifty_1m
)



# ==========================================
# NIFTY : 1m Channel -> 5m Smooth Projection
# ==========================================

nifty_1m_curve = (
    nifty_1m[["SMAX", "SMIN"]]
    .resample("5min")
    .last()
)

nifty["SMAX_1M"] = nifty_1m_curve["SMAX"]
nifty["SMIN_1M"] = nifty_1m_curve["SMIN"]

nifty[["SMAX_1M", "SMIN_1M"]] = (
    nifty[["SMAX_1M", "SMIN_1M"]]
    .interpolate(method="linear")
)


# ==========================================
# BANKNIFTY : 5m -> 1m
# ==========================================

bank_5m_curve = (
    banknifty[["SMAX", "SMIN"]]
    .resample("1min")
    .interpolate(method="linear")
)

banknifty_1m["SMAX_5M"] = (
    bank_5m_curve["SMAX"]
    .reindex(banknifty_1m.index)
    .ffill()
)

banknifty_1m["SMIN_5M"] = (
    bank_5m_curve["SMIN"]
    .reindex(banknifty_1m.index)
    .ffill()
)

banknifty_1m = add_5m_breakout_signals(
    banknifty_1m
)


# ==========================================
# BANKNIFTY : 1m -> 5m
# ==========================================

bank_1m_curve = (
    banknifty_1m[["SMAX", "SMIN"]]
    .resample("5min")
    .last()
)

banknifty["SMAX_1M"] = bank_1m_curve["SMAX"]
banknifty["SMIN_1M"] = bank_1m_curve["SMIN"]

banknifty[["SMAX_1M", "SMIN_1M"]] = (
    banknifty[["SMAX_1M", "SMIN_1M"]]
    .interpolate(method="linear")
)

nifty_1m, banknifty_1m = add_confirmed_signals(
    nifty_1m,
    banknifty_1m
)
nifty, banknifty = add_confirmed_signals(
    nifty,
    banknifty
)

if selected_stock_df is not None:

    stock_5m = add_stock_confirmed_signals(
        stock_5m,
        nifty
    )

    stock_1m = add_stock_confirmed_signals(
        stock_1m,
        nifty_1m
    )

latest_signal = ""

# NIFTY 5m
if nifty["BUY"].iloc[-1]:
    latest_signal = "NIFTY 5M BUY"

elif nifty["SELL"].iloc[-1]:
    latest_signal = "NIFTY 5M SELL"

# BANKNIFTY 5m
elif banknifty["BUY"].iloc[-1]:
    latest_signal = "BANKNIFTY 5M BUY"

elif banknifty["SELL"].iloc[-1]:
    latest_signal = "BANKNIFTY 5M SELL"

# NIFTY 1m
elif nifty_1m["BUY"].iloc[-1]:
    latest_signal = "NIFTY 1M BUY"

elif nifty_1m["SELL"].iloc[-1]:
    latest_signal = "NIFTY 1M SELL"

# BANKNIFTY 1m
elif banknifty_1m["BUY"].iloc[-1]:
    latest_signal = "BANKNIFTY 1M BUY"

elif banknifty_1m["SELL"].iloc[-1]:
    latest_signal = "BANKNIFTY 1M SELL"




if (
    latest_signal
    and
    latest_signal != st.session_state.last_signal
):

    st.session_state.last_signal = latest_signal

    st.toast(
        f"🔔 {latest_signal}",
        icon="🚀"
    )

    send_windows_notification(latest_signal)


def filter_day_data(df, selected_date):

    selected_date = pd.Timestamp(selected_date).date()

    df = df[df.index.date == selected_date]

    return df


# Full data used for pivots
nifty_full = nifty.copy()
banknifty_full = banknifty.copy()

if (
    not st.session_state.today_mode
    and selected_stock_df is not None
):

    stock_full = stock_5m.copy()

    stock_1m_full = stock_1m.copy()

if st.session_state.today_mode:

    # Today's latest view
    nifty = nifty.tail(75).copy()
    banknifty = banknifty.tail(75).copy()

else:

    nifty = filter_day_data(
        nifty_full,
        selected_date
    )

    if selected_stock_df is None:

        banknifty = filter_day_data(
            banknifty_full,
            selected_date
        )

    else:

        stock_5m = filter_day_data(
            stock_full,
            selected_date
        )

    if len(nifty) > 75:
        nifty = nifty.tail(75)

    if selected_stock_df is None:

        if len(banknifty) > 75:
            banknifty = banknifty.tail(75)

    else:

        if len(stock_5m) > 75:
            stock_5m = stock_5m.tail(75)

# Display chart only last 75 candles
nifty = nifty.tail(75).copy()
if selected_stock_df is None:

    banknifty = banknifty.tail(75).copy()

else:

    stock_5m = stock_5m.tail(75).copy()

st_nifty = ta.supertrend(
    high=nifty["High"],
    low=nifty["Low"],
    close=nifty["Close"],
    length=2,
    multiplier=1
)


if st_nifty is not None:
    nifty["SUPERT"] = st_nifty.iloc[:, 0]
else:
    st.error("SuperTrend returned None")
    st.stop()

st_bank = ta.supertrend(
    high=banknifty["High"],
    low=banknifty["Low"],
    close=banknifty["Close"],
    length=2,
    multiplier=1
)


if st_bank is not None:
    banknifty["SUPERT"] = st_bank.iloc[:, 0]
else:
    st.error("SuperTrend returned None")
    st.stop()

def pivot_levels(df, selected_date=None):

    daily = df.resample("D").agg(
        {
            "High": "max",
            "Low": "min",
            "Close": "last"
        }
    ).dropna()

    if selected_date is None:

        prev = daily.iloc[-2]

    else:

        selected_date = pd.Timestamp(selected_date).date()

        daily_dates = [d.date() for d in daily.index]

        if selected_date not in daily_dates:

            return None

        current_idx = daily_dates.index(selected_date)

        if current_idx <= 0:
            return None

        prev = daily.iloc[current_idx - 1]

    h = prev["High"]
    l = prev["Low"]
    c = prev["Close"]

    pp = (h + l + c) / 3

    r1 = 2 * pp - l
    s1 = 2 * pp - h

    r2 = pp + (h - l)
    s2 = pp - (h - l)

    r3 = h + 2 * (pp - l)
    s3 = l - 2 * (h - pp)

    return pp, r1, r2, r3, s1, s2, s3

def mark_pivot_reversal_candles(
    df,
    all_pivots,
    pivot_distance_pct=0.0005
):

    df["PIVOT_REVERSAL"] = False

    bullish_1 = [
        "HAMMER",
        "INVERTED_HAMMER",
        "DRAGONFLY_DOJI"
    ]

    bearish_1 = [
        "SHOOTING_STAR",
        "HANGING_MAN",
        "GRAVESTONE_DOJI"
    ]

    bullish_2 = [
        "BULLISH_ENGULFING",
        "BULLISH_HARAMI",
        "PIERCING",
        "HOMING_PIGEON"
    ]

    bearish_2 = [
        "DARK_CLOUD",
        "BEARISH_HARAMI",
        "COUNTER_ATTACK"
    ]

    bullish_3 = [
        "MORNING_STAR",
        "MORNING_DOJI_STAR",
        "THREE_WHITE_SOLDIERS",
        "THREE_INSIDE",
        "THREE_OUTSIDE"
    ]

    bearish_3 = [
        "EVENING_STAR",
        "EVENING_DOJI_STAR",
        "THREE_BLACK_CROWS"
    ]

    for i in range(len(df)):

        #pattern = ""
        pattern = str(
            df.iloc[i]["PATTERN_NAME"]
        ).strip()

        current_low = df.iloc[i]["Low"]
        current_high = df.iloc[i]["High"]

        if pattern == "":

            body = abs(
                df.iloc[i]["Close"]
                - df.iloc[i]["Open"]
            )

            lower_wick = (
                min(
                    df.iloc[i]["Open"],
                    df.iloc[i]["Close"]
                )
                - df.iloc[i]["Low"]
            )

            upper_wick = (
                df.iloc[i]["High"]
                - max(
                    df.iloc[i]["Open"],
                    df.iloc[i]["Close"]
                )
            )

            for pivot in all_pivots:

                low_near = (
                    abs(current_low - pivot) / pivot
                ) <= pivot_distance_pct

                high_near = (
                    abs(current_high - pivot) / pivot
                ) <= pivot_distance_pct

                pivot_between_buy = (
                    current_low <= pivot <= df.iloc[i]["Close"]
                )

                pivot_between_sell = (
                    df.iloc[i]["Close"] <= pivot <= current_high
                )

                buy_level_valid = (
                    low_near
                    or pivot_between_buy
                )

                sell_level_valid = (
                    high_near
                    or pivot_between_sell
                )

                # BUY REVERSAL
                if (
                    buy_level_valid
                    and body > 0
                    and lower_wick >= body * 0.75
                ):
                    df.iloc[
                        i,
                        df.columns.get_loc(
                            "PIVOT_REVERSAL"
                        )
                    ] = True
                    break

                # SELL REVERSAL
                if (
                    sell_level_valid
                    and body > 0
                    and upper_wick >= body * 0.75
                ):
                    df.iloc[
                        i,
                        df.columns.get_loc(
                            "PIVOT_REVERSAL"
                        )
                    ] = True
                    break

            continue

        current_low = df.iloc[i]["Low"]
        current_high = df.iloc[i]["High"]

        for pivot in all_pivots:

            current_low_near = (
                abs(current_low - pivot) / pivot
            ) <= pivot_distance_pct

            current_high_near = (
                abs(current_high - pivot) / pivot
            ) <= pivot_distance_pct

            # =================================
            # 1 Candle Bullish
            # =================================

            if (
                pattern in bullish_1
                and current_low_near
            ):
                df.iloc[i, df.columns.get_loc(
                    "PIVOT_REVERSAL"
                )] = True
                break

            # =================================
            # 1 Candle Bearish
            # =================================

            if (
                pattern in bearish_1
                and current_high_near
            ):
                df.iloc[i, df.columns.get_loc(
                    "PIVOT_REVERSAL"
                )] = True
                break

            # =================================
            # 2 Candle Bullish
            # Both candle LOW near pivot
            # =================================

            if (
                pattern in bullish_2
                and i >= 1
            ):

                prev_low = df.iloc[i - 1]["Low"]

                prev_low_near = (
                    abs(prev_low - pivot) / pivot
                ) <= pivot_distance_pct

                if (
                    current_low_near
                    and prev_low_near
                ):
                    df.iloc[i, df.columns.get_loc(
                        "PIVOT_REVERSAL"
                    )] = True
                    break

            # =================================
            # 2 Candle Bearish
            # Both candle HIGH near pivot
            # =================================

            if (
                pattern in bearish_2
                and i >= 1
            ):

                prev_high = df.iloc[i - 1]["High"]

                prev_high_near = (
                    abs(prev_high - pivot) / pivot
                ) <= pivot_distance_pct

                if (
                    current_high_near
                    and prev_high_near
                ):
                    df.iloc[i, df.columns.get_loc(
                        "PIVOT_REVERSAL"
                    )] = True
                    break

            # =================================
            # 3 Candle Bullish
            # All 3 LOW near pivot
            # =================================

            if (
                pattern in bullish_3
                and i >= 2
            ):

                prev1_low = df.iloc[i - 1]["Low"]
                prev2_low = df.iloc[i - 2]["Low"]

                prev1_low_near = (
                    abs(prev1_low - pivot) / pivot
                ) <= pivot_distance_pct

                prev2_low_near = (
                    abs(prev2_low - pivot) / pivot
                ) <= pivot_distance_pct

                if (
                    current_low_near
                    and prev1_low_near
                    and prev2_low_near
                ):
                    df.iloc[i, df.columns.get_loc(
                        "PIVOT_REVERSAL"
                    )] = True
                    break

            # =================================
            # 3 Candle Bearish
            # All 3 HIGH near pivot
            # =================================

            if (
                pattern in bearish_3
                and i >= 2
            ):

                prev1_high = df.iloc[i - 1]["High"]
                prev2_high = df.iloc[i - 2]["High"]

                prev1_high_near = (
                    abs(prev1_high - pivot) / pivot
                ) <= pivot_distance_pct

                prev2_high_near = (
                    abs(prev2_high - pivot) / pivot
                ) <= pivot_distance_pct

                if (
                    current_high_near
                    and prev1_high_near
                    and prev2_high_near
                ):
                    df.iloc[i, df.columns.get_loc(
                        "PIVOT_REVERSAL"
                    )] = True
                    break

    return df

def mark_gaussian_reversal_candles(
    df,
    distance_pct=0.0005
):

    df["GAUSSIAN_REVERSAL"] = False

    bullish_1 = [
        "HAMMER",
        "INVERTED_HAMMER",
        "DRAGONFLY_DOJI"
    ]

    bearish_1 = [
        "SHOOTING_STAR",
        "HANGING_MAN",
        "GRAVESTONE_DOJI"
    ]

    bullish_2 = [
        "BULLISH_ENGULFING",
        "BULLISH_HARAMI",
        "PIERCING",
        "HOMING_PIGEON"
    ]

    bearish_2 = [
        "DARK_CLOUD",
        "BEARISH_HARAMI",
        "COUNTER_ATTACK"
    ]

    bullish_3 = [
        "MORNING_STAR",
        "MORNING_DOJI_STAR",
        "THREE_WHITE_SOLDIERS",
        "THREE_INSIDE",
        "THREE_OUTSIDE"
    ]

    bearish_3 = [
        "EVENING_STAR",
        "EVENING_DOJI_STAR",
        "THREE_BLACK_CROWS"
    ]

    for i in range(len(df)):

        #pattern = ""
        pattern = str(
            df.iloc[i]["PATTERN_NAME"]
        ).strip()

        if (
            "PIVOT_REVERSAL" in df.columns
            and df.iloc[i]["PIVOT_REVERSAL"]
        ):
            continue

        current_low = df.iloc[i]["Low"]
        current_high = df.iloc[i]["High"]

        smax = df.iloc[i]["SMAX_5M"]
        smin = df.iloc[i]["SMIN_5M"]

        current_low_near = (
            abs(current_low - smin) / smin
        ) <= distance_pct

        current_high_near = (
            abs(current_high - smax) / smax
        ) <= distance_pct

        smin_between_buy = (
            current_low <= smin <= df.iloc[i]["Close"]
        )

        smax_between_sell = (
            df.iloc[i]["Close"] <= smax <= current_high
        )

        buy_level_valid = (
            current_low_near
            or smin_between_buy
        )

        sell_level_valid = (
            current_high_near
            or smax_between_sell
        )

        if pattern == "":

            body = abs(
                df.iloc[i]["Close"]
                - df.iloc[i]["Open"]
            )

            lower_wick = (
                min(
                    df.iloc[i]["Open"],
                    df.iloc[i]["Close"]
                )
                - df.iloc[i]["Low"]
            )

            upper_wick = (
                df.iloc[i]["High"]
                - max(
                    df.iloc[i]["Open"],
                    df.iloc[i]["Close"]
                )
            )

            if (
                buy_level_valid
                and body > 0
                and lower_wick >= body * 0.75
            ):
                df.iloc[
                    i,
                    df.columns.get_loc(
                        "GAUSSIAN_REVERSAL"
                    )
                ] = True
                continue

            if (
                sell_level_valid
                and body > 0
                and upper_wick >= body * 0.75
            ):
                df.iloc[
                    i,
                    df.columns.get_loc(
                        "GAUSSIAN_REVERSAL"
                    )
                ] = True
                continue

        # 1 Candle Bullish
        if (
            pattern in bullish_1
            and current_low_near
        ):
            df.iloc[
                i,
                df.columns.get_loc(
                    "GAUSSIAN_REVERSAL"
                )
            ] = True
            continue

        # 1 Candle Bearish
        if (
            pattern in bearish_1
            and current_high_near
        ):
            df.iloc[
                i,
                df.columns.get_loc(
                    "GAUSSIAN_REVERSAL"
                )
            ] = True
            continue

        # 2 Candle Bullish
        if (
            pattern in bullish_2
            and i >= 1
        ):

            prev_low = df.iloc[i - 1]["Low"]

            prev_low_near = (
                abs(prev_low - smin) / smin
            ) <= distance_pct

            if (
                current_low_near
                and prev_low_near
            ):
                df.iloc[
                    i,
                    df.columns.get_loc(
                        "GAUSSIAN_REVERSAL"
                    )
                ] = True
                continue

        # 2 Candle Bearish
        if (
            pattern in bearish_2
            and i >= 1
        ):

            prev_high = df.iloc[i - 1]["High"]

            prev_high_near = (
                abs(prev_high - smax) / smax
            ) <= distance_pct

            if (
                current_high_near
                and prev_high_near
            ):
                df.iloc[
                    i,
                    df.columns.get_loc(
                        "GAUSSIAN_REVERSAL"
                    )
                ] = True
                continue

        # 3 Candle Bullish
        if (
            pattern in bullish_3
            and i >= 2
        ):

            prev1_low = df.iloc[i - 1]["Low"]
            prev2_low = df.iloc[i - 2]["Low"]

            prev1_low_near = (
                abs(prev1_low - smin) / smin
            ) <= distance_pct

            prev2_low_near = (
                abs(prev2_low - smin) / smin
            ) <= distance_pct

            if (
                current_low_near
                and prev1_low_near
                and prev2_low_near
            ):
                df.iloc[
                    i,
                    df.columns.get_loc(
                        "GAUSSIAN_REVERSAL"
                    )
                ] = True
                continue

        # 3 Candle Bearish
        if (
            pattern in bearish_3
            and i >= 2
        ):

            prev1_high = df.iloc[i - 1]["High"]
            prev2_high = df.iloc[i - 2]["High"]

            prev1_high_near = (
                abs(prev1_high - smax) / smax
            ) <= distance_pct

            prev2_high_near = (
                abs(prev2_high - smax) / smax
            ) <= distance_pct

            if (
                current_high_near
                and prev1_high_near
                and prev2_high_near
            ):
                df.iloc[
                    i,
                    df.columns.get_loc(
                        "GAUSSIAN_REVERSAL"
                    )
                ] = True

    return df

if nifty.empty:

    st.warning(
        f"No NIFTY data available for {selected_date}"
    )
    st.stop()

nifty = nifty.tail(75).copy()
nifty_fig = go.Figure()

nifty_fig.add_trace(
    go.Candlestick(
        x=nifty.index,
        open=nifty["Open"],
        high=nifty["High"],
        low=nifty["Low"],
        close=nifty["Close"],
        name="Price",

        increasing=dict(
            line=dict(
                color="#00C853",
                width=1.5
            ),
            fillcolor="#00C853"
        ),

        decreasing=dict(
            line=dict(
                color="#FF1744",
                width=1.5
            ),
            fillcolor="#FF1744"
        )
    )
)

nifty_fig.add_trace(
    go.Scatter(
        x=nifty.index,
        y=nifty["GMA"],
        name="Gaussian",
        line=dict(color="blue")
    )
)

nifty_fig.add_trace(
    go.Scatter(
        x=nifty.index,
        y=nifty["SMAX"],
        line=dict(color="purple")
    )
)

nifty_fig.update_yaxes(
    visible=False
)

nifty_fig.add_trace(
    go.Scatter(
        x=nifty.index,
        y=nifty["SMIN"],
        line=dict(color="purple")
    )
)

# 1 Min SMAX on 5 Min Chart
nifty_fig.add_trace(
    go.Scatter(
        x=nifty.index,
        y=nifty["SMAX_1M"],
        line=dict(
            color="white",
            width=2,
            dash="dot"
        )
    )
)

# 1 Min SMIN on 5 Min Chart
nifty_fig.add_trace(
    go.Scatter(
        x=nifty.index,
        y=nifty["SMIN_1M"],
        line=dict(
            color="white",
            width=2,
            dash="dot"
        )
    )
)

if st.session_state.today_mode:

    pivots = pivot_levels(nifty_full)

else:

    pivots = pivot_levels(
        nifty_full,
        selected_date
    )

if pivots is not None:

    pp,r1,r2,r3,s1,s2,s3 = pivots
    nifty = apply_pivot_filter(
        nifty,
        all_pivots=[
            pp,
            r1,
            r2,
            r3,
            s1,
            s2,
            s3
        ],
        pivot_distance_pct=0.002,
        wait_candles=4
    )


buy_df = nifty[nifty["BUY"]]
sell_df = nifty[nifty["SELL"]]

nifty_fig.add_trace(
    go.Scatter(
        x=buy_df.index,
        y=buy_df["Low"]* 0.999,
        mode="markers",
        marker=dict(
            color="green",
            size=16,
            symbol="triangle-up"
        ),
        name="BUY"
    )
)


nifty_fig.add_trace(
    go.Scatter(
        x=sell_df.index,
        y=sell_df["High"] * 1.001,
        mode="markers",
        marker=dict(
            color="red",
            size=16,
            symbol="triangle-down"
        ),
        name="SELL"
    )
)


pivot_levels_to_show = [
    (pp,"PP"),
    (r1,"R1"),
    (r2,"R2"),
    (r3,"R3"),
    (s1,"S1"),
    (s2,"S2"),
    (s3,"S3")
]

chart_high = nifty["High"].max()
chart_low  = nifty["Low"].min()

buffer = (chart_high - chart_low) * 0.10

pivot_colors = {
    "PP": "yellow",
    "R1": "red",
    "R2": "darkred",
    "R3": "darkred",
    "S1": "green",
    "S2": "darkgreen",
    "S3": "darkgreen"
}

for level,name in pivot_levels_to_show:

    if chart_low - buffer <= level <= chart_high + buffer:

        nifty_fig.add_hline(
            y=level,
            line_color=pivot_colors[name],
            opacity=0.8,
            annotation_text=name,
            annotation_position="right"
        )

nifty_fig.update_layout(
    showlegend=False,
    height=500,
    bargap=0,
    margin=dict(
        l=2,
        r=2,
        t=1,
        b=10
    ),
    xaxis_rangeslider_visible=False
)

holiday_days = get_market_holidays(nifty)

nifty_fig.update_xaxes(
    rangebreaks=[
        dict(bounds=["sat", "mon"]),
        dict(values=holiday_days),
        dict(bounds=[15.5, 9.25], pattern="hour")
    ],
    showgrid=False,
    tickformat="%H:%M"
)
banknifty = banknifty.tail(75).copy()

if (
    not st.session_state.today_mode
    and selected_stock_df is not None
):

    banknifty = stock_5m.copy()

bank_fig = go.Figure()

bank_fig.add_trace(
    go.Candlestick(
        x=banknifty.index,
        open=banknifty["Open"],
        high=banknifty["High"],
        low=banknifty["Low"],
        close=banknifty["Close"],
        name="Price",

        increasing=dict(
            line=dict(
                color="#00C853",
                width=1.5
            ),
            fillcolor="#00C853"
        ),

        decreasing=dict(
            line=dict(
                color="#FF1744",
                width=1.5
            ),
            fillcolor="#FF1744"
        )
    )
)

bank_fig.add_trace(
    go.Scatter(
        x=banknifty.index,
        y=banknifty["GMA"],
        name="Gaussian",
        line=dict(color="blue")
    )
)

bank_fig.add_trace(
    go.Scatter(
        x=banknifty.index,
        y=banknifty["SMAX"],
        line=dict(color="purple")
    )
)

bank_fig.add_trace(
    go.Scatter(
        x=banknifty.index,
        y=banknifty["SMIN"],
        line=dict(color="purple")
    )
)

# 1 Min SMAX
bank_fig.add_trace(
    go.Scatter(
        x=banknifty.index,
        y=banknifty["SMAX_1M"],
        line=dict(
            color="white",
            width=2,
            dash="dot"
        )
    )
)

# 1 Min SMIN
bank_fig.add_trace(
    go.Scatter(
        x=banknifty.index,
        y=banknifty["SMIN_1M"],
        line=dict(
            color="white",
            width=2,
            dash="dot"
        )
    )
)

bank_fig.update_yaxes(
    visible=False
)


pivot_source = (
    stock_full
    if selected_stock_df is not None
    else banknifty_full
)

if st.session_state.today_mode:

    pivots = pivot_levels(pivot_source)

else:

    pivots = pivot_levels(
        pivot_source,
        selected_date
    )

if pivots is not None:

    pp,r1,r2,r3,s1,s2,s3 = pivots
    banknifty = apply_pivot_filter(
        banknifty,
        all_pivots=[
            pp,
            r1,
            r2,
            r3,
            s1,
            s2,
            s3
        ],
        pivot_distance_pct=0.002,
        wait_candles=4
    )

buy_df = banknifty[banknifty["BUY"]]
sell_df = banknifty[banknifty["SELL"]]

bank_fig.add_trace(
    go.Scatter(
        x=buy_df.index,
        y=buy_df["Low"]* 0.999,
        mode="markers",
        marker=dict(
            color="green",
            size=16,
            symbol="triangle-up"
        ),
        name="BUY"
    )
)

bank_fig.add_trace(
    go.Scatter(
        x=sell_df.index,
        y=sell_df["High"]* 1.001,
        mode="markers",
        marker=dict(
            color="red",
            size=16,
            symbol="triangle-down"
        ),
        name="SELL"
    )
)

pivot_levels_to_show = [
    (pp,"PP"),
    (r1,"R1"),
    (r2,"R2"),
    (r3,"R3"),
    (s1,"S1"),
    (s2,"S2"),
    (s3,"S3")
]

chart_high = banknifty["High"].max()
chart_low  = banknifty["Low"].min()

buffer = (chart_high - chart_low) * 0.10

pivot_colors = {
    "PP": "yellow",
    "R1": "red",
    "R2": "darkred",
    "R3": "darkred",
    "S1": "green",
    "S2": "darkgreen",
    "S3": "darkgreen"
}

for level,name in pivot_levels_to_show:

    if chart_low - buffer <= level <= chart_high + buffer:

        bank_fig.add_hline(
            y=level,
            line_color=pivot_colors[name],
            opacity=0.8,
            annotation_text=name,
            annotation_position="right"
        )

bank_fig.update_layout(
    showlegend=False,
    height=500,
    bargap=0,
    margin=dict(
        l=2,
        r=2,
        t=1,
        b=10
    ),
    xaxis_rangeslider_visible=False
)

holiday_days = get_market_holidays(banknifty)

bank_fig.update_xaxes(
    rangebreaks=[
        dict(bounds=["sat", "mon"]),
        dict(values=holiday_days),
        dict(bounds=[15.5, 9.25], pattern="hour")
    ],
    showgrid=False,
    tickformat="%H:%M"
)

col1, col2 = st.columns(2)

with col1:
    st.markdown("""
    <h2 style="
        margin-bottom:-10px;
        margin-top:0px;
        text-align:center;
    ">
    NIFTY
    </h2>
    """, unsafe_allow_html=True)
    st.plotly_chart(
        nifty_fig,
        width="stretch",
        config={"displayModeBar": False}
    )

with col2:
    st.markdown(f"""
    <h2 style="
        margin-bottom:-10px;
        margin-top:0px;
        text-align:center;
    ">
    {
        "BANKNIFTY"
        if selected_stock_df is None
        else selected_stock
    }
    </h2>
    """, unsafe_allow_html=True)
    st.plotly_chart(
        bank_fig,
        width="stretch",
        config={"displayModeBar": False}
    )

st.markdown("---")

col3, col4 = st.columns(2)

with col3:

    st.markdown("""
    <h2 style="
        margin-bottom:-10px;
        margin-top:0px;
        text-align:center;
    ">
    NIFTY 1 MIN
    </h2>
    """, unsafe_allow_html=True)

    if st.session_state.today_mode:

        today_date = pd.Timestamp.today().date()

        nifty_1m = nifty_1m[
            nifty_1m.index.date == today_date
        ].copy()

    else:

        nifty_1m = filter_day_data(
            nifty_1m,
            selected_date
        )

        nifty_1m = filter_day_data(
            nifty_1m,
            selected_date
        )

    nifty_1m_fig = go.Figure()

    nifty_1m_fig.add_trace(
        go.Candlestick(
            x=nifty_1m.index,
            open=nifty_1m["Open"],
            high=nifty_1m["High"],
            low=nifty_1m["Low"],
            close=nifty_1m["Close"],
            increasing=dict(
                line=dict(color="#00C853", width=1.5),
                fillcolor="#00C853"
            ),
            decreasing=dict(
                line=dict(color="#FF1744", width=1.5),
                fillcolor="#FF1744"
            )
        )
    )


    nifty_1m_fig.add_trace(
        go.Scatter(
            x=nifty_1m.index,
            y=nifty_1m["GMA"],
            line=dict(color="blue")
        )
    )

    nifty_1m_fig.add_trace(
        go.Scatter(
            x=nifty_1m.index,
            y=nifty_1m["SMAX"],
            line=dict(color="purple")
        )
    )

    nifty_1m_fig.add_trace(
        go.Scatter(
            x=nifty_1m.index,
            y=nifty_1m["SMIN"],
            line=dict(color="purple")
        )
    )

    # 5 Min SMAX projected smoothly
    nifty_1m_fig.add_trace(
        go.Scatter(
            x=nifty_1m.index,
            y=nifty_1m["SMAX_5M"],
            line=dict(
                color="white",
                width=2,
                dash="dot"
            )
        )
    )

    # 5 Min SMIN projected smoothly
    nifty_1m_fig.add_trace(
        go.Scatter(
            x=nifty_1m.index,
            y=nifty_1m["SMIN_5M"],
            line=dict(
                color="white",
                width=2,
                dash="dot"
            )
        )
    )

    # EMA 44
    nifty_1m_fig.add_trace(
        go.Scatter(
            x=nifty_1m.index,
            y=nifty_1m["EMA44"],
            name="EMA 44",
            line=dict(
                color="orange",
                width=4
            )
        )
    )

    # EMA 200
    nifty_1m_fig.add_trace(
        go.Scatter(
            x=nifty_1m.index,
            y=nifty_1m["EMA200"],
            name="EMA 200",
            line=dict(
                color="cyan",
                width=4
            )
        )
    )


    buy_df = nifty_1m[nifty_1m["BUY"]]
    sell_df = nifty_1m[nifty_1m["SELL"]]


    if st.session_state.today_mode:

        pivots_1m = pivot_levels(nifty_full)

    else:

        pivots_1m = pivot_levels(
            nifty_full,
            selected_date
        )

    if pivots_1m is not None:

        pp,r1,r2,r3,s1,s2,s3 = pivots_1m

        nifty_1m = mark_pivot_reversal_candles(
                    nifty_1m,
                    [
                        pp,
                        r1,
                        r2,
                        r3,
                        s1,
                        s2,
                        s3
                    ],
                    pivot_distance_pct=0.0005
                )

        nifty_1m = mark_gaussian_reversal_candles(
            nifty_1m,
            distance_pct=0.0002
        )

        pivot_pattern_df = nifty_1m[
                nifty_1m["PIVOT_REVERSAL"]
            ]

        gaussian_pattern_df = nifty_1m[
            nifty_1m["GAUSSIAN_REVERSAL"]
        ]

        if not pivot_pattern_df.empty:

            nifty_1m_fig.add_trace(
                go.Candlestick(
                    x=pivot_pattern_df.index,
                    open=pivot_pattern_df["Open"],
                    high=pivot_pattern_df["High"],
                    low=pivot_pattern_df["Low"],
                    close=pivot_pattern_df["Close"],
                    increasing=dict(
                        line=dict(color="yellow", width=3),
                        fillcolor="yellow"
                    ),
                    decreasing=dict(
                        line=dict(color="yellow", width=3),
                        fillcolor="yellow"
                    ),
                    showlegend=False
                )
            )

        if not gaussian_pattern_df.empty:

            nifty_1m_fig.add_trace(
                    go.Candlestick(
                        x=gaussian_pattern_df.index,
                        open=gaussian_pattern_df["Open"],
                        high=gaussian_pattern_df["High"],
                        low=gaussian_pattern_df["Low"],
                        close=gaussian_pattern_df["Close"],
                        increasing=dict(
                            line=dict(color="deeppink", width=3),
                            fillcolor="deeppink"
                        ),
                        decreasing=dict(
                            line=dict(color="deeppink", width=3),
                            fillcolor="deeppink"
                        ),
                        showlegend=False
                    )
                )

        pivot_levels_to_show = [
            (pp,"PP"),
            (r1,"R1"),
            (r2,"R2"),
            (r3,"R3"),
            (s1,"S1"),
            (s2,"S2"),
            (s3,"S3")
        ]

        chart_high = nifty_1m["High"].max()
        chart_low = nifty_1m["Low"].min()

        buffer = (chart_high - chart_low) * 0.10

        y_min = chart_low - buffer
        y_max = chart_high + buffer

        pivot_colors = {
            "PP": "yellow",
            "R1": "red",
            "R2": "darkred",
            "R3": "darkred",
            "S1": "green",
            "S2": "darkgreen",
            "S3": "darkgreen"
        }

        for level,name in pivot_levels_to_show:

            if chart_low - buffer <= level <= chart_high + buffer:

                nifty_1m_fig.add_hline(
                    y=level,
                    line_color=pivot_colors[name],
                    opacity=0.8,
                    annotation_text=name,
                    annotation_position="right"
                )

    nifty_1m_fig.add_trace(
        go.Scatter(
            x=buy_df.index,
            y=buy_df["Low"] * 0.999,
            mode="markers",
            marker=dict(
                color="green",
                size=16,
                symbol="triangle-up"
            )
        )
    )

    nifty_1m_fig.add_trace(
        go.Scatter(
            x=sell_df.index,
            y=sell_df["High"] * 1.001,
            mode="markers",
            marker=dict(
                color="red",
                size=16,
                symbol="triangle-down"
            )
        )
    )

    buy_5m = nifty_1m[
        nifty_1m["BUY_5M_BREAK"]
    ]

    sell_5m = nifty_1m[
        nifty_1m["SELL_5M_BREAK"]
    ]

    initial_bars = 60

    if len(nifty_1m) > initial_bars:

        start_x = nifty_1m.index[-initial_bars]

        end_x = (
            nifty_1m.index[-1]
            + pd.Timedelta(minutes=10)
        )

    else:

        start_x = nifty_1m.index[0]

        end_x = (
            nifty_1m.index[-1]
            + pd.Timedelta(minutes=10)
        )

    nifty_1m_fig.update_layout(
        showlegend=False,
        height=750,
        bargap=0,
        margin=dict(
            l=2,
            r=2,
            t=1,
            b=5
        ),
        xaxis_rangeslider_visible=True
    )

    nifty_1m_fig.update_xaxes(
        range=[start_x, end_x]
    )

    nifty_1m_fig.update_yaxes(
        range=[y_min, y_max]
    )

    st.plotly_chart(
        nifty_1m_fig,
        width="stretch",
        config={"displayModeBar": False}
    )

with col4:

    if (
        not st.session_state.today_mode
        and selected_stock_df is not None
    ):

        banknifty_1m = stock_1m.copy()

    st.markdown(f"""
    <h2 style="
        margin-bottom:-10px;
        margin-top:0px;
        text-align:center;
    ">
    {
        "BANKNIFTY 1 MIN"
        if selected_stock_df is None
        else f"{selected_stock} 1 MIN"
    }
    </h2>
    """, unsafe_allow_html=True)

    if st.session_state.today_mode:

        today_date = pd.Timestamp.today().date()

        banknifty_1m = banknifty_1m[
            banknifty_1m.index.date == today_date
        ].copy()

    else:

        banknifty_1m = filter_day_data(
            banknifty_1m,
            selected_date
        )

    bank_1m_fig = go.Figure()

    bank_1m_fig.add_trace(
        go.Candlestick(
            x=banknifty_1m.index,
            open=banknifty_1m["Open"],
            high=banknifty_1m["High"],
            low=banknifty_1m["Low"],
            close=banknifty_1m["Close"],
            increasing=dict(
                line=dict(color="#00C853", width=1.5),
                fillcolor="#00C853"
            ),
            decreasing=dict(
                line=dict(color="#FF1744", width=1.5),
                fillcolor="#FF1744"
            )
        )
    )

    bank_1m_fig.add_trace(
        go.Scatter(
            x=banknifty_1m.index,
            y=banknifty_1m["GMA"],
            line=dict(color="blue")
        )
    )

    bank_1m_fig.add_trace(
        go.Scatter(
            x=banknifty_1m.index,
            y=banknifty_1m["SMAX"],
            line=dict(color="purple")
        )
    )

    bank_1m_fig.add_trace(
        go.Scatter(
            x=banknifty_1m.index,
            y=banknifty_1m["SMIN"],
            line=dict(color="purple")
        )
    )

    # 5 Min SMAX
    bank_1m_fig.add_trace(
        go.Scatter(
            x=banknifty_1m.index,
            y=banknifty_1m["SMAX_5M"],
            line=dict(
                color="white",
                width=2,
                dash="dot"
            )
        )
    )

    # 5 Min SMIN
    bank_1m_fig.add_trace(
        go.Scatter(
            x=banknifty_1m.index,
            y=banknifty_1m["SMIN_5M"],
            line=dict(
                color="white",
                width=2,
                dash="dot"
            )
        )
    )

    # EMA 44
    bank_1m_fig.add_trace(
        go.Scatter(
            x=banknifty_1m.index,
            y=banknifty_1m["EMA44"],
            name="EMA 44",
            line=dict(
                color="orange",
                width=4
            )
        )
    )

    # EMA 200
    bank_1m_fig.add_trace(
        go.Scatter(
            x=banknifty_1m.index,
            y=banknifty_1m["EMA200"],
            name="EMA 200",
            line=dict(
                color="cyan",
                width=4
            )
        )
    )

    buy_df = banknifty_1m[banknifty_1m["BUY"]]
    sell_df = banknifty_1m[banknifty_1m["SELL"]]


    pivot_source = (
        stock_full
        if selected_stock_df is not None
        else banknifty_full
    )

    if st.session_state.today_mode:

        pivots_1m = pivot_levels(pivot_source)

    else:

        pivots_1m = pivot_levels(
            pivot_source,
            selected_date
        )

    if pivots_1m is not None:

        pp,r1,r2,r3,s1,s2,s3 = pivots_1m

        banknifty_1m = mark_pivot_reversal_candles(
            banknifty_1m,
            [
                pp,r1,r2,r3,s1,s2,s3
            ],
            pivot_distance_pct=0.0005
        )

        banknifty_1m = mark_gaussian_reversal_candles(
            banknifty_1m,
            distance_pct=0.0002
        )

        pivot_pattern_df = banknifty_1m[
            banknifty_1m["PIVOT_REVERSAL"]
        ]

        gaussian_pattern_df = banknifty_1m[
            banknifty_1m["GAUSSIAN_REVERSAL"]
        ]

        if not pivot_pattern_df.empty:

            bank_1m_fig.add_trace(
                go.Candlestick(
                    x=pivot_pattern_df.index,
                    open=pivot_pattern_df["Open"],
                    high=pivot_pattern_df["High"],
                    low=pivot_pattern_df["Low"],
                    close=pivot_pattern_df["Close"],
                    increasing=dict(
                        line=dict(color="yellow", width=3),
                        fillcolor="yellow"
                    ),
                    decreasing=dict(
                        line=dict(color="yellow", width=3),
                        fillcolor="yellow"
                    ),
                    showlegend=False
                )
            )

        if not gaussian_pattern_df.empty:

            bank_1m_fig.add_trace(
                go.Candlestick(
                    x=gaussian_pattern_df.index,
                    open=gaussian_pattern_df["Open"],
                    high=gaussian_pattern_df["High"],
                    low=gaussian_pattern_df["Low"],
                    close=gaussian_pattern_df["Close"],
                    increasing=dict(
                        line=dict(color="deeppink", width=3),
                        fillcolor="deeppink"
                    ),
                    decreasing=dict(
                        line=dict(color="deeppink", width=3),
                        fillcolor="deeppink"
                    ),
                    showlegend=False
                )
            )

        pivot_levels_to_show = [
            (pp,"PP"),
            (r1,"R1"),
            (r2,"R2"),
            (r3,"R3"),
            (s1,"S1"),
            (s2,"S2"),
            (s3,"S3")
        ]

        chart_high = banknifty_1m["High"].max()
        chart_low = banknifty_1m["Low"].min()

        buffer = (chart_high - chart_low) * 0.10

        y_min = chart_low - buffer
        y_max = chart_high + buffer

        pivot_colors = {
            "PP": "yellow",
            "R1": "red",
            "R2": "darkred",
            "R3": "darkred",
            "S1": "green",
            "S2": "darkgreen",
            "S3": "darkgreen"
        }

        for level,name in pivot_levels_to_show:

            if chart_low - buffer <= level <= chart_high + buffer:

                bank_1m_fig.add_hline(
                    y=level,
                    line_color=pivot_colors[name],
                    opacity=0.8,
                    annotation_text=name,
                    annotation_position="right"
                )

    bank_1m_fig.add_trace(
        go.Scatter(
            x=buy_df.index,
            y=buy_df["Low"] * 0.999,
            mode="markers",
            marker=dict(
                color="green",
                size=16,
                symbol="triangle-up"
            )
        )
    )

    bank_1m_fig.add_trace(
        go.Scatter(
            x=sell_df.index,
            y=sell_df["High"] * 1.001,
            mode="markers",
            marker=dict(
                color="red",
                size=16,
                symbol="triangle-down"
            )
        )
    )

    initial_bars = 60

    if len(banknifty_1m) > initial_bars:

        start_x = banknifty_1m.index[-initial_bars]

        end_x = (
            banknifty_1m.index[-1]
            + pd.Timedelta(minutes=10)
        )

    else:

        start_x = banknifty_1m.index[0]

        end_x = (
            banknifty_1m.index[-1]
            + pd.Timedelta(minutes=10)
        )

    bank_1m_fig.update_layout(
        showlegend=False,
        height=750,
        bargap=0,
        margin=dict(
            l=2,
            r=2,
            t=1,
            b=5
        ),
        xaxis_rangeslider_visible=True
    )

    bank_1m_fig.update_xaxes(
        range=[start_x, end_x]
    )

    bank_1m_fig.update_yaxes(
        range=[y_min, y_max]
    )

    st.plotly_chart(
        bank_1m_fig,
        width="stretch",
        config={"displayModeBar": False}
    )

if st.button("Test Notification"):

    send_windows_notification(
        "TEST BUY SIGNAL"
    )

    st.success(
        "Notification Sent"
    )