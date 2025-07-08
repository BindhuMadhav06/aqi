# Air Quality Index Prediction using LSTM
# Complete implementation with data preprocessing, model training, and visualization

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import warnings
warnings.filterwarnings('ignore')

# Deep Learning Libraries
import tensorflow as tf
from tensorflow import keras
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import LSTM, Dense, Dropout
from tensorflow.keras.optimizers import Adam  # Fixed import
from tensorflow.keras.callbacks import EarlyStopping, ModelCheckpoint

# Sklearn Libraries
from sklearn.preprocessing import MinMaxScaler
from sklearn.metrics import mean_squared_error, mean_absolute_error, r2_score
from sklearn.model_selection import train_test_split

# Set random seeds for reproducibility
np.random.seed(42)
tf.random.set_seed(42)

class AQIPredictor:
    def __init__(self, n_steps=3, n_features=1):
        self.n_steps = n_steps
        self.n_features = n_features
        self.scaler = MinMaxScaler(feature_range=(0, 1))
        self.model = None
        self.history = None
        
    def load_data(self, station_city=None):
        """Load and preprocess the air quality data for a specific station"""
        try:
            if station_city:
                # Load Stations_Info.csv to find the file_name for the given city
                stations_info = pd.read_csv("Stations_Info.csv")
                file_row = stations_info[stations_info["city"] == station_city]
                if file_row.empty:
                    print(f"No station found for city: {station_city}")
                    return False
                file_name = file_row["file_name"].iloc[0]
            else:
                file_name = "data.csv"  # Default fallback
            
            # Load data
            self.df = pd.read_csv(file_name)
            print(f"Data loaded successfully for {station_city}! Shape: {self.df.shape}")
            print(f"Columns: {list(self.df.columns)}")
            
            # Display basic info
            print("\nFirst few rows:")
            print(self.df.head())
            
            print(f"\nData info:")
            print(self.df.info())
            
            # Check for missing values
            print(f"\nMissing values per column:")
            print(self.df.isnull().sum())
            
            # Remove rows with NaN values
            self.df = self.df.dropna()
            print(f"\nData shape after removing NaN: {self.df.shape}")
            
            return True
            
        except Exception as e:
            print(f"Error loading data: {e}")
            return False
    
    def create_sample_data(self):
        """Create sample data if no file is provided"""
        print("Creating sample air quality data...")
        
        # Generate sample data similar to the original dataset
        np.random.seed(42)
        n_samples = 5000
        
        # Create datetime index
        date_range = pd.date_range(start='2020-01-01', periods=n_samples, freq='H')
        
        # Generate correlated pollutant data
        base_trend = np.sin(np.arange(n_samples) * 2 * np.pi / 24) * 20 + 50  # Daily pattern
        
        data = {
            'datetime': date_range,
            'PM2.5': np.maximum(base_trend + np.random.normal(0, 15, n_samples), 1),
            'PM10': np.maximum(base_trend * 1.5 + np.random.normal(0, 20, n_samples), 1),
            'SO2': np.maximum(base_trend * 0.3 + np.random.normal(0, 5, n_samples), 0.1),
            'NO2': np.maximum(base_trend * 0.8 + np.random.normal(0, 10, n_samples), 1),
            'CO': np.maximum(base_trend * 15 + np.random.normal(0, 200, n_samples), 100),
            'O3': np.maximum(base_trend * 0.7 + np.random.normal(0, 20, n_samples), 1),
            'TEMP': 20 + np.sin(np.arange(n_samples) * 2 * np.pi / 24) * 10 + np.random.normal(0, 3, n_samples),
            'PRES': 1013 + np.random.normal(0, 10, n_samples),
            'DEWP': 5 + np.random.normal(0, 8, n_samples),
            'RAIN': np.maximum(np.random.exponential(0.1, n_samples), 0),
            'WSPM': np.maximum(np.random.exponential(2, n_samples), 0)
        }
        
        self.df = pd.DataFrame(data)
        print(f"Sample data created! Shape: {self.df.shape}")
        print(f"Columns: {list(self.df.columns)}")
        
        return True
    
    def split_sequence(self, sequence, n_steps):
        """Split sequence into X and y for time series prediction"""
        X, y = [], []
        for i in range(len(sequence)):
            end_ix = i + n_steps
            if end_ix > len(sequence) - 1:
                break
            seq_x, seq_y = sequence[i:end_ix], sequence[end_ix]
            X.append(seq_x)
            y.append(seq_y)
        return np.array(X), np.array(y)
    
    def prepare_data(self, target_column='PM2.5', train_size=0.8):
        """Prepare data for LSTM model"""
        # Extract target variable
        data = self.df[target_column].values.reshape(-1, 1)
        
        # Remove zero values while maintaining 2D shape
        non_zero_mask = data.flatten() != 0
        data = data[non_zero_mask].reshape(-1, 1)
        
        # Split into train and test
        split_idx = int(len(data) * train_size)
        train_data = data[:split_idx]
        test_data = data[split_idx:]
        
        # Scale the data
        train_scaled = self.scaler.fit_transform(train_data)
        test_scaled = self.scaler.transform(test_data)
        
        # Create sequences
        self.X_train, self.y_train = self.split_sequence(train_scaled.flatten(), self.n_steps)
        self.X_test, self.y_test = self.split_sequence(test_scaled.flatten(), self.n_steps)
        
        # Reshape for LSTM
        self.X_train = self.X_train.reshape((self.X_train.shape[0], self.X_train.shape[1], self.n_features))
        self.X_test = self.X_test.reshape((self.X_test.shape[0], self.X_test.shape[1], self.n_features))
        
        print(f"Training data shape: X_train: {self.X_train.shape}, y_train: {self.y_train.shape}")
        print(f"Testing data shape: X_test: {self.X_test.shape}, y_test: {self.y_test.shape}")
        
        return True
    
    def build_model(self, lstm_units=50, dropout_rate=0.2):
        """Build LSTM model"""
        self.model = Sequential([
            LSTM(lstm_units, activation='relu', input_shape=(self.n_steps, self.n_features), return_sequences=True),
            Dropout(dropout_rate),
            LSTM(lstm_units//2, activation='relu'),
            Dropout(dropout_rate),
            Dense(25, activation='relu'),
            Dense(1)
        ])
        
        # Compile model
        self.model.compile(
            optimizer=Adam(learning_rate=0.001),
            loss='mse',
            metrics=['mae']
        )
        
        print("Model built successfully!")
        print(self.model.summary())
        
        return True
    
    def train_model(self, epochs=50, batch_size=32, validation_split=0.2):
        """Train the LSTM model"""
        # Callbacks
        early_stopping = EarlyStopping(
            monitor='val_loss',
            patience=10,
            restore_best_weights=True
        )
        
        # Train model
        print("Training model...")
        self.history = self.model.fit(
            self.X_train, self.y_train,
            epochs=epochs,
            batch_size=batch_size,
            validation_split=validation_split,
            callbacks=[early_stopping],
            verbose=1
        )
        
        print("Model training completed!")
        return True
    
    def evaluate_model(self):
        """Evaluate the model performance"""
        # Make predictions
        y_pred_train = self.model.predict(self.X_train)
        y_pred_test = self.model.predict(self.X_test)
        
        # Calculate metrics
        train_mse = mean_squared_error(self.y_train, y_pred_train)
        test_mse = mean_squared_error(self.y_test, y_pred_test)
        train_mae = mean_absolute_error(self.y_train, y_pred_train)
        test_mae = mean_absolute_error(self.y_test, y_pred_test)
        train_r2 = r2_score(self.y_train, y_pred_train)
        test_r2 = r2_score(self.y_test, y_pred_test)
        
        print(f"\nModel Performance:")
        print(f"Training MSE: {train_mse:.6f}")
        print(f"Testing MSE: {test_mse:.6f}")
        print(f"Training MAE: {train_mae:.6f}")
        print(f"Testing MAE: {test_mae:.6f}")
        print(f"Training R²: {train_r2:.6f}")
        print(f"Testing R²: {test_r2:.6f}")
        
        return y_pred_train, y_pred_test
    
    def plot_results(self, y_pred_train, y_pred_test):
        """Plot training history and predictions"""
        fig, axes = plt.subplots(2, 2, figsize=(15, 10))
        
        # Plot training history
        axes[0, 0].plot(self.history.history['loss'], label='Training Loss')
        axes[0, 0].plot(self.history.history['val_loss'], label='Validation Loss')
        axes[0, 0].set_title('Model Loss')
        axes[0, 0].set_xlabel('Epoch')
        axes[0, 0].set_ylabel('Loss')
        axes[0, 0].legend()
        axes[0, 0].grid(True)
        
        # Plot MAE
        axes[0, 1].plot(self.history.history['mae'], label='Training MAE')
        axes[0, 1].plot(self.history.history['val_mae'], label='Validation MAE')
        axes[0, 1].set_title('Model MAE')
        axes[0, 1].set_xlabel('Epoch')
        axes[0, 1].set_ylabel('MAE')
        axes[0, 1].legend()
        axes[0, 1].grid(True)
        
        # Plot predictions vs actual (training)
        axes[1, 0].scatter(self.y_train, y_pred_train, alpha=0.5)
        axes[1, 0].plot([self.y_train.min(), self.y_train.max()], 
                    [self.y_train.min(), self.y_train.max()], 'r--', lw=2)
        axes[1, 0].set_title('Training: Predicted vs Actual')
        axes[1, 0].set_xlabel('Actual')
        axes[1, 0].set_ylabel('Predicted')
        axes[1, 0].grid(True)
        
        # Plot predictions vs actual (testing)
        axes[1, 1].scatter(self.y_test, y_pred_test, alpha=0.5)
        axes[1, 1].plot([self.y_test.min(), self.y_test.max()], 
                    [self.y_test.min(), self.y_test.max()], 'r--', lw=2)
        axes[1, 1].set_title('Testing: Predicted vs Actual')
        axes[1, 1].set_xlabel('Actual')
        axes[1, 1].set_ylabel('Predicted')
        axes[1, 1].grid(True)
        
        plt.tight_layout()
        plt.show()
    
    def plot_time_series(self, y_pred_test, n_points=200):
        """Plot time series comparison"""
        plt.figure(figsize=(12, 6))
        
        # Plot only a subset for clarity
        end_idx = min(n_points, len(self.y_test))
        
        plt.plot(range(end_idx), self.y_test[:end_idx], label='Actual', linewidth=2)
        plt.plot(range(end_idx), y_pred_test[:end_idx], label='Predicted', linewidth=2)
        plt.title('Time Series Prediction Comparison')
        plt.xlabel('Time Steps')
        plt.ylabel('Normalized Values')
        plt.legend()
        plt.grid(True, alpha=0.3)
        plt.show()
    
    def visualize_data(self):
        """Create data visualizations"""
        # Select numeric columns for visualization
        numeric_cols = self.df.select_dtypes(include=[np.number]).columns
        
        # Correlation heatmap
        plt.figure(figsize=(12, 8))
        correlation_matrix = self.df[numeric_cols].corr()
        sns.heatmap(correlation_matrix, annot=True, cmap='coolwarm', center=0, 
                square=True, linewidths=0.5)
        plt.title('Correlation Heatmap of Air Quality Parameters')
        plt.tight_layout()
        plt.show()
        
        # Distribution plots
        n_cols = 3
        n_rows = (len(numeric_cols) + n_cols - 1) // n_cols
        
        fig, axes = plt.subplots(n_rows, n_cols, figsize=(15, 4*n_rows))
        axes = axes.flatten() if n_rows > 1 else [axes]
        
        for i, col in enumerate(numeric_cols):
            if i < len(axes):
                axes[i].hist(self.df[col], bins=30, alpha=0.7, edgecolor='black')
                axes[i].set_title(f'Distribution of {col}')
                axes[i].set_xlabel(col)
                axes[i].set_ylabel('Frequency')
                axes[i].grid(True, alpha=0.3)
        
        # Hide empty subplots
        for i in range(len(numeric_cols), len(axes)):
            axes[i].set_visible(False)
        
        plt.tight_layout()
        plt.show()
        
    
    def predict_future(self, n_future_steps=24):
        """Predict future values"""
        # Use last sequence from test data
        last_sequence = self.X_test[-1].reshape(1, self.n_steps, self.n_features)
        
        predictions = []
        current_sequence = last_sequence.copy()
        
        for _ in range(n_future_steps):
            # Predict next value
            next_pred = self.model.predict(current_sequence, verbose=0)
            predictions.append(next_pred[0, 0])
            
            # Update sequence for next prediction
            current_sequence = np.roll(current_sequence, -1, axis=1)
            current_sequence[0, -1, 0] = next_pred[0, 0]
        
        # Transform back to original scale
        predictions = np.array(predictions).reshape(-1, 1)
        predictions_original = self.scaler.inverse_transform(predictions)
        
        return predictions_original.flatten()

def main():
    # Initialize predictor
    predictor = AQIPredictor(n_steps=3, n_features=1)
    
    # Load data for a specific city (example: Delhi)
    print("Loading data...")
    success = predictor.load_data(station_city="Delhi")
    
    if not success:
        print("Could not load data for Delhi, creating sample data...")
        predictor.create_sample_data()
    
    # Visualize data
    print("\nCreating data visualizations...")
    predictor.visualize_data()
    
    # Prepare data
    print("\nPreparing data for LSTM...")
    predictor.prepare_data(target_column='PM2.5', train_size=0.8)
    
    # Build model
    print("\nBuilding LSTM model...")
    predictor.build_model(lstm_units=50, dropout_rate=0.2)
    
    # Train model
    print("\nTraining model...")
    predictor.train_model(epochs=50, batch_size=32, validation_split=0.2)
    
    # Evaluate model
    print("\nEvaluating model...")
    y_pred_train, y_pred_test = predictor.evaluate_model()
    
    # Plot results
    print("\nPlotting results...")
    predictor.plot_results(y_pred_train, y_pred_test)
    
    # Plot time series
    predictor.plot_time_series(y_pred_test)
    
    # Predict future values
    print("\nPredicting future values...")
    future_predictions = predictor.predict_future(n_future_steps=24)
    
    plt.figure(figsize=(10, 6))
    plt.plot(range(len(future_predictions)), future_predictions, 'ro-', linewidth=2)
    plt.title('Future PM2.5 Predictions (Next 24 Hours)')
    plt.xlabel('Hours')
    plt.ylabel('PM2.5 Concentration')
    plt.grid(True, alpha=0.3)
    plt.show()
    
    print(f"\nFuture predictions for next 24 hours:")
    for i, pred in enumerate(future_predictions):
        print(f"Hour {i+1}: {pred:.2f}")

if __name__ == "__main__":
    main()