import pandas as pd
import numpy as np

def smma(series, length):
    return series.ewm(span=length, adjust=False).mean()

def calculate_gaussian(df, period=20):

    src = (df["High"] + df["Low"] + df["Close"]) / 3

    # -------------------------
    # CURRENT LOGIC
    # (Less overnight influence)
    # -------------------------

    trade_date = pd.to_datetime(df.index).date

    gma = pd.Series(index=df.index, dtype=float)

    for date, idx in df.groupby(trade_date).groups.items():

        day_src = src.loc[idx]

        base = day_src.iloc[0]

        movement = day_src - base

        day_gma = movement.ewm(
            span=period,
            adjust=False
        ).mean()

        gma.loc[idx] = day_gma + base

    signal = gma.groupby(trade_date).transform(
        lambda x: x.ewm(span=9, adjust=False).mean()
    )

    # -------------------------
    # OLD LOGIC
    # (Yesterday affects today)
    # -------------------------

    # gma = src.ewm(
    #     span=period,
    #     adjust=False
    # ).mean()

    # signal = gma.ewm(
    #     span=9,
    #     adjust=False
    # ).mean()

    return gma, signal

def gaussian_channel(df):

    gma, signal = calculate_gaussian(df)

    mult = 0.9

    atr = (
        df["High"] - df["Low"]
    ).rolling(14).mean()

    smax = gma + (atr * mult)
    smin = gma - (atr * mult)

    df["GMA"] = gma
    df["GSIGNAL"] = signal
    df["SMAX"] = smax
    df["SMIN"] = smin

    return df

def add_signals(df):

    buy = (
        (df["Close"] > df["SMAX"])
        &
        (df["Low"] < df["SMAX"])
    )

    sell = (
        (df["Close"] < df["SMIN"])
        &
        (df["High"] > df["SMIN"])
    )

    df["BUY"] = buy
    df["SELL"] = sell
    return df

def add_confirmed_signals(
    nifty,
    banknifty
):

    # -----------------
    # NIFTY SIGNALS
    # -----------------

    nifty_buy = (
        (nifty["Close"] > nifty["SMAX"])
        &
        (nifty["Close"].shift(1) <= nifty["SMAX"].shift(1))
        &
        (banknifty["Close"] >= banknifty["SMIN"])
    )

    nifty_sell = (
        (nifty["Close"] < nifty["SMIN"])
        &
        (nifty["Close"].shift(1) >= nifty["SMIN"].shift(1))
        &
        (banknifty["Close"] <= banknifty["SMAX"])
    )

    nifty["BUY"] = nifty_buy
    nifty["SELL"] = nifty_sell

    # -----------------
    # BANKNIFTY SIGNALS
    # -----------------

    bank_buy = (
        (banknifty["Close"] > banknifty["SMAX"])
        &
        (banknifty["Close"].shift(1) <= banknifty["SMAX"].shift(1))
        &
        (nifty["Close"] >= nifty["SMIN"])
    )

    bank_sell = (
        (banknifty["Close"] < banknifty["SMIN"])
        &
        (banknifty["Close"].shift(1) >= banknifty["SMIN"].shift(1))
        &
        (nifty["Close"] <= nifty["SMAX"])
    )

    banknifty["BUY"] = bank_buy
    banknifty["SELL"] = bank_sell

    return nifty, banknifty

def apply_pivot_filter(
    df,
    all_pivots,
    pivot_distance_pct=0.00010,
    wait_candles=4
):

    buy_final = pd.Series(False, index=df.index)
    sell_final = pd.Series(False, index=df.index)

    # ------------------
    # BUY FILTER
    # ------------------

    buy_idx = df.index[df["BUY"]]

    for idx in buy_idx:

        pos = df.index.get_loc(idx)

        close_price = df.loc[idx, "Close"]

        future_pivots = sorted([
            p for p in all_pivots
            if p > close_price
        ])

        if not future_pivots:
            buy_final.loc[idx] = True
            continue

        nearest_pivot = future_pivots[0]

        distance_pct = (
            nearest_pivot - close_price
        ) / close_price

        if distance_pct > pivot_distance_pct:

            buy_final.loc[idx] = True
            continue

        for j in range(
            pos + 1,
            min(pos + wait_candles + 1, len(df))
        ):

            if df.iloc[j]["High"] > nearest_pivot:

                buy_final.iloc[j] = True
                break

    # ------------------
    # SELL FILTER
    # ------------------

    sell_idx = df.index[df["SELL"]]

    for idx in sell_idx:

        pos = df.index.get_loc(idx)

        close_price = df.loc[idx, "Close"]

        lower_pivots = sorted([
            p for p in all_pivots
            if p < close_price
        ])

        if not lower_pivots:

            sell_final.loc[idx] = True
            continue

        nearest_pivot = lower_pivots[-1]

        distance_pct = (
            close_price - nearest_pivot
        ) / close_price

        if distance_pct > pivot_distance_pct:

            sell_final.loc[idx] = True
            continue

        for j in range(
            pos + 1,
            min(pos + wait_candles + 1, len(df))
        ):

            if df.iloc[j]["Low"] < nearest_pivot:

                sell_final.iloc[j] = True
                break

    df["BUY"] = buy_final
    df["SELL"] = sell_final

    return df

def add_stock_confirmed_signals(
    stock,
    nifty
):
    nifty = nifty.reindex(
        stock.index,
        method="ffill"
    )

    stock_buy = (
        (stock["Close"] > stock["SMAX"])
        &
        (stock["Close"].shift(1) <= stock["SMAX"].shift(1))
        &
        (nifty["Close"] >= nifty["SMIN"])
    )

    stock_sell = (
        (stock["Close"] < stock["SMIN"])
        &
        (stock["Close"].shift(1) >= stock["SMIN"].shift(1))
        &
        (nifty["Close"] <= nifty["SMAX"])
    )

    stock["BUY"] = stock_buy
    stock["SELL"] = stock_sell

    return stock

def add_5m_breakout_signals(
    df,
    cooldown=3
):

    buy_cross = (
        (df["Close"] > df["SMAX_5M"])
        &
        (
            df["Close"].shift(1)
            <=
            df["SMAX_5M"].shift(1)
        )
    )

    sell_cross = (
        (df["Close"] < df["SMIN_5M"])
        &
        (
            df["Close"].shift(1)
            >=
            df["SMIN_5M"].shift(1)
        )
    )

    buy_final = pd.Series(
        False,
        index=df.index
    )

    sell_final = pd.Series(
        False,
        index=df.index
    )

    last_buy = -999
    last_sell = -999

    for i in range(len(df)):

        if buy_cross.iloc[i]:

            if (i - last_buy) > cooldown:

                buy_final.iloc[i] = True
                last_buy = i

        if sell_cross.iloc[i]:

            if (i - last_sell) > cooldown:

                sell_final.iloc[i] = True
                last_sell = i

    df["BUY_5M_BREAK"] = buy_final
    df["SELL_5M_BREAK"] = sell_final

    return df
