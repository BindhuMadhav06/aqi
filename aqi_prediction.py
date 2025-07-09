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
import logging
import sys

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('app.log')
    ]
)
logger = logging.getLogger(__name__)

warnings.filterwarnings('ignore')

app = Flask(__name__)
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size
app.config['SEND_FILE_MAX_AGE_DEFAULT'] = 300  # 5 minutes cache
app.config['JSONIFY_PRETTYPRINT_REGULAR'] = False

# Global cache for data and predictions
DATA_CACHE = {}
PREDICTION_CACHE = {}

class OptimizedAQIPredictor:
    def __init__(self, n_steps=3, n_features=1):
        self.n_steps = n_steps
        self.n_features = n_features
        self.plot_dir = "static/plots"
        try:
            os.makedirs(self.plot_dir, exist_ok=True)
            os.makedirs("static", exist_ok=True)
        except Exception as e:
            logger.error(f"Failed to create directories: {e}")
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
        self.current_city = None

    def load_data(self, station_city=None):
        cache_key = f"data_{station_city}"
        if station_city != self.current_city:
            logger.info(f"City changed to {station_city}, clearing cache")
            DATA_CACHE.clear()
            PREDICTION_CACHE.clear()
            self.current_city = station_city
        if cache_key in DATA_CACHE:
            self.df = DATA_CACHE[cache_key]['df']
            logger.info(f"Loaded data from cache for {station_city}")
            return DATA_CACHE[cache_key]['info'], None
        try:
            if station_city:
                try:
                    stations_info = pd.read_csv("Stations_Info.csv")
                    file_row = stations_info[stations_info["city"] == station_city]
                    if not file_row.empty:
                        file_name = file_row["file_name"].iloc[0]
                        self.df = pd.read_csv(file_name)
                        logger.info(f"Data loaded from {file_name} for {station_city}! Shape: {self.df.shape}")
                    else:
                        logger.warning(f"No data file for {station_city} in Stations_Info.csv, creating sample data")
                        return self.create_sample_data(station_city)
                except FileNotFoundError as e:
                    logger.warning(f"File not found for {station_city}: {e}, creating sample data")
                    return self.create_sample_data(station_city)
            else:
                try:
                    self.df = pd.read_csv("data.csv")
                    logger.info(f"Data loaded from data.csv! Shape: {self.df.shape}")
                except FileNotFoundError:
                    logger.warning("data.csv not found, creating sample data")
                    return self.create_sample_data()
            if 'datetime' in self.df.columns:
                self.df['datetime'] = pd.to_datetime(self.df['datetime']).astype(str)
            required_columns = ['PM2.5', 'PM10', 'SO2', 'NO2', 'CO', 'O3', 'TEMP', 'HUMIDITY', 'PRESSURE', 'WIND_SPEED']
            missing_cols = [col for col in required_columns if col not in self.df.columns]
            if missing_cols:
                logger.warning(f"Missing columns in data: {missing_cols}, creating sample data")
                return self.create_sample_data(station_city)
            data_info = {
                "shape": self.df.shape,
                "columns": list(self.df.columns),
                "pollutants": [col for col in self.df.columns if col in required_columns]
            }
            self.df = self.df.dropna()
            logger.info(f"Data shape after removing NaN: {self.df.shape}")
            if self.df.empty:
                logger.warning("Dataframe empty after cleaning, creating sample data")
                return self.create_sample_data(station_city)
            DATA_CACHE[cache_key] = {
                'df': self.df.copy(),
                'info': data_info,
                'timestamp': time.time()
            }
            return data_info, None
        except Exception as e:
            logger.error(f"Data loading error: {e}")
            return self.create_sample_data(station_city)

    def create_sample_data(self, station_city=None):
        cache_key = f"sample_{station_city}"
        if cache_key in DATA_CACHE:
            self.df = DATA_CACHE[cache_key]['df']
            logger.info(f"Loaded sample data from cache for {station_city}")
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
            n_samples = 72
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
            DATA_CACHE[cache_key] = {
                'df': self.df.copy(),
                'info': data_info,
                'timestamp': time.time()
            }
            logger.info(f"Created sample data for {station_city}! Shape: {self.df.shape}")
            return data_info, None
        except Exception as e:
            logger.error(f"Sample data creation error: {e}")
            return None, {'code': 'E009', 'message': self.error_codes['E009'], 'details': str(e)}

    def calculate_aqi_from_pm25(self, pm25):
        try:
            pm25 = float(pm25)
            if pm25 < 0:
                pm25 = 0
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
        except:
            return 50

    def get_aqi_category(self, aqi):
        try:
            aqi = int(aqi)
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
        except:
            return {'category': 'Unknown', 'color': '#666666', 'icon': 'AlertCircle'}

    def filter_data(self, time_range='24h'):
        try:
            hours_map = {'6h': 6, '12h': 12, '24h': 24, '3d': 72, '7d': 168}
            hours = hours_map.get(time_range, 24)
            if hasattr(self, 'df') and not self.df.empty:
                if len(self.df) >= hours:
                    filtered_df = self.df.tail(hours)
                else:
                    filtered_df = self.df
                if filtered_df.empty:
                    return None, {'code': 'E007', 'message': self.error_codes['E007'], 'details': f'No data for {time_range}'}
                return filtered_df.to_dict('records'), None
            else:
                return None, {'code': 'E007', 'message': self.error_codes['E007'], 'details': 'No data available'}
        except Exception as e:
            logger.error(f"Data filtering error: {e}")
            return None, {'code': 'E003', 'message': self.error_codes['E003'], 'details': str(e)}

    def get_current_stats(self, data):
        try:
            if not data or len(data) == 0:
                return {
                    'aqi': 50,
                    'category': 'Good',
                    'color': '#00e400',
                    'icon': 'CheckCircle',
                    'pm25': 10.0,
                    'pm10': 20.0,
                    'so2': 2.0,
                    'no2': 8.0,
                    'co': 200.0,
                    'o3': 15.0,
                    'temperature': 25.0,
                    'humidity': 50.0,
                    'windSpeed': 5.0
                }, None
            latest = data[-1]
            aqi_info = self.get_aqi_category(latest.get('aqi', 50))
            return {
                'aqi': latest.get('aqi', 50),
                'category': aqi_info['category'],
                'color': aqi_info['color'],
                'icon': aqi_info['icon'],
                'pm25': round(float(latest.get('PM2.5', 10)), 2),
                'pm10': round(float(latest.get('PM10', 20)), 2),
                'so2': round(float(latest.get('SO2', 2)), 2),
                'no2': round(float(latest.get('NO2', 8)), 2),
                'co': round(float(latest.get('CO', 200)), 2),
                'o3': round(float(latest.get('O3', 15)), 2),
                'temperature': round(float(latest.get('TEMP', 25)), 2),
                'humidity': round(float(latest.get('HUMIDITY', 50)), 2),
                'windSpeed': round(float(latest.get('WIND_SPEED', 5)), 2)
            }, None
        except Exception as e:
            logger.error(f"Current stats error: {e}")
            return {
                'aqi': 50,
                'category': 'Good',
                'color': '#00e400',
                'icon': 'CheckCircle',
                'pm25': 10.0,
                'pm10': 20.0,
                'so2': 2.0,
                'no2': 8.0,
                'co': 200.0,
                'o3': 15.0,
                'temperature': 25.0,
                'humidity': 50.0,
                'windSpeed': 5.0
            }, {'code': 'E007', 'message': self.error_codes['E007'], 'details': str(e)}

    def get_pollutant_trends(self, data):
        try:
            if len(data) < 2:
                return {}, {'code': 'E007', 'message': self.error_codes['E007'], 'details': 'Insufficient data for trends'}
            latest = data[-1]
            previous = data[-2]
            trends = {}
            for pollutant in ['PM2.5', 'PM10', 'SO2', 'NO2', 'CO', 'O3']:
                try:
                    current_val = float(latest.get(pollutant, 0))
                    prev_val = float(previous.get(pollutant, 0))
                    change = current_val - prev_val
                    trends[pollutant] = {
                        'current': round(current_val, 2),
                        'change': round(change, 2),
                        'trend': 'up' if change > 0 else 'down' if change < 0 else 'stable'
                    }
                except:
                    trends[pollutant] = {
                        'current': 0.0,
                        'change': 0.0,
                        'trend': 'stable'
                    }
            return trends, None
        except Exception as e:
            logger.error(f"Trend calculation error: {e}")
            return {}, {'code': 'E007', 'message': self.error_codes['E007'], 'details': str(e)}

    def get_radar_data(self, data):
        try:
            if not data:
                return [], {'code': 'E007', 'message': self.error_codes['E007'], 'details': 'No data for radar chart'}
            latest = data[-1]
            return [
                {'subject': 'PM2.5', 'value': min((float(latest.get('PM2.5', 25)) / 250) * 100, 100), 'fullMark': 100},
                {'subject': 'PM10', 'value': min((float(latest.get('PM10', 50)) / 420) * 100, 100), 'fullMark': 100},
                {'subject': 'SO2', 'value': min((float(latest.get('SO2', 10)) / 80) * 100, 100), 'fullMark': 100},
                {'subject': 'NO2', 'value': min((float(latest.get('NO2', 20)) / 180) * 100, 100), 'fullMark': 100},
                {'subject': 'CO', 'value': min((float(latest.get('CO', 1000)) / 30000) * 100, 100), 'fullMark': 100},
                {'subject': 'O3', 'value': min((float(latest.get('O3', 60)) / 240) * 100, 100), 'fullMark': 100}
            ], None
        except Exception as e:
            logger.error(f"Radar data error: {e}")
            return [], {'code': 'E007', 'message': self.error_codes['E007'], 'details': str(e)}

    def get_hourly_distribution(self, data, pollutant):
        try:
            if not data:
                return [], {'code': 'E007', 'message': self.error_codes['E007'], 'details': 'No data for hourly distribution'}
            hourly_data = {}
            for d in data:
                hour = d.get('hour', 0)
                if hour not in hourly_data:
                    hourly_data[hour] = {'hour': hour, 'count': 0, 'total': 0}
                hourly_data[hour]['count'] += 1
                hourly_data[hour]['total'] += float(d.get(pollutant, 0))
            result = []
            for hour in range(24):
                if hour in hourly_data and hourly_data[hour]['count'] > 0:
                    avg = hourly_data[hour]['total'] / hourly_data[hour]['count']
                    result.append({'hour': hour, 'average': round(avg, 1)})
                else:
                    result.append({'hour': hour, 'average': 0})
            return result, None
        except Exception as e:
            logger.error(f"Hourly distribution error: {e}")
            return [], {'code': 'E007', 'message': self.error_codes['E007'], 'details': str(e)}

    def get_simple_predictions(self, data, pollutant='PM2.5', n_future=24):
        cache_key = f"pred_{pollutant}_{len(data)}"
        if cache_key in PREDICTION_CACHE:
            logger.info(f"Loaded predictions from cache for {pollutant}")
            return PREDICTION_CACHE[cache_key], None, None
        try:
            if len(data) < 3:
                return [25.0] * n_future, None, {'code': 'E007', 'message': 'Insufficient data for predictions'}
            recent_values = [float(d.get(pollutant, 25)) for d in data[-12:]]
            weights = np.array([0.1, 0.1, 0.1, 0.1, 0.15, 0.15, 0.2, 0.2, 0.25, 0.25, 0.3, 0.3])
            weights = weights[:len(recent_values)] / sum(weights[:len(recent_values)])
            base_value = np.average(recent_values, weights=weights)
            if len(recent_values) >= 3:
                trend = (recent_values[-1] - recent_values[-3]) / 2
            else:
                trend = 0
            predictions = []
            for i in range(n_future):
                variation = np.random.normal(0, abs(base_value) * 0.05)
                pred_value = max(base_value + (trend * (i + 1) * 0.3) + variation, 1.0)
                predictions.append(round(pred_value, 2))
            PREDICTION_CACHE[cache_key] = predictions
            return predictions, None, None
        except Exception as e:
            logger.error(f"Prediction error: {e}")
            return [25.0] * n_future, None, {'code': 'E008', 'message': self.error_codes['E008'], 'details': str(e)}

    def generate_simple_plots(self, data, predictions, city, pollutants=['PM2.5', 'PM10', 'SO2', 'NO2', 'CO', 'O3']):
        try:
            plot_data = {}
            for pollutant in pollutants:
                plt.figure(figsize=(10, 6))
                values = [float(d.get(pollutant, 0)) for d in data[-24:]]
                plt.plot(values, label='Actual', color='#2c3e50', linewidth=2)
                plt.title(f'{pollutant} Levels - {city}')
                plt.xlabel('Hours')
                plt.ylabel(f'{pollutant} Concentration (μg/m³)')
                plt.legend()
                plt.grid(True, alpha=0.3)
                time_series_path = os.path.join(self.plot_dir, f'time_series_{city}_{pollutant}.png')
                plt.savefig(time_series_path, bbox_inches='tight', dpi=100)
                plt.close()
                plt.figure(figsize=(10, 6))
                plt.plot(range(1, len(predictions[pollutant]) + 1), predictions[pollutant], 
                        label='Predictions', color='#27ae60', linewidth=2)
                plt.title(f'Future {pollutant} Predictions (Next 24 Hours) - {city}')
                plt.xlabel('Hours')
                plt.ylabel(f'{pollutant} Concentration (μg/m³)')
                plt.legend()
                plt.grid(True, alpha=0.3)
                future_pred_path = os.path.join(self.plot_dir, f'future_predictions_{city}_{pollutant}.png')
                plt.savefig(future_pred_path, bbox_inches='tight', dpi=100)
                plt.close()
                with open(time_series_path, 'rb') as f:
                    time_series_base64 = base64.b64encode(f.read()).decode('utf-8')
                with open(future_pred_path, 'rb') as f:
                    future_pred_base64 = base64.b64encode(f.read()).decode('utf-8')
                plot_data[pollutant] = {
                    'time_series': time_series_base64,
                    'future_predictions': future_pred_base64
                }
            return plot_data, None
        except Exception as e:
            logger.error(f"Plot generation error: {e}")
            return {}, {'code': 'E008', 'message': self.error_codes['E008'], 'details': str(e)}

def cleanup_cache():
    try:
        current_time = time.time()
        cache_lifetime = 3600
        for cache_dict in [DATA_CACHE, PREDICTION_CACHE]:
            keys_to_remove = []
            for key, value in cache_dict.items():
                if isinstance(value, dict) and 'timestamp' in value:
                    if current_time - value['timestamp'] > cache_lifetime:
                        keys_to_remove.append(key)
            for key in keys_to_remove:
                del cache_dict[key]
        logger.info(f"Cache cleanup completed. Removed {len(keys_to_remove)} entries")
    except Exception as e:
        logger.error(f"Cache cleanup error: {e}")

def start_cleanup_task():
    def cleanup_loop():
        while True:
            time.sleep(1800)
            cleanup_cache()
    cleanup_thread = threading.Thread(target=cleanup_loop, daemon=True)
    cleanup_thread.start()
    logger.info("Background cleanup task started")

@app.errorhandler(500)
def internal_error(error):
    logger.error(f"Internal server error: {error}")
    return jsonify({
        'error': 'Internal Server Error',
        'message': 'The server encountered an internal error.',
        'code': 500
    }), 500

@app.errorhandler(404)
def not_found(error):
    logger.error(f"Not found error: {error}")
    return jsonify({
        'error': 'Not Found',
        'message': 'The requested resource was not found.',
        'code': 404
    }), 404

@app.route('/health')
def health_check():
    try:
        return jsonify({
            'status': 'healthy',
            'timestamp': datetime.now().isoformat(),
            'version': '1.0.0',
            'cache_size': len(DATA_CACHE)
        })
    except Exception as e:
        logger.error(f"Health check error: {e}")
        return jsonify({
            'status': 'unhealthy',
            'error': str(e)
        }), 500

@app.route('/favicon.ico')
def favicon():
    return send_file(os.path.join(app.root_path, 'static', 'favicon.ico'))

@app.route('/api/cities')
def get_cities():
    try:
        stations_info = pd.read_csv("Stations_Info.csv")
        cities = stations_info['city'].tolist()
        logger.info(f"Returning available cities: {cities}")
        return jsonify({'cities': cities})
    except Exception as e:
        logger.error(f"Error loading cities: {e}")
        return jsonify({'error': {'code': 'E001', 'message': 'Failed to load cities', 'details': str(e)}}), 500

@app.route('/api/log', methods=['POST'])
def log_client():
    try:
        log_data = request.get_json()
        if log_data:
            logger.info(f"Client log: {json.dumps(log_data)}")
            return jsonify({'status': 'success', 'message': 'Log received'}), 200
        else:
            logger.warning("Received empty log data")
            return jsonify({'status': 'error', 'message': 'No log data provided'}), 400
    except Exception as e:
        logger.error(f"Error processing client log: {e}")
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/')
def index():
    try:
        predictor = OptimizedAQIPredictor(n_steps=3, n_features=1)
        selected_city = request.args.get('city', 'Delhi')
        time_range = request.args.get('timeRange', '24h')
        view_type = request.args.get('view', 'overview')
        selected_pollutant = request.args.get('pollutant', 'PM2.5')  # Added for chart consistency
        
        # Load available cities
        try:
            stations_info = pd.read_csv("Stations_Info.csv")
            cities = stations_info['city'].tolist()
        except Exception as e:
            logger.error(f"Error loading cities for dropdown: {e}")
            cities = ['Delhi', 'Mumbai', 'Bengaluru', 'Chennai', 'Kolkata', 'Hyderabad']

        # Load data for the selected city
        data_info, error = predictor.load_data(station_city=selected_city)
        if error:
            logger.error(f"Error loading data for {selected_city}: {error}")
            return render_template('index.html', 
                                 error=error,
                                 selected_city=selected_city,
                                 time_range=time_range,
                                 view_type=view_type,
                                 cities=cities,
                                 pollutants=[],
                                 current_stats={
                                     'aqi': 50,
                                     'category': 'Good',
                                     'color': '#00e400',
                                     'icon': 'CheckCircle',
                                     'pm25': 10.0
                                 },
                                 plot_data={},
                                 last_updated=datetime.now().strftime('%Y-%m-%d %H:%M:%S'))

        # Filter data based on time range
        filtered_data, error = predictor.filter_data(time_range)
        if error:
            logger.error(f"Error filtering data for {selected_city}: {error}")
            return render_template('index.html',
                                 error=error,
                                 selected_city=selected_city,
                                 time_range=time_range,
                                 view_type=view_type,
                                 cities=cities,
                                 pollutants=[],
                                 current_stats={
                                     'aqi': 50,
                                     'category': 'Good',
                                     'color': '#00e400',
                                     'icon': 'CheckCircle',
                                     'pm25': 10.0
                                 },
                                 plot_data={},
                                 last_updated=datetime.now().strftime('%Y-%m-%d %H:%M:%S'))

        # Get pollutants
        pollutants = data_info['pollutants']

        # Get current stats
        current_stats, error = predictor.get_current_stats(filtered_data)
        if error:
            logger.error(f"Error getting stats for {selected_city}: {error}")
            current_stats = {
                'aqi': 50,
                'category': 'Good',
                'color': '#00e400',
                'icon': 'CheckCircle',
                'pm25': 10.0
            }

        # Get trends
        trends, error = predictor.get_pollutant_trends(filtered_data)
        if error:
            logger.error(f"Error getting trends for {selected_city}: {error}")
            trends = {}

        # Get radar data
        radar_data, error = predictor.get_radar_data(filtered_data)
        if error:
            logger.error(f"Error getting radar data for {selected_city}: {error}")
            radar_data = []

        # Get hourly distributions and predictions for all pollutants
        hourly_distributions = {}
        future_predictions = {}
        for pollutant in pollutants:
            hourly_dist, error = predictor.get_hourly_distribution(filtered_data, pollutant)
            if error:
                logger.error(f"Error getting hourly distribution for {pollutant}: {error}")
                hourly_dist = []
            hourly_distributions[pollutant] = hourly_dist

            predictions, _, error = predictor.get_simple_predictions(filtered_data, pollutant)
            if error:
                logger.error(f"Error getting predictions for {pollutant}: {error}")
                predictions = [25.0] * 24
            future_predictions[pollutant] = predictions

        # Generate plots
        plot_data, error = predictor.generate_simple_plots(filtered_data, future_predictions, selected_city, pollutants)
        if error:
            logger.error(f"Error generating plots for {selected_city}: {error}")
            plot_data = {}

        # Prepare dashboard data for JavaScript
        dashboard_data = {
            'filteredData': filtered_data,
            'radarData': radar_data,
            'hourlyDistributions': hourly_distributions,
            'futurePredictions': future_predictions,
            'pollutants': pollutants,
            'selectedPollutant': selected_pollutant,
            'stats': current_stats,
            'trends': trends,
            'selectedCity': selected_city
        }

        return render_template('index.html',
                             selected_city=selected_city,
                             time_range=time_range,
                             view_type=view_type,
                             cities=cities,
                             pollutants=pollutants,
                             current_stats=current_stats,  # Changed from stats to current_stats
                             plot_data=plot_data,
                             dashboard_data_json=json.dumps(dashboard_data),
                             last_updated=datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
    except Exception as e:
        logger.error(f"Error in index route: {e}")
        return render_template('index.html',
                             error={'code': 'E500', 'message': 'Internal Server Error', 'details': str(e)},
                             selected_city=selected_city,
                             time_range=time_range,
                             view_type=view_type,
                             cities=['Delhi', 'Mumbai', 'Bengaluru', 'Chennai', 'Kolkata', 'Hyderabad'],
                             pollutants=[],
                             current_stats={
                                 'aqi': 50,
                                 'category': 'Good',
                                 'color': '#00e400',
                                 'icon': 'CheckCircle',
                                 'pm25': 10.0
                             },
                             plot_data={},
                             last_updated=datetime.now().strftime('%Y-%m-%d %H:%M:%S')), 500

@app.route('/api/dashboard')
def api_dashboard():
    try:
        predictor = OptimizedAQIPredictor(n_steps=3, n_features=1)
        selected_city = request.args.get('city', 'Delhi')
        time_range = request.args.get('timeRange', '24h')
        selected_pollutant = request.args.get('pollutant', 'PM2.5')

        data_info, error = predictor.load_data(station_city=selected_city)
        if error:
            logger.error(f"API: Error loading data for {selected_city}: {error}")
            return jsonify({'error': error}), 500
        filtered_data, error = predictor.filter_data(time_range)
        if error:
            logger.error(f"API: Error filtering data for {selected_city}: {error}")
            return jsonify({'error': error}), 500
        pollutants = data_info['pollutants']
        radar_data, error = predictor.get_radar_data(filtered_data)
        if error:
            logger.error(f"API: Error getting radar data for {selected_city}: {error}")
            radar_data = []
        current_stats, error = predictor.get_current_stats(filtered_data)
        if error:
            logger.error(f"API: Error getting stats for {selected_city}: {error}")
            current_stats = {
                'aqi': 50,
                'category': 'Good',
                'color': '#00e400',
                'icon': 'CheckCircle',
                'pm25': 10.0
            }
        hourly_distributions = {}
        future_predictions = {}
        for pollutant in pollutants:
            hourly_dist, error = predictor.get_hourly_distribution(filtered_data, pollutant)
            if error:
                logger.error(f"API: Error getting hourly distribution for {pollutant}: {error}")
                hourly_dist = []
            hourly_distributions[pollutant] = hourly_dist
            predictions, _, error = predictor.get_simple_predictions(filtered_data, pollutant)
            if error:
                logger.error(f"API: Error getting predictions for {pollutant}: {error}")
                predictions = [25.0] * 24
            future_predictions[pollutant] = predictions
        return jsonify({
            'filteredData': filtered_data,
            'radarData': radar_data,
            'hourlyDistributions': hourly_distributions,
            'futurePredictions': future_predictions,
            'pollutants': pollutants,
            'selectedPollutant': selected_pollutant,
            'stats': current_stats,
            'selectedCity': selected_city,
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        })
    except Exception as e:
        logger.error(f"API: Error in dashboard endpoint: {e}")
        return jsonify({
            'error': {
                'code': 'E500',
                'message': 'Internal Server Error',
                'details': str(e)
            }
        }), 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)  # Hardcode port 5000