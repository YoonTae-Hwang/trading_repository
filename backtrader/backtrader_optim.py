import datetime 
import os.path  
import sys 
import backtrader as bt
import matplotlib.pyplot as plt
%matplotlib inline

class TestStrategy(bt.Strategy):
    params = (("maperiod", 15),
              ("printlog", False),)
    
    def log(self, txt, dt=None, doprint = False):
        ''' Logging function fot this strategy'''
        
        if self.params.printlog or doprint:
        
            dt = dt or self.datas[0].datetime.date(0)
            print('%s, %s' % (dt.isoformat(), txt))
        
    def __init__(self):
        self.dataclose = self.datas[0].close

        self.order = None
        self.buyprice = None
        self.buycomm = None    
        
        # Add a MovingAverageSimple indicator
        self.sma = bt.indicators.SimpleMovingAverage(self.datas[0], period=self.params.maperiod)
        
        # Indicators for the plotting show
        bt.indicators.ExponentialMovingAverage(self.datas[0], period=25)
        bt.indicators.WeightedMovingAverage(self.datas[0], period=25, subplot=True)
        bt.indicators.StochasticSlow(self.datas[0])
        bt.indicators.MACDHisto(self.datas[0])
        rsi = bt.indicators.RSI(self.datas[0])
        bt.indicators.SmoothedMovingAverage(rsi, period=10)
        bt.indicators.ATR(self.datas[0], plot=False)
    
    def notify_order(self, order):
        if order.status in [order.Submitted, order.Accepted]:
            return

        if order.status in [order.Completed]:
            if order.isbuy():
                self.log(
                    'BUY EXECUTED, Price: %.2f, Cost: %.2f, Comm %.2f' %
                    (order.executed.price,
                     order.executed.value,
                     order.executed.comm))

                self.buyprice = order.executed.price
                self.buycomm = order.executed.comm
            else:  # Sell
                self.log('SELL EXECUTED, Price: %.2f, Cost: %.2f, Comm %.2f' %
                         (order.executed.price,
                          order.executed.value,
                          order.executed.comm))

            self.bar_executed = len(self)

        elif order.status in [order.Canceled, order.Margin, order.Rejected]:
            self.log('Order Canceled/Margin/Rejected')

        self.order = None    
        
    def notify_trade(self, trade):
        if not trade.isclosed:
            return

        self.log('OPERATION PROFIT, GROSS %.2f, NET %.2f' %
                 (trade.pnl, trade.pnlcomm))        

        
    def next(self):
        self.log('Close, %.2f' % self.dataclose[0])

        if self.order:
            return

        if not self.position:
            if self.dataclose[0] > self.sma[0]:
                self.log('BUY CREATE, %.2f' % self.dataclose[0])
                self.order = self.buy()
        else:

            if self.dataclose[0] < self.sma[0]:
                self.log('SELL CREATE, %.2f' % self.dataclose[0])
                self.order = self.sell()
                
    def stop(self):
        self.log('(MA Period %2d) Ending Value %.2f' %
                 (self.params.maperiod, self.broker.getvalue()), doprint=True)
if __name__ == "__main__":
    cerebro = bt.Cerebro()
    
    strats = cerebro.optstrategy(
        TestStrategy,
        maperiod=range(10, 31))
    
    data = bt.feeds.YahooFinanceCSVData(dataname="BTC-USD.csv",
                                        fromdate=datetime.datetime(2005, 4, 10),
                                        todate=datetime.datetime(2020, 4, 10),
                                        reverse=False)
    
    cerebro.adddata(data) #add the data feed to cerebro
    cerebro.broker.setcash(100000.0) #set up our start cash
    cerebro.addsizer(bt.sizers.FixedSize, stake=10)     # Add a FixedSize sizer according to the stake [Check]
    cerebro.broker.setcommission(commission=0.01)     # Set the commission - 0.1% ... divide by 100 to remove the %

    print('Starting Portfolio Value : %.2f' %cerebro.broker.getvalue())
    cerebro.run(maxcpus=1)
    print("final Portfolio Value: %.2f" %cerebro.broker.getvalue())
    
