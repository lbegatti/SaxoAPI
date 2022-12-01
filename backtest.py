from __future__ import print_function
import datetime
import pprint
import queue
import time


class Backtest(object):
    """
    Contains the settings and components for carrying out an event-driven backtest.
    """

    def __int__(self, api, symbol_list, initial_capital, heartbeat, start_date, data_handler, execution_handler,
                portfolio, strategy):
        """

        api: the data from the API you are using.
        symbol_list: the list of symbols.
        initial_capital: The starting capital
        heartbeat: time of "refresh" for the whole backtesting.
        start_date: The start date of the strategy.
        data_handler: (Class) Handles the market data feed.
        execution_handler: (Class) Handles the orders/fills for trades.
        portfolio: (Class) Keeps track of portfolio current and prior positions.
        strategy: (Class) Generates signals based on market data.
        """
        self.api = api
        self.symbol_list = symbol_list
        self.initial_capital = initial_capital
        self.heartbeat = heartbeat
        self.start_date = start_date
        self.data_handler_cls = data_handler
        self.execution_handler_cls = execution_handler
        self.portfolio_cls = portfolio
        self.strategy_cls = strategy

        self.events = queue.Queue()

        self.signals = 0
        self.orders = 0
        self.fills = 0
        self.num_strats = 1

        self._generate_trading_instances()

    def _generate_trading_instances(self):
        """
        Generate the trading instance objects from their class types.
        """
        print("Creating DataHandler, Strategy, Portfolio, ExecutionHandler")
        self.data_handler = self.data_handler_cls(self.events, self.api, self.symbol_list)
        self.strategy = self.strategy_cls(self.data_handler, self.events)
        self.portfolio = self.portfolio_cls(self.data_handler, self.events, self.start_date, self.initial_capital)
        self.execution_handler = self.execution_handler_cls(self.events)

    def _run_backtest(self):
        """
        Execution of backtest.
        """
        i = 0
        while True:
            i += 1
            print(i)
            # update the market bars
            if self.data_handler.continue_backtest:
                self.data_handler.update_bars()
            else:
                break
            # handle the events
            while True:
                try:
                    event = self.events.get(False)
                except queue.Empty:
                    break
                else:
                    if event is not None:
                        if event.type == "Market":
                            self.strategy.calculate_signals(event)
                            self.portfolio.update_timeindex(event)
                        elif event.type == 'SIGNAL':
                            self.signals += 1
                            self.portfolio.update_signal(event)
                        elif event.type == 'ORDER':
                            self.orders += 1
                            self.execution_handler.execute_order(event)
                        elif event.type == "FILL":
                            self.fills += 1
                            self.portfolio.update_fill(event)
            time.sleep(self.heartbeat)

    def _output_performance(self):
        """
        Displays the performance from the backtesting of the strategy.
        """
        self.portfolio.create_fx_curve_dataframe()
        print("Creating summary stats...")
        stats = self.portfolio.output_summary_stats()
        print("Creating FX curve...")
        print(self.portfolio.fx_curve.tail(10))
        pprint.pprint(stats)

        print("Signals: %s" % self.signals)
        print("Orders: %s" % self.orders)
        print("Fills: %s" % self.fills)

    def simulate_trading(self):
        """
        It calls the previously defined methods in order.
        """
        self._run_backtest()
        self._output_performance()
