import asyncio
import logging
from datetime import datetime

import pandas as pd

log = logging.getLogger("finresearch.forecast")


def _run_prophet(df: pd.DataFrame, periods: int) -> dict:
    from prophet import Prophet

    m = Prophet(daily_seasonality=False, weekly_seasonality=True, yearly_seasonality=True)
    m.fit(df)
    future = m.make_future_dataframe(periods=periods)
    fc = m.predict(future)

    tail = fc.tail(periods)[["ds", "yhat", "yhat_lower", "yhat_upper"]]
    predictions = [
        {
            "date": row["ds"].strftime("%Y-%m-%d"),
            "predicted_close": round(row["yhat"], 2),
            "lower_bound": round(row["yhat_lower"], 2),
            "upper_bound": round(row["yhat_upper"], 2),
        }
        for _, row in tail.iterrows()
    ]

    last_actual = float(df["y"].iloc[-1])
    last_forecast = predictions[-1]["predicted_close"]
    pct_change = round((last_forecast - last_actual) / last_actual * 100, 2)

    return {
        "forecast_days": periods,
        "last_actual_close": round(last_actual, 2),
        "predicted_close_end": last_forecast,
        "predicted_pct_change": pct_change,
        "trend": "bullish" if pct_change > 2 else "bearish" if pct_change < -2 else "neutral",
        "predictions": predictions,
    }


class ForecastAgent:
    """Runs a Prophet time-series forecast on historical price data."""

    async def forecast(self, ticker: str, price_bars: list[dict], periods: int = 30) -> dict:
        ticker = ticker.upper()
        log.info(f"[ForecastAgent] Forecasting {ticker} ({periods} days)")

        if len(price_bars) < 30:
            return {
                "forecast_days": periods,
                "error": f"Insufficient data: need ≥30 bars, got {len(price_bars)}",
                "trend": "unknown",
            }

        df = pd.DataFrame({
            "ds": pd.to_datetime([b["date"] for b in price_bars]),
            "y": [b["close"] for b in price_bars],
        }).sort_values("ds")

        try:
            result = await asyncio.to_thread(_run_prophet, df, periods)
        except Exception as e:
            log.error(f"[ForecastAgent] Prophet failed: {e}")
            closes = [b["close"] for b in price_bars[-30:]]
            last_date = pd.to_datetime(price_bars[-1]["date"])
            avg_daily = (closes[-1] - closes[0]) / len(closes)
            predicted_end = round(closes[-1] + avg_daily * periods, 2)
            pct = round((predicted_end - closes[-1]) / closes[-1] * 100, 2)
            predictions = [
                {
                    "date": (last_date + pd.Timedelta(days=i + 1)).strftime("%Y-%m-%d"),
                    "predicted_close": round(closes[-1] + avg_daily * (i + 1), 2),
                    "lower_bound": round(closes[-1] + avg_daily * (i + 1) * 0.97, 2),
                    "upper_bound": round(closes[-1] + avg_daily * (i + 1) * 1.03, 2),
                }
                for i in range(periods)
            ]
            result = {
                "forecast_days": periods,
                "last_actual_close": round(closes[-1], 2),
                "predicted_close_end": predicted_end,
                "predicted_pct_change": pct,
                "trend": "bullish" if pct > 2 else "bearish" if pct < -2 else "neutral",
                "predictions": predictions,
                "note": "Linear fallback used (Prophet unavailable)",
            }

        log.info(f"[ForecastAgent] {ticker} forecast: {result['trend']} ({result.get('predicted_pct_change', '?')}%)")
        return result
