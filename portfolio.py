from __future__ import print_function
import datetime
from math import floor
import queue
import numpy as np
import pandas as pd

#
from event import FillEvent, OrderEvent
from performance import create_drawdowns, create_sharpe_ratio

"""The initialization of the Portfolio object requires access to the bars DataHandler, the events Event Queue, a 
start datetime stamp and an initial capital value"""


class Portfolio(object):
    """The portfolio class handles the positions and market value of
    all instruments at each update of the "bar" which can be every 5 mins.
    1h or 1y...

    The position DataFrame stores a time-index of the quantity of positions held.

    The holding DataFrame stores the cash and total market holdings value of each symbol for
    a particular time-index, as well as the percentage change in portfolio total across bars.
    """

    def __init__(self, bars, events, start_date, initial_capital=1000000.0):
        """
        Initializes the portfolio with bars and an event queue. It also
        includes a starting datetime index and initial capital unless otherwise stated.
        In saxo in the demo account it should be EUR 1,000,000.
        bars: The DataHandler object with current market data.
        events: The Event Queue object.
        start_date: The start date (bar) of the portfolio.
        initial_capital: The starting capital in EUR.
        """
        self.bars = bars
        self.events = events
        self.symbol_list = self.bars.symbol_list
        self.start_date = start_date
        self.initial_capital = initial_capital

        self.all_positions = self.construct_all_positions()
        self.current_positions = dict((k, v) for k, v in [(s, 0) for s in self.symbol_list])

        self.all_holdings = self.construct_all_holdings()
        self.current_holdings = self.construct_current_holdings()
        self.fx_curve = None

    def construct_all_positions(self):
        """
        Constructs the positions list using the start_date to determine when the time index will begin.
        """
        d = dict((k, v) for k, v in [(s, 0) for s in self.symbol_list])
        # d['datetime'] = self.start_date
        d["Time"] = self.start_date
        return [d]

    def construct_all_holdings(self):
        """
        Construct the holdings list using the start_date
        to determine when the time index will begin.
        """
        d = dict((k, v) for k, v in [(s, 0.0) for s in self.symbol_list])
        d["Time"] = self.start_date
        d["cash"] = self.initial_capital
        d["commission"] = 0.0
        d["total"] = self.initial_capital
        return [d]

    def construct_current_holdings(self):
        d = dict((k, v) for k, v in [(s, 0.0) for s in self.symbol_list])
        d["Time"] = self.start_date
        d["cash"] = self.initial_capital
        d["commission"] = 0.0
        d["total"] = self.initial_capital
        return d

    def update_timeindex(self, event):
        """
        Adds a new record to the position matrix for the current market data bar.This reflects
        the PREVIOUS bar, i.e. all current market data at this stage is known (OHLCV)

        Makes use of a MarketEvent from the events queue.
        param event: from MarketEvent
        return:
        """
        latest_datetime = self.bars.get_latest_bar_datetime(self.symbol_list[0])

        ## update positions
        dp = dict((k, v) for k, v in [(s, 0) for s in self.symbol_list])
        dp['Time'] = latest_datetime

        for s in self.symbol_list:
            dp[s] = self.current_positions[s]
        # Append the current positions
        self.all_positions.append(dp)

        # update holdings
        dh = dict((k, v) for k, v in [(s, 0) for s in self.symbol_list])
        dh["Time"] = latest_datetime
        dh["cash"] = self.current_holdings['cash']
        dh["commission"] = self.current_holdings['commission']
        dh["total"] = self.current_holdings['cash']

        for s in self.symbol_list:
            market_value = self.current_positions[s] * self.bars.get_latest_bar_value(s, "Adj Close")
            dh[s] = market_value
            dh["total"] += market_value

        # append the current holdings
        self.all_holdings.append(dh)

    def update_positions_from_fill(self, fill):
        """
        Takes a Fill object and updates the position matrix to reflect the new position.
        param fill: The Fill object to update the positions with.
        return:
        """

        # Check whether the Fill order is Buy or Sell
        fill_dir = 0
        if fill.direction == "BUY":
            fill_dir = 1
        if fill.direction == "SELL":
            fill_dir = -1

        # update position list with new quantities
        self.current_positions[fill.symbol] += fill_dir * fill.quantity

    def update_holdings_from_fill(self, fill):
        """
        Takes a FIll objects and updates the holdings matrix to reflect the holdings value.
        param fill: The Fill objects to update the holdings with.
        return:
        """
        # Check whether the Fill order is Buy or Sell
        fill_dir = 0
        if fill.direction == "BUY":
            fill_dir = 1
        if fill.direction == "SELL":
            fill_dir = -1

        # update holdings list with new quantities
        fill_cost = self.bars.get_latest_bar_value(fill.symbol, "CloseMid")
        cost = fill_dir * fill_cost * fill.quantity
        self.current_holdings[fill.symbol] += cost
        self.current_holdings['commission'] += fill.commission
        self.current_holdings['cash'] -= (cost + fill.commission)
        self.current_holdings['total'] -= (cost + fill.commission)

    def update_fill(self, event):
        """
        Updates the portfolio current positions and holdings from a FillEvent
        param event: The Fill event
        return:
        """
        if event.type == "FILL":
            self.update_positions_from_fill(fill=event)
            self.update_holdings_from_fill(fill=event)

    def generate_naive_order(self, signal):
        """
        Simply files an order object as a constant quantity sizing of the signal object
        param signal: The tuple containing Signal information
        return:
        """
        order = None
        symbol = signal.symbol
        direction = signal.direction
        strength = signal.strength

        mkt_quantity = 10000  # 10,000 of the currency (it can be adjusted obviously)
        cur_quantity = self.current_positions[symbol]
        order_type = "Market"

        if direction == "LONG" and cur_quantity == 0:
            order = OrderEvent(symbol=symbol, order_type=order_type, quantity=mkt_quantity, direction="BUY")
        if direction == "LONG" and cur_quantity == 0:
            order = OrderEvent(symbol=symbol, order_type=order_type, quantity=mkt_quantity, direction="SELL")

        if direction == "EXIT" and cur_quantity > 0:
            order = OrderEvent(symbol=symbol, order_type=order_type, quantity=abs(mkt_quantity), direction="SELL")
        if direction == "EXIT" and cur_quantity < 0:
            order = OrderEvent(symbol=symbol, order_type=order_type, quantity=abs(mkt_quantity), direction="BUY")

        return order

    def update_signal(self, event):
        """
        Acts on a SignalEvent to generate new orders based on the portfolio logic
        param event: Signal event
        :return: 
        """
        if event.type == "SIGNAL":
            order_event = self.generate_naive_order(signal=event)
            self.events.put(order_event)

    def create_fx_curve_dataframe(self):
        """
        Creates a pandas DataFrame from the all_holdings list of dictionaries.
        return: 
        """
        curve = pd.DataFrame(self.all_holdings)
        curve.set_index('Time', inplace=True)
        curve['returns'] = curve['total'].pct_change()
        curve['fx_curve'] = (1.0 + curve['returns']).cumprod()
        self.fx_curve = curve

    def output_summary_stats(self):
        """
        Creates a list of summary statistics for the portfolio.
        return:
        """
        total_return = self.fx_curve['fx_curve'][-1]
        returns = self.fx_curve['returns']
        pnl = self.fx_curve['fx_curve']

        sharpe_ratio = create_sharpe_ratio(returns, periods=252 * 60 * 6.5)
        drawdown, max_dd, dd_duration = create_drawdowns(pnl)
        self.fx_curve['drawdown'] = drawdown
        stats = [("Total Return", "%0.2f%%" % ((total_return - 1.0) * 100.0)),
                 ("Sharpe Ratio", "%0.2f" % sharpe_ratio),
                 ("Max Drawdown", "%0.2f%%" % (max_dd * 100.0)),
                 ("Drawdown Duration", "%d" % dd_duration)]
        self.fx_curve.to_csv('fx.csv')
        return stats
