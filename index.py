from pandas import DataFrame
from pandas import Series
from pandas import concat
from pandas import read_csv
from pandas import datetime
from sklearn.metrics import mean_squared_error
from sklearn.preprocessing import MinMaxScaler
from sklearn.model_selection import train_test_split
from sklearn.linear_model import LinearRegression
from keras.models import Sequential
from keras.layers import Dense
from keras.layers import LSTM
from math import sqrt
from matplotlib import pyplot
import numpy

# date-time parsing function for loading the dataset
def parser(x):
	return datetime.strptime('190'+x, '%Y-%m')

# frame a sequence as a supervised learning problem
def timeseries_to_supervised(data, lag=1):
	df = DataFrame(data)
	columns = [df.shift(i) for i in range(1, lag+1)]
	columns.append(df)
	df = concat(columns, axis=1)
	df.fillna(0, inplace=True)
	return df

# create a differenced series
def difference(dataset, interval=1):
	diff = list()
	for i in range(interval, len(dataset)):
		value = dataset[i] - dataset[i - interval]
		diff.append(value)
	return Series(diff)

def getTrend(dataset):
	X = [i for i in range(0, len(dataset))]
	X = numpy.reshape(X, (len(X), 1))
	model = LinearRegression()
	model.fit(X, dataset)
	trend = model.predict(X)
	return trend

def detrend(dataset,trend):
	detrended = list()
	for i in range(0, len(dataset)):
		value = dataset[i]-trend[i]
		detrended.append(value)
	return Series(detrended)

def retrend(value,at,trend):
	return value + trend[at]

# invert differenced value
def inverse_difference(history, yhat, interval=1):
	return yhat + history[-interval]

# scale train and test data to [-1, 1]
def scale(train, test):
	# fit scaler
	scaler = MinMaxScaler(feature_range=(-1, 1))
	scaler = scaler.fit(train)
	# transform train
	train = train.reshape(train.shape[0], train.shape[1])
	train_scaled = scaler.transform(train)
	# transform test
	test = test.reshape(test.shape[0], test.shape[1])
	test_scaled = scaler.transform(test)
	return scaler, train_scaled, test_scaled

# inverse scaling for a forecasted value
def invert_scale(scaler, X, value):
	new_row = [x for x in X] + [value]
	array = numpy.array(new_row)
	array = array.reshape(1, len(array))
	inverted = scaler.inverse_transform(array)
	return inverted[0, -1]

# fit an LSTM network to training data
def fit_lstm(train, batch_size, nb_epoch, neurons):
	X, y = train[:, 0:-1], train[:, -1]
	X = X.reshape(X.shape[0], 1, X.shape[1])
	model = Sequential()
	model.add(LSTM(neurons, batch_input_shape=(batch_size, X.shape[1], X.shape[2]), stateful=True))
	model.add(Dense(1))
	model.compile(loss='mean_squared_error', optimizer='adam')
	for i in range(nb_epoch):
		model.fit(X, y, epochs=1, batch_size=batch_size, verbose=1, shuffle=False)
		model.reset_states()
		print('End iteration : ', i)
	return model

# make a one-step forecast
def forecast_lstm(model, batch_size, X):
	X = X.reshape(1, 1, len(X))
	print(X)
	yhat = model.predict(X, batch_size=batch_size)
	return yhat[0,0]

# load dataset
# series = read_csv('shampoo.csv', header=0, parse_dates=[0], index_col=0, squeeze=True, date_parser=parser)
series = read_csv('cleanedData2.csv')

print(series)
# transform data to be stationary
raw_values = series['Value'].values
trend = getTrend(raw_values)
diff_values = detrend(raw_values,trend)

# diff_values = difference(raw_values, 1)
# diff_values = Series(raw_values)
print(raw_values)
print(diff_values)

# transform data to be supervised learning
supervised = timeseries_to_supervised(diff_values, 1)
supervised_values = supervised.values

print(supervised_values)
# split data into train and test-sets
train, test = train_test_split(supervised_values, shuffle=False)

# transform the scale of the data
scaler, train_scaled, test_scaled = scale(train, test)

print(train_scaled)
print(test_scaled)
# pyplot.plot(train)
# pyplot.plot(train_scaled)
# pyplot.show()
# fit the model
batchSize = 1
lstm_model = fit_lstm(train_scaled, batchSize, 12, 5)
# forecast the entire training dataset to build up state for forecasting
train_reshaped = train_scaled[:, 0].reshape(len(train_scaled), 1, 1)
lstm_model.predict(train_reshaped, batch_size=batchSize)

predictionsTrain = list()
for i in range(len(train_scaled)):
	# make one-step forecast
	X, y = train_scaled[i, 0:-1], train_scaled[i, -1]
	yhat = forecast_lstm(lstm_model, batchSize, X)
	# yhat = y
	# invert scaling
	yhat = invert_scale(scaler, X, yhat)
	# invert differencing
	# yhat = inverse_difference(raw_values, yhat, len(test_scaled)+1-i)
	yhat = retrend(yhat, i, trend)

	# store forecast
	predictionsTrain.append(yhat)
	# expected = raw_values[len(train) + i + 1]
	expected = raw_values[len(test) + i]
	print('Month=%d, Predicted=%f, Expected=%f' % (i+1, yhat, expected))

rmse = sqrt(mean_squared_error(raw_values[:len(predictionsTrain)], predictionsTrain))
print('Test RMSE train: %.3f' % rmse)
# line plot of observed vs predicted
pyplot.plot(raw_values[:len(predictionsTrain)])
pyplot.plot(predictionsTrain)
pyplot.show()
# walk-forward validation on the test data
predictions = list()
for i in range(len(test_scaled)):
	# make one-step forecast
	X, y = test_scaled[i, 0:-1], test_scaled[i, -1]
	yhat = forecast_lstm(lstm_model, batchSize, X)
	# yhat = y
	# invert scaling
	yhat = invert_scale(scaler, X, yhat)
	# invert differencing
	# yhat = inverse_difference(raw_values, yhat, len(test_scaled)+1-i)
	yhat = retrend(yhat, i + len(train_scaled), trend)

	# store forecast
	predictions.append(yhat)
	# expected = raw_values[len(train) + i + 1]
	expected = raw_values[len(train) + i]
	print('Month=%d, Predicted=%f, Expected=%f' % (i+1, yhat, expected))

# report performance
rmse = sqrt(mean_squared_error(raw_values[-len(predictions):], predictions))
print('Test RMSE: %.3f' % rmse)
# line plot of observed vs predicted
pyplot.plot(raw_values[-len(predictions):])
pyplot.plot(predictions)
pyplot.show()
