from __future__ import print_function


class Event(object):
    """
    Event is base class providing an interface for all subsequent (inherited) events, that will trigger
    further events in the trading infrastructure.
    """
    pass


class MarketEvent(Event):
    """
    Handles the event of receiving a new market update with corresponding bars.
    """

    def __init__(self):
        """
        Initialize the market event.
        """
        self.type = 'MARKET'


class SignalEvent(Event):
    """
    Handles the event of sending a Signal from a Strategy object. This is received by a Portfolio object and acted upon.
    """

    def __init__(self, strategy_id, symbol, datetime, signal_type, strength):
        """

        :param strategy_id: The unique identifier for the strategy that generated the signal
        :param symbol: The ticker symbol
        :param datetime: The timestamp at which the signal was generated.
        :param signal_type: 'LONG' or 'SHORT'
        :param strength: An adjustment factor "suggestion" used to scale quantity at the portfolio level.
                        Useful for pairs strategies.
        """
        self.type = 'SIGNAL'
        self.strategy_id = strategy_id
        self.symbol = symbol
        self.datetime = datetime
        self.signal_type = signal_type
        self.strength = strength


class OrderEvent(Event):
    """
    Handles the event of sending an Order to an execution system. The order contains a symbol (e.g. GOOG),
    a type (market or limit), quantity and a direction.
    """

    def __init__(self, symbol, order_type, quantity, direction):
        """
        Initialises the order type, setting whether it is a Market order (’Market’) or Limit order (’Limit’), has
        a quantity (integral) and its direction (’BUY’ or ’SELL’).

        :param symbol: The instrument to trade.
        :param order_type: 'Market' or 'Limit'
        :param quantity: Non-negative integer for quantities.
        :param direction: 'Buy' or 'Sell
        """
        self.type = 'ORDER'
        self.symbol = symbol
        self.order_type = order_type
        self.quantity = quantity
        self.direction = direction

    def print_order(self):
        """
        Outputs the values within the Order.
        :return: order details
        """
        print(
            "Order: Symbol = %s, Type = %s, Quantity = %s, Direction = %s" % (self.symbol, self.type, self.quantity,
                                                                              self.direction)
        )


class FillEvent(Event):
    """
    Encapsulates the notion of a Filled Order, as returned from a brokerage. Stores the quantity of an instrument
    actually filled and at what price. In addition, stores the commission of the trade from the brokerage.
    """

    def __init__(self, timeindex, symbol, exchange, quantity, direction, fill_cost, commission=None):
        """
        Initialises the FillEvent object. Sets the symbol, exchange, quantity, direction, cost of fill and
        an optional commission. If commission is not provided, the Fill object will calculate it based on
        the trade size and Saxo Bank fees.

        :param timeindex: The bar-resolution when the order was filled.
        :param symbol: The instrument which was filled.
        :param exchange: The exchange where the order was filled.
        :param quantity: The filled quantity.
        :param direction: The direction of fill ('Buy' or 'Sell')
        :param fill_cost: The holdings value in dollars.
        :param commission: Optional commission sent from Saxo.
        """
        self.type = 'FILL'
        self.timeindex = timeindex
        self.symbol = symbol
        self.exchange = exchange
        self.quantity = quantity
        self.direction = direction
        self.fill_cost = fill_cost
        if commission is None:
            self.commission = self.calculate_sb_commission()
        else:
            self.commission = commission

    def calculate_sb_commission(self):
        if self.quantity <= 500:
            full_cost = max(1.3, 0.013 * self.quantity)
        else:  # Greater than 500
            full_cost = max(1.3, 0.008 * self.quantity)
        return full_cost








































