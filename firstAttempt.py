from orders import *
from charts import *

# Initialize the class getFromApi()
begin = getFromApi("FxSpot", 'EUR', True, 'EURUSD', 'EURRUB', 'XAUEUR', 15)

# Get UCIs symbols for each pair
info = begin.getUCI()

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


def fake(symbol):
    """
    param symbol: The ticker or FX pair of interest.
    :return: Returns the latest bar from the data feed.
    """
    yield fx[-1:]


a = fake(fx.Symbol)

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

first_order = newOrder(1000.0, "Buy", "Market", None, 21)
