from __future__ import print_function
import numpy as np
import pandas as pd


def create_sharpe_ratio(returns, periods=252):
    """
    Create the sharpe ratio for the strategy.

    param returns: a pandas Series representing period percentage returns.
    param periods: Daily (252), Hourly (252 * 6.5)...
    return: the sharpe ratio
    """
    return np.sqrt(periods) * (np.mean(returns)) / np.std(returns)


def create_drawdowns(pnl: pd.Series):
    """
    Calculate the largest peak-to-through drawdown of the PnL curve as well as the
    duration of the drawdown. Pnl returns must be a pandas series.

    param pnl: pandas series representing period percentage returns.
    return: drawdown, duration - highest peak-to-through drawdown and duration
    """
    # Calculate the cumulative return curve
    # and set up the High WaterMark
    hwm = [0]

    # Create the drawdown and the duration series
    idx = pnl.index
    drawdown = pd.Series(index=idx)
    duration = pd.Series(index=idx)

    # loop over the index range
    for t in range(1, len(idx)):
        hwm.append(max(hwm[t-1], pnl[t]))
        drawdown[t] = (hwm[t] - pnl[t])
        duration[t] = (0 if drawdown[t] == 0 else duration[t-1]+1)
    return drawdown, drawdown.max(), duration.max()
