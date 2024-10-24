import requests
import pandas as pd
from datetime import datetime
from dateutil import parser
from get_data import fetch_data_from_api

API_URL = "https://mongodb-api-hmeu.onrender.com"

# Shared preprocessing function for data
def preprocess_data(data, date_format="%d-%b-%Y %H:%M:%S"):
    if not data:
        print("No data received")
        return pd.DataFrame()

    df = pd.DataFrame(data)
    if df.empty:
        print("DataFrame is empty after conversion")
        return df

    df['timestamp'] = pd.to_datetime(df['timestamp'], format=date_format, errors='coerce')
    df.dropna(subset=['timestamp'], inplace=True)  # Drop rows with invalid timestamps
    df.fillna(0, inplace=True)
    return df

# Fetch and preprocess data once
def fetch_and_preprocess_data():
    data = fetch_data_from_api(API_URL)
    return preprocess_data(data)

# Generic filter function
def filter_data(df, from_date, to_date):
    from_date = parser.parse(from_date).date()
    to_date = parser.parse(to_date).date()
    return df[(df['timestamp'].dt.date >= from_date) & (df['timestamp'].dt.date <= to_date)]

# Filter for daily data
def filter_data_daily(df, from_date, to_date):
    filtered_df = filter_data(df, from_date, to_date)
    filtered_df.set_index('timestamp', inplace=True)

    water_data = filtered_df.resample('D').agg({
        'FlowInd': 'mean',
        'Depth': 'mean'
    }).reset_index()

    valid_df = filtered_df[(filtered_df['TDS'] != 0) & (filtered_df['pH'] != 0)]
    tds_ph_data = valid_df.resample('D').agg({
        'TDS': 'mean',
        'pH': 'mean'
    }).reset_index()

    return water_data.merge(tds_ph_data, on='timestamp')

# Filter for weekly data
def filter_data_weekly(df, from_date, to_date):
    filtered_df = filter_data(df, from_date, to_date)
    filtered_df.set_index('timestamp', inplace=True)

    return filtered_df.resample('W-Mon').agg({
        'FlowInd': 'mean',
        'Depth': 'mean',
        'TDS': 'mean',
        'pH': 'mean'
    }).reset_index()

# Filter for monthly data
def filter_data_monthly(df, from_date, to_date):
    filtered_df = filter_data(df, from_date, to_date)
    filtered_df = filtered_df[(filtered_df['TDS'] != 0) & (filtered_df['pH'] != 0)]
    filtered_df.set_index('timestamp', inplace=True)

    return filtered_df.resample('M').agg({
        'FlowInd': 'mean',
        'Depth': 'mean',
        'TDS': 'mean',
        'pH': 'mean'
    }).reset_index()

# Filter for hourly data
def filter_data_hourly(df):
    df = df[(df['TDS'] != 0) & (df['pH'] != 0)]
    df.set_index('timestamp', inplace=True)

    return df.resample('H').agg({
        'FlowInd': 'mean',
        'Depth': 'mean',
        'TDS': 'mean',
        'pH': 'mean'
    }).reset_index()

# Main function to execute filtering operations
def main():
    # Fetch and preprocess data once
    df = fetch_and_preprocess_data()

    if df.empty:
        print("No data to process.")
        return

    # Example calls to the filter functions
    daily_data = filter_data_daily(df, '2024-10-01', '2024-10-31')
    weekly_data = filter_data_weekly(df, '2024-10-01', '2024-10-31')
    monthly_data = filter_data_monthly(df, '2024-10-01', '2024-10-31')
    hourly_data = filter_data_hourly(df)

    # You can handle or save the filtered data as needed
    print("Daily Data:\n", daily_data)
    #print("Weekly Data:\n", weekly_data)
    #print("Monthly Data:\n", monthly_data)
    print("Hourly Data:\n", hourly_data)

if __name__ == "__main__":
    main()
