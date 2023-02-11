from __future__ import print_function
import datetime
import time
from saxo_openapi import API
from saxo_openapi.contrib.orders import tie_account_to_order, StopOrderFxSpot

from event import FillEvent, OrderEvent
from execution import ExecutionHandler
from data import *
from orders import *


class SBExecutionHandler(ExecutionHandler):
    """
    Handles order execution via Saxo Bank API.
    """

    def __init__(self, events, order_routing='SMART', currency='USD'):
        self.events = events
        self.order_routing = order_routing
        self.currency = currency
        self.fill_dict = {}

        # self.sb_conn = self.create_sb_connection()
        self.order_id = self.create_initial_order_id()
        # self.register_handlers()

    def _error_handler(self, msg):
        """
        Handles the capturing of error messages
        """
        # no error handling
        print("Server Error: %s" % msg)

    def _reply_handler(self, msg):
        """
        Handles server replies.
        """
        # Handles open order orderId processing
        if msg.typeName == "openOrder" and msg.orderId == self.order_id and msg.orderId not in self.fill_dict:
            self.create_fill_dict_entry(msg)
        # Handles fills order
        if msg.typeName == "orderStatus" and msg.status == "Filled" and not self.fill_dict[msg.orderId]['filled']:
            self.create_fill(msg)
        print("Server Response: %s, %s\n" % (msg.typeName, msg))

    def create_initial_order_id(self):
        """
        Creates the initial order ID used for Saxo Bank to keep track of submitted orders.
        """
        # this can be expanded
        # use 1 as default
        return 1

    def create_order(self, uic_id, order_type, quantity, action):
        """
        Create an Order object (market/limit) to go Long/Short
        """
        if order_type == 'Market':
            order = Order(amount=quantity, uic=uic_id).newOrder(buysell=action, orderPrice=None, orderType=order_type)
        elif order_type == 'Limit':
            order = Order(amount=quantity, uic=uic_id).newOrder(buysell=action, orderPrice='1.05', orderType=order_type)
        order_info = {
            'order_type': order_type,
            'totalQuantity': quantity,
            'action': action
        }

        # order.m_orderType = order_type
        # order.m_totalQuantity = quantity
        # order.m_action = action

        return order_info

    def create_fill_dict_entry(self, msg):
        """
        Creates an entry in the fill dictionary that lists orderID and provides security information.
        This is needed for event-driven behavior.This stores keys defining a particular order id, so there is
        no duplication
        """
        self.fill_dict[msg.orderId] = {
            "uic_id": msg.order.uic,
            'direction': msg.order_info['action'],
            'filled': False
        }

    def create_fill(self, msg):
        """
        Handles the creation of the FillEvent that will be placed on the events queue after
        an order has been filled.
        """
        fd = self.fill_dict[msg.orderId]

        # prepare the fill data
        uic_id = fd['uic_id']
        direction = fd['direction']
        filled = msg.filled
        fill_cost = msg.avgFillPrice

        # create a fill event

        fill_event = FillEvent(timeindex=datetime.datetime.utcnow(), symbol=uic_id, quantity=filled,
                               direction=direction, fill_cost=fill_cost)

        # make sure multiple messages do not create additional fills
        self.fill_dict[msg.orderId]['filled'] = True

        # place the fill on the event queue
        self.events.put(fill_event)

    def execute_order(self, event):
        """
        Creates the Saxo Bank order object and submits it to SB via the API.
        The results are then queried in order to generate a corresponding Fill object,
        which is placed back on the event queue.

        """
        if event.type == 'ORDER':
            # prep the parameters for the order
            asset = event.symbol
            search_uci = {
                "AssetTypes": 'FxSpot',
                "Keywords": asset,
                "IncludeNonTradable": True
            }
            retrieve_info = requests.get("https://gateway.saxobank.com/sim/openapi/" + "ref/v1/instruments",
                                         params=search_uci,
                                         headers={'Authorization': 'Bearer ' + TOKEN})
            searchOutput = retrieve_info.json()
            info = pd.DataFrame.from_dict(searchOutput["Data"])
            uci_id = int(info[info['Symbol'] == asset]['Identifier'][0])

            order_type = event.order_type
            quantity = event.quantity
            direction = event.direction

            # no contract needed here but just the request is embedded in the order
            self.create_order(uic_id=uci_id, order_type=order_type, quantity=quantity, action=direction)

            # this ensures the order goes through
            time.sleep(1)

            # increment the order ID
            self.order_id += 1

            fill_event = FillEvent(datetime.datetime.utcnow(), event.symbol, event.quantity, event.direction,
                                   None)
            self.events.put(fill_event)
