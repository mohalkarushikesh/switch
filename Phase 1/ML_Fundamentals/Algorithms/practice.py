# imports 
from sklearn.datasets import load_diabetes 
from sklearn.model_selection import train_test_split
from sklearn.linear_model import LinearRegression
import matplotlib.pyplot as plt 
# from sklearn.metrics import mean_squared_error, r2_score 
import pandas as pd 

# load the dataset 
x, y = load_diabetes(return_X_y=True)

# df = pd.DataFrame(data=diabetes.data, columns=diabetes.feature_names)
# print(df.head())
# print(df.iloc[:, :4])
# print(df[['age', 'bp']])
# print(df[df.columns[[0, 4]]])
# print(df.shape)

# train test split 
x_train, x_test, y_train, y_test = train_test_split(x, y, test_size=0.2, random_state=42)

# train 
model = LinearRegression()
model.fit(x_train, y_train) 

y_predict = model.predict(x_test)

# print("predicted: ", y_predict[:5])
# print("actual   : ", y_test[:5])
# evaluate 

# visualize 
plt.scatter(y_test, y_predict, color="purple", label="Data points")
plt.plot([y_test.min(), y_test.max()], [y_test.min(), y_test.max()], "r-")
plt.title("Diabetes")
plt.xlabel("Actual")
plt.ylabel("Predicted")
plt.legend()
plt.show()
