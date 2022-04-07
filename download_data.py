import websocket, requests, secrets, json
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
import numpy as np
from pprint import pprint
from plotly.subplots import make_subplots

# copy your (24-hour) token here
TOKEN = "eyJhbGciOiJFUzI1NiIsIng1dCI6IkRFNDc0QUQ1Q0NGRUFFRTlDRThCRDQ3ODlFRTZDOTEyRjVCM0UzOTQifQ.ey" \
        "JvYWEiOiI3Nzc3NSIsImlzcyI6Im9hIiwiYWlkIjoiMTA5IiwidWlkIjoiYnFra3Y2Y2ZxNmVrN3pwZ2lJckN1QT09Iiw" \
        "iY2lkIjoiYnFra3Y2Y2ZxNmVrN3pwZ2lJckN1QT09IiwiaXNhIjoiRmFsc2UiLCJ0aWQiOiIyMDAyIiwic2lkIjoiYjk5MWEx" \
        "ODEzMjcwNGFmN2I1OTNiYjYwOWFjNjY2NDQiLCJkZ2kiOiI4NCIsImV4cCI6IjE2NDk0NTIzOTIiLCJvYWwiOiIxRiJ9.ZtTC1FxL" \
        "cNwlY3zytGi_UWAS5f13kd1BfSo9WZs2iUzoU2ye1IhUfy3AZxKwcnRHBbphAMEjIqO3BEZZQyBHgQ"

# create a random string for context ID and reference ID
CONTEXT_ID = secrets.token_urlsafe(10)
REF_ID = secrets.token_urlsafe(5)


# class to download data from the API
class getFromApi:
    """
    Class for getting data from the SaxoOpenAPI.
    Also initial manipulation of data building up moving averages (15d,75d,200d)
    """
    def __init__(self, assettype: str, keyword: str, isnontradable: bool, pair1: str, pair2: str, pair3: str,
                 horizon: int):
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

    def getUCI(self) -> pd.DataFrame:
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
            df_fx = pd.DataFrame.from_dict(fx_pair["Data"])
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
        fig.show()

    def getFacet(self):
        facet_graph = self.fx_data.set_index("Time")
        facet_graph.columns.name = 'Pairs'
        facet_fig = px.area(facet_graph, facet_col='Pairs', facet_col_wrap=2,
                            title="Ukraine vs Russia Fx 15mins Effect, normalized")
        facet_fig.show()

    def candle_stick_chart(self):
        candlestick = pd.DataFrame.from_dict(self.download_data.json["Data"])
