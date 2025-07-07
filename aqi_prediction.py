# aqi_prediction_optimized.py
import matplotlib
matplotlib.use('Agg')
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import warnings
import os
import json
import io
import base64
from flask import Flask, render_template, jsonify, request, send_file
from datetime import datetime, timedelta
import threading
import time
from concurrent.futures import ThreadPoolExecutor
warnings.filterwarnings('ignore')

# Deep Learning Libraries
import tensorflow as tf
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import LSTM, Dense, Dropout
from tensorflow.keras.optimizers import Adam
from tensorflow.keras.callbacks import EarlyStopping

# Sklearn Libraries
from sklearn.preprocessing import MinMaxScaler
from sklearn.metrics import mean_squared_error, mean_absolute_error, r2_score

app = Flask(__name__)

# Global cache for models and data
MODEL_CACHE = {}
DATA_CACHE = {}
PREDICTION_CACHE = {}

class OptimizedAQIPredictor:
    def __init__(self, n_steps=3, n_features=1):
        self.n_steps = n_steps
        self.n_features = n_features
        self.scaler = MinMaxScaler(feature_range=(0, 1))
        self.model = None
        self.history = None
        self.plot_dir = "static/plots"
        os.makedirs(self.plot_dir, exist_ok=True)
        self.error_codes = {
            'E001': 'Data loading failed - File not found',
            'E002': 'Invalid pollutant parameter',
            'E003': 'Time range out of bounds',
            'E004': 'Missing required data fields',
            'E005': 'Data validation failed',
            'E007': 'Insufficient data for visualization',
            'E008': 'Model prediction failed',
            'E009': 'Data preprocessing error',
            'E010': 'Memory allocation error'
        }
        self.city_data = {}

    def load_data(self, station_city=None):
        """Optimized data loading with caching"""
        cache_key = f"data_{station_city}"
        
        # Check cache first
        if cache_key in DATA_CACHE:
            self.df = DATA_CACHE[cache_key]['df']
            return DATA_CACHE[cache_key]['info'], None
        
        try:
            # Try to load from file first
            if station_city:
                try:
                    stations_info = pd.read_csv("Stations_Info.csv")
                    file_row = stations_info[stations_info["city"] == station_city]
                    if not file_row.empty:
                        file_name = file_row["file_name"].iloc[0]
                        self.df = pd.read_csv(file_name)
                        print(f"Data loaded from {file_name} for {station_city}! Shape: {self.df.shape}")
                    else:
                        return self.create_sample_data(station_city)
                except FileNotFoundError:
                    return self.create_sample_data(station_city)
            else:
                try:
                    self.df = pd.read_csv("data.csv")
                    print(f"Data loaded from data.csv! Shape: {self.df.shape}")
                except FileNotFoundError:
                    return self.create_sample_data()

            if 'datetime' in self.df.columns:
                self.df['datetime'] = pd.to_datetime(self.df['datetime']).astype(str)

            required_columns = ['PM2.5', 'PM10', 'SO2', 'NO2', 'CO', 'O3', 'TEMP', 'HUMIDITY', 'PRESSURE', 'WIND_SPEED']
            missing_cols = [col for col in required_columns if col not in self.df.columns]
            if missing_cols:
                return self.create_sample_data(station_city)

            data_info = {
                "shape": self.df.shape,
                "columns": list(self.df.columns),
                "pollutants": [col for col in self.df.columns if col in required_columns]
            }
            
            self.df = self.df.dropna()
            
            if self.df.empty:
                return self.create_sample_data(station_city)

            # Cache the data
            DATA_CACHE[cache_key] = {
                'df': self.df.copy(),
                'info': data_info,
                'timestamp': time.time()
            }

            return data_info, None
        except Exception as e:
            return self.create_sample_data(station_city)

    def create_sample_data(self, station_city=None):
        """Optimized sample data creation"""
        cache_key = f"sample_{station_city}"
        
        if cache_key in DATA_CACHE:
            self.df = DATA_CACHE[cache_key]['df']
            return DATA_CACHE[cache_key]['info'], None
        
        try:
            np.random.seed(42)
            
            city_multipliers = {
                'Delhi': {'pollution': 1.5, 'temp_base': 25},
                'Mumbai': {'pollution': 1.2, 'temp_base': 28},
                'Bengaluru': {'pollution': 0.8, 'temp_base': 22},
                'Chennai': {'pollution': 1.0, 'temp_base': 30},
                'Kolkata': {'pollution': 1.3, 'temp_base': 26},
                'Hyderabad': {'pollution': 1.1, 'temp_base': 24}
            }
            
            multiplier = city_multipliers.get(station_city, {'pollution': 1.0, 'temp_base': 25})
            
            # Reduced sample size for faster processing
            n_samples = 72  # Reduced from 168
            end_date = datetime.now()
            start_date = end_date - timedelta(hours=n_samples-1)
            date_range = pd.date_range(start=start_date, periods=n_samples, freq='H')
            
            hours = np.arange(n_samples)
            daily_pattern = np.sin(hours * 2 * np.pi / 24) * 20
            base_trend = daily_pattern + 50
            
            pollution_base = base_trend * multiplier['pollution']
            
            data = {
                'datetime': date_range,
                'hour': [d.hour for d in date_range],
                'day': [d.day for d in date_range],
                'PM2.5': np.maximum(pollution_base + np.random.normal(0, 15, n_samples), 5),
                'PM10': np.maximum(pollution_base * 1.8 + np.random.normal(0, 25, n_samples), 10),
                'SO2': np.maximum(pollution_base * 0.4 + np.random.normal(0, 8, n_samples), 2),
                'NO2': np.maximum(pollution_base * 0.9 + np.random.normal(0, 12, n_samples), 8),
                'CO': np.maximum(pollution_base * 20 + np.random.normal(0, 500, n_samples), 200),
                'O3': np.maximum(120 - pollution_base * 0.6 + np.random.normal(0, 25, n_samples), 15),
                'TEMP': multiplier['temp_base'] + np.sin(hours * 2 * np.pi / 24) * 8 + np.random.normal(0, 3, n_samples),
                'HUMIDITY': 50 + np.sin(hours * 2 * np.pi / 24 + np.pi) * 20 + np.random.normal(0, 10, n_samples),
                'PRESSURE': 1013 + np.random.normal(0, 15, n_samples),
                'WIND_SPEED': np.maximum(np.random.exponential(3, n_samples), 0.5)
            }
            
            self.df = pd.DataFrame(data)
            
            pm25_aqi = self.df['PM2.5'].apply(self.calculate_aqi_from_pm25)
            self.df['aqi'] = pm25_aqi
            
            self.df['datetime'] = self.df['datetime'].astype(str)
            self.df['HUMIDITY'] = np.clip(self.df['HUMIDITY'], 20, 95)

            data_info = {
                "shape": self.df.shape,
                "columns": list(self.df.columns),
                "pollutants": ['PM2.5', 'PM10', 'SO2', 'NO2', 'CO', 'O3']
            }
            
            # Cache the sample data
            DATA_CACHE[cache_key] = {
                'df': self.df.copy(),
                'info': data_info,
                'timestamp': time.time()
            }
            
            return data_info, None
        except Exception as e:
            return None, {'code': 'E009', 'message': self.error_codes['E009'], 'details': str(e)}

    def calculate_aqi_from_pm25(self, pm25):
        """Fast AQI calculation"""
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

    def get_aqi_category(self, aqi):
        """Fast AQI category lookup"""
        if aqi <= 50:
            return {'category': 'Good', 'color': '#00e400', 'icon': 'CheckCircle'}
        elif aqi <= 100:
            return {'category': 'Moderate', 'color': '#ffff00', 'icon': 'AlertCircle'}
        elif aqi <= 150:
            return {'category': 'Unhealthy for Sensitive Groups', 'color': '#ff7e00', 'icon': 'AlertTriangle'}
        elif aqi <= 200:
            return {'category': 'Unhealthy', 'color': '#ff0000', 'icon': 'XCircle'}
        elif aqi <= 300:
            return {'category': 'Very Unhealthy', 'color': '#8f3f97', 'icon': 'XCircle'}
        else:
            return {'category': 'Hazardous', 'color': '#7e0023', 'icon': 'XCircle'}

    def filter_data(self, time_range='24h'):
        """Optimized data filtering"""
        try:
            hours_map = {'6h': 6, '12h': 12, '24h': 24, '3d': 72, '7d': 168}
            hours = hours_map.get(time_range, 24)
            
            if len(self.df) >= hours:
                filtered_df = self.df.tail(hours)
            else:
                filtered_df = self.df
            
            if filtered_df.empty:
                return None, {'code': 'E007', 'message': self.error_codes['E007'], 'details': f'No data for {time_range}'}
            
            return filtered_df.to_dict('records'), None
        except Exception as e:
            return None, {'code': 'E003', 'message': self.error_codes['E003'], 'details': str(e)}

    def get_current_stats(self, data):
        """Fast current stats calculation"""
        if not data:
            return {}, {'code': 'E007', 'message': self.error_codes['E007'], 'details': 'No data available'}
        latest = data[-1]
        aqi_info = self.get_aqi_category(latest['aqi'])
        return {
            'aqi': latest['aqi'],
            'category': aqi_info['category'],
            'color': aqi_info['color'],
            'icon': aqi_info['icon'],
            'pm25': latest['PM2.5'],
            'pm10': latest['PM10'],
            'temperature': latest['TEMP'],
            'humidity': latest['HUMIDITY'],
            'windSpeed': latest['WIND_SPEED']
        }, None

    def get_pollutant_trends(self, data):
        """Fast trend calculation"""
        if len(data) < 2:
            return {}, {'code': 'E007', 'message': self.error_codes['E007'], 'details': 'Insufficient data for trends'}
        latest = data[-1]
        previous = data[-2]
        trends = {}
        for pollutant in ['PM2.5', 'PM10', 'SO2', 'NO2', 'CO', 'O3']:
            change = latest[pollutant] - previous[pollutant]
            trends[pollutant] = {
                'current': round(latest[pollutant], 2),
                'change': round(change, 2),
                'trend': 'up' if change > 0 else 'down' if change < 0 else 'stable'
            }
        return trends, None

    def get_radar_data(self, data):
        """Fast radar chart data"""
        if not data:
            return [], {'code': 'E007', 'message': self.error_codes['E007'], 'details': 'No data for radar chart'}
        latest = data[-1]
        return [
            {'subject': 'PM2.5', 'value': min((latest['PM2.5'] / 250) * 100, 100), 'fullMark': 100},
            {'subject': 'PM10', 'value': min((latest['PM10'] / 420) * 100, 100), 'fullMark': 100},
            {'subject': 'SO2', 'value': min((latest['SO2'] / 80) * 100, 100), 'fullMark': 100},
            {'subject': 'NO2', 'value': min((latest['NO2'] / 180) * 100, 100), 'fullMark': 100},
            {'subject': 'CO', 'value': min((latest['CO'] / 30000) * 100, 100), 'fullMark': 100},
            {'subject': 'O3', 'value': min((latest['O3'] / 240) * 100, 100), 'fullMark': 100}
        ], None

    def get_hourly_distribution(self, data, pollutant):
        """Fast hourly distribution calculation"""
        if not data:
            return [], {'code': 'E007', 'message': self.error_codes['E007'], 'details': 'No data for hourly distribution'}
        
        hourly_data = {}
        for d in data:
            hour = d['hour']
            if hour not in hourly_data:
                hourly_data[hour] = {'hour': hour, 'count': 0, 'total': 0}
            hourly_data[hour]['count'] += 1
            hourly_data[hour]['total'] += d[pollutant]
        
        result = []
        for hour in range(24):
            if hour in hourly_data:
                avg = hourly_data[hour]['total'] / hourly_data[hour]['count']
                result.append({'hour': hour, 'average': round(avg, 1)})
            else:
                result.append({'hour': hour, 'average': 0})
        
        return result, None

    def get_simple_predictions(self, data, pollutant='PM2.5', n_future=24):
        """Simple prediction using moving average (much faster than LSTM)"""
        cache_key = f"pred_{pollutant}_{len(data)}"
        
        if cache_key in PREDICTION_CACHE:
            return PREDICTION_CACHE[cache_key], None, None
        
        try:
            if len(data) < 3:
                return None, None, {'code': 'E007', 'message': 'Insufficient data for predictions'}
            
            # Get recent values
            recent_values = [d[pollutant] for d in data[-12:]]  # Last 12 hours
            
            # Simple trend-based prediction
            if len(recent_values) >= 3:
                # Calculate trend
                trend = (recent_values[-1] - recent_values[-3]) / 2
                base_value = recent_values[-1]
                
                # Generate predictions with some variation
                predictions = []
                for i in range(n_future):
                    # Add slight random variation and trend
                    variation = np.random.normal(0, abs(base_value) * 0.1)
                    pred_value = max(base_value + (trend * (i + 1) * 0.5) + variation, 1.0)
                    predictions.append(pred_value)
                
                # Cache the predictions
                PREDICTION_CACHE[cache_key] = predictions
                
                return predictions, None, None
            else:
                # Fallback to simple repetition with variation
                base_value = recent_values[-1]
                predictions = []
                for i in range(n_future):
                    variation = np.random.normal(0, abs(base_value) * 0.1)
                    pred_value = max(base_value + variation, 1.0)
                    predictions.append(pred_value)
                
                return predictions, None, None
                
        except Exception as e:
            return None, None, {'code': 'E008', 'message': self.error_codes['E008'], 'details': str(e)}

    def generate_simple_plots(self, data, predictions, pollutant, city):
        """Generate simple plots without heavy computation"""
        try:
            # Time series plot
            plt.figure(figsize=(10, 6))
            values = [d[pollutant] for d in data[-24:]]  # Last 24 hours
            plt.plot(values, label='Actual', color='#2c3e50', linewidth=2)
            plt.title(f'{pollutant} Levels - {city}')
            plt.xlabel('Hours')
            plt.ylabel(f'{pollutant} Concentration (μg/m³)')
            plt.legend()
            plt.grid(True, alpha=0.3)
            
            time_series_path = os.path.join(self.plot_dir, f'time_series_{city}_{pollutant}.png')
            plt.savefig(time_series_path, bbox_inches='tight', dpi=100)
            plt.close()

            # Future predictions plot
            plt.figure(figsize=(10, 6))
            plt.plot(range(1, len(predictions) + 1), predictions, label='Predictions', color='#27ae60', linewidth=2)
            plt.title(f'Future {pollutant} Predictions (Next 24 Hours) - {city}')
            plt.xlabel('Hours')
            plt.ylabel(f'{pollutant} Concentration (μg/m³)')
            plt.legend()
            plt.grid(True, alpha=0.3)
            
            future_pred_path = os.path.join(self.plot_dir, f'future_predictions_{city}_{pollutant}.png')
            plt.savefig(future_pred_path, bbox_inches='tight', dpi=100)
            plt.close()

            # Convert to base64
            with open(time_series_path, 'rb') as f:
                time_series_base64 = base64.b64encode(f.read()).decode('utf-8')
            with open(future_pred_path, 'rb') as f:
                future_pred_base64 = base64.b64encode(f.read()).decode('utf-8')

            return time_series_base64, future_pred_base64, None
        except Exception as e:
            return None, None, {'code': 'E008', 'message': self.error_codes['E008'], 'details': str(e)}

# Background task for cache cleanup
def cleanup_cache():
    """Clean up old cache entries"""
    current_time = time.time()
    cache_lifetime = 3600  # 1 hour
    
    for cache_dict in [DATA_CACHE, PREDICTION_CACHE]:
        keys_to_remove = []
        for key, value in cache_dict.items():
            if isinstance(value, dict) and 'timestamp' in value:
                if current_time - value['timestamp'] > cache_lifetime:
                    keys_to_remove.append(key)
        
        for key in keys_to_remove:
            del cache_dict[key]

# Start background cleanup task
def start_cleanup_task():
    def cleanup_loop():
        while True:
            time.sleep(1800)  # Clean up every 30 minutes
            cleanup_cache()
    
    cleanup_thread = threading.Thread(target=cleanup_loop, daemon=True)
    cleanup_thread.start()

start_cleanup_task()

@app.route('/')
def index():
    """Optimized main route"""
    predictor = OptimizedAQIPredictor(n_steps=3, n_features=1)
    selected_city = request.args.get('city', 'Delhi')
    selected_pollutant = request.args.get('pollutant', 'PM2.5')
    time_range = request.args.get('timeRange', '24h')
    view_type = request.args.get('view', 'overview')

    last_updated = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    # Load data
    data_info, error = predictor.load_data(station_city=selected_city)
    if error:
        return render_template('index.html', error=error, 
                            data_info={'pollutants': ['PM2.5', 'PM10', 'SO2', 'NO2', 'CO', 'O3']}, 
                            last_updated=last_updated,
                            selected_city=selected_city,
                            selected_pollutant=selected_pollutant,
                            time_range=time_range,
                            view_type=view_type)

    # Process data in parallel
    with ThreadPoolExecutor(max_workers=4) as executor:
        future_filtered = executor.submit(predictor.filter_data, time_range)
        
        filtered_data, error = future_filtered.result()
        if error:
            return render_template('index.html', error=error, data_info=data_info, 
                                last_updated=last_updated,
                                selected_city=selected_city,
                                selected_pollutant=selected_pollutant,
                                time_range=time_range,
                                view_type=view_type)

        # Process other data concurrently
        future_stats = executor.submit(predictor.get_current_stats, filtered_data)
        future_trends = executor.submit(predictor.get_pollutant_trends, filtered_data)
        future_radar = executor.submit(predictor.get_radar_data, filtered_data)
        future_hourly = executor.submit(predictor.get_hourly_distribution, filtered_data, selected_pollutant)
        future_predictions = executor.submit(predictor.get_simple_predictions, filtered_data, selected_pollutant)

        # Get results
        current_stats, error = future_stats.result()
        if error:
            current_stats = {}

        pollutant_trends, error = future_trends.result()
        if error:
            pollutant_trends = {}

        radar_data, error = future_radar.result()
        if error:
            radar_data = []

        hourly_distribution, error = future_hourly.result()
        if error:
            hourly_distribution = []

        future_predictions, _, error = future_predictions.result()
        if error:
            future_predictions = []

    # Generate plots (optional, only if requested)
    time_series_base64, future_pred_base64 = None, None
    if view_type in ['overview', 'trends']:
        time_series_base64, future_pred_base64, error = predictor.generate_simple_plots(
            filtered_data, future_predictions, selected_pollutant, selected_city)

    # Prepare dashboard data
    dashboard_data = {
        'filteredData': filtered_data,
        'radarData': radar_data,
        'hourlyDistribution': hourly_distribution,
        'futurePredictions': future_predictions,
        'selectedPollutant': selected_pollutant
    }

    return render_template(
        'index.html',
        data_info=data_info,
        filtered_data=filtered_data,
        current_stats=current_stats,
        pollutant_trends=pollutant_trends,
        radar_data=radar_data,
        hourly_distribution=hourly_distribution,
        future_predictions=future_predictions,
        time_series_base64=time_series_base64,
        future_pred_base64=future_pred_base64,
        selected_city=selected_city,
        selected_pollutant=selected_pollutant,
        time_range=time_range,
        view_type=view_type,
        last_updated=last_updated,
        dashboard_data_json=json.dumps(dashboard_data)
    )

@app.route('/api/dashboard')
def api_dashboard():
    """Fast API endpoint for dashboard data"""
    predictor = OptimizedAQIPredictor(n_steps=3, n_features=1)
    selected_city = request.args.get('city', 'Delhi')
    selected_pollutant = request.args.get('pollutant', 'PM2.5')
    time_range = request.args.get('timeRange', '24h')

    data_info, error = predictor.load_data(station_city=selected_city)
    if error:
        return jsonify({'error': error}), 500

    filtered_data, error = predictor.filter_data(time_range)
    if error:
        return jsonify({'error': error}), 500

    radar_data, error = predictor.get_radar_data(filtered_data)
    if error:
        radar_data = []

    hourly_distribution, error = predictor.get_hourly_distribution(filtered_data, selected_pollutant)
    if error:
        hourly_distribution = []

    future_predictions, _, error = predictor.get_simple_predictions(filtered_data, selected_pollutant)
    if error:
        future_predictions = []

    return jsonify({
        'filteredData': filtered_data,
        'radarData': radar_data,
        'hourlyDistribution': hourly_distribution,
        'futurePredictions': future_predictions,
        'selectedPollutant': selected_pollutant
    })

@app.route('/export_predictions')
def export_predictions():
    """Export predictions to CSV"""
    pollutant = request.args.get('pollutant', 'PM2.5')
    predictions = request.args.getlist('predictions', type=float)
    
    df = pd.DataFrame({
        'Hour': range(1, len(predictions) + 1),
        f'{pollutant}_Prediction': predictions
    })
    
    buffer = io.StringIO()
    df.to_csv(buffer, index=False)
    buffer.seek(0)
    
    return send_file(
        io.BytesIO(buffer.getvalue().encode()),
        mimetype='text/csv',
        as_attachment=True,
        download_name=f'{pollutant}_future_predictions.csv'
    )

if __name__ == "__main__":
    app.run(debug=True, threaded=True)