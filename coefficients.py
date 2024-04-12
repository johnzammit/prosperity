import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.linear_model import LinearRegression
from sklearn.metrics import mean_squared_error
from sklearn.impute import SimpleImputer

price_data = pd.read_csv('round-1-island-data-bottle/prices_round_1_day_0.csv', delimiter=';', parse_dates=['timestamp'])
price_data1 = pd.read_csv('round-1-island-data-bottle/prices_round_1_day_-1.csv', delimiter=';', parse_dates=['timestamp'])
price_data2 = pd.read_csv('round-1-island-data-bottle/prices_round_1_day_-2.csv', delimiter=';', parse_dates=['timestamp'])

price_data1 = price_data1.drop(price_data1.index[0])
price_data2 = price_data2.drop(price_data2.index[0])
price_data = pd.concat([price_data1,price_data,price_data2])
price_data = price_data.drop(columns=['day'])
price_data = price_data[price_data['product'] == 'STARFRUIT']

price_data['m1'] = price_data['mid_price'].shift(1)
price_data['m2'] = price_data['mid_price'].shift(2)
price_data['m3'] = price_data['mid_price'].shift(3)


price_data.columns = [col.strip() for col in price_data.columns] 
#remove first three rows
price_data = price_data.drop(price_data.index[1:4])

price_data['future_price'] = price_data['mid_price'].shift(-1)
price_data['returns'] = price_data['future_price']
price_data.dropna(subset=['returns'], inplace=True)

imputer = SimpleImputer(strategy='mean')
price_data[['m1', 'm2', 'm3']] = imputer.fit_transform(price_data[['m1', 'm2', 'm3']])
features = ['m1', 'm2', 'm3']
X = price_data[features]
y = price_data['returns']

X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2)


model = LinearRegression()
model.fit(X_train, y_train)


y_pred = model.predict(X_test)
mse = mean_squared_error(y_test, y_pred)
print('Mean Squared Error:', mse)
print('R^2 Score:', model.score(X_test, y_test)) 


coefficients = model.coef_ 
intercept = model.intercept_ 

features = ['m1', 'm2', 'm3']
for feature, coef in zip(features, coefficients):
    print(f"{feature}: {coef}")
print("intercept:", intercept)
