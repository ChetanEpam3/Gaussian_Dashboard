# Swing-Based Patchy Range Curves

## Purpose and conversation decisions

This document describes the swing-range prototype added to the dashboard and
the design decisions made while refining it.

The goal is to show a compact upper/lower range on the 5-minute charts when
price action is patchy, and to avoid drawing a continuous channel through
sections that do not have enough nearby swing evidence. The range is intended
to be a visual structure and a basis for close-confirmed breakout markers; it
is separate from the existing Gaussian SMax/SMin calculation.

The implementation reflects these decisions:

- Detect local swing highs and lows from OHLC candles.
- Do not use ATR or GMA proximity as swing filters. Those approaches were
  discussed, but were removed from the final swing-selection logic.
- Pair an upper swing and a lower swing only when they are close in time and
  close in price.
- Connect only nearby, successive valid swing pairs. Leave gaps where points
  are isolated or too far apart.
- Skip a single otherwise-valid pair unless another pair connects to it.
- Anchor each curve to the actual swing-pivot candles, not to the later candles
  that confirm those swings.
- Detect a breakout when the candle close crosses a valid range boundary.
- Keep the 1-minute SMax/SMin overlays on the 5-minute charts commented out.

## Files and chart integration

- `swing_range.py` contains the swing detection, pairing, curve construction,
  range validation, and breakout-state logic.
- `app.py` calls `add_swing_range` for the NIFTY 5-minute data and for either
  BANKNIFTY or the selected stock's 5-minute data. The calculations happen
  before the chart data is limited to the latest 75 candles.
- The charts plot the paired swing markers, upper/lower swing curves, and
  close-confirmed breakout markers.
- The 1-minute SMax/SMin traces on these 5-minute charts remain commented out.
  This does not remove the existing Gaussian/SMax/SMin calculation or its
  other chart uses.

## Current defaults and controls

| Setting | Default | Meaning |
|---|---:|---|
| `swing_bars` | 1 | Number of candles on each side of a candidate pivot used to confirm it. |
| `max_swing_gap` | 6 bars | Maximum time gap for pairing opposite swings and connecting consecutive same-side pivots. On a 5-minute chart, six bars are about 30 minutes. |
| `max_range_pct` | 0.20% | Maximum permitted separation between a paired high and low, measured relative to their midpoint. |

The sidebar exposes the maximum range width from 0.05% through 1.00%, in
0.05% steps, with a default of 0.20%. `swing_bars` and `max_swing_gap` use
their function defaults in the current dashboard integration; they are not
sidebar controls.

The sidebar help currently describes the width as a percentage of closing
price. The implementation uses the midpoint of the paired high and low for
pair eligibility and the interpolated upper/lower values for per-candle range
validation. The calculation is:

```text
midpoint = (swing_high + swing_low) / 2
pair_width_pct = (swing_high - swing_low) / abs(midpoint) * 100
```

The pair is eligible when `pair_width_pct <= max_range_pct`. This midpoint
definition is the authoritative behavior of the current code.

## Processing stages

### 1. Input checks and session grouping

`add_swing_range(df, swing_bars=1, max_swing_gap=6, max_range_pct=0.2)`
requires `High`, `Low`, and `Close` columns. It raises a `ValueError` if
parameters are outside the accepted ranges or required columns are absent.
The input frame is copied; the returned frame contains the original data plus
the swing-range result columns.

For a `DatetimeIndex`, pivots and pairing are kept within a calendar date.
Pending swings and the previous pair are cleared at a date boundary, and
breakout-lock state resets there. For a non-datetime index, the function
treats all rows as one session.

### 2. Local swing detection

For each candidate pivot, the detector examines `swing_bars` candles before
and after it. The pivot is not available to the matching logic until the
right-side candles have completed.

For a swing high at index `p`:

```text
High[p] >= every High in the left window
High[p] >  every High in the right window
```

For a swing low:

```text
Low[p] <= every Low in the left window
Low[p] <  every Low in the right window
```

The asymmetric strict and non-strict comparisons are intentional in the
current code. They allow a tie on the left side but require the pivot to be
strictly higher/lower than the right-side candles. Candidates that do not
have enough left-side history or whose confirmation window crosses a session
boundary are not accepted.

The swing flag and raw swing price are stored on the pivot candle. The
candidate is queued for pairing on its confirmation candle. As a result, a
marker is displayed at the historical pivot location only after enough later
candles have confirmed it.

### 3. Pairing nearby upper and lower swings

Confirmed highs and lows are kept in pending lists for a short time. A
candidate high/low combination is eligible only when:

1. The high's price is greater than the low's price.
2. Their pivot indices are no more than `max_swing_gap` bars apart.
3. Their midpoint-relative width is no greater than `max_range_pct`.

Eligible candidates are sorted by shortest time gap first, then narrowest
percentage width. The first candidate whose high and low have not already
been used is selected for that confirmation step. Used points are removed
from their pending lists. Unmatched pending points expire after the
`max_swing_gap + swing_bars` age allowance.

This is a greedy matching approach: it favors the closest-in-time eligible
pair rather than globally optimizing all possible pairings. At most one pair
is emitted for any one confirmation index.

### 4. Connecting pairs into patchy curves

Two successive pairs can connect only if both boundaries progress forward
and remain nearby:

```text
0 < current_high_pivot - previous_high_pivot <= max_swing_gap
0 < current_low_pivot  - previous_low_pivot  <= max_swing_gap
```

When these conditions hold:

- The upper line is linearly interpolated from the previous upper swing pivot
  to the current upper swing pivot.
- The lower line is independently linearly interpolated from the previous
  lower swing pivot to the current lower swing pivot.
- Each line therefore uses its own pivot timestamps. It is not anchored to
  the later confirmation candle.
- The paired swing markers are emitted at the actual high and low pivot
  indices belonging to the connected segment.

If either boundary has too large a time gap, moves backward in pivot order, or
has no valid partner, the pair does not create a connected curve. A single
pair is not drawn on its own. This is how isolated points and non-patchy
sections are skipped.

The curves are piecewise straight-line interpolation, not a spline or a
smoothed curve. The implementation evaluates each boundary over the segment
spanning the paired pivots; interpolation clamps to an endpoint if the other
boundary's pivot makes that overall segment extend beyond this boundary's
own endpoint.

### 5. Per-candle range validation

After constructing candidate curves, each candle is checked again. A candle
has a valid range only when:

- Both upper and lower curve values are finite.
- The upper value is greater than the lower value.
- The interpolated width is finite.
- The interpolated midpoint-relative width is at most `max_range_pct`.

Invalid rows are left as gaps in both plotted boundaries. This paired
validation helps prevent showing only one side of a range or rendering a
range that becomes too wide between swing pivots.

### 6. Breakout and locked-boundary behavior

An upward breakout is marked when a valid range is available, the current
close is above the current upper boundary, and the previous valid close was
not above its preceding upper boundary. A downward breakout uses the
corresponding lower-boundary cross.

After a breakout, the boundary values are held at the breakout range while
the close remains outside that range. The locked range is released when a
close returns inside the locked upper/lower boundaries. Lock state does not
carry into the next session.

These are close-cross markers and a simple post-breakout boundary hold. They
do not independently classify an extended breakout phase, establish that a
move is genuine, or identify post-breakout consolidation.

## Result columns

| Column | Contents |
|---|---|
| `SWING_HIGH`, `SWING_LOW` | Boolean flags on confirmed pivot candles. |
| `SWING_HIGH_PRICE`, `SWING_LOW_PRICE` | Raw detected swing prices, including swings not used in the displayed patchy range. |
| `SWING_RANGE_PAIR_HIGH`, `SWING_RANGE_PAIR_LOW` | High/low pivot prices used by a connected pair sequence; isolated or unused points remain `NaN`. |
| `SWING_RANGE_UPPER`, `SWING_RANGE_LOWER` | Valid interpolated range boundaries, or the held breakout boundaries while locked; gaps are `NaN`. |
| `SWING_RANGE_WIDTH_PCT` | Width of the plotted range as a percentage of its midpoint. |
| `SWING_RANGE_VALID` | Boolean flag indicating a plotted or locked range on that candle. |
| `SWING_RANGE_UPPER_LOCKED`, `SWING_RANGE_LOWER_LOCKED` | Boolean flags indicating the upper/lower boundary is being held after a breakout. |
| `SWING_BREAKOUT_UP`, `SWING_BREAKOUT_DOWN` | Boolean flags for upward/downward close-cross breakouts. |

The dashboard's visible swing markers use `SWING_RANGE_PAIR_HIGH` and
`SWING_RANGE_PAIR_LOW`, so unmatched raw swings do not appear as range-pair
markers. The raw swing columns remain available for analysis.

## Earlier approaches that were not retained

During iteration, the following alternatives were tried or discussed and then
removed from the final curve-selection behavior:

- Filtering swings by ATR: rejected because ATR should not determine whether
  a swing exists.
- Filtering swings by distance from GMA: rejected in favor of pairing swings
  by time and price proximity.
- Connecting every detected swing or holding a curve through long gaps:
  replaced by a maximum time gap and explicit blank sections.
- Plotting an isolated valid pair: replaced by requiring a second pair that
  connects to it.
- Drawing a segment at confirmation-bar positions: corrected so each curve
  passes through its actual swing-pivot markers.

The separate Gaussian channel and its calculation are not replaced by this
prototype.

## Validation performed

Focused synthetic checks verified that:

- A connected pair sequence produces curves that pass through the paired
  upper and lower pivot prices at their actual pivot timestamps.
- The resulting range remains within the configured maximum width.
- An isolated pair produces no visible range.
- Pairs separated beyond the time threshold produce no visible range.
- A too-wide pair is rejected.

Pylance syntax and Problems checks reported no errors for the implementation,
`git diff --check` passed, and the running Streamlit health endpoint returned
`ok`. These checks validate implementation behavior; they are not a
performance or profitability backtest.

## Current limitations and tuning notes

- `swing_bars=1` is deliberately sensitive and can identify frequent local
  turning points. Increasing it would require changing the function call or
  its default.
- `max_swing_gap=6` controls both opposite-side pairing and successive
  same-side pivot connections. It is currently fixed in the app rather than
  exposed as a control.
- The width limit is configurable in the sidebar, but its code calculation is
  based on the range midpoint, not the candle close.
- Pair selection is greedy and emits no more than one pair per confirmation
  candle; dense or overlapping candidates can therefore be skipped.
- Linear interpolation may produce visibly sloped or temporarily clamped
  sections. It does not apply additional curve smoothing.
- The breakout lock resumes normal processing when price closes back inside
  the locked range; this is not a full market-regime or consolidation model.
- Chart rendering is limited to the latest 75 rows after swing ranges are
  calculated. Earlier rows can contribute to swing confirmation and pairing,
  but are not part of the displayed window.

## Main implementation references

- `swing_range.py` — `add_swing_range`
- `app.py` — the “Swing Range Settings” sidebar, 5-minute data preparation,
  and NIFTY/BANKNIFTY-or-stock chart traces
