#!/usr/bin/env python
import pandas as pd
import matplotlib.pyplot as plt
from nepse import NEPSE
market = NEPSE()
idx = pd.DataFrame(market.indices(), columns=['stamp', 'price'])
# stamp is whatever is downloaded as the index/timestamp/x-axis
# resample so that point is added every 30 sec. with the last point always being the latest
idx = idx.iloc[::-1,:].iloc[::30,:].iloc[::-1,:]
# shift origin of time to 0
idx['time'] = (idx['stamp'] - idx.stamp.min() + 200)
plot = idx.plot('time', "price", figsize=(16,5), marker="*")
plot.grid()
plot.set_xlim(0, 15600)
plot.set_ylim(idx.price.min()-2, idx.price.max()+6)
plt.text(idx.time.values[-1] - 300, idx.price.values[-1] + 1.5, idx.price.values[-1])
plt.savefig("intraday.png")

