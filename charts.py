import pandas as pd
import plotly.offline as pyo
from download_data import *


def candlestick(df: pd.DataFrame, title: str):
    """
        Definition
        ----------
        Python method to build a candlestick graph with moving averges and bollinger bands.


        Parameters
        ----------
        df: pd.Dataframe
        title: the title to the graph.


        Return
        ------
        candlestick plot with indicators.

    """

    INCREASING_COLOR = '#04bd0d'
    DECREASING_COLOR = '#d10202'

    data = [dict(
        type='candlestick',
        close=df.Close,
        open=df.Open,
        low=df.Low,
        high=df.High,
        x=df.Time,
        yaxis='y2',
        name='Pair',
        increasing=dict(line=dict(color=INCREASING_COLOR)),
        decreasing=dict(line=dict(color=DECREASING_COLOR)),
    )]

    # empty layout
    layout = dict()
    fig = dict(data=data, layout=layout)

    # create the layout object
    fig['layout'] = dict()
    fig['layout']['plot_bgcolor'] = 'rgb(250, 250, 250)'
    fig['layout']['xaxis'] = dict(rangeselector=dict(visible=True))
    fig['layout']['yaxis'] = dict(domain=[0, 0.2], showticklabels=False)
    fig['layout']['yaxis2'] = dict(domain=[0.2, 0.8])
    fig['layout']['legend'] = dict(orientation='h', y=0.9, x=0.3, yanchor='bottom')
    fig['layout']['margin'] = dict(t=40, b=40, r=40, l=40)
    fig['layout']['title'] = title

    # Add range button
    rangeselector = dict(
        visible=True,
        x=0,
        y=0.9,
        bgcolor='rgba(150, 200, 250, 0.4)',
        font=dict(size=13),
        buttons=list([
            dict(count=1,
                 label='reset',
                 step='all'),
            dict(count=1,
                 label='1h',
                 step='hour',
                 stepmode='backward'),
            dict(count=1,
                 label='1d',
                 step='day',
                 stepmode='backward'),
            dict(count=1,
                 label='1w',
                 step='week',
                 stepmode='backward'),
            dict(step='all')
        ])
    )

    # add the rangeselector to the layout
    fig['layout']['xaxis']['rangeselector'] = rangeselector

    # Add moving average
    def moving_average(interval: pd.Series, window_size=10):
        """
            Definition
            ----------
            Python method to build a moving average.


            Parameters
            ----------
            interval: pd.Series or column of a dataframe where to calculate the moving average.

            window_size: int default 10, the window for the moving average.


            Return
            ------
            moving average.

        """
        window = np.ones(int(window_size)) / float(window_size)
        return np.convolve(interval, window, 'same')

    mv_y = moving_average(df.Close)
    mv_x = list(df.Time)

    # clip the ends
    mv_x = mv_x[5:-5]
    mv_y = mv_y[5:-5]
    fig['data'].append(dict(
        x=mv_x,
        y=mv_y,
        type='scatter',
        mode='lines',
        line=dict(width=1),
        marker=dict(color='#E377C2'),
        yaxis='y2',
        name='Moving Average'
    ))

    # Set volume bar chart colors
    colors = []

    for i in range(len(df.Close)):
        if i != 0:
            if df.Close[i] > df.Close[i - 1]:
                colors.append(INCREASING_COLOR)
            else:
                colors.append(DECREASING_COLOR)
        else:
            colors.append(DECREASING_COLOR)

    # Add bollinger bands
    def bbands(price, window_size=10, num_of_std=5):
        """
            Definition
            ----------
            Python method to build the Bollinger bands.


            Parameters
            ----------
            price: pd.Serie or df.column, where to calculate the BB.

            window_size: int default 10, the window for the moving average.

            num_of_std: int default 5, the number of std to apply to build the BB.


            Return
            ------
            rolling_mean, upper_band, lower_band.

        """
        rolling_mean = price.rolling(window=window_size).mean()
        rolling_std = price.rolling(window=window_size).std()
        upper_band = rolling_mean + (rolling_std * num_of_std)
        lower_band = rolling_mean - (rolling_std * num_of_std)
        return rolling_mean, upper_band, lower_band

    bb_avg, bb_upper, bb_lower = bbands(df.Close)

    fig['data'].append(dict(
        x=df.Time,
        y=bb_upper,
        type='scatter',
        yaxis='y2',
        line=dict(width=1),
        marker=dict(color='#ccc'),
        hoverinfo='none',
        legendgroup='Bollinger Bands',
        name='Bollinger Bands'
    ))

    fig['data'].append(dict(
        x=df.Time,
        y=bb_lower,
        type='scatter',
        yaxis='y2',
        line=dict(width=1),
        marker=dict(color='#ccc'),
        hoverinfo='none',
        legendgroup='Bollinger Bands',
        showlegend=False
    ))

    # plot
    pyo.plot(fig, filename='candlestick_test.html', validate=False)
