from orders import *
from charts import *

# Initialize the class getFromApi()
begin = getFromApi("FxSpot", 'EUR', True, 'EURUSD', 'EURRUB', 'XAUEUR', 15)

# Get UCIs symbols for each pair
info = begin.getUCI()

# Download forex data using the UCI

## normalized data for charts and comparison
forexData = begin.downloadData()

### Extracting the Close, High, Low and Open for the candlestick.
XAUEUR = begin.BidAskCloseOpen[['Time', 'XAUEUR_CloseMid', 'XAUEUR_HighMid', 'XAUEUR_LowMid', 'XAUEUR_OpenMid']]
XAUEUR = XAUEUR.rename(
    columns={'XAUEUR_CloseMid': 'Close', 'XAUEUR_HighMid': 'High', 'XAUEUR_LowMid': 'Low', 'XAUEUR_OpenMid': 'Open'})

EURRUB = begin.BidAskCloseOpen[['Time', 'EURRUB_CloseMid', 'EURRUB_HighMid', 'EURRUB_LowMid', 'EURRUB_OpenMid']]
EURRUB = EURRUB.rename(
    columns={'EURRUB_CloseMid': 'Close', 'EURRUB_HighMid': 'High', 'EURRUB_LowMid': 'Low', 'EURRUB_OpenMid': 'Open'})

EURUSD = begin.BidAskCloseOpen[['Time', 'EURUSD_CloseMid', 'EURUSD_HighMid', 'EURUSD_LowMid', 'EURUSD_OpenMid']]
EURUSD = EURUSD.rename(
    columns={'EURUSD_CloseMid': 'Close', 'EURUSD_HighMid': 'High', 'EURUSD_LowMid': 'Low', 'EURUSD_OpenMid': 'Open'})

# Plot the forex overview
forex_overview = begin.getGraph()

# plot the candlestick
eurusd = candlestick(EURUSD)
eurrub = candlestick(EURRUB)
xaueur = candlestick(XAUEUR)

# correlation

# trade
place = Order(1000.0, 21)
first = place.newOrder("Buy", 1.05, "Limit")
modify = place.changeExistingOrder(first, 1.09, "Market")
cancel = place.cancelExistingOrder(first)

first_order = newOrder(1000.0, "Buy", "Market", None, 21)
