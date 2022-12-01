from __future__ import print_function

import secrets
from abc import ABCMeta, abstractmethod, ABC

import pandas as pd
import numpy as np
from event import MarketEvent

# copy your (24-hour) token here
import requests

TOKEN = "eyJhbGciOiJFUzI1NiIsIng1dCI6IkRFNDc0QUQ1Q0NGRUFFRTlDRThCRDQ3ODlFRTZDOTEyRjVCM0UzOTQifQ.eyJvYWEiO" \
        "iI3Nzc3NSIsImlzcyI6Im9hIiwiYWlkIjoiMTA5IiwidWlkIjoiWXw0VDl3Rk1HVzZrQ2cwME5WWTJ6QT09IiwiY2lkIjoiWXw0V" \
        "Dl3Rk1HVzZrQ2cwME5WWTJ6QT09IiwiaXNhIjoiRmFsc2UiLCJ0aWQiOiIyMDAyIiwic2lkIjoiNGJjY2JmNzNhNWEyNGNmY2ExOGIw" \
        "NmFjYWE4MDkxZTciLCJkZ2kiOiI4NCIsImV4cCI6IjE2Njg3MTkxNDYiLCJvYWwiOiIxRiIsImlpZCI6IjBjZWQxYWZjYjFiYTQxM2Q1MzE" \
        "yMDhkYWM3YzFlZjI4In0.mrjrbhkoyya_BbD4FIhfM2KsC0FZawFGVOfeE-sHWs1rgYlpJgAxh_WSFv5LYrxXn-dsTeKLh3kM3Nq6ssMnPg"

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


class SaxoAPIDataHandler(DataHandler):  # it inherits from DataHandler with its abstracts methods.
    """
    Python Class for getting data from the SaxoOpenAPI.
    """

    def __init__(self, events, asset_type: str, keyword: str, is_nontradable: bool, symbol,
                 horizon: int):
        """
            Definition
            ----------
            Python instantiation of the class.

            Parameters
            ----------
            events: The Event Queue.
            asset_type: str, 'FxSpot'. Since it is a demo account.
            keyword: str to help filter among the currencies.
            is_nontradable: bool, necessary to filter those which are also not tradable.
            symbol: str, first FX pair of interest.
            horizon: int, the frequency of the data. For instance if horizon=15 then it is a
                15min frequency for the data under observation.

            Return
            ------
            None.

        """
        self.events = events
        self.search = None
        self.asset_type = asset_type
        self.keyword = keyword
        self.is_nontradable = is_nontradable
        self.symbol = symbol
        self.uci = None
        self.rel_info = None
        self.params_fx_spot = None
        self.horizon = horizon
        self.download_data = None
        self.symbol_data = {}
        self.latest_symbol_data = {}
        self.continued_backtest = True

    def getUCI(self) -> pd.DataFrame:
        """
            Definition
            ----------
            Python method to get the info for each currency of interest.


            Parameters
            ----------
            self: the instance of the class.


            Return
            ------
            pd.Dataframe with the relevant info to identify the FX pairs of interest.

        """
        self.search = {
            "AssetTypes": self.asset_type,
            "Keywords": self.keyword,
            "IncludeNonTradable": self.is_nontradable
        }
        self.uci = requests.get("https://gateway.saxobank.com/sim/openapi/" + "ref/v1/instruments", params=self.search,
                                headers={'Authorization': 'Bearer ' + TOKEN})
        searchOutput = self.uci.json()
        info = pd.DataFrame.from_dict(searchOutput["Data"])
        self.rel_info = info[info.Symbol.isin([self.symbol])].reset_index(drop=True)
        return self.rel_info

    def downloadData(self):

        rel_info = self.rel_info

        self.params_fx_spot = {
            "AssetType": self.asset_type,
            "Horizon": self.horizon,
            "Uic": rel_info.Identifier
        }
        self.download_data = requests.get("https://gateway.saxobank.com/sim/openapi/" + "chart/v1/charts",
                                          params=self.params_fx_spot, headers={'Authorization': 'Bearer ' + TOKEN})
        fx_pair = self.download_data.json()
        df_fx = pd.DataFrame.from_dict(fx_pair["Data"])

        # Close, High, Low, Open price info for the candlestick
        self.symbol_data = df_fx.copy()
        self.symbol_data["Symbol"] = rel_info.Symbol
        self.symbol_data["CloseMid"] = (self.symbol_data["CloseAsk"] + self.symbol_data["CloseBid"]) / 2
        self.symbol_data["HighMid"] = (self.symbol_data["HighAsk"] + self.symbol_data["HighBid"]) / 2
        self.symbol_data["LowMid"] = (self.symbol_data["LowAsk"] + self.symbol_data["LowBid"]) / 2
        self.symbol_data["OpenMid"] = (self.symbol_data["OpenAsk"] + self.symbol_data["OpenBid"]) / 2
        self.symbol_data = self.symbol_data[["Time", "Symbol", "OpenMid", "CloseMid", "HighMid", "LowMid"]]

        # set the latest symbol data to None (so it can be loaded afterwords)
        self.latest_symbol_data[self.symbol_data.Symbol[0]] = []

        return self.symbol_data

    def _get_new_bar(self, symbol):
        """
        param symbol: The ticker or FX pair of interest.
        return: Returns the latest bar from the data feed.
        """
        yield self.symbol_data[-1:]
        # for s in self.symbol_data[symbol]:
        #    yield s

    def get_latest_bar(self, symbol):
        """
        param symbol: The ticker or FX pair of interest.
        return:
        """
        try:
            bars_list = self.latest_symbol_data[self.symbol]
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
            bars_list = self.latest_symbol_data[self.symbol]
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
            bars_list = self.latest_symbol_data[self.symbol]
        except KeyError:
            print("That symbol is not available in the historical data set.")
            raise
        else:
            return bars_list.iloc[-1, 0]

    def get_latest_bar_value(self, symbol, val_type):
        """
        param symbol: The ticker of interest.
        param val_type: OpenMid, CloseMid, HighMid, LowMid
        return: returns values from the pandas object.
        """
        try:
            bars_list = self.latest_symbol_data[self.symbol]
        except KeyError:
            print("That symbol is not available in the historical data set.")
            raise
        else:
            return getattr(bars_list[-1:], val_type)

    def get_latest_bars_values(self, symbol, val_type, N=1):
        """
        param symbol:  The ticker of interest.
        param val_type: OpenMid, CloseMid, HighMid, LowMid
        param N: last N bars
        return: the last N bars values of the symbol (or symbol list), or N-k if less available.
        """
        try:
            bars_list = self.get_latest_bars(self.symbol, N)
        except KeyError:
            print("That symbol is not available in the historical data set.")
            raise
        else:
            np.array([getattr(bars_list.iloc[N:1199:], val_type)])

    ## check this because it is not so obvious

    def update_bars(self):
        """
        return: pushes the latest bar to the latest_symbol_data structure
        for all symbols in the symbol list (so far no list so only one symbol)
        """
        # we have only the EURUSD for now, as a symbol not a list...
        try:
            bar = next(self._get_new_bar(self.symbol))
        except StopIteration:
            self.continued_backtest = False
        else:
            if bar is not None:
                self.latest_symbol_data[self.symbol].append(bar)
        self.events.put(MarketEvent())  # this put() adds elements (events) to the queue
