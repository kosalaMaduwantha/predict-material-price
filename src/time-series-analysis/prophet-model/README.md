# Prophet Model for Time Series Forecasting

Based on the additive model type(non-linear trends filts with seasonality and holiday effects)
This model reflects the seasonality and trend component.

### Required variables of the data to the forecasting

data with the date needs to be named as the “ds” key and the values should be named as “y”.

```python
data_frame = data_frame.rename(columns={"Date": "ds",
                                        "Value": "y"})
```

### Separating the dataset for the training and the testing or the validating of the model

```python
# splitting the dataset into train and test sets
train_data = data_frame[data_frame['ds'] < '2023-01-01']
test_data = data_frame[data_frame['ds'] >= '2023-01-01']****
```

### Fitting the model

with the parameters (additive by default)

```python
# model is trained using the default parameters. Model can be tuned using the arguments that can be passed to the constructor when definining the model instance. 
model = Prophet(seasonality_mode='additive')
model.fit(train_data)
```

### Predict the values for the testing data

model.predict() method requires another data frame as the input argument and for the validation of the testing data as follows.

```python
model_test_forecast = model.predict(test_data)
model_test_forecast.head()
```

After fitting the model, it provides range of values including decomposed trend component values, seasonal component values and the prediction values etc.

### Plotting the model predictions and the components

```python
# plot the forecast
fig, ax = plt.subplots(figsize=(14, 7))
fig = model.plot(model_test_forecast, ax=ax)
plt.show()
```

```python
# plotting the components of the model
fig = model.plot_components(model_test_forecast)
plt.show()
```

### Parameters that can be used to control the model predictions

1. **changepoint_prior_scale**

Controls the flexibility of the trend to change. Higher values allow more flexibility (can lead to overfitting), lower values restrict trend changes (can lead to underfitting). Default: 0.05

1. **seasonality_prior_scale**

Controls the flexibility of the seasonality component. Higher values allow more flexibility in fitting seasonal effects. Default: 10.0

1. **holiday_prior_scale**

Controls the flexibility of holiday effects. Higher values allow more flexibility in fitting holiday-related effects. Default: 10.0

1. **seasonality_mode**

Can be 'additive' or 'multiplicative'. Changes how seasonality interacts with the trend and can affect accuracy depending on your data.

1. **changepoint_range**

Proportion of history in which trend changepoints are allowed. Default is 0.8 (first 80% of the data).

1. **n_changepoints**

Number of potential changepoints in the trend. More changepoints allow for greater flexibility but can lead to overfitting. Default: 25

1. **yearly_seasonality, weekly_seasonality, daily_seasonality**

Boolean or integer (number of Fourier terms). Controls whether to fit these seasonalities and their complexity.

1. **fourier_order**

When adding custom seasonalities, the number of Fourier terms controls smoothness and flexibility.

1. **holidays**

Supplying a well-defined holidays dataframe can improve accuracy if holidays are important in your data.

1. **cap and floor (for logistic growth)**

Setting these properly for your data can significantly affect forecasts.

1. **growth**

'linear' or 'logistic'. The growth type should suit your data's trend.

1. **mcmc_samples**

Number of MCMC samples. Increases the accuracy of uncertainty intervals.

1. **interval_width**

Width of the uncertainty intervals (doesn’t control prediction accuracy but affects the forecast intervals).