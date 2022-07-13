from download_data import *

ClientKey = 'vJS9h8wkxd7a3YrJF9fo4w=='
AccountKey = ClientKey


# these newOrder, changeOrder and cancelOrder are needed to modify or cancel ANY order as amount and other parameters
## are inputed directly, i.e. not part of a class
def newOrder(amount: float, buysell: str, orderType: str, orderPrice: None, uic: int):
    search = {
        "AccountKey": AccountKey,
        "Amount": amount,
        "BuySell": buysell,
        "OrderType": orderType,
        "OrderPrice": orderPrice,
        "ManualOrder": True,
        "Uic": uic,
        "AssetType": "FxSpot",  ## for now I can do only this one
        "OrderDuration": {
            "DurationType": "DayOrder"
        }
    }
    order = requests.post("https://gateway.saxobank.com/sim/openapi/" + "trade/v2/orders",
                          headers={'Authorization': 'Bearer ' + TOKEN}, json=search)
    out = order.json()
    if len(out) != 0:
        orderId = out["OrderId"]
        print("Order " + orderId + " placed successfully!")
        return orderId
    else:
        print("Order not placed successfully.")


def changeOrder(orderid: int, amount: float, orderPrice: float, orderType: str):
    search = {
        "AccountKey": AccountKey,
        "Amount": amount,
        "AssetType": "FxSpot",
        "OrderDuration": {
            "DurationType": "DayOrder"
        },
        "Orderid": orderid,
        "OrderPrice": orderPrice,
        "OrderType": orderType
    }
    ch_order = requests.patch("https://gateway.saxobank.com/sim/openapi/" + "trade/v2/orders",
                              headers={'Authorization': 'Bearer ' + TOKEN}, json=search)
    out = ch_order.json()
    if len(out) != 0:
        chOrderId = out["OrderId"]
        print("Order " + chOrderId + " changed successfully!")
        return chOrderId
    else:
        print("Order not updated successfully.")


def cancelOrder(orderid: str):
    search = {
        "AccountKey": AccountKey
    }

    del_order = requests.delete("https://gateway.saxobank.com/sim/openapi/" + f"trade/v2/orders/{orderid}/",
                                headers={'Authorization': 'Bearer ' + TOKEN}, params=search)
    out = del_order.json()
    if len(out) != 0:
        delOrder = out["Orders"][0]['OrderId']
        print("Order " + delOrder + " deleted successfully!")
        return delOrder
    else:
        print("Order not deleted successfully.")


class Order:
    """Order Class: provides methods to place a new order, change and delete it.
                    The class is built to modify or delete orders who have been
                    just created as amount and uic are utilized in the
                    class to avoid retyping them.

        To change, delete ANY order refer to the methods above.
    """

    def __init__(self, amount, uic):
        self.amount = amount
        self.uic = uic

    def newOrder(self, buysell: str, orderPrice: None, orderType: str):
        search = {
            "AccountKey": AccountKey,
            "Amount": self.amount,
            "BuySell": buysell,
            "OrderType": orderType,
            "OrderPrice": orderPrice,
            "ManualOrder": True,
            "Uic": self.uic,
            "AssetType": "FxSpot",  ## for now i can do only this one
            "OrderDuration": {
                "DurationType": "DayOrder"
            }
        }
        order = requests.post("https://gateway.saxobank.com/sim/openapi/" + "trade/v2/orders",
                              headers={'Authorization': 'Bearer ' + TOKEN}, json=search)
        out = order.json()
        if len(out) != 0:
            orderId = out["OrderId"]
            print("Order " + orderId + " placed successfully!")
            return orderId  # this is needed if you have to change the order
        else:
            print("Order not placed successfully.")

    def changeExistingOrder(self, orderid: str, orderPrice: float, orderType: str):
        search = {
            "AccountKey": AccountKey,
            "Amount": self.amount,
            "AssetType": "FxSpot",
            "OrderDuration": {
                "DurationType": "DayOrder"
            },
            "Orderid": orderid,
            "OrderPrice": orderPrice,
            "OrderType": orderType
        }
        ch_order = requests.patch("https://gateway.saxobank.com/sim/openapi/" + "trade/v2/orders",
                                  headers={'Authorization': 'Bearer ' + TOKEN}, json=search)
        out = ch_order.json()
        if len(out) != 0:
            chOrderId = out["OrderId"]
            print("Order " + chOrderId + " updated successfully!")
            return chOrderId
        else:
            print("Order not updated successfully.")

    def cancelExistingOrder(self, orderid: str):
        search = {
            "AccountKey": AccountKey
        }
        del_order = requests.delete("https://gateway.saxobank.com/sim/openapi/" + f"trade/v2/orders/{orderid}/",
                                    headers={'Authorization': 'Bearer ' + TOKEN}, params=search)
        out = del_order.json()
        if len(out) != 0:
            delOrder = out["Orders"][0]['OrderId']
            print("Order " + delOrder + " deleted successfully!")
            return delOrder
        else:
            print("Order not deleted successfully.")
