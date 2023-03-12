**Trading algo SaxoOpenAPI**

This code is the building block to perform a few operations in Python via 
the SaxoOpenAPI. 
- The firstAttempt.py is a prototype performing basic trading operation using
the API, but it is limited to the FX world due to accessibility constraints.

- The main.py code will be calibrated for an FX pair.

- The forecast.py code is instead shows an example of forecasting with various
sklearn algos.

- The snp_forecast.py taking data from Yahoo focuses instead on the SPY index.

Both main.py and snp_forecast.py are not a trading per se but more backtesting algo to grasp how a certain
strategy would have performed if it had been implement, in hindsight. 

The code is based on the book "Successful algorithmic
trading by _Michael L. Halls-Moore_" adapted to SaxoOpenAPI specifications.
