from __future__ import print_function

import secrets
from abc import ABCMeta, abstractmethod, ABC

import pandas as pd
import numpy as np
from event import MarketEvent
from forecast import get_lag_data

# copy your (24-hour) token here
import requests

TOKEN = "eyJhbGciOiJFUzI1NiIsIng1dCI6IkRFNDc0QUQ1Q0NGRUFFRTlDRThCRDQ3ODlFRTZDOTEyRjVCM0UzOTQifQ.eyJvY" \
        "WEiOiI3Nzc3NSIsImlzcyI6Im9hIiwiYWlkIjoiMTA5IiwidWlkIjoiYVFrdHF2WC04UEdudzJQZWIzc0VLZz09IiwiY2l" \
        "kIjoiYVFrdHF2WC04UEdudzJQZWIzc0VLZz09IiwiaXNhIjoiRmFsc2UiLCJ0aWQiOiIyMDAyIiwic2lkIjoiMDdiOTJmN2I" \
        "xOWEwNDI5ZTkwMjM3NTBjNzcxZWZmNDUiLCJkZ2kiOiI4NCIsImV4cCI6IjE2ODM3NTEyMjMiLCJvYWwiOiIxRiIsImlpZCI6I" \
        "mQ0OGE2YWNkMjUzNTQzNjU5YTA4MDhkYWVmZTZiYzRmIn0.JhEzAviNoYQkNhKH4Re5RxTVbizYrbnKJDCJiDyWjrNdmBvs6GVdOG" \
        "b3_D1XatAoZAnKcCoYdthDj7qVmCUxnQ"

# create a random string for context ID and reference ID
CONTEXT_ID = secrets.token_urlsafe(10)
REF_ID = secrets.token_urlsafe(5)


class DataHandler(object):
    """
    DataHandler is an abstract base class (ABC) providing an interface for all subsequent (inherited)
    data handlers (both live and historic). The goal of a (derived) DataHandler object is to output a
    generated set of bars (OHLCVI -> Open, High, Low, Close, Volume, OpenInterest) for each symbol requested.
    This will replicate how a live strategy would function as current market data would be sent "down the pipe".
    Thus, a historic and live system will be treated identically by the rest of the backtesting suite.
    """
    __metaclass__ = ABCMeta

    @abstractmethod
    def get_latest_bar(self, symbol):
        """
        param symbol: The ticker or FX pair of interest.
        return: The last bar updated.
        """
        raise NotImplementedError("Should implement get_latest_bar()")

    @abstractmethod
    def get_latest_bars(self, symbol, N=1):
        """
        param symbol: The ticker or FX pair of interest.
        param N: The number of bars.
        return: The last N bars updated.
        """
        raise NotImplementedError("Should implement get_latest_bars()")

    @abstractmethod
    def get_latest_bar_datetime(self, symbol):
        """
        param symbol: The ticker or FX pair of interest.
        return: Returns a Python datetime object for the last bar.
        """
        raise NotImplementedError("Should implement get_latest_bar_datetime()")

    @abstractmethod
    def get_latest_bar_value(self, symbol, val_type):
        """
        param symbol: The ticker or FX pair of interest.
        param val_type: Open, High, Low, Close, Volume or OI
        return: Returns one of the val_type from the last bar
        """
        raise NotImplementedError("Should implement get_latest_bar_value()")

    @abstractmethod
    def get_latest_bars_values(self, symbol, val_type, N=1):
        """
        param symbol: The ticker or FX pair of interest
        param val_type: Open, High, Low, Close, Volume or OI
        param N: The number of bars.
        return: Returns the last N bar values from the latest_symbol list, or N-k if less available.
        """
        raise NotImplementedError("Should implement get_latest_bar_values()")

    @abstractmethod
    def update_bars(self):
        """
        return: Pushes the latest bars to the bars_queue for each symbol
                in a tuple OHLCVI format: (datetime, open, high, low,
                close, volume, open interest)
        """
        raise NotImplementedError("Should implement update_bars()")


class HistoricDataHandler(DataHandler):  # it inherits from DataHandler with its abstracts methods.
    """
    Python Class for getting data from the SaxoOpenAPI.
    """

    def __init__(self, events, api, symbol_list):
        """
            Definition
            ----------
            Python instantiation of the class.

            Parameters
            ----------
            events: The Event Queue.
            symbol_list: str, first FX pair of interest.

            Return
            ------
            None.

        """
        self.events = events
        self.symbol_list = symbol_list
        self.symbol_data = {}
        self.api = api
        self.latest_symbol_data = {}
        self.continue_backtest = True

        self.yahooData()

    def yahooData(self):

        # set the latest symbol data to None (so it can be loaded afterwords)

        comb_index = None
        for s in self.symbol_list:
            # Combine the index to pad forward values
            self.symbol_data[s] = self.api.sort_index(ascending=False)
            if comb_index is None:
                comb_index = self.symbol_data[s].index
            else:
                comb_index.union(self.symbol_data[s].index)

            self.latest_symbol_data[s] = []

        # reindex the dataframe
        for s in self.symbol_list:
            self.symbol_data[s] = self.symbol_data[s].reindex(index=comb_index, method='pad').iterrows()

    def _get_new_bar(self, symbol):
        """
        param symbol: The ticker or FX pair of interest.
        return: Returns the latest bar from the data feed.
        """
        # yield self.symbol_data[-1:]
        for s in self.symbol_data[symbol]:
            yield s
    def get_latest_bar(self, symbol):
        """
        param symbol: The ticker or FX pair of interest.
        return:
        """
        try:
            bars_list = self.latest_symbol_data[symbol]
        except KeyError:
            print("That symbol is not available from Saxo API.")
            raise
        else:
            return bars_list[-1]

    def get_latest_bars(self, symbol, N=1):
        """
        return: returns the last N bars from the latest_symbol list, or N-k if less available.
        """
        try:
            bars_list = self.latest_symbol_data[symbol]
        except KeyError:
            print("That symbol is not available in the historical data set")
            raise
        else:
            return bars_list[-N:]

    def get_latest_bar_datetime(self, symbol):
        """
        param symbol: The ticker of interest.
        return: a python datetime object for the last bar.
        """
        try:
            bars_list = self.latest_symbol_data[symbol]
        except KeyError:
            print("That symbol is not available in the historical data set.")
            raise
        else:
            return bars_list[-1][0]

    def get_latest_bar_value(self, symbol, val_type):
        """
        param symbol: The ticker of interest.
        param val_type: OpenMid, CloseMid, HighMid, LowMid
        return: returns values from the pandas object.
        """
        try:
            bars_list = self.latest_symbol_data[symbol]
        except KeyError:
            print("That symbol is not available in the historical data set.")
            raise
        else:
            return getattr(bars_list[-1][1], val_type)

    def get_latest_bars_values(self, symbol, val_type, N=1):
        """
        param symbol:  The ticker of interest.
        param val_type: OpenMid, CloseMid, HighMid, LowMid
        param N: last N bars
        return: the last N bars values of the symbol (or symbol list), or N-k if less available.
        """
        try:
            bars_list = self.get_latest_bars(symbol, N)
        except KeyError:
            print("That symbol is not available in the historical data set.")
            raise
        else:
            return np.array([getattr(b[1], val_type) for b in bars_list])

    ## check this because it is not so obvious

    def update_bars(self):
        """
        return: pushes the latest bar to the latest_symbol_data structure
        for all symbols in the symbol list.
        """

        for s in self.symbol_list:
            try:
                bar = next(self._get_new_bar(s))
            except StopIteration:
                self.continue_backtest = False
            else:
                if bar is not None:
                    self.latest_symbol_data[s].append(bar)
        self.events.put(MarketEvent())  # this put() adds elements (events) to the queue
