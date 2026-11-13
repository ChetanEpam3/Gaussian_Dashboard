import os
import pandas as pd
import yfinance as yf

DATA_FOLDER = r"C:\Users\ChetanPatil3\OneDrive - EPAM\Stock_Market_Data"

SYMBOLS = [
    "^NSEI",
    "^NSEBANK",

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
    "TMCV.NS",
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

def update_all_1m_data():

    os.makedirs(DATA_FOLDER, exist_ok=True)

    for symbol in SYMBOLS:

        try:

            print(f"Downloading {symbol}")

            df = yf.download(
                symbol,
                period="7d",
                interval="1m",
                progress=False,
                auto_adjust=False
            )

            if df.empty:
                continue

            if isinstance(df.columns, pd.MultiIndex):
                df.columns = [col[0] for col in df.columns]

            df = df.reset_index()

            csv_name = (
                symbol
                .replace("^", "")
                .replace(".", "_")
            ) + ".csv"

            csv_path = os.path.join(
                DATA_FOLDER,
                csv_name
            )

            if os.path.exists(csv_path):

                old_df = pd.read_csv(csv_path)

                old_df["Datetime"] = pd.to_datetime(
                    old_df["Datetime"]
                )

                df["Datetime"] = pd.to_datetime(
                    df["Datetime"]
                )

                df = pd.concat(
                    [old_df, df],
                    ignore_index=True
                )

                df.drop_duplicates(
                    subset=["Datetime"],
                    keep="last",
                    inplace=True
                )

                df.sort_values(
                    "Datetime",
                    inplace=True
                )

            df.to_csv(
                csv_path,
                index=False
            )

            print(f"Saved : {csv_name}")

        except Exception as e:

            print(symbol, e)