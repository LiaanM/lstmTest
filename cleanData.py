import pandas as pd
from sklearn.linear_model import LinearRegression
from matplotlib import pyplot as plt
import numpy

series = pd.read_csv('cleanedData2.csv')
series = series.set_index(pd.DatetimeIndex(series['Date']))

X = [i for i in range(0, len(series))]
X = numpy.reshape(X, (len(X), 1))
y = series['Value'].values
model = LinearRegression()
model.fit(X, y)
trend = model.predict(X)
# plt.plot(y)
# plt.plot(trend)
# plt.show()

detrended = [y[i]-trend[i] for i in range(0, len(series))]

prevVal = 0;
for i in range(0,len(detrended)):
    ts = pd.datetime.strptime(series.iloc[i]['Date'], '%Y-%m-%d %H:%M:%S')

    if(ts.hour is 1 and detrended[i] < 1000):
        print('Detrend Val : ',detrended[i], ' Date : ', series.iloc[i]['Date'], ' Orig Val : ', series.iloc[i]['Value'], ' Replace with : ', prevVal)
        series.at[series.iloc[i]['Date'],'Value'] = prevVal
    if(ts.hour is 1):
        prevVal = series.iloc[i]['Value']
    # if(detrended[i] > 20 and ts.hour is not 1):
    #     print('Detrend Val : ',detrended[i], ' Date : ', series.iloc[i]['Date'], ' Orig Val : ', series.iloc[i]['Value'])
    #     if(series.iloc[i-1]['Value'] < 200):
    #         print('Replace With : ', series.iloc[i-1]['Value'])
    #         series.at[series.iloc[i]['Date'],'Value'] = series.iloc[i-1]['Value']
    #     else:
    #         print('Replace With : ', series.iloc[i-2]['Value'])
    #         series.at[series.iloc[i]['Date'],'Value'] = series.iloc[i-2]['Value']

series.plot()
plt.show()

plt.plot(detrended)
plt.show()

# series.to_csv('cleanedData2.csv', columns=['Value'])
