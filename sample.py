import pandas as pd
import numpy as np

def create_sample_data(city, file_name):
    """Create sample air quality data for a specific city"""
    np.random.seed(42)
    n_samples = 5000
    
    # Create datetime index
    date_range = pd.date_range(start='2020-01-01', periods=n_samples, freq='H')
    
    # Generate correlated pollutant data with realistic patterns
    base_trend = np.sin(np.arange(n_samples) * 2 * np.pi / 24) * 20 + 50  # Daily pattern
    seasonal_trend = np.sin(np.arange(n_samples) * 2 * np.pi / (24 * 365)) * 10  # Seasonal pattern
    
    # City-specific variations
    city_multipliers = {
        'Delhi': {'pollution': 1.5, 'temp_base': 25},
        'Mumbai': {'pollution': 1.2, 'temp_base': 28},
        'Bengaluru': {'pollution': 0.8, 'temp_base': 22},
        'Chennai': {'pollution': 1.0, 'temp_base': 30},
        'Kolkata': {'pollution': 1.3, 'temp_base': 26},
        'Hyderabad': {'pollution': 1.1, 'temp_base': 24}
    }
    
    multiplier = city_multipliers.get(city, {'pollution': 1.0, 'temp_base': 25})
    pollution_base = base_trend * multiplier['pollution']
    
    data = {
        'datetime': date_range,
        'hour': date_range.hour,
        'day': date_range.day,
        'PM2.5': np.maximum(pollution_base + np.random.normal(0, 15, n_samples), 1),
        'PM10': np.maximum(pollution_base * 1.5 + np.random.normal(0, 20, n_samples), 1),
        'SO2': np.maximum(pollution_base * 0.3 + np.random.normal(0, 5, n_samples), 0.1),
        'NO2': np.maximum(pollution_base * 0.8 + np.random.normal(0, 10, n_samples), 1),
        'CO': np.maximum(pollution_base * 15 + np.random.normal(0, 200, n_samples), 100),
        'O3': np.maximum(pollution_base * 0.7 + np.random.normal(0, 20, n_samples), 1),
        'TEMP': multiplier['temp_base'] + np.sin(np.arange(n_samples) * 2 * np.pi / 24) * 10 + np.random.normal(0, 3, n_samples),
        'HUMIDITY': np.clip(50 + np.sin(np.arange(n_samples) * 2 * np.pi / 24 + np.pi) * 20 + np.random.normal(0, 10, n_samples), 20, 95),
        'PRESSURE': 1013 + np.random.normal(0, 10, n_samples),
        'WIND_SPEED': np.maximum(np.random.exponential(2, n_samples), 0),
        'wd': np.random.choice(['N', 'NE', 'E', 'SE', 'S', 'SW', 'W', 'NW'], n_samples),
    }
    
    df = pd.DataFrame(data)
    
    # Calculate AQI based on PM2.5
    def calculate_aqi_from_pm25(pm25):
        if pm25 <= 12.0:
            return int((50 - 0) / (12.0 - 0) * (pm25 - 0) + 0)
        elif pm25 <= 35.4:
            return int((100 - 51) / (35.4 - 12.1) * (pm25 - 12.1) + 51)
        elif pm25 <= 55.4:
            return int((150 - 101) / (55.4 - 35.5) * (pm25 - 35.5) + 101)
        elif pm25 <= 150.4:
            return int((200 - 151) / (150.4 - 55.5) * (pm25 - 55.5) + 151)
        elif pm25 <= 250.4:
            return int((300 - 201) / (250.4 - 150.5) * (pm25 - 150.5) + 201)
        else:
            return int((500 - 301) / (500.4 - 250.5) * (pm25 - 250.5) + 301)
    
    df['aqi'] = df['PM2.5'].apply(calculate_aqi_from_pm25)
    df['datetime'] = df['datetime'].astype(str)
    df.to_csv(file_name, index=False)
    print(f"Sample data created and saved as '{file_name}' for {city}")
    return df

if __name__ == "__main__":
    stations_info = pd.read_csv("Stations_Info.csv")
    for _, row in stations_info.iterrows():
        create_sample_data(row["city"], row["file_name"])