from __future__ import print_function

import datetime
import pandas as pd
import numpy as np

from sklearn.discriminant_analysis import QuadraticDiscriminantAnalysis
from sklearn.ensemble import RandomForestClassifier

from strategy import Strategy
from event import SignalEvent
from backtest import Backtest
from data import HistoricDataHandler
from execution import SimulatedExecutionHandler
from portfolio import Portfolio
from forecast import get_lag_data

import yfinance as yf


class SPYDailyForecastStrategy(Strategy):
    def __init__(self, bars, events):
        self.bars = bars
        self.symbol_list = self.bars.symbol_list
        self.events = events
        self.datetime_now = datetime.datetime.utcnow()

        self.model_start_date = datetime.datetime(2001, 1, 10)
        self.model_end_date = datetime.datetime(2022, 2, 1)
        self.model_start_test_date = datetime.datetime(2021, 2, 1)

        self.long_market = False
        self.short_market = False
        self.bar_index = 0

        self.model = self.create_symbol_forecast_model()

    def create_symbol_forecast_model(self):
        self.bars.ret = get_lag_data(self.symbol_list[0], self.model_start_date, self.model_end_date, lags=5)
        X = self.bars.ret[['Lag1', 'Lag2']]
        y = self.bars.ret['Direction']
        start_test = self.model_start_test_date
        X_train = X[X.index < start_test]
        X_test = X[X.index >= start_test]

        y_train = y[y.index < start_test]
        y_test = y[y.index >= start_test]

        model = QuadraticDiscriminantAnalysis()
        model.fit(X_train.values, y_train)

        return model

    def calculate_signals(self, event):
        sym = self.symbol_list[0]
        dt = self.datetime_now
        x = 0
        y = 0

        if event.type == 'MARKET':
            self.bar_index += 1
            if self.bar_index > 5:
                if x < len(self.bars.ret['Today']) - 2:
                    if y == 0:
                        lags = np.array(self.bars.ret['Today'][-3:])
                    else:
                        lags = np.array(self.bars.ret['Today'][-3 - x:-y])

                    pred_series = pd.Series({
                        'Lag1': lags[1] * 100.0,
                        'Lag2': lags[2] * 100.0
                    })
                    pred = self.model.predict([pred_series])
                    # if pred > 0 and not self.long_market:
                    #    self.long_market = True
                    #    signal = SignalEvent(1, sym, dt, 'LONG', 1.0)
                    #    self.events.put(signal)
                    # if pred < 0 and self.long_market:
                    #    self.long_market = False
                    #    signal = SignalEvent(1, sym, dt, 'EXIT', 1.0)
                    #    self.events.put(signal)
                    if pred > 0 and not self.long_market:
                        self.long_market = True
                        signal = SignalEvent(1, sym, dt, 'LONG', 1.0)
                        self.events.put(signal)
                    elif pred < 0 and not self.short_market:
                        self.short_market = True
                        signal = SignalEvent(1, sym, dt, 'SELL', 1.0)
                        self.events.put(signal)
                    else:
                        signal = SignalEvent(1, sym, dt, 'EXIT', 1.0)
                        self.events.put(signal)
                    x += 1
                    y += 1


if __name__ == "__main__":
    symbol_list = ['SPY']
    initial_capital = 1000000.0
    heartbeat = 0.0
    model_start_date = datetime.datetime(2001, 1, 10)
    model_end_date = datetime.datetime(2022, 2, 1)
    snret = yf.download(tickers=symbol_list, start=model_start_date, end=model_end_date)
    snret.index = [datetime.datetime.combine(snret.index[i].to_pydatetime(), snret.index[i].to_pydatetime().time()) for
                   i in range(0, len(snret))]
    # TODO you need the data to run the backtest against
    b = Backtest(api=snret, symbol_list=symbol_list, initial_capital=initial_capital, heartbeat=heartbeat,
                 start_date=model_start_date, data_handler=HistoricDataHandler,
                 execution_handler=SimulatedExecutionHandler, portfolio=Portfolio, strategy=SPYDailyForecastStrategy)
    b.simulate_trading()
