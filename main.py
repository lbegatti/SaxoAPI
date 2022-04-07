from orders import *

# Initialize the class getFromApi()
begin = getFromApi("FxSpot", 'EUR', True, 'EURUSD', 'EURRUB', 'XAUEUR', 15)

# Get UCIs symbols for each pair
info = begin.getUCI()

# Download forex data using the UCI
## normalized data for charts and comparison
forexData = begin.downloadData()
## real fx prices
real_data = begin.extract_fx

# Plot the forex overview
forex_overview = begin.getGraph()

# Plot the forex as facet
# forex_facet = begin.getFacet()

# correlation

# trade
place = Order(1000.0, 21)
first = place.newOrder("Sell", 1.09, "Limit")
modify = place.changeExistingOrder(first, 1.09, "Limit")
cancel = place.cancelExistingOrder(first)

first_order = newOrder(1000.0, "Buy", "Market", None, 21)

search = {
    "AccountKey": AccountKey,
    "Amount": 1000.0,
    "BuySell": "Sell",
    "OrderType": "Market",
    # "OrderPrice": 1.06285,
    "ManualOrder": True,
    "Uic": 21,
    "AssetType": "FxSpot",
    "OrderDuration": {
        "DurationType": "DayOrder"
    }
}

order = requests.post("https://gateway.saxobank.com/sim/openapi/trade/v2/orders",
                      headers={'Authorization': 'Bearer ' + TOKEN},
                      json=search)
out = order.json()
if len(out) != 0:
    orderId = out["OrderId"]
    print("Order " + orderId + " placed successfully!")
else:
    print("Order did not go through.")
orderID = pd.DataFrame.from_dict(out)

ch_order = requests.patch("https://gateway.saxobank.com/sim/openapi/" + "trade/v2/orders",
                          headers={'Authorization': 'Bearer ' + TOKEN}, json=search)
out1 = ch_order.json()


search = {
    "AccountKey": AccountKey,
    "OrderIds": first
}
del_order = requests.delete("https://gateway.saxobank.com/sim/openapi/" + "trade/v2/orders",
                            headers={'Authorization': 'Bearer ' + TOKEN}, json=search)
out = del_order.json()
if len(out) != 0:
    delOrder = out["OrderId"]
    print("Order " + delOrder + " deleted successfully!")