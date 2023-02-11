from orders import *
from charts import *

# Initialize the class getFromApi()
begin = getFromApi("FxSpot", 'EUR', True, 'EURUSD', 'EURRUB', 'XAUEUR', 15)

# Get UCIs symbols for each pair
info = begin.getUCI()
a = info[info['Symbol'] == 'EURUSD']
b = int(a['Identifier'][0])
## normalized data for charts and comparison
forexData = begin.downloadData

prova = begin.downloaded_data.json()
fx = pd.DataFrame.from_dict(prova["Data"])
fx["Symbol"] = info.Symbol[0]
fx["CloseMid"] = (fx["CloseAsk"] + fx["CloseBid"]) / 2
fx["HighMid"] = (fx["HighAsk"] + fx["HighBid"]) / 2
fx["LowMid"] = (fx["LowAsk"] + fx["LowBid"]) / 2
fx["OpenMid"] = (fx["OpenAsk"] + fx["OpenBid"]) / 2
fx = fx[["Time", "Symbol", "CloseMid", "OpenMid", "HighMid", "LowMid"]]
latest_fx = {fx["Symbol"][0]: []}

# Plot the forex overview
forex_overview = begin.getGraph()

# plot the candlestick
eurusd = candlestick(begin.EURUSD, 'EURUSD spot, 15min')
eurrub = candlestick(begin.EURRUB, 'EURRUB spot, 15min')
xaueur = candlestick(begin.XAUEUR, 'XAUEUR Spot, 15min')

# correlation

# trade
place = Order(1000.0, 21)
first = place.newOrder("Buy", 1.05, "Limit")
modify = place.changeExistingOrder(first, 1.09, "Market")
cancel = place.cancelExistingOrder(first)

first_order = newOrder(1000.0, "Buy", "Market", 1.06, 21)

limit_order = {
    "AccountKey": AccountKey,
    "AssetType": 'FxSpot',
    "Uic": 21,
    "BuySell": "Buy",
    "Amount": 1000,
    "OrderType": "Market",
    # "OrderPrice": '1.05',  # for serialization
    "OrderDuration": {"DurationType": "DayOrder"},
    "ExternalReference": secrets.token_urlsafe(16),  # a random identifier for this order
    "ManualOrder": True,
}
order = requests.post("https://gateway.saxobank.com/sim/openapi/" + "trade/v2/orders",
                      headers={'Authorization': 'Bearer ' + TOKEN}, json=limit_order)
out = order.json()
if len(out) != 0:
    orderId = out["OrderId"]
    print("Order " + orderId + " placed successfully!")
else:
    print("Order not placed successfully.")
