import websocket, requests, secrets, json
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
import numpy as np
from pprint import pprint
from plotly.subplots import make_subplots

# copy your (24-hour) token here
TOKEN = "eyJhbGciOiJFUzI1NiIsIng1dCI6IkRFNDc0QUQ1Q0NGRUFFRTlDRThCRDQ3ODlFRTZDOTEyRjVCM0UzOTQifQ.eyJ" \
        "vYWEiOiI3Nzc3NSIsImlzcyI6Im9hIiwiYWlkIjoiMTA5IiwidWlkIjoiYnFra3Y2Y2ZxNmVrN3pwZ2lJckN1QT09IiwiY2l" \
        "kIjoiYnFra3Y2Y2ZxNmVrN3pwZ2lJckN1QT09IiwiaXNhIjoiRmFsc2UiLCJ0aWQiOiIyMDAyIiwic2lkIjoiZDFhNTNiY2QxZjg4" \
        "NGZjODk2YTg0MmQxYmRjOTE1MmYiLCJkZ2kiOiI4NCIsImV4cCI6IjE2NTE3MDE4NjgiLCJvYWwiOiIxRiJ9.WW0_j2ZJgt9d5tCQ2FgN" \
        "xxZWWGuNAfcj6JGEZ-ytx1EQoNaRYWY_cuiA2DUu968Irfi85savqrNTpO-0uI_2Jg"

# create a random string for context ID and reference ID
CONTEXT_ID = secrets.token_urlsafe(10)
REF_ID = secrets.token_urlsafe(5)


# class to download data from the API
class getFromApi:
    """
        Definition
        ----------
        Python Class for getting data from the SaxoOpenAPI. Also initial manipulation of data
            building up moving averages (15d,75d,200d).

    """

    def __init__(self, assettype: str, keyword: str, isnontradable: bool, pair1: str, pair2: str, pair3: str,
                 horizon: int):
        """
            Definition
            ----------
            Python instantiation of the class.


            Parameters
            ----------
            assettype: str, 'FxSpot'. Since it is a demo account.
            keyword: str. Used to refine the search among the many FX pairs available.
            isnontradable: bool, necessary to filter those which are also not tradable.
            pair1: str, first FX pair of interest.
            pair2: str, second FX pair of interest.
            pair3: str, thir FX pair of interest.
            horizon: int, the frequency of the data. For instance if horizon=15 then it is a
                15min frequency for the data under observation.


            Return
            ------
            None.

        """
        self.search = None
        self.assettype = assettype
        self.keyword = keyword
        self.isnontradable = isnontradable
        self.uci = None
        self.rel_info = None
        self.pair1 = pair1
        self.pair2 = pair2
        self.pair3 = pair3
        self.fx_data = pd.DataFrame()
        self.extract_fx = pd.DataFrame()
        self.extract_fx_final = pd.DataFrame()
        self.params_fx_spot = None
        self.horizon = horizon
        self.download_data = None
        self.BidAskCloseOpen = pd.DataFrame()
        # self.palle = pd.DataFrame()

    def getUCI(self) -> pd.DataFrame:
        """
            Definition
            ----------
            Python method to get the info for each currency of interest.


            Parameters
            ----------
            self: the instance of the class.


            Return
            ------
            pd.Dataframe with the relevant info to identify the FX pairs of interest.

        """
        self.search = {
            "AssetTypes": self.assettype,
            "Keywords": self.keyword,
            "IncludeNonTradable": self.isnontradable
        }
        self.uci = requests.get("https://gateway.saxobank.com/sim/openapi/" + "ref/v1/instruments", params=self.search,
                                headers={'Authorization': 'Bearer ' + TOKEN})
        searchOutput = self.uci.json()
        info = pd.DataFrame.from_dict(searchOutput["Data"])
        self.rel_info = info[info.Symbol.isin([self.pair1, self.pair2, self.pair3])].reset_index(drop=True)
        return self.rel_info

    def downloadData(self) -> pd.DataFrame:
        """
            Definition
            ----------
            Python method to download data from the SaxoOpenAPI.


            Parameters
            ----------
            self: instance of the class.


            Return
            ------
            pd.Dataframe with the relevant information of the FX pairs.

        """
        rel_info = self.rel_info
        for i in range(len(rel_info.Symbol)):
            self.params_fx_spot = {
                "AssetType": self.assettype,
                "Horizon": self.horizon,
                "Uic": rel_info.Identifier[i]
            }
            self.download_data = requests.get("https://gateway.saxobank.com/sim/openapi/" + "chart/v1/charts",
                                              params=self.params_fx_spot,
                                              headers={'Authorization': 'Bearer ' + TOKEN})
            fx_pair = self.download_data.json()
            # self.palle = pd.DataFrame.from_dict(fx_pair["Data"])
            df_fx = pd.DataFrame.from_dict(fx_pair["Data"])

            # Close, High, Low, Open price info for the candlestick
            candlestick_data = df_fx.copy()
            candlestick_data[rel_info.Symbol[i] + "_CloseMid"] = (candlestick_data["CloseAsk"] +
                                                                  candlestick_data["CloseBid"]) / 2
            candlestick_data[rel_info.Symbol[i] + "_HighMid"] = (candlestick_data["HighAsk"] +
                                                                 candlestick_data["HighBid"]) / 2
            candlestick_data[rel_info.Symbol[i] + "_LowMid"] = (candlestick_data["LowAsk"] +
                                                                candlestick_data["LowBid"]) / 2
            candlestick_data[rel_info.Symbol[i] + "_OpenMid"] = (candlestick_data["OpenAsk"] +
                                                                 candlestick_data["OpenBid"]) / 2
            candlestick_data = candlestick_data[
                ["Time", rel_info.Symbol[i] + "_CloseMid", rel_info.Symbol[i] + "_HighMid",
                 rel_info.Symbol[i] + "_LowMid", rel_info.Symbol[i] + "_OpenMid"]]
            self.BidAskCloseOpen = pd.merge(candlestick_data, self.BidAskCloseOpen, how='outer', left_index=True,
                                            right_index=True, suffixes=('', '_remove'))
            self.BidAskCloseOpen.drop([i for i in self.BidAskCloseOpen.columns if 'remove' in i], axis=1, inplace=True)

            # take only the close bid for the MA

            df_fx = df_fx[["Time", "CloseBid"]]

            # save the data before the normalization
            self.extract_fx = pd.merge(df_fx, self.extract_fx, how='outer', left_index=True, right_index=True,
                                       suffixes=('', '_remove'))
            self.extract_fx.drop([i for i in self.extract_fx.columns if 'remove' in i], axis=1, inplace=True)
            self.extract_fx.rename(columns={'CloseBid': rel_info.Symbol[i]}, inplace=True)

            df_fx['Symbol'] = rel_info.loc[rel_info['Symbol'] == rel_info.Symbol[i], 'Symbol'].iloc[0]

            df_fx[rel_info.Symbol[i] + '_N'] = (df_fx['CloseBid'] - np.mean(df_fx['CloseBid'])) / (
                np.std(df_fx['CloseBid']))
            df_fx = df_fx[["Time", rel_info.Symbol[i] + '_N']]
            self.fx_data = pd.merge(df_fx, self.fx_data, how='outer', left_index=True, right_index=True,
                                    suffixes=('', '_remove'))
            self.fx_data.drop([i for i in self.fx_data.columns if 'remove' in i], axis=1, inplace=True)

        self.fx_data = self.fx_data[
            ["Time", rel_info.Symbol[0] + '_N', rel_info.Symbol[1] + '_N', rel_info.Symbol[2] + '_N']]

        # first pair MAs 15d - 75d - 200d
        self.fx_data['MA_15d_' + self.fx_data.columns[1]] = self.fx_data.iloc[:, 1].rolling(window=15).mean()
        self.fx_data['MA_75d_' + self.fx_data.columns[1]] = self.fx_data.iloc[:, 1].rolling(window=75).mean()
        self.fx_data['MA_200d_' + self.fx_data.columns[1]] = self.fx_data.iloc[:, 1].rolling(window=200).mean()

        # second pair MAs
        self.fx_data['MA_15d_' + self.fx_data.columns[2]] = self.fx_data.iloc[:, 2].rolling(window=15).mean()
        self.fx_data['MA_75d_' + self.fx_data.columns[2]] = self.fx_data.iloc[:, 2].rolling(window=75).mean()
        self.fx_data['MA_200d_' + self.fx_data.columns[2]] = self.fx_data.iloc[:, 2].rolling(window=200).mean()

        # third pair MAs
        self.fx_data['MA_15d_' + self.fx_data.columns[3]] = self.fx_data.iloc[:, 3].rolling(window=15).mean()
        self.fx_data['MA_75d_' + self.fx_data.columns[3]] = self.fx_data.iloc[:, 3].rolling(window=75).mean()
        self.fx_data['MA_200d_' + self.fx_data.columns[3]] = self.fx_data.iloc[:, 3].rolling(window=200).mean()

        return self.fx_data

    def getGraph(self):
        """
            Definition
            ----------
            Python method to create subplots of the currencies pairs of interest.


            Parameters
            ----------
            self: instance of the class.


            Return
            ------
            the figure with subplots.

        """
        fig = make_subplots(rows=3, cols=1, shared_xaxes=True, shared_yaxes=True,
                            subplot_titles=(
                                self.pair1 + '_analysis', self.pair2 + '_analysis', self.pair3 + '_analysis'))
        fig.add_trace(
            go.Scatter(
                x=self.fx_data["Time"],
                y=self.fx_data.iloc[:, 1],
                name=self.fx_data.iloc[:, 1].name,
                mode='lines'
            ),
            row=1,
            col=1
        ),
        fig.add_trace(
            go.Scatter(
                x=self.fx_data["Time"],
                y=self.fx_data.iloc[:, 4],
                name=self.fx_data.iloc[:, 4].name,
                mode='lines'
            ),
            row=1,
            col=1
        ),
        fig.add_trace(
            go.Scatter(
                x=self.fx_data["Time"],
                y=self.fx_data.iloc[:, 5],
                name=self.fx_data.iloc[:, 5].name,
                mode='lines'
            ),
            row=1,
            col=1
        ),
        fig.add_trace(
            go.Scatter(
                x=self.fx_data["Time"],
                y=self.fx_data.iloc[:, 6],
                name=self.fx_data.iloc[:, 6].name,
                mode='lines'
            ),
            row=1,
            col=1
        )
        fig.add_trace(
            go.Scatter(
                x=self.fx_data["Time"],
                y=self.fx_data.iloc[:, 2],
                name=self.fx_data.iloc[:, 2].name,
                mode='lines'
            ),
            row=2,
            col=1
        ),
        fig.add_trace(
            go.Scatter(
                x=self.fx_data["Time"],
                y=self.fx_data.iloc[:, 7],
                name=self.fx_data.iloc[:, 7].name,
                mode='lines'
            ),
            row=2,
            col=1
        ),
        fig.add_trace(
            go.Scatter(
                x=self.fx_data["Time"],
                y=self.fx_data.iloc[:, 8],
                name=self.fx_data.iloc[:, 8].name,
                mode='lines'
            ),
            row=2,
            col=1
        ),
        fig.add_trace(
            go.Scatter(
                x=self.fx_data["Time"],
                y=self.fx_data.iloc[:, 9],
                name=self.fx_data.iloc[:, 9].name,
                mode='lines'
            ),
            row=2,
            col=1
        ),
        fig.add_trace(
            go.Scatter(
                x=self.fx_data["Time"],
                y=self.fx_data.iloc[:, 3],
                name=self.fx_data.iloc[:, 3].name,
                mode='lines'
            ),
            row=3,
            col=1
        ),
        fig.add_trace(
            go.Scatter(
                x=self.fx_data["Time"],
                y=self.fx_data.iloc[:, 10],
                name=self.fx_data.iloc[:, 10].name,
                mode='lines'
            ),
            row=3,
            col=1
        ),
        fig.add_trace(
            go.Scatter(
                x=self.fx_data["Time"],
                y=self.fx_data.iloc[:, 11],
                name=self.fx_data.iloc[:, 11].name,
                mode='lines'
            ),
            row=3,
            col=1
        ),
        fig.add_trace(
            go.Scatter(
                x=self.fx_data["Time"],
                y=self.fx_data.iloc[:, 12],
                name=self.fx_data.iloc[:, 12].name,
                mode='lines'
            ),
            row=3,
            col=1
        )
        fig.update_layout(
            title="Ukraine vs Russia Forex 15mins Effect, normalized",
            font=dict(
                family="Courier New, monospace",
                size=16,
                color="RebeccaPurple"
            )
        )
        fig.show(renderer='browser')

    def getFacet(self):
        """
            Definition
            ----------
            Python method to plot facet-graphs of the FX pairs


            Parameters
            ----------
            self: instance of the class.


            Return
            ------
            returns the facet fig with the plots for each currency pair.

        """
        facet_graph = self.fx_data.set_index("Time")
        facet_graph.columns.name = 'Pairs'
        facet_fig = px.area(facet_graph, facet_col='Pairs', facet_col_wrap=2,
                            title="Ukraine vs Russia Fx 15mins Effect, normalized")
        facet_fig.show()

    def candle_stick_chart(self):
        """
            Definition
            ----------
            Python method for candlestick chart (not sure if it is the best approach)


            Parameters
            ----------
            self: instance of the class.


            Return
            ------
            the candlestick plots.

        """
        candlestick = self.BidAskCloseOpen
        if 'XAU' in candlestick.columns[1] or 'XAU' in candlestick.columns[5] or 'XAU' in candlestick.columns[9]:
            title = 'XAU/EUR FX Pair'

        elif 'EURRUB' in candlestick.columns[1] or 'EURRUB' in candlestick.columns[5] or 'EURRUB' in \
                candlestick.columns[9]:
            title = 'EUR/RUB FX Pair'

        else:
            title = 'EUR/USD FX Pair'

        first = go.Figure(data=[go.Candlestick(x=candlestick["Time"],
                                               close=candlestick.iloc[:, 1],
                                               high=candlestick.iloc[:, 2],
                                               low=candlestick.iloc[:, 3],
                                               open=candlestick.iloc[:, 4])

                                ])
        first.update_layout(
            title=title,
            yaxis_title='FX Rate'
        )

        second = go.Figure(data=[go.Candlestick(x=candlestick["Time"],
                                                close=candlestick.iloc[:, 5],
                                                high=candlestick.iloc[:, 6],
                                                low=candlestick.iloc[:, 7],
                                                open=candlestick.iloc[:, 8])

                                 ])
        second.update_layout(
            title=title,
            yaxis_title='FX Rate'
        )
        third = go.Figure(data=[go.Candlestick(x=candlestick["Time"],
                                               close=candlestick.iloc[:, 9],
                                               high=candlestick.iloc[:, 10],
                                               low=candlestick.iloc[:, 11],
                                               open=candlestick.iloc[:, 12])

                                ])
        third.update_layout(
            title=title,
            yaxis_title='FX Rate'
        )
        first.show()
        second.show()
        third.show()
