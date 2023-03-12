from __future__ import print_function

import datetime
import numpy as np
import pandas as pd
import sklearn
import yfinance as yf

from pandas_datareader.yahoo.daily import YahooDailyReader
from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.discriminant_analysis import LinearDiscriminantAnalysis
from sklearn.metrics import confusion_matrix
from sklearn.discriminant_analysis import QuadraticDiscriminantAnalysis
from sklearn.svm import LinearSVC, SVC


def get_lag_data(symbol, start_date, end_date, lags=50):
    ts = yf.download(tickers=symbol, start=start_date - datetime.timedelta(days=365), end=end_date)
    ts.index = [datetime.datetime.combine(ts.index[i].to_pydatetime(), ts.index[i].to_pydatetime().time()) for i in
                range(0, len(ts))]

    # create the new lagged df
    tslag = pd.DataFrame(index=ts.index)
    tslag['Today'] = ts['Adj Close']
    tslag['Volume'] = ts['Volume']

    for i in range(0, lags):
        tslag['Lag%s' % str(i + 1)] = ts['Adj Close'].shift(i + 1)

    # create the returns Dataframe
    tsret = pd.DataFrame(index=tslag.index)
    tsret["Volume"] = tslag["Volume"]
    tsret["Today"] = tslag["Today"].pct_change() * 100.0

    tsret.index = pd.DatetimeIndex(tsret.index)

    # returns = 0 are "rounded" to 0.0001 to avoid errors
    for i, x in enumerate(tsret["Today"]):
        if abs(x) < 0.0001:
            tsret["Today"][i] = 0.0001

    # lagged % returns

    for i in range(0, lags):
        tsret["Lag%s" % str(i + 1)] = tslag["Lag%s" % str(i + 1)].pct_change() * 100.0

    # direction column (up/down) move (1 or -1)
    tsret["Direction"] = np.sign(tsret["Today"])

    tsret = tsret[tsret.index >= start_date]

    return tsret


if __name__ == "__main__":
    snret = get_lag_data('SPY', datetime.datetime(2001, 1, 1), datetime.datetime(2023, 1, 1), lags=5)

    X = snret[['Lag1', "Lag2"]]
    y = snret["Direction"]

    # the test data is split into 2 before and after 1jan2022
    start_test = datetime.datetime(2022, 1, 1)

    X_train = X[X.index < start_test]
    X_test = X[X.index >= start_test]

    y_train = y[y.index < start_test]
    y_test = y[y.index >= start_test]

    print("Hit Rates/Confusion matrices:\n")
    models = [('LR', LogisticRegression()),
              ('LDA', LinearDiscriminantAnalysis()),
              ('QDA', QuadraticDiscriminantAnalysis()),
              ("LSVC", LinearSVC()),
              ("RSVM", SVC(
                  C=1000000.0, cache_size=200, class_weight=None, coef0=0.0, degree=3, gamma=0.0001, kernel='rbf',
                  max_iter=-1, probability=False, random_state=None, shrinking=True, tol=0.001, verbose=False)),
              ("RF", RandomForestClassifier(n_estimators=1000, criterion='gini', max_depth=None, min_samples_split=2,
                                            min_samples_leaf=1, bootstrap=True, oob_score=False,
                                            n_jobs=1,
                                            random_state=None, verbose=0)
               )]

    for m in models:
        m[1].fit(X_train, y_train)

        pred = m[1].predict(X_test)

        # Output the hit-rate and the confusion matrix for each model
        print("%s:\n%0.3f" % (m[0], m[1].score(X_test, y_test)))
        print("%s\n" % confusion_matrix(pred, y_test))
