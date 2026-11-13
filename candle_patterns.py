import pandas as pd
import talib


def detect_candle_patterns(df):

    o = df["Open"].values
    h = df["High"].values
    l = df["Low"].values
    c = df["Close"].values

    patterns = {

        # =================================
        # 1 Candle Bullish
        # =================================

        "HAMMER":
            talib.CDLHAMMER(o, h, l, c),

        "INVERTED_HAMMER":
            talib.CDLINVERTEDHAMMER(o, h, l, c),

        "DRAGONFLY_DOJI":
            talib.CDLDRAGONFLYDOJI(o, h, l, c),

        # =================================
        # 1 Candle Bearish
        # =================================

        "SHOOTING_STAR":
            talib.CDLSHOOTINGSTAR(o, h, l, c),

        "HANGING_MAN":
            talib.CDLHANGINGMAN(o, h, l, c),

        "GRAVESTONE_DOJI":
            talib.CDLGRAVESTONEDOJI(o, h, l, c),

        # =================================
        # 2 Candle Bullish
        # =================================

        "BULLISH_ENGULFING":
            talib.CDLENGULFING(o, h, l, c),

        "BULLISH_HARAMI":
            talib.CDLHARAMI(o, h, l, c),

        "PIERCING":
            talib.CDLPIERCING(o, h, l, c),

        "HOMING_PIGEON":
            talib.CDLHOMINGPIGEON(o, h, l, c),

        # =================================
        # 2 Candle Bearish
        # =================================

        "DARK_CLOUD":
            talib.CDLDARKCLOUDCOVER(o, h, l, c),

        "BEARISH_HARAMI":
            talib.CDLHARAMI(o, h, l, c),

        "COUNTER_ATTACK":
            talib.CDLCOUNTERATTACK(o, h, l, c),

        # =================================
        # 3 Candle Bullish
        # =================================

        "MORNING_STAR":
            talib.CDLMORNINGSTAR(o, h, l, c),

        "MORNING_DOJI_STAR":
            talib.CDLMORNINGDOJISTAR(o, h, l, c),

        "THREE_WHITE_SOLDIERS":
            talib.CDL3WHITESOLDIERS(o, h, l, c),

        "THREE_INSIDE":
            talib.CDL3INSIDE(o, h, l, c),

        "THREE_OUTSIDE":
            talib.CDL3OUTSIDE(o, h, l, c),

        # =================================
        # 3 Candle Bearish
        # =================================

        "EVENING_STAR":
            talib.CDLEVENINGSTAR(o, h, l, c),

        "EVENING_DOJI_STAR":
            talib.CDLEVENINGDOJISTAR(o, h, l, c),

        "THREE_BLACK_CROWS":
            talib.CDL3BLACKCROWS(o, h, l, c),

        # =================================
        # Neutral
        # =================================

        "DOJI":
            talib.CDLDOJI(o, h, l, c),

        "LONG_LEGGED_DOJI":
            talib.CDLLONGLEGGEDDOJI(o, h, l, c)
    }

    # ==========================
    # Create Columns
    # ==========================

    for name, values in patterns.items():
        df[name] = values

    # ==========================
    # Final Pattern Detection
    # ==========================

    df["PATTERN_NAME"] = ""
    df["PATTERN_TYPE"] = ""

    for pattern in patterns.keys():

        bullish_mask = df[pattern] > 0
        bearish_mask = df[pattern] < 0

        df.loc[
            bullish_mask,
            "PATTERN_NAME"
        ] = pattern

        df.loc[
            bearish_mask,
            "PATTERN_NAME"
        ] = pattern

        df.loc[
            bullish_mask,
            "PATTERN_TYPE"
        ] = "BULLISH"

        df.loc[
            bearish_mask,
            "PATTERN_TYPE"
        ] = "BEARISH"

    return df