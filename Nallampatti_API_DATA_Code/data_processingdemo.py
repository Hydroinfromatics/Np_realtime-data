# import  dependencies 

import pandas as pd
from dateutil import parser
from get_data import fetch_data_from_api
import time


# start Processing

API_URL= "https://mongodb-api-hmeu.onrender.com"


def preprocess_data(date_format="%d-%b-%Y %H:%M:%S"):
    data = fetch_data_from_api(API_URL)
    df = pd.DataFrame(data)
    df['timestamp'] = pd.to_datetime(df['timestamp'], format=date_format, errors='coerce')
    df.dropna(subset=['timestamp'], inplace=True)
    df.fillna(0, inplace=True)
    #df['FlowInd'] = df['FlowInd'].round().astype(int)
    df['TDS'] = df['TDS'].round().astype(int)
    #df['pH'] = df['pH'].round().astype(int)
    df['Depth'] = df['Depth'].round().astype(int)
    return df


def filter_data(from_date, to_date):
    df = preprocess_data()
    from_date = parser.parse(from_date)
    to_date = parser.parse(to_date)
    return df[(df['timestamp'].dt.date >= from_date.date()) & (df['timestamp'].dt.date <= to_date.date())]


def filter_data_daily(from_date, to_date):
    df = preprocess_data()
    from_date = parser.parse(from_date)
    to_date = parser.parse(to_date)
    df = df[(df['timestamp'].dt.date >= from_date.date()) & (df['timestamp'].dt.date <= to_date.date())]
    df.set_index('timestamp', inplace=True)
    water_data = df.resample('D').agg({'FlowInd': 'mean', 'Depth': 'mean'}).reset_index()
    df = df[(df['TDS'] != 0)]
    df = df[(df['pH'] != 0)]
    tds_ph_data = df.resample('D').agg({'TDS': 'mean', 'pH': 'mean'}).reset_index()
    return water_data.merge(tds_ph_data, how='inner', on='timestamp')


def filter_data_weekly(from_date, to_date):
    df = preprocess_data()
    from_date = parser.parse(from_date)
    to_date = parser.parse(to_date)
    df = df[(df['timestamp'].dt.date >= from_date.date()) & (df['timestamp'].dt.date <= to_date.date())]
    df.set_index('timestamp', inplace=True)
    return df.resample('W-Mon').agg({'FlowInd': 'sum', 'Depth': 'sum', 'TDS': 'mean', 'pH': 'mean'}).reset_index()


def filter_data_monthly(from_date, to_date):
    df = preprocess_data()
    from_date = parser.parse(from_date)
    to_date = parser.parse(to_date)
    df = df[(df['TDS'] != 0)]
    df = df[(df['pH'] != 0)]
    df = df[(df['timestamp'].dt.date >= from_date.date()) & (df['timestamp'].dt.date <= to_date.date())]
    df.set_index('timestamp', inplace=True)
    return df.resample('ME').agg({'FlowInd': 'sum', 'Depth': 'sum', 'TDS': 'mean', 'pH': 'mean'}).reset_index()


def filter_data_hourly():
    df = preprocess_data()
    df = df[(df['TDS'] != 0)]
    df = df[(df['pH'] != 0)]
    df.set_index('timestamp', inplace=True)
    return df.resample('h').agg({'FlowInd': 'sum', 'Depth': 'sum', 'TDS': 'mean', 'pH': 'mean'}).reset_index()


# Preprocessing
'''df = preprocess_data()
#print("Processed Data:")
#print(df.head())  # Display the first few rows of the processed DataFrame

# Filter Data within a Date Range
from_date = "2024-08-21"
to_date = "2024-10-21"
filtered_df = filter_data(from_date, to_date)
print("Filtered Data (From 2024-10-01 to 2024-10-21):")
print(filtered_df.head())  # Display first few rows of the filtered DataFrame

# Daily Aggregation
daily_df = filter_data_daily(from_date, to_date)
print("Daily Aggregated Data:")
print(daily_df)

#df = preprocess_data()
#df.to_csv("processed_data.csv", index=False)  # Saves the preprocessed data as a CSV file

filtered_df = filter_data(from_date, to_date)
#filtered_df.to_csv("filtered_data.csv", index=False)  # Saves the filtered data as a CSV file'''
#D:\Work\Realtime_data_NP\Demo2\Dashboards-main\filtered_data.csv
'''# Assuming daily_df is the DataFrame with the aggregated daily data
daily_df = filter_data_daily(from_date, to_date)

# Convert DataFrame to JSON
daily_json = daily_df.to_json(orient='records')

# Print the JSON output
print("Daily Aggregated Data (JSON):")
print(daily_json)'''



'''# Define your function to filter and aggregate daily data
def aggregate_daily_data():
    daily_df = filter_data_daily(from_date, to_date)
    daily_json = daily_df.to_json(orient='records')
    print("Daily Aggregated Data (JSON):")
    print(daily_json)
    return daily_json

# Loop to run the aggregation every 10 minutes
while True:
    aggregate_daily_data()
    print("Waiting for 10 minutes...")
    time.sleep(650)  # Wait for 600 seconds (10 minutes)'''
