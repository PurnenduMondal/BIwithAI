import pandas as pd
import numpy as np
from typing import Dict, List, Any, Optional
import logging
from datetime import datetime, timedelta

try:
    from prophet import Prophet
    PROPHET_AVAILABLE = True
except ImportError:
    PROPHET_AVAILABLE = False
    logging.warning("Prophet not installed. Forecasting will use simple methods only.")

from sklearn.linear_model import LinearRegression
from scipy import stats

logger = logging.getLogger(__name__)

class ForecastingService:
    """Service for time series forecasting and prediction"""
    
    def __init__(self):
        self.prophet_available = PROPHET_AVAILABLE
    
    async def forecast(
        self,
        df: pd.DataFrame,
        time_col: str,
        metric_col: str,
        periods: int = 30,
        method: str = "auto",
        confidence_interval: float = 0.95
    ) -> Dict[str, Any]:
        """
        Generate forecast for time series data
        
        Args:
            df: DataFrame with time series data
            time_col: Name of datetime column
            metric_col: Name of metric to forecast
            periods: Number of periods to forecast
            method: Forecasting method ('auto', 'prophet', 'linear', 'moving_average', 'exponential')
            confidence_interval: Confidence level (0.80, 0.90, 0.95, 0.99)
        
        Returns:
            Dictionary containing forecast results
        """
        try:
            # Validate inputs
            if time_col not in df.columns:
                raise ValueError(f"Time column '{time_col}' not found in DataFrame")
            
            if metric_col not in df.columns:
                raise ValueError(f"Metric column '{metric_col}' not found in DataFrame")
            
            # Prepare data
            df_clean = self._prepare_data(df, time_col, metric_col)
            
            if len(df_clean) < 3:
                raise ValueError("Insufficient data points for forecasting (minimum 3 required)")
            
            # Select forecasting method
            if method == "auto":
                method = self._select_best_method(df_clean, time_col, metric_col)
            
            # Generate forecast based on method
            if method == "prophet" and self.prophet_available:
                result = await self._forecast_prophet(df_clean, time_col, metric_col, periods, confidence_interval)
            elif method == "linear":
                result = await self._forecast_linear(df_clean, time_col, metric_col, periods, confidence_interval)
            elif method == "moving_average":
                result = await self._forecast_moving_average(df_clean, time_col, metric_col, periods, confidence_interval)
            elif method == "exponential":
                result = await self._forecast_exponential(df_clean, time_col, metric_col, periods, confidence_interval)
            else:
                # Fallback to linear regression
                logger.warning(f"Method '{method}' not available, falling back to linear regression")
                result = await self._forecast_linear(df_clean, time_col, metric_col, periods, confidence_interval)
            
            # Add metadata
            result['metadata'] = {
                'method': method,
                'periods': periods,
                'confidence_interval': confidence_interval,
                'historical_points': len(df_clean),
                'forecast_points': len(result['forecast']),
                'generated_at': datetime.utcnow().isoformat()
            }
            
            return result
        
        except Exception as e:
            logger.error(f"Error in forecasting: {str(e)}", exc_info=True)
            raise
    
    def _prepare_data(
        self,
        df: pd.DataFrame,
        time_col: str,
        metric_col: str
    ) -> pd.DataFrame:
        """Prepare and clean data for forecasting"""
        # Create copy
        df_clean = df[[time_col, metric_col]].copy()
        
        # Remove rows with null values
        df_clean = df_clean.dropna()
        
        # Ensure datetime
        if not pd.api.types.is_datetime64_any_dtype(df_clean[time_col]):
            df_clean[time_col] = pd.to_datetime(df_clean[time_col])
        
        # Sort by time
        df_clean = df_clean.sort_values(time_col)
        
        # Remove duplicates (keep last)
        df_clean = df_clean.drop_duplicates(subset=[time_col], keep='last')
        
        return df_clean
    
    def _select_best_method(
        self,
        df: pd.DataFrame,
        time_col: str,
        metric_col: str
    ) -> str:
        """Automatically select best forecasting method"""
        data_points = len(df)
        
        # Check for seasonality
        has_seasonality = self._detect_seasonality(df[metric_col])
        
        # Decision logic
        if data_points >= 20 and self.prophet_available and has_seasonality:
            return "prophet"
        elif data_points >= 10:
            return "linear"
        else:
            return "moving_average"
    
    def _detect_seasonality(self, series: pd.Series) -> bool:
        """Detect if time series has seasonality"""
        if len(series) < 14:
            return False
        
        try:
            # Simple autocorrelation check
            autocorr_7 = series.autocorr(lag=7)
            autocorr_30 = series.autocorr(lag=min(30, len(series) // 2))
            
            return abs(autocorr_7) > 0.5 or abs(autocorr_30) > 0.5
        except Exception:
            return False
    
    async def _forecast_prophet(
        self,
        df: pd.DataFrame,
        time_col: str,
        metric_col: str,
        periods: int,
        confidence_interval: float
    ) -> Dict[str, Any]:
        """Forecast using Facebook Prophet"""
        if not PROPHET_AVAILABLE:
            raise ImportError("Prophet is not installed. Install with: pip install prophet")
        
        # Prepare data for Prophet (requires 'ds' and 'y' columns)
        prophet_df = pd.DataFrame({
            'ds': df[time_col],
            'y': df[metric_col]
        })
        
        # Create and fit model
        model = Prophet(
            interval_width=confidence_interval,
            daily_seasonality=False,
            weekly_seasonality='auto',
            yearly_seasonality='auto'
        )
        
        model.fit(prophet_df)
        
        # Create future dataframe
        future = model.make_future_dataframe(periods=periods)
        
        # Generate forecast
        forecast = model.predict(future)
        
        # Extract results
        historical = []
        for idx, row in prophet_df.iterrows():
            historical.append({
                'date': row['ds'].isoformat(),
                'actual': float(row['y'])
            })
        
        forecast_results = []
        future_forecast = forecast.tail(periods)
        
        for idx, row in future_forecast.iterrows():
            forecast_results.append({
                'date': row['ds'].isoformat(),
                'forecast': float(row['yhat']),
                'lower_bound': float(row['yhat_lower']),
                'upper_bound': float(row['yhat_upper'])
            })
        
        # Calculate accuracy metrics on historical data
        historical_forecast = forecast.head(len(prophet_df))
        accuracy = self._calculate_accuracy_metrics(
            prophet_df['y'].values,
            historical_forecast['yhat'].values
        )
        
        return {
            'historical': historical,
            'forecast': forecast_results,
            'accuracy': accuracy,
            'trend': self._determine_trend(forecast_results)
        }
    
    async def _forecast_linear(
        self,
        df: pd.DataFrame,
        time_col: str,
        metric_col: str,
        periods: int,
        confidence_interval: float
    ) -> Dict[str, Any]:
        """Forecast using linear regression"""
        # Convert dates to numeric (days since first date)
        df = df.copy()
        df['days'] = (df[time_col] - df[time_col].min()).dt.total_seconds() / 86400
        
        X = df['days'].values.reshape(-1, 1)
        y = df[metric_col].values
        
        # Fit linear regression
        model = LinearRegression()
        model.fit(X, y)
        
        # Calculate residuals for confidence intervals
        y_pred = model.predict(X)
        residuals = y - y_pred
        std_error = np.std(residuals)
        
        # Z-score for confidence interval
        z_scores = {0.80: 1.28, 0.90: 1.645, 0.95: 1.96, 0.99: 2.576}
        z = z_scores.get(confidence_interval, 1.96)
        
        # Historical data
        historical = []
        for idx, row in df.iterrows():
            historical.append({
                'date': row[time_col].isoformat(),
                'actual': float(row[metric_col])
            })
        
        # Generate future dates
        last_date = df[time_col].max()
        freq = self._infer_frequency(df[time_col])
        future_dates = pd.date_range(
            start=last_date + freq,
            periods=periods,
            freq=freq
        )
        
        # Generate forecast
        forecast_results = []
        last_days = df['days'].max()
        
        for i, future_date in enumerate(future_dates):
            days = last_days + (i + 1) * (freq.total_seconds() / 86400)
            forecast_value = model.predict([[days]])[0]
            
            # Confidence interval (increases with distance from training data)
            margin = z * std_error * np.sqrt(1 + 1/len(X) + ((days - X.mean())**2) / np.sum((X - X.mean())**2))
            
            forecast_results.append({
                'date': future_date.isoformat(),
                'forecast': float(forecast_value),
                'lower_bound': float(forecast_value - margin),
                'upper_bound': float(forecast_value + margin)
            })
        
        # Calculate accuracy
        accuracy = self._calculate_accuracy_metrics(y, y_pred)
        
        return {
            'historical': historical,
            'forecast': forecast_results,
            'accuracy': accuracy,
            'trend': self._determine_trend(forecast_results),
            'model_params': {
                'slope': float(model.coef_[0]),
                'intercept': float(model.intercept_),
                'r_squared': float(model.score(X, y))
            }
        }
    
    async def _forecast_moving_average(
        self,
        df: pd.DataFrame,
        time_col: str,
        metric_col: str,
        periods: int,
        confidence_interval: float
    ) -> Dict[str, Any]:
        """Forecast using moving average"""
        window = min(7, len(df) // 2)  # Use 7-day window or half the data
        
        # Calculate moving average
        df = df.copy()
        df['ma'] = df[metric_col].rolling(window=window, min_periods=1).mean()
        
        # Calculate standard deviation for confidence intervals
        df['ma_std'] = df[metric_col].rolling(window=window, min_periods=1).std()
        
        # Z-score
        z_scores = {0.80: 1.28, 0.90: 1.645, 0.95: 1.96, 0.99: 2.576}
        z = z_scores.get(confidence_interval, 1.96)
        
        # Historical
        historical = []
        for idx, row in df.iterrows():
            historical.append({
                'date': row[time_col].isoformat(),
                'actual': float(row[metric_col])
            })
        
        # Use last moving average as forecast
        last_ma = df['ma'].iloc[-1]
        last_std = df['ma_std'].iloc[-1] if not pd.isna(df['ma_std'].iloc[-1]) else df[metric_col].std()
        
        # Generate future dates
        last_date = df[time_col].max()
        freq = self._infer_frequency(df[time_col])
        future_dates = pd.date_range(
            start=last_date + freq,
            periods=periods,
            freq=freq
        )
        
        # Generate forecast
        forecast_results = []
        for future_date in future_dates:
            margin = z * last_std
            
            forecast_results.append({
                'date': future_date.isoformat(),
                'forecast': float(last_ma),
                'lower_bound': float(last_ma - margin),
                'upper_bound': float(last_ma + margin)
            })
        
        # Calculate accuracy
        accuracy = self._calculate_accuracy_metrics(
            df[metric_col].values,
            df['ma'].values
        )
        
        return {
            'historical': historical,
            'forecast': forecast_results,
            'accuracy': accuracy,
            'trend': 'stable',
            'model_params': {
                'window': window,
                'last_ma': float(last_ma)
            }
        }
    
    async def _forecast_exponential(
        self,
        df: pd.DataFrame,
        time_col: str,
        metric_col: str,
        periods: int,
        confidence_interval: float
    ) -> Dict[str, Any]:
        """Forecast using exponential smoothing"""
        alpha = 0.3  # Smoothing parameter
        
        df = df.copy()
        values = df[metric_col].values
        
        # Calculate exponential moving average
        ema = [values[0]]
        for i in range(1, len(values)):
            ema.append(alpha * values[i] + (1 - alpha) * ema[-1])
        
        df['ema'] = ema
        
        # Calculate residuals for confidence intervals
        residuals = values - np.array(ema)
        std_error = np.std(residuals)
        
        z_scores = {0.80: 1.28, 0.90: 1.645, 0.95: 1.96, 0.99: 2.576}
        z = z_scores.get(confidence_interval, 1.96)
        
        # Historical
        historical = []
        for idx, row in df.iterrows():
            historical.append({
                'date': row[time_col].isoformat(),
                'actual': float(row[metric_col])
            })
        
        # Forecast
        last_ema = ema[-1]
        
        last_date = df[time_col].max()
        freq = self._infer_frequency(df[time_col])
        future_dates = pd.date_range(
            start=last_date + freq,
            periods=periods,
            freq=freq
        )
        
        forecast_results = []
        for future_date in future_dates:
            margin = z * std_error
            
            forecast_results.append({
                'date': future_date.isoformat(),
                'forecast': float(last_ema),
                'lower_bound': float(last_ema - margin),
                'upper_bound': float(last_ema + margin)
            })
        
        # Calculate accuracy
        accuracy = self._calculate_accuracy_metrics(values, np.array(ema))
        
        return {
            'historical': historical,
            'forecast': forecast_results,
            'accuracy': accuracy,
            'trend': self._determine_trend(forecast_results),
            'model_params': {
                'alpha': alpha,
                'last_ema': float(last_ema)
            }
        }
    
    def _infer_frequency(self, time_series: pd.Series) -> pd.Timedelta:
        """Infer frequency from time series"""
        if len(time_series) < 2:
            return pd.Timedelta(days=1)
        
        # Calculate median time difference
        diffs = time_series.diff().dropna()
        median_diff = diffs.median()
        
        # Round to common frequencies
        if median_diff < pd.Timedelta(hours=2):
            return pd.Timedelta(hours=1)
        elif median_diff < pd.Timedelta(days=1):
            return pd.Timedelta(days=1)
        elif median_diff < pd.Timedelta(days=8):
            return pd.Timedelta(days=7)
        elif median_diff < pd.Timedelta(days=40):
            return pd.Timedelta(days=30)
        else:
            return pd.Timedelta(days=365)
    
    def _calculate_accuracy_metrics(
        self,
        actual: np.ndarray,
        predicted: np.ndarray
    ) -> Dict[str, float]:
        """Calculate forecast accuracy metrics"""
        # Remove any NaN values
        mask = ~(np.isnan(actual) | np.isnan(predicted))
        actual = actual[mask]
        predicted = predicted[mask]
        
        if len(actual) == 0:
            return {
                'mae': 0.0,
                'rmse': 0.0,
                'mape': 0.0,
                'r_squared': 0.0
            }
        
        # Mean Absolute Error
        mae = np.mean(np.abs(actual - predicted))
        
        # Root Mean Squared Error
        rmse = np.sqrt(np.mean((actual - predicted) ** 2))
        
        # Mean Absolute Percentage Error
        # Avoid division by zero
        non_zero_mask = actual != 0
        if non_zero_mask.any():
            mape = np.mean(np.abs((actual[non_zero_mask] - predicted[non_zero_mask]) / actual[non_zero_mask])) * 100
        else:
            mape = 0.0
        
        # R-squared
        ss_res = np.sum((actual - predicted) ** 2)
        ss_tot = np.sum((actual - np.mean(actual)) ** 2)
        r_squared = 1 - (ss_res / ss_tot) if ss_tot != 0 else 0.0
        
        return {
            'mae': float(mae),
            'rmse': float(rmse),
            'mape': float(mape),
            'r_squared': float(r_squared)
        }
    
    def _determine_trend(self, forecast_data: List[Dict]) -> str:
        """Determine overall trend from forecast"""
        if len(forecast_data) < 2:
            return "stable"
        
        first_value = forecast_data[0]['forecast']
        last_value = forecast_data[-1]['forecast']
        
        change_pct = ((last_value - first_value) / abs(first_value)) * 100 if first_value != 0 else 0
        
        if change_pct > 5:
            return "increasing"
        elif change_pct < -5:
            return "decreasing"
        else:
            return "stable"
    
    async def detect_anomalies(
        self,
        df: pd.DataFrame,
        time_col: str,
        metric_col: str,
        sensitivity: float = 2.0
    ) -> List[Dict[str, Any]]:
        """
        Detect anomalies in time series data
        
        Args:
            df: DataFrame with time series data
            time_col: Name of datetime column
            metric_col: Name of metric column
            sensitivity: Number of standard deviations for threshold (default 2.0)
        
        Returns:
            List of anomalies with dates and values
        """
        df_clean = self._prepare_data(df, time_col, metric_col)
        
        # Calculate rolling statistics
        window = min(7, len(df_clean) // 3)
        df_clean['rolling_mean'] = df_clean[metric_col].rolling(window=window, center=True).mean()
        df_clean['rolling_std'] = df_clean[metric_col].rolling(window=window, center=True).std()
        
        # Forward/backward fill NaN values
        df_clean['rolling_mean'].fillna(method='bfill', inplace=True)
        df_clean['rolling_mean'].fillna(method='ffill', inplace=True)
        df_clean['rolling_std'].fillna(df_clean[metric_col].std(), inplace=True)
        
        # Detect anomalies
        df_clean['lower_bound'] = df_clean['rolling_mean'] - (sensitivity * df_clean['rolling_std'])
        df_clean['upper_bound'] = df_clean['rolling_mean'] + (sensitivity * df_clean['rolling_std'])
        
        df_clean['is_anomaly'] = (
            (df_clean[metric_col] < df_clean['lower_bound']) |
            (df_clean[metric_col] > df_clean['upper_bound'])
        )
        
        # Extract anomalies
        anomalies = []
        for idx, row in df_clean[df_clean['is_anomaly']].iterrows():
            anomaly_type = 'high' if row[metric_col] > row['upper_bound'] else 'low'
            deviation = abs(row[metric_col] - row['rolling_mean']) / row['rolling_std'] if row['rolling_std'] > 0 else 0
            
            anomalies.append({
                'date': row[time_col].isoformat(),
                'value': float(row[metric_col]),
                'expected_value': float(row['rolling_mean']),
                'type': anomaly_type,
                'deviation_score': float(deviation),
                'lower_bound': float(row['lower_bound']),
                'upper_bound': float(row['upper_bound'])
            })
        
        return anomalies
    
    async def calculate_trend_strength(
        self,
        df: pd.DataFrame,
        time_col: str,
        metric_col: str
    ) -> Dict[str, Any]:
        """
        Calculate trend strength and characteristics
        
        Returns:
            Dictionary with trend analysis
        """
        df_clean = self._prepare_data(df, time_col, metric_col)
        
        # Convert to numeric days
        df_clean['days'] = (df_clean[time_col] - df_clean[time_col].min()).dt.total_seconds() / 86400
        
        X = df_clean['days'].values.reshape(-1, 1)
        y = df_clean[metric_col].values
        
        # Linear regression
        model = LinearRegression()
        model.fit(X, y)
        
        # Calculate R-squared
        r_squared = model.score(X, y)
        
        # Determine trend direction and strength
        slope = model.coef_[0]
        
        if slope > 0:
            direction = "increasing"
        elif slope < 0:
            direction = "decreasing"
        else:
            direction = "stable"
        
        # Trend strength based on R-squared
        if r_squared > 0.7:
            strength = "strong"
        elif r_squared > 0.4:
            strength = "moderate"
        else:
            strength = "weak"
        
        # Calculate percentage change
        first_value = y[0]
        last_value = y[-1]
        pct_change = ((last_value - first_value) / abs(first_value)) * 100 if first_value != 0 else 0
        
        return {
            'direction': direction,
            'strength': strength,
            'slope': float(slope),
            'r_squared': float(r_squared),
            'percentage_change': float(pct_change),
            'start_value': float(first_value),
            'end_value': float(last_value),
            'time_period_days': float(df_clean['days'].max())
        }