import requests
import matplotlib.pyplot as plt
import pandas as pd
from datetime import datetime, timedelta
import time
import os
import queue
import threading
from . import var


def floorsheets():
    """
    Threaded Scraper For FloorSheets as we need to scrape more than 75k Data
    Returns in less than 2 seconds.
    """
    q = queue.Queue()
    contents = []
    response = requests.get(
        'https://newweb.nepalstock.com.np/api/' +
        'nots/nepse-data/floorsheet?size=2000&sort=contractId,desc',
        headers=var.header)
    pages = response.json()['floorsheets']['totalPages']

    def scrapePage(pageNUM):
        response = requests.get(
            'https://newweb.nepalstock.com.np/api/' +
            f'nots/nepse-data/floorsheet?page={pageNUM}&size=2000&sort=contractId,desc',
            headers=var.header)
        return response.json()['floorsheets']['content']

    def queGET(q):
        while True:
            task = q.get()
            contents.extend(scrapePage(task))
            q.task_done()

    for i in range(30):
        worker = threading.Thread(target=queGET, args=(q, ), daemon=True)
        worker.start()

    for j in range(pages):
        q.put(j)

    q.join()

    return pd.DataFrame(contents)


class Floorsheet:
    def __init__(self):
        self.fs = floorsheets()

    def update(self):
        self.fs = floorsheets()

    def volume(self, scrip):
        return self.fs[self.fs.stockSymbol == scrip].contractQuantity.sum()

    def matching_amt(self):
        return len(self.fs[self.fs.buyerMemberId == self.fs.sellerMemberId].
                   index) / len(self.fs.index) * 100

    def buy_to_sell(self, bid, scrip=None):
        if not scrip:
            return self.fs[self.fs.buyerMemberId == bid].contractQuantity.sum(
            ) / self.fs[self.fs.sellerMemberId == bid].contractQuantity.sum()
        else:
            return self.fs[self.fs.buyerMemberId == bid][
                self.fs.stockSymbol == scrip].contractQuantity.sum() / self.fs[
                    self.fs.sellerMemberId == bid][
                        self.fs.stockSymbol == scrip].contractQuantity.sum()


class NEPSE:
    def __init__(self):
        self.headers = var.header
        self.sectors = var.sectors
        self.host = 'https://newweb.nepalstock.com.np/api/'
        #  self.securities = requests.get(self.host +
        #                                 'nots/securityDailyTradeStat/58',
        #                                 headers=self.headers).json()
        pass

    def dateFilter(self, working_date, data):
        """
        Function to return next working day , if the date provided is non-working day.

        Returns either first or last date if the date provided is too ahead or too back.

        """

        all_dates = [date['businessDate'] for date in data]
        if working_date in all_dates:
            return working_date
        else:
            i = 0
            while 1:

                date = datetime.strptime(working_date, '%Y-%m-%d')
                new_date = str(date + timedelta(days=i)).split(' ')[0]
                if new_date in all_dates:
                    return new_date
                i += 1
                if i >= 7:
                    month = working_date.split('-')[1]
                    year = working_date.split('-')[0]
                    day = working_date.split('-')[-1]
                    if year > all_dates[-1].split(
                            '-')[0] and month > all_dates[-1].split('-')[1]:
                        return all_dates[-1]
                    return all_dates[0]

    def isOpen(self):
        """
        Returns True if the market is Open .

        """
        response = requests.get(self.host + '/nots/nepse-data/market-open',
                                headers=self.headers).json()
        if response['isOpen'] != 'CLOSE':
            return True
        return False

    def nonthreadedfloorsheets(self):
        content = []
        page = 0
        while 1:
            response = requests.get(
                'https://newweb.nepalstock.com.np/api/nots/nepse-data/floorsheet?page={page}&size=2000&sort=contractId,desc',
                headers=self.headers)
            data = (response.json())['floorsheets']['content']
            isLast = response.json()['floorsheets']['last']
            content.extend(data)
            page += 1
            if isLast:
                return content

    def indices(self, sector='NEPSE Index', start_date=None, end_date=None):
        index = sector
        index_id = [
            id['id'] for id in self.sectors if id['indexName'] == index
        ][0]
        resp = requests.get(self.host + 'nots/graph/index/58',
                            headers=self.headers).json()
        #  if start_date:
        #      start_date = self.dateFilter(start_date, resp)
        #      start_index = next((index for (index, d) in enumerate(resp)
        #                          if d["businessDate"] == start_date), None)
        #      resp = resp[start_index:]
        #  if end_date:

        #      end_date = self.dateFilter(end_date, resp)
        #      end_index = next((index for (index, d) in enumerate(resp)
        #                        if d["businessDate"] == end_date), None) + 1
        #      if start_date and end_date:
        #          if end_index == start_index:
        #              end_index = -1
        #      resp = resp[:end_index]
        return resp

    def brokers(self):
        """ 
        Returns all the registered brokers along with tms url and other information

        """
        resp = requests.get(self.host + 'nots/member?&size=500',
                            headers=self.headers).json()
        return resp

    def alerts(self):
        """

        returns alerts and news published by 

        """
        resp = requests.get(self.host + 'nots/news/media/news-and-alerts',
                            headers=self.headers).json()
        return resp

    def todayPrice(self, scrip=None):
        """

        Get Live Price of All The Securities in one call or specify

        """
        resp = requests.get(self.host +
                            'nots/nepse-data/today-price?&size=500',
                            headers=self.headers).json()['content']
        if scrip == None:
            return resp
        return [
            script for script in resp if script['symbol'] == scrip.upper()
        ][0]

    def markCap(self):
        """

        Get Market Caps

        """
        resp = requests.get(self.host + 'nots/nepse-data/marcapbydate/?',
                            headers=self.headers).json()
        return resp

    def getChartHistory(self, scrip, start_date=None, end_date=None):
        """

        returns charts data 
        raises Exception if start_date or end_date != working_days (will fix it)

        """

        scripID = [
            security for security in self.securities
            if security['symbol'] == scrip.upper()
        ][0]['securityId']
        resp = requests.get(self.host + f'nots/market/graphdata/{scripID}',
                            headers=self.headers).json()
        if start_date:
            start_date = self.dateFilter(start_date, resp)
            start_index = next((index for (index, d) in enumerate(resp)
                                if d["businessDate"] == start_date), None)
            resp = resp[start_index:]
        if end_date:

            end_date = self.dateFilter(end_date, resp)
            end_index = next((index for (index, d) in enumerate(resp)
                              if d["businessDate"] == end_date), None) + 1
            if start_date and end_date:
                if end_index == start_index:
                    end_index = -1
            resp = resp[:end_index]
        return resp

    def createChart(self,
                    scrip,
                    theme='dark',
                    start_date=None,
                    end_date=None,
                    close=True,
                    high=True,
                    low=True):

        symbol = scrip.upper()
        if theme.upper() == 'DARK':
            plt.style.use(['dark_background'])

        data = self.getChartHistory(symbol, start_date, end_date)
        open_price = [d['openPrice'] for d in data]
        x = [d['businessDate'] for d in data]
        high_data = [d['highPrice'] for d in data]
        low_data = [d['lowPrice'] for d in data]
        close_price = [d['closePrice'] for d in data]

        plt.plot(open_price, label='Open Price')
        if close:
            plt.plot(close_price, label="Close Price")
        if high:
            plt.plot(high_data, label="High")
        if low:
            plt.plot(low_data, label="Low")

        plt.legend(loc="upper left")

        plt.title(f'{symbol} Prices As of {x[-1]}')

        plt.xlabel(
            f"Start Date : {x[0]} | END DATE : {x[-1]}\n\nOPEN PRICE : {open_price[-1]}  | ClOSE PRICE : {close_price[-1]} | High : {high_data[-1]} | Low : {low_data[-1]}"
        )
        ax = plt.gcf().autofmt_xdate()
        ax = plt.gca()
        ax.axes.xaxis.set_ticks([])
        filename = f'{symbol}_{str(time.time())}.png'
        data = plt.savefig(filename)
        abspath = os.path.abspath(filename)
        plt.clf()
        return {'file': abspath}

    def saveCSV(self, scrip, start_date=None, end_date=None, filename=None):
        scripID = [
            security for security in self.securities
            if security['symbol'] == scrip.upper()
        ][0]['securityId']
        resp = self.getChartHistory(scrip, start_date, end_date)
        if not filename:
            filename = f'{scrip.upper()}_{str(time.time())}.csv'
        pd.DataFrame(resp).to_csv(filename)
        return os.path.abspath(filename)

    def watch(self, watchlist):
        watchlist = [scrip.upper() for scrip in watchlist]
        priceList = self.todayPrice()
        data = [scrip for scrip in priceList if scrip["symbol"] in watchlist]

        text = "  SCRIP   PCT-CH   PrevCLOSE   LTP" + "\n" + "=" * 40 + "\n"
        for datum in data:
            scrip = datum["symbol"]
            closing = int(datum["previousDayClosePrice"])
            ltp = int(datum["lastUpdatedPrice"])
            pctchange = (ltp - closing) * 100 / closing
            text = text + (scrip.upper().center(8) +
                           "%.2f".center(9) % pctchange +
                           str(closing).center(12) + str(ltp).center(8)) + "\n"
        return (text)


def checkIPO(scripID, boid):
    """
    CHECK IPO RESULT

    """

    #  published = requests.get('https://iporesult.cdsc.com.np/result/companyShares/fileUploaded').json()['body']
    #  print()

    #  scripID = [
    #      resp['id'] for resp in if resp['scrip'] == scrip.upper()
    #  ][0]

    return requests.post('https://iporesult.cdsc.com.np/result/result/check',
                         json={
                             "companyShareId": scripID,
                             "boid": boid
                         }).json()["success"]


if __name__ == '__main__':
    data = NEPSE()
    print(data.indices())
