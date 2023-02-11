from __future__ import print_function
import datetime
import numpy as np
import pandas as pd
import statsmodels.api as sm
import yfinance as yf

from strategy import Strategy
from event import SignalEvent
from backtest import Backtest
from data import HistoricDataHandler
from execution import SimulatedExecutionHandler
from portfolio import Portfolio
from sb_execution import SBExecutionHandler


class MovingAverageCrossStrategy(Strategy):
    """
    Carries out basic MA Crossover strategy with a short/long simple weighted moving average.
    Default short/long periods are 100/400 periods respectively

    bars - The DataHandler object that provides bar information
    events - The Event Queue object.
    short_window - The short moving average lookback.
    long_window - The long moving average lookback.
    """

    def __init__(self, bars, events, short_window=1, long_window=2):
        """
                Initializes the MA Crossover strategy.
                """
        self.bars = bars
        self.symbol_list = self.bars.symbol_list
        self.events = events
        self.short_window = short_window
        self.long_window = long_window

        # set to True if a symbol is in the market
        self.bought = self._calculate_initial_bought()

    def _calculate_initial_bought(self):
        """
        Adds the keys to the bought dictionary for all symbols and set them to 'OUT'.
        If the strategy begins out of the market we set the initial "bought" value to be "OUT".
        """

        bought = {}
        for s in self.symbol_list:
            bought[s] = 'OUT'
        return bought

    def calculate_signals(self, event):
        """
        Generates a new set of signal based on the MA.
        """
        if event.type == 'MARKET':
            for s in self.symbol_list:
                bars = self.bars.get_latest_bars_values(s, 'Adj Close', N=self.long_window)
                bar_date = self.bars.get_latest_bar_datetime(s)
                if len(bars) > 0 and bars is not None:
                    short_sma = np.mean(bars[-self.short_window:])
                    long_sma = np.mean(bars[-self.long_window:])

                    symbol = s
                    dt = datetime.datetime.utcnow()

                    if short_sma > long_sma and self.bought[s] == "OUT":
                        print("LONG: %s" % bar_date)
                        sig_dir = "LONG"
                        signal = SignalEvent(1, symbol=symbol, datetime=dt, signal_type=sig_dir, strength=1.0)
                        self.events.put(signal)
                        self.bought[s] = 'LONG'
                    elif short_sma < long_sma and self.bought[s] == 'LONG':
                        print('SHORT: %s' % bar_date)
                        sig_dir = 'SHORT'
                        signal = SignalEvent(1, symbol=symbol, datetime=dt, signal_type=sig_dir, strength=1.0)
                        self.events.put(signal)
                        self.bought[s] = 'SHORT'
        elif event.type == 'Limit':
            # TODO: not set up the limit order.
            pass


if __name__ == '__main__':
    symbol_list = ['EURUSD']
    get_yf_fxdata = yf.download(tickers='EURUSD=X', start='2000-01-02', end='2023-02-04')
    start_date = datetime.datetime(2000, 1, 1, 0, 0, 0)
    get_yf_fxdata.index = pd.to_datetime(get_yf_fxdata.index)
    initial_capital = 1000000.0
    heartbeat = 0.0
    # TODO you need the data to run the backtest against
    b = Backtest(api=get_yf_fxdata, symbol_list=symbol_list, initial_capital=initial_capital, heartbeat=heartbeat,
                 start_date=start_date, data_handler=HistoricDataHandler,
                 execution_handler=SimulatedExecutionHandler, portfolio=Portfolio, strategy=MovingAverageCrossStrategy)
    b.simulate_trading()
