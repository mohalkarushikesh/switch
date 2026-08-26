from sklearn.model_selection import train_test_split
from sklearn.linear_model import LinearRegression
import numpy as np 
import pandas as pd 
import matplotlib.pyplot as plt 
import seaborn as sns
from sklearn.metrics import r2_score, mean_absolute_error, root_mean_squared_error

df = pd.read_csv('USA_housing.csv')

# sns.pairplot(df)
# plt.show()

mean_price = df['Price'].mean()
median_price = df['Price'].median()

# sns.histplot(df['Price'], kde=True, bins=40, color='purple')
# plt.axvline(mean_price, color='green', linestyle='--', label=f'Mean: ${mean_price:,.0f}')
# plt.axvline(mean_price, color='blue', linestyle='--', label=f'Median: ${median_price:,.0f}')
# plt.xlabel('Price [USD]')
# plt.ylabel('Density')
# plt.title('House price distribution with Mean & Median')
# plt.legend()
# plt.grid(True)
# plt.show()

# heatmap = sns.heatmap(df.select_dtypes('number').corr(), annot=True, cmap='viridis', fmt='.2f')
# heatmap.set_xticklabels(heatmap.get_xticklabels(), rotation=45, ha='right')
# heatmap.set_xticklabels(heatmap.get_xticklabels(), rotation=0)

# plt.title('heatmap correction')
# plt.show()

x = df[['Avg. Area Income', 'Avg. Area House Age', 'Avg. Area Number of Rooms',
        'Avg. Area Number of Bedrooms', 'Area Population']]

y = df['Price']

x_train, x_test, y_train, y_test = train_test_split(x, y, test_size=0.20, random_state=42)

model = LinearRegression()

model.fit(x_train, y_train)

preds = model.predict(x_test)

print(f"R²   : {r2_score(y_test, preds):.3f}")
print(f"MAE  : {mean_absolute_error(y_test, preds):,.0f}")
print(f"RMSE : {root_mean_squared_error(y_test, preds):,.0f}")

# colors = np.abs(y_test - preds)
# plt.figure(figsize=(8, 6))
# plt.scatter(y_test, preds, c=colors, cmap='coolwarm', edgecolors='black', alpha=0.5)
# plt.title('Prediction Error')
# plt.xlabel('Actual Prices')
# plt.ylabel('Predicted Prices')
# plt.show()


