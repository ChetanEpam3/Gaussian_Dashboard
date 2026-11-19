# Range Engine Research Documentation

## 1. Purpose

This document describes the complete range-engine research framework developed in this workspace.

The first objective is not to create buy or sell signals. The objective is to determine whether a parameter combination creates a meaningful, stable SMax/SMin range.

Only after range quality is understood should the system measure:

- Whether SMax/SMin breakouts are genuine or false.
- How much price follows through after a breakout.
- Whether upper or lower breakouts perform differently.
- Whether a breakout should become a trade entry.
- Whether additional EMA, pivot, candle, or market-confirmation logic should be applied.

The research order is:

```text
Historical data
    -> Generate range
    -> Evaluate range quality
    -> Compare parameter combinations
    -> Classify market regimes
    -> Evaluate breakout reliability
    -> Add entry logic
    -> Add trade filters
```

## 2. Existing Range Engine

The range engine is implemented in `gaussian.py`.

The Gaussian centerline is calculated with:

```text
source = (High + Low + Close) / 3
GMA = intraday session Gaussian moving average
GSIGNAL = intraday session smoothing of GMA
```

The current implementation recalculates GMA from the first candle of each trading session. It does not directly carry the old continuous GMA into the next session.

The range is generated as:

```text
SMax = GMA + ATR * multiplier
SMin = GMA - ATR * multiplier
```

The current baseline parameters are:

```text
GMA period = 20
GSIGNAL period = 9
ATR period = 14
ATR multiplier = 0.9
ATR method = high-low range
```

The baseline remains the live fallback. Existing live dashboard behavior is not changed when a range candidate is generated or a parameter store is loaded.

### Important parameter distinction

The current GSIGNAL period does not change SMax/SMin directly. It changes GSIGNAL, which is a separate line.

The current range-width inputs are:

1. GMA period.
2. ATR period.
3. ATR method.
4. ATR multiplier.

## 3. ATR Methods

Two ATR methods are available.

### High-low ATR

```text
True Range = High - Low
ATR = rolling mean(True Range, ATR period)
```

This is the exact baseline behavior and remains the live-compatible default.

### Standard True Range

```text
TR = maximum of:
    High - Low
    absolute(High - previous close)
    absolute(Low - previous close)
ATR = rolling mean(TR, ATR period)
```

The True Range implementation prevents overnight values from being mixed into the intraday same-session calculation. For the first candle or a session boundary, it falls back to the candle's high-low range.

True Range is more suitable for gaps and volatility expansion. High-low ATR is simpler and preserves the existing model.

## 4. Historical Data

The first 1-minute dataset consists of CSV files under `Stock_Market_Data`.

Each CSV contains:

```text
Datetime
Open
High
Low
Close
Volume
```

The initial implementation loaded and analyzed:

- 51 historical instrument files.
- NSEI and NSEBANK index files.
- Approximately 6,869–7,125 1-minute rows per instrument.
- 19 trading sessions per instrument.
- Data from 2026-10-22 through 2026-11-18 for the NSEI and NSEBANK examples.

This is sufficient for:

- Testing the range implementation.
- Running parameter grids.
- Comparing candidate ranges.
- Running limited session validation.
- Producing candidate pools.

It is not sufficient to declare a parameter set future-proof or suitable for live capital deployment.

## 5. Session and Candle Rules

To prevent artificial results, the range engine uses session-aware rules.

### Excluded candles

The final five 1-minute candles of every trading session are excluded from range-quality and candidate fitting.

This excludes end-of-day movement that can produce:

- Closing imbalances.
- Overnight preparation behavior.
- Artificial final-candle shocks.
- Candle-count distortions unrelated to normal intraday range structure.

### Overnight comparisons

A previous candle from a new trading session is not compared with the previous session's width or boundary.

The overnight gap is therefore not counted as a same-session width shock or boundary shock.

### Recording rule

Range metrics use completed candles only.

Wick-based and close-based range behavior are separate concepts and should not be combined unless explicitly defined.

## 6. Range-Only Metrics

Range-only analysis does not measure breakout profit or false entries.

### Width volatility

```text
range_width = SMax - SMin
range_width_std = standard deviation(range_width)
range_width_cv = range_width_std / average_range_width
```

Lower coefficient of variation is preferred.

### Width shocks

A width shock occurs when:

```text
absolute(current_width - previous_width)
/
previous_width
>
30%
```

The 30% threshold is a configurable parameter.

### Boundary shocks

A boundary shock occurs when SMax or SMin changes by more than 30% relative to the previous candle.

Both SMax and SMin boundary changes are measured separately.

### Range persistence

Range persistence is the number of consecutive completed candles in which price closes inside SMax/SMin.

It is measured as:

- Average persistence.
- Median persistence.
- Session-local persistence only.

### Range respect

```text
Range respect = candles inside the range / valid candles
```

Range respect should not be maximized blindly:

- 90–100% can indicate an overly wide range.
- 10–20% can indicate an overly tight or unstable range.
- The useful target is based on range structure, not a universal percentage.

### Width relative to close

Range width is also measured as a fraction of the current close:

```text
range_width_pct_of_close = range_width / absolute(close)
```

This improves comparison across stocks and indices.

## 7. Range Candidate Score

The range-only candidate score is currently:

```text
range_score =
    30% range-width coefficient-of-variation score
  + 25% boundary-shock score
  + 15% width-shock score
  + 10% range-persistence score
  + 10% range-respect target score
  + 5% SMax change score
  + 5% SMin change score
```

Each metric is percentile-ranked across candidates before the final weighted score is calculated.

The score does not include:

- Breakout magnitude.
- False-breakout count.
- Trade profit.
- Entry success.
- Buy or sell direction.
- Volume confirmation.
- Pivot filtering.
- Candle-pattern confirmation.

## 8. Parameter Search Space

The current range-only search grid is:

```text
GMA period:
14, 18, 20, 24, 30, 36, 44

Signal span:
fixed in the range analysis at 9

ATR period:
7, 10, 14, 21

ATR multiplier:
0.6, 0.8, 1.0, 1.2, 1.5

ATR method:
high-low
True Range
```

The first focused ATR experiment uses:

```text
GMA period: 14, 20, 30
ATR period: 7, 10, 14, 21
ATR multiplier: 0.6, 0.8, 1.0, 1.2, 1.5
ATR method: high-low, True Range
```

This produces 120 combinations.

Signal span is not included in range-width ranking because the current `SMax/SMin` calculation does not use GSIGNAL.

## 9. 51-Symbol 1-Minute Range Analysis

A 51-symbol 1-minute range-candidate search was run across the available CSVs.

The search returned:

- 51 instruments.
- 255 candidate rows.
- Five ranked candidates per symbol.
- Zero detected boundary shocks for every reported top candidate.

### Cross-symbol period result

Top candidate distribution:

```text
Period 30: 46 symbols
Period 20: 5 symbols
Period 14: 0 symbols
```

This result is descriptive for the initial 19-session sample, not a final period recommendation.

### Cross-symbol multiplier result

```text
Multiplier 0.8: 22 symbols
Multiplier 1.0: 12 symbols
Multiplier 1.2: 17 symbols
```

### Most common combinations

```text
Period 30, multiplier 0.8: 21 symbols
Period 30, multiplier 1.2: 15 symbols
Period 30, multiplier 1.0: 10 symbols
```

This pattern shows period and multiplier can differ materially by symbol and volatility profile. It does not prove that period 30 is universally superior.

## 10. NSEI Candidate Results

A focused NSEI 1-minute candidate test produced:

| Period | ATR multiplier | Range respect | Width CV | Persistence | Boundary shocks |
|---:|---:|---:|---:|---:|---:|
| 20 | 1.0 | 49.81% | 0.371 | 4.68 candles | 0 |
| 30 | 1.0 | 39.45% | 0.371 | 4.33 candles | 0 |
| 14 | 1.0 | 59.30% | 0.371 | 5.04 candles | 0 |

Interpretation:

- Period 20 is a balanced NSEI candidate.
- Period 30 is slower and showed lower range respect.
- Period 14 is more reactive and showed higher range respect.
- All three candidates had zero boundary shocks in this full sample.

The result should be interpreted as a range-fitting candidate pool, not a live parameter choice.

## 11. NSEI ATR and Multiplier Candidate Result

A 120-combination NSEI analysis compared:

- GMA periods 14, 20, 30.
- ATR periods 7, 10, 14, 21.
- ATR multipliers 0.6, 0.8, 1.0, 1.2, 1.5.
- High-low ATR and True Range ATR.

The highest-ranked combinations clustered around:

```text
GMA period: 20 or 30
ATR period: 21
ATR multiplier: 1.2 or 1.5
ATR method: True Range or high-low
```

The range results showed:

- ATR period 21 produced wider, more persistent ranges.
- ATR multiplier 1.2–1.5 produced wider ranges and higher range respect.
- True Range and high-low ATR were close because NSEI intraday gaps were not dominant in this sample.
- ATR period and multiplier had a larger visible effect on width than GMA period.

This confirms that the main range-width variables are:

```text
ATR period
ATR method
ATR multiplier
```

GMA period mainly moves and shapes the centerline of the range.

## 12. Market-Regime Candidate Analysis

The implementation classifies candles into:

### Volatility

- Low.
- Normal.
- High.

### Trend

- Uptrend.
- Sideways.
- Downtrend.

### Compression

- Compressed.
- Normal.
- Expanded.

### Noise

- Low.
- Normal.
- High.

The initial top-five regime search in NSEI produced:

- High/downtrend: period 20, multiplier 1.2.
- High/sideways: period 14, multiplier 1.2.
- High/uptrend: period 14, multiplier 1.0.
- Low/downtrend: period 20, multiplier 1.2.
- Low/sideways: period 14, multiplier 1.2.
- Low/uptrend: period 20, multiplier 1.0.
- Normal/downtrend: period 20, multiplier 1.2.
- Normal/sideways: period 20, multiplier 1.2.
- Normal/uptrend: period 30, multiplier 1.2.

These values are preliminary observations, not accepted live settings.

## 13. Walk-Forward Range Validation

NSEI 1-minute walk-forward validation split the 19 sessions into:

```text
Training: 60%
Validation: 20%
Test: 20%
```

Candidate parameters were selected on training sessions and locked before validation and test periods.

Results:

### Period 20, multiplier 1.0

- Validation range respect: 48.86%.
- Test range respect: 51.06%.
- Boundary shock rate: 0%.
- Persistence: 4.49–4.92 candles.

### Period 20, multiplier 1.2

- Validation range respect: 55.88%.
- Test range respect: 60.70%.
- Boundary shock rate: 0%.
- Persistence: 6.16–6.52 candles.

### Period 30, multiplier 1.0

- Validation range respect: 39.20%.
- Test range respect: 42.41%.
- Boundary shock rate: 0%.
- Persistence near 4.4–5.0 candles.

The candidate pool remained stable in this short data sample, but 19 sessions are too few for a live parameter claim.

## 14. NSEI Breakout Results

A range-only study was followed by a descriptive breakout test on three NSEI 1-minute ranges.

Final five candles were removed before range analysis.

| Period | Breakouts | Combined false rate | Average follow-through | Outside persistence |
|---:|---:|---:|---:|---:|
| 14 | 687 | 94.91% | 0.93 range widths | 2.15 candles |
| 20 | 644 | 87.11% | 0.92 range widths | 2.73 candles |
| 30 | 564 | 82.45% | 0.94 range widths | 3.35 candles |

Interpretation:

- Period 14 creates more breakouts but the most false breakouts.
- Period 20 gives a moderate balance.
- Period 30 gives fewer breakouts but longer persistence and a lower false-breakout rate.

These values are from 19 NSEI sessions and remain breakout-stage observations, not entry recommendations.

## 15. Session-Level Report

The range-fit report contains:

- Interactive 1-minute Close/SMax/SMin charts.
- Session dropdown selection.
- Candidate parameter overlay.
- Range respect.
- Width CV.
- Worst width CV.
- Width and boundary shock rates.
- Range persistence.
- Average range width.

Generated files:

```text
range_analysis_results/all_symbols_1m_range_fit_report.html
range_analysis_results/all_symbols_1m_symbol_range_fit.csv
range_analysis_results/all_symbols_1m_session_range_fit.csv
range_analysis_results/all_symbols_1m_range_candidates.csv
range_analysis_results/NSEI_1m_range_candidates.csv
range_analysis_results/NSEI_1m_ATR_method_full_results.csv
range_analysis_results/NSEI_1m_ATR_method_top_candidates.csv
range_analysis_results/NSEI_1m_range_walk_forward.csv
range_analysis_results/NSEI_1m_top_range_breakout_results.csv
```

## 16. Live-Parameter Safeguards

No optimized parameter set is currently applied to the dashboard.

The live range remains:

```text
GMA period = 20
GSIGNAL period = 9
ATR period = 14
ATR multiplier = 0.9
ATR method = high-low
```

A parameter set should not be saved for live use until:

1. It has been tested across substantially more sessions.
2. It beats baseline range stability.
3. It remains stable in validation and test periods.
4. It is visually meaningful on selected charts.
5. It performs consistently in the same symbol and timeframe.
6. It does not create excessive boundary or width shocks.
7. Regime switching improves stability rather than introducing regime noise.
8. Existing live buy/sell behavior remains unchanged during the rollout.

## 17. What Is Implemented

### Completed

- 1-minute historical CSV loader.
- 5-minute resampling helper.
- Session-safe Gaussian calculation.
- Configurable GMA period.
- Configurable GSIGNAL period.
- Configurable ATR period and multiplier.
- High-low ATR baseline.
- True Range ATR option.
- Range-only candidate scoring.
- Width CV, shocks, and persistence metrics.
- Upper/lower breakout detection.
- Follow-through, MAE, MFE, persistence, and false-breakout metrics.
- Separate upper/lower reporting.
- Volatility, trend, compression, and noise classification.
- Regime-candidate ranking.
- Session-aware 60/20/20 walk-forward range validation.
- Symbol-level candidate CSV output.
- Session-level candidate CSV output.
- Interactive range-fit HTML report.
- 51-symbol coarse range-candidate analysis.
- NSEI 120-combination ATR/GMA/multiplier grid.

### Not Yet Implemented as a Live System

- Automatic live switching by detected regime.
- Production parameter-store integration.
- Direction-specific live parameter sets.
- Entry confirmation logic.
- Trade profitability testing.
- Real-world slippage and transaction costs.
- Robust volume confirmation.
- Multi-month or multi-year history.
- Production stability thresholds for parameter switching.

## 18. Implementation Limitations

### Limited history

The 19-session dataset is useful for implementation and candidate discovery, but it is not enough for a final live parameter claim.

### Session sample

Several regime buckets contain relatively few 1-minute observations. Candidate scores from those buckets should be marked low-confidence.

### Volume

NSEI and NSEBANK volume is zero in the current files. Stock volume exists, but it has not been used as a range parameter.

### Multiple comparisons

A parameter grid naturally produces many candidate combinations. A winner must not be selected only from one sample or only from one score.

### Range fitting and breakout fitting are separate

A parameter combination that creates a smooth range may not produce profitable breakouts.

Similarly, a parameter combination that generates profitable-looking breakouts may create unstable or overly wide ranges.

The system should remain range-first until the range is accepted.

## 19. Recommended Next Steps

### Phase A: Complete NSEI range fitting

1. Run a focused ATR-period/multiplier grid.
2. Compare True Range against high-low ATR.
3. Add swing-level or H1/H4 comparison where useful.
4. Inspect the top five candidates visually by session.
5. Validate them across all 19 sessions.

### Phase B: Confirm regime behavior

1. Use volatility buckets with enough observations.
2. Use trend buckets with enough observations.
3. Remove sparse compression buckets or combine them.
4. Prevent rapid parameter switching between adjacent candles.
5. Require a regime to persist for a minimum number of candles.

### Phase C: Compare fixed versus switching ranges

Compare:

```text
Fixed baseline
Fixed period-20 candidate
Fixed period-30 candidate
Regime-switched candidate
```

The switching model should only be accepted if it consistently improves range stability in unseen sessions.

### Phase D: Then study breakouts

After regime ranges pass:

1. Detect SMax/SMin breakouts.
2. Separate upper and lower breakouts.
3. Measure follow-through.
4. Measure immediate re-entry.
5. Measure persistence.
6. Measure adverse excursion.
7. Evaluate retests.
8. Introduce entry filters.

Only after this stage should buy/sell logic be optimized.

## 20. Final Current Conclusion

The range engine is implemented and the existing live range behavior remains unchanged.

The current evidence shows:

- ATR period and multiplier materially change range width and persistence.
- GMA period changes the centerline and candidate behavior.
- The 19-session dataset is enough for candidate discovery and implementation validation.
- It is not enough for final live parameter selection.
- Period 30 appeared frequently in the initial all-symbol range pool, but period 30 is not yet a proven universal winner.
- True Range and high-low ATR need more data and regime-specific validation.
- The correct next decision is to complete range fitting for NSEI and representative symbols, then compare fixed and regime-switched ranges before breakout optimization.
