import yfinance as yf
import pandas as pd

def get_nifty(period, interval="5m"):

    df = yf.download(
        "^NSEI",
        period=period,
        interval=interval,
        progress=False,
        auto_adjust=False
    )

    if isinstance(df.columns, pd.MultiIndex):
        df.columns = [col[0] for col in df.columns]

    return df


def get_banknifty(period, interval="5m"):

    df = yf.download(
        "^NSEBANK",
        period=period,
        interval=interval,
        progress=False,
        auto_adjust=False
    )

    if isinstance(df.columns, pd.MultiIndex):
        df.columns = [col[0] for col in df.columns]

    return df


import streamlit as st

@st.cache_data(ttl=10)
def load_indices(period, interval="5m"):

    nifty = get_nifty(period, interval)
    banknifty = get_banknifty(period, interval)

    return nifty, banknifty