#!/usr/bin/env python
from nepse import NEPSE
import pandas as pd
import matplotlib.pyplot as plt
from time import sleep
from datetime import datetime
market = NEPSE()
watchlist = ["nil", "nifra", "igi", "nica", "hidcl", "ILBS", "kbl", "Men", "lec", "rhpl"]


def minutechart():
    idx = pd.DataFrame(market.indices(), columns=['stamp', 'price'])
    time = datetime.now()
    # stamp is whatever is downloaded as the index/timestamp/x-axis
    # resample so that point is added every 30 sec. with the last point always being the latest
    idx = idx.iloc[::-1,:].iloc[::60,:].iloc[::-1,:]
    # shift origin of time to 0
    idx['time'] = (idx['stamp'] - idx.stamp.min() + 200)
    plot = idx.plot('time', "price", figsize=(16,5), marker="*")
    plot.grid()
    plot.title(str(time))
    plot.set_xlim(0, 15600)
    plot.set_ylim(idx.price.min()-2, idx.price.max()+6)
    plt.text(idx.time.values[-1] - 300, idx.price.values[-1] + 1.5, idx.price.values[-1])
    plt.savefig("/home/bibek/git/nepse/intraday.png")
    plt.close()

text = chr(27) + "[2J\n"
while 1:
    time = datetime.now()
    try:
        idx = pd.DataFrame(market.indices(), columns=['stamp', 'price'])
        # stamp is whatever is downloaded as the index/timestamp/x-axis
        # resample so that point is added every 30 sec. with the last point always being the latest
        idx = idx.iloc[::-1,:].iloc[::60,:].iloc[::-1,:]
        # shift origin of time to 0
        idx['time'] = (idx['stamp'] - idx.stamp.min() + 200)
        plot = idx.plot('time', "price", figsize=(16,5), marker="*")
        plot.grid()
        plot.set_xlim(0, 15600)
        plot.set_ylim(idx.price.min()-2, idx.price.max()+6)
        plt.title(str(time))
        plt.text(idx.time.values[-1] - 300, idx.price.values[-1] + 1.5, idx.price.values[-1])
        plt.savefig("/home/bibek/git/nepse/intraday.png")
        plt.close()
    except Exception as e:
        print(e)
    try:
        print(text + str(time)+ "\n" + market.watch(watchlist))
    except:
        pass
    sleep(10)
