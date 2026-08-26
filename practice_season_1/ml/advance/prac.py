# from sklearn.model_selection import train_test_split
# from sklearn.linear_model import LinearRegression
# import numpy as np 
import pandas as pd 
import matplotlib.pyplot as plt 
import seaborn as sns

df = pd.read_csv('USA_housing.csv')

# sns.pairplot(df)
# plt.show()

mean_price = df['Price'].mean()
median_price = df['Price'].mean()

# sns.histplot(df['Price'], kde=True, bins=40, color='purple')
# plt.axvline(mean_price, color='green', linestyle='--', label=f'Mean: ${mean_price:,.0f}')
# plt.axvline(mean_price, color='blue', linestyle='--', label=f'Median: ${median_price:,.0f}')
# plt.xlabel('Price [USD]')
# plt.ylabel('Density')
# plt.title('House price distribution with Mean & Median')
# plt.legend()
# plt.grid(True)
# plt.show()
