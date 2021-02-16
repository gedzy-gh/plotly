import glob
import os
from time import sleep
import pandas as pd
import plotly.graph_objects as go
import plotly.io as pio
from binance.client import Client
from plotly.subplots import make_subplots
from pricelevels.cluster import ZigZagClusterLevels
from zigzag import peak_valley_pivots
from config import Key, Converter, Formatter, File

pd.set_option('display.max_columns', 100)
pd.set_option('display.max_rows', 100)


class Market:

    def __init__(self, k, s):
        self.k, self.s = k, s
        self.client = Client(self.k, self.k)
        self.request_count = 0

    def info(self, pair='BTCUSDT'):
        rp = self.client.get_symbol_info(symbol=pair)
        df = pd.DataFrame.from_dict(rp, orient='index', columns=['info'])
        self.request_count += 1
        del rp
        return df

    def ticker(self, pair='BTCUSDT'):
        rp = self.client.get_ticker(symbol=pair)
        df = pd.DataFrame.from_dict(rp, orient='index', columns=['ticker'])
        df.ticker.openTime = Converter.unix_to_timestamp(df.ticker.openTime)
        df.ticker.closeTime = Converter.unix_to_timestamp(df.ticker.closeTime)
        df = df.ticker.map(Formatter.tidy_string_decimal)
        df = pd.DataFrame(df, columns=['ticker'])
        self.request_count += 1
        del rp
        return df

    def kline(self, symbol, cycle='1h'):
        rp = self.client.get_klines(symbol=symbol, interval=cycle)
        kn = ['date',
              'open',
              'high',
              'low',
              'close',
              'volume',
              'closeTime',
              'quoteAssetVolume',
              'numberOfTrades',
              'takerBuyBasesAssetVolume',
              'takerBuyQuotAssetVolume',
              'Ignore']
        df = pd.DataFrame(data=rp, columns=kn)
        df['date'] = df['date'].map(Converter.unix_to_timestamp)
        df['closeTime'] = df['closeTime'].map(Converter.unix_to_timestamp)
        for i in df.columns:
            df[i] = df[i].map(Formatter.tidy_string_decimal)
        df = df.drop(['Ignore'], axis=1)
        df = df.reset_index(drop=True)
        self.request_count += 1
        del rp
        return df


class Kline:

    def __init__(self, df):
        self.kline = df

    def precision(self):
        return Formatter.tidy_df_decimal(self.kline.close[0])

    def add_moving_average(self, n):
        v = self.kline.close[0]
        p = Formatter.get_string_decimal(v)
        for i in n:
            ma = 'ma' + str(i)
            self.kline[ma] = self.kline.close
            self.kline[ma] = self.kline.close.rolling(i).mean().round(p)

    def find_support_and_resistance(self):

        percent = 0.1

        def zig_zag_cluster_levels(ppd, md, mp, mb, pk):
            return ZigZagClusterLevels(peak_percent_delta=ppd, merge_distance=md, merge_percent=mp,
                                       min_bars_between_peaks=mb, peaks=pk)

        zig = zig_zag_cluster_levels(percent, None, round(365.25 / 12 / 2) - 1, round(365.25 / 12) + 1, 'Low')
        if zig.levels is None:
            percent = 0.25
            zig = zig_zag_cluster_levels(percent, None, 0.25, 100, 'Low')

        self.kline[self.kline.columns[1:5]] = \
            self.kline[self.kline.columns[1:5]].astype('float')

        zig.fit(self.kline)
        val = self.kline.close.values
        piv = peak_valley_pivots(val, percent / 100, -percent / 100)
        return zig.levels, piv


class Investment:

    def __init__(self):
        pass

    @staticmethod
    def worth(candles=None, amount=100, price=None):
        if candles is not None:
            df = pd.DataFrame(index=candles.index, columns=['worth'])
            df = df.fillna(0)
            if not price:
                price = float(candles.close.iloc[0])
            df['worth'] = (candles.close.astype(float) * amount) / price
            df = df['worth'].map(Formatter.tidy_string_decimal)
            df = pd.DataFrame(df, columns=['worth'])
            return df


market = Market(Key.public, Key.secret)

symbols = ['BTCGBP', 'XRPGBP']
intervals = ['1m', '3m', '5m', '30m', '1h', '2h', '4h', '6h', '8h', '12h', '1d', '3d', '1M']

for i1, v1 in enumerate(symbols):
    for i2, v2 in enumerate(intervals):

        info = market.info(v1)
        tick = market.ticker(v1)
        line = market.kline(v1, v2)

        kline = Kline(line)
        precision = kline.precision()
        klines = kline.kline
        kline.add_moving_average([20, 50, 200])

        investment = Investment()
        total = investment.worth(candles=klines, amount=1500)
        levels, pivots = kline.find_support_and_resistance()

        def make_plotly_graph():
            # Make Figure
            theme = pio.templates['plotly_dark']

            # Create subplots and mention plot grid size
            fig = make_subplots(shared_xaxes=True, vertical_spacing=0.03, rows=2, cols=1, row_width=[0.2, 0.7])

            def plot_levels(where, lvl, only_good=False, n=2):
                if lvl:
                    for i in lvl:
                        if isinstance(i, float):
                            where.add_hline(y=i,
                                            line=dict(color='rgba(158,160,162, 1)', width=2),
                                            line_width=0.1,
                                            line_dash='solid',
                                            annotation_position='left',
                                            annotation_text=Formatter.float(value=i, place=n))
                        elif isinstance(i, dict):
                            if 'score' in i.keys():
                                if only_good and i['score'] < 0:
                                    continue
                                color = 'rgba(224,41,74, 1)' if i['score'] < 0 else 'rgba(46,189,133, 1)'
                                name_is = 'Resistance' if i['score'] < 0 else 'Support'
                                where.add_hline(y=i['price'],
                                                color=color,
                                                line_dash='solid',
                                                line_width=0.1 * abs(i['score']),
                                                name=name_is,
                                                annotation_position='left',
                                                annotation_text=Formatter.float(value=i['price'], place=n))
                            else:
                                where.add_hline(y=i['price'],
                                                name='Support',
                                                line=dict(color='rgba(158,160,162, 1)', width=2),
                                                line_dash='solid',
                                                annotation_position='left',
                                                annotation_text=Formatter.float(value=i['price'], place=n))
            show_candles = False
            if show_candles:
                # Add Candle-sticks to figure
                fig.add_trace(go.Candlestick(x=klines.date,
                                             open=klines.open,
                                             high=klines.high,
                                             low=klines.low,
                                             close=klines.close,
                                             increasing={'line': {'color': 'rgba(46,189,133, 1)'}},
                                             decreasing={'line': {'color': 'rgba(224,41,74, 1)'}},
                                             name='Candlesticks'), row=1, col=1)

            # Add close values with curved line to figure
            fig.add_trace(go.Scatter(x=klines.date[pivots != 0],
                                     y=klines.close[pivots != 0],
                                     mode='lines', name='Price',
                                     line=dict(shape='spline', width=2, color='rgba(240,185,11, 1)')),  # or 240,185,11
                          row=1, col=1)

            # Plot horizontal line of support and resistance
            plot_levels(fig, levels, only_good=True, n=precision)

            # Add the 20 moving average to figure
            fig.add_trace(go.Scatter(x=klines.date,
                                     y=klines.ma20,
                                     name='Short',
                                     text='20 MA',
                                     mode='lines',
                                     line=dict(color='rgba(9,9,177, 1)', width=2, shape='spline')),
                          row=1, col=1)

            # Add the 50 moving average to figure
            fig.add_trace(go.Scatter(x=klines.date,
                                     y=klines.ma50,
                                     name='Medium',
                                     text='50 MA',
                                     mode='lines',
                                     line=dict(color='rgba(54,12,158, 1)', width=2, shape='spline')),
                          row=1, col=1)

            # Add the 200 moving average to figure
            fig.add_trace(go.Scatter(x=klines.date,
                                     y=klines.ma200,
                                     name='Trend',
                                     text='200 MA',
                                     mode='lines',
                                     line=dict(color='rgba(85,14,136, 1)', width=2, shape='spline')),
                          row=1, col=1)

            # Add profit made from set price
            fig.add_trace(go.Scatter(x=klines.date,
                                     y=total.worth,
                                     name='Investment',
                                     text='P&L',
                                     line=dict(color='rgba(46,189,133, 1)', width=2, shape='spline'),  # 46,189,133
                                     showlegend=True), row=2, col=1)

            fig.layout.font.family = 'Share Tech'
            fig.update_xaxes(showgrid=True, gridwidth=1, gridcolor='rgba(25,27,32, 1)')  # 43,47,54,255
            fig.update_yaxes(showgrid=True, gridwidth=1, gridcolor='rgba(25,27,32, 1)')  # 43,47,54,255
            fig.update_layout(template=theme, xaxis_rangeslider_visible=False,
                              plot_bgcolor='rgba(25,27,32, 1)',
                              paper_bgcolor='rgba(25,27,32, 1)',
                              xaxis_tickformat='%d %B (%a)<br>%Y',
                              yaxis_tickformat=f'{precision}.f',
                              title=f'Plotly Graph for Market: {v1} (Binance)'),  # annotations=annotations)

            fn = f'({i2 + 1}) {v2}.png'
            File.to_desktop('Binance', v1, '*png', lvl=(i1, i2))
            fig.to_image(format='png', engine='kaleido')
            fig.write_image(fn)
            pd.DataFrame.to_csv(klines)

        make_plotly_graph()
        sleep(2)
