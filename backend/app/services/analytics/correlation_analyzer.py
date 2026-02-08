import pandas as pd
import numpy as np
from typing import Dict, List, Any, Optional, Tuple
from scipy import stats
from scipy.cluster import hierarchy
from sklearn.preprocessing import StandardScaler
import logging

logger = logging.getLogger(__name__)

class CorrelationAnalyzer:
    """Service for analyzing correlations between metrics"""
    
    def __init__(self):
        self.scaler = StandardScaler()
    
    async def analyze(
        self,
        df: pd.DataFrame,
        method: str = "pearson",
        min_correlation: float = 0.0,
        max_p_value: float = 0.05
    ) -> Dict[str, Any]:
        """
        Analyze correlations between all numeric columns in DataFrame
        
        Args:
            df: DataFrame with numeric columns to analyze
            method: Correlation method ('pearson', 'spearman', 'kendall')
            min_correlation: Minimum absolute correlation to report
            max_p_value: Maximum p-value for statistical significance
        
        Returns:
            Dictionary containing correlation analysis results
        """
        try:
            # Validate input
            if df.empty:
                raise ValueError("DataFrame is empty")
            
            # Select only numeric columns
            numeric_df = df.select_dtypes(include=[np.number])
            
            if numeric_df.empty:
                raise ValueError("No numeric columns found in DataFrame")
            
            # Remove columns with all NaN or constant values
            numeric_df = self._clean_data(numeric_df)
            
            if len(numeric_df.columns) < 2:
                raise ValueError("Need at least 2 numeric columns for correlation analysis")
            
            # Calculate correlation matrix
            corr_matrix, p_value_matrix = self._calculate_correlations(
                numeric_df,
                method
            )
            
            # Find significant correlations
            significant_pairs = self._find_significant_correlations(
                corr_matrix,
                p_value_matrix,
                min_correlation,
                max_p_value
            )
            
            # Identify correlation clusters
            clusters = self._identify_clusters(corr_matrix)
            
            # Calculate partial correlations
            partial_corr = self._calculate_partial_correlations(numeric_df)
            
            # Detect multicollinearity
            vif_scores = self._calculate_vif(numeric_df)
            
            return {
                'correlation_matrix': corr_matrix.to_dict(),
                'p_value_matrix': p_value_matrix.to_dict(),
                'significant_pairs': significant_pairs,
                'clusters': clusters,
                'partial_correlations': partial_corr,
                'vif_scores': vif_scores,
                'method': method,
                'num_variables': len(numeric_df.columns),
                'num_observations': len(numeric_df),
                'metadata': {
                    'columns': list(numeric_df.columns),
                    'min_correlation_threshold': min_correlation,
                    'max_p_value_threshold': max_p_value
                }
            }
        
        except Exception as e:
            logger.error(f"Error in correlation analysis: {str(e)}", exc_info=True)
            raise
    
    def _clean_data(self, df: pd.DataFrame) -> pd.DataFrame:
        """Clean data for correlation analysis"""
        cleaned_df = df.copy()
        
        # Remove columns with all NaN
        cleaned_df = cleaned_df.dropna(axis=1, how='all')
        
        # Remove columns with constant values (std = 0)
        std_values = cleaned_df.std()
        cleaned_df = cleaned_df.loc[:, std_values > 0]
        
        # Fill remaining NaN with column mean
        cleaned_df = cleaned_df.fillna(cleaned_df.mean())
        
        return cleaned_df
    
    def _calculate_correlations(
        self,
        df: pd.DataFrame,
        method: str
    ) -> Tuple[pd.DataFrame, pd.DataFrame]:
        """Calculate correlation and p-value matrices"""
        n = len(df.columns)
        corr_matrix = pd.DataFrame(
            np.zeros((n, n)),
            index=df.columns,
            columns=df.columns
        )
        p_value_matrix = pd.DataFrame(
            np.ones((n, n)),
            index=df.columns,
            columns=df.columns
        )
        
        for i, col1 in enumerate(df.columns):
            for j, col2 in enumerate(df.columns):
                if i == j:
                    corr_matrix.iloc[i, j] = 1.0
                    p_value_matrix.iloc[i, j] = 0.0
                elif i < j:
                    # Calculate correlation
                    if method == 'pearson':
                        corr, p_value = stats.pearsonr(df[col1], df[col2])
                    elif method == 'spearman':
                        corr, p_value = stats.spearmanr(df[col1], df[col2])
                    elif method == 'kendall':
                        corr, p_value = stats.kendalltau(df[col1], df[col2])
                    else:
                        raise ValueError(f"Unknown correlation method: {method}")
                    
                    corr_matrix.iloc[i, j] = corr
                    corr_matrix.iloc[j, i] = corr
                    p_value_matrix.iloc[i, j] = p_value
                    p_value_matrix.iloc[j, i] = p_value
        
        return corr_matrix, p_value_matrix
    
    def _find_significant_correlations(
        self,
        corr_matrix: pd.DataFrame,
        p_value_matrix: pd.DataFrame,
        min_correlation: float,
        max_p_value: float
    ) -> List[Dict[str, Any]]:
        """Find statistically significant correlation pairs"""
        significant_pairs = []
        
        columns = corr_matrix.columns
        for i in range(len(columns)):
            for j in range(i + 1, len(columns)):
                corr = corr_matrix.iloc[i, j]
                p_value = p_value_matrix.iloc[i, j]
                
                if abs(corr) >= min_correlation and p_value <= max_p_value:
                    # Determine correlation strength
                    abs_corr = abs(corr)
                    if abs_corr >= 0.7:
                        strength = "strong"
                    elif abs_corr >= 0.4:
                        strength = "moderate"
                    else:
                        strength = "weak"
                    
                    # Determine direction
                    direction = "positive" if corr > 0 else "negative"
                    
                    significant_pairs.append({
                        'variable1': columns[i],
                        'variable2': columns[j],
                        'correlation': float(corr),
                        'p_value': float(p_value),
                        'strength': strength,
                        'direction': direction,
                        'is_significant': True
                    })
        
        # Sort by absolute correlation (descending)
        significant_pairs.sort(key=lambda x: abs(x['correlation']), reverse=True)
        
        return significant_pairs
    
    def _identify_clusters(self, corr_matrix: pd.DataFrame) -> List[Dict[str, Any]]:
        """Identify clusters of highly correlated variables using hierarchical clustering"""
        try:
            # Convert correlation to distance
            distance_matrix = 1 - abs(corr_matrix)
            
            # Perform hierarchical clustering
            linkage_matrix = hierarchy.linkage(
                distance_matrix.values[np.triu_indices_from(distance_matrix.values, k=1)],
                method='average'
            )
            
            # Cut tree to form clusters (using correlation threshold of 0.7)
            cluster_labels = hierarchy.fcluster(
                linkage_matrix,
                t=0.3,  # distance threshold (1 - 0.7 correlation)
                criterion='distance'
            )
            
            # Organize variables into clusters
            clusters = {}
            for idx, label in enumerate(cluster_labels):
                if label not in clusters:
                    clusters[label] = []
                clusters[label].append(corr_matrix.columns[idx])
            
            # Format output
            cluster_list = []
            for cluster_id, variables in clusters.items():
                if len(variables) > 1:  # Only include clusters with multiple variables
                    # Calculate average correlation within cluster
                    cluster_corrs = []
                    for i in range(len(variables)):
                        for j in range(i + 1, len(variables)):
                            cluster_corrs.append(
                                abs(corr_matrix.loc[variables[i], variables[j]])
                            )
                    
                    avg_correlation = np.mean(cluster_corrs) if cluster_corrs else 0
                    
                    cluster_list.append({
                        'cluster_id': int(cluster_id),
                        'variables': variables,
                        'size': len(variables),
                        'avg_correlation': float(avg_correlation)
                    })
            
            # Sort by cluster size
            cluster_list.sort(key=lambda x: x['size'], reverse=True)
            
            return cluster_list
        
        except Exception as e:
            logger.warning(f"Error in clustering: {str(e)}")
            return []
    
    def _calculate_partial_correlations(
        self,
        df: pd.DataFrame
    ) -> Dict[str, Any]:
        """Calculate partial correlations (correlation controlling for other variables)"""
        try:
            columns = df.columns.tolist()
            partial_corr_matrix = {}
            
            # Only calculate for first few variable pairs to avoid computational overhead
            max_pairs = min(10, len(columns) * (len(columns) - 1) // 2)
            pair_count = 0
            
            for i in range(len(columns)):
                for j in range(i + 1, len(columns)):
                    if pair_count >= max_pairs:
                        break
                    
                    var1 = columns[i]
                    var2 = columns[j]
                    
                    # Variables to control for
                    control_vars = [col for col in columns if col not in [var1, var2]]
                    
                    if control_vars:
                        # Calculate partial correlation
                        partial_corr = self._partial_correlation(
                            df[var1],
                            df[var2],
                            df[control_vars]
                        )
                        
                        partial_corr_matrix[f"{var1}_{var2}"] = {
                            'variable1': var1,
                            'variable2': var2,
                            'partial_correlation': float(partial_corr),
                            'controlled_for': control_vars
                        }
                    
                    pair_count += 1
            
            return partial_corr_matrix
        
        except Exception as e:
            logger.warning(f"Error calculating partial correlations: {str(e)}")
            return {}
    
    def _partial_correlation(
        self,
        x: pd.Series,
        y: pd.Series,
        z: pd.DataFrame
    ) -> float:
        """Calculate partial correlation between x and y, controlling for z"""
        try:
            # Residualize x and y against z
            from sklearn.linear_model import LinearRegression
            
            model_x = LinearRegression()
            model_y = LinearRegression()
            
            model_x.fit(z, x)
            model_y.fit(z, y)
            
            residual_x = x - model_x.predict(z)
            residual_y = y - model_y.predict(z)
            
            # Calculate correlation of residuals
            partial_corr, _ = stats.pearsonr(residual_x, residual_y)
            
            return partial_corr
        
        except Exception as e:
            logger.warning(f"Error in partial correlation calculation: {str(e)}")
            return 0.0
    
    def _calculate_vif(self, df: pd.DataFrame) -> Dict[str, float]:
        """
        Calculate Variance Inflation Factor (VIF) to detect multicollinearity
        VIF > 10 indicates high multicollinearity
        """
        try:
            from sklearn.linear_model import LinearRegression
            
            vif_scores = {}
            columns = df.columns.tolist()
            
            for i, col in enumerate(columns):
                # Use all other columns as predictors
                X = df.drop(columns=[col])
                y = df[col]
                
                # Fit model
                model = LinearRegression()
                model.fit(X, y)
                
                # Calculate R-squared
                r_squared = model.score(X, y)
                
                # Calculate VIF
                if r_squared < 1.0:
                    vif = 1 / (1 - r_squared)
                else:
                    vif = float('inf')
                
                vif_scores[col] = float(vif)
            
            return vif_scores
        
        except Exception as e:
            logger.warning(f"Error calculating VIF: {str(e)}")
            return {}
    
    async def analyze_time_lagged_correlations(
        self,
        df: pd.DataFrame,
        time_col: str,
        metric1: str,
        metric2: str,
        max_lag: int = 10
    ) -> Dict[str, Any]:
        """
        Analyze time-lagged correlations between two metrics
        Useful for finding leading/lagging indicators
        
        Args:
            df: DataFrame with time series data
            time_col: Name of time column
            metric1: First metric
            metric2: Second metric
            max_lag: Maximum number of time periods to lag
        
        Returns:
            Dictionary with lagged correlation analysis
        """
        try:
            # Sort by time
            df_sorted = df.sort_values(time_col).copy()
            
            # Calculate correlations at different lags
            lagged_correlations = []
            
            for lag in range(-max_lag, max_lag + 1):
                if lag == 0:
                    # No lag
                    corr, p_value = stats.pearsonr(
                        df_sorted[metric1],
                        df_sorted[metric2]
                    )
                elif lag > 0:
                    # metric2 is lagged (metric1 leads metric2)
                    corr, p_value = stats.pearsonr(
                        df_sorted[metric1].iloc[:-lag],
                        df_sorted[metric2].iloc[lag:]
                    )
                else:
                    # metric1 is lagged (metric2 leads metric1)
                    abs_lag = abs(lag)
                    corr, p_value = stats.pearsonr(
                        df_sorted[metric1].iloc[abs_lag:],
                        df_sorted[metric2].iloc[:-abs_lag]
                    )
                
                lagged_correlations.append({
                    'lag': lag,
                    'correlation': float(corr),
                    'p_value': float(p_value),
                    'is_significant': p_value < 0.05
                })
            
            # Find best lag
            best_lag = max(lagged_correlations, key=lambda x: abs(x['correlation']))
            
            # Determine relationship
            if best_lag['lag'] > 0:
                relationship = f"{metric1} leads {metric2} by {best_lag['lag']} periods"
            elif best_lag['lag'] < 0:
                relationship = f"{metric2} leads {metric1} by {abs(best_lag['lag'])} periods"
            else:
                relationship = f"{metric1} and {metric2} are contemporaneously correlated"
            
            return {
                'metric1': metric1,
                'metric2': metric2,
                'lagged_correlations': lagged_correlations,
                'best_lag': best_lag,
                'relationship': relationship,
                'max_lag_tested': max_lag
            }
        
        except Exception as e:
            logger.error(f"Error in lagged correlation analysis: {str(e)}", exc_info=True)
            raise
    
    async def detect_spurious_correlations(
        self,
        df: pd.DataFrame,
        corr_matrix: pd.DataFrame,
        p_value_matrix: pd.DataFrame,
        min_correlation: float = 0.7
    ) -> List[Dict[str, Any]]:
        """
        Detect potentially spurious correlations
        (high correlation but no logical causation)
        """
        suspicious_pairs = []
        
        columns = corr_matrix.columns
        for i in range(len(columns)):
            for j in range(i + 1, len(columns)):
                corr = corr_matrix.iloc[i, j]
                p_value = p_value_matrix.iloc[i, j]
                
                if abs(corr) >= min_correlation and p_value < 0.05:
                    var1 = columns[i]
                    var2 = columns[j]
                    
                    # Check for non-stationarity (could indicate spurious correlation)
                    from statsmodels.tsa.stattools import adfuller
                    
                    try:
                        # ADF test for stationarity
                        adf1 = adfuller(df[var1].dropna())
                        adf2 = adfuller(df[var2].dropna())
                        
                        is_stationary1 = adf1[1] < 0.05  # p-value
                        is_stationary2 = adf2[1] < 0.05
                        
                        # If both are non-stationary, correlation might be spurious
                        if not is_stationary1 and not is_stationary2:
                            suspicious_pairs.append({
                                'variable1': var1,
                                'variable2': var2,
                                'correlation': float(corr),
                                'reason': 'Both variables are non-stationary (trending)',
                                'adf_pvalue1': float(adf1[1]),
                                'adf_pvalue2': float(adf2[1]),
                                'warning': 'Correlation may be spurious - consider differencing or detrending'
                            })
                    
                    except Exception as e:
                        logger.warning(f"Error in spurious correlation detection: {str(e)}")
        
        return suspicious_pairs
    
    async def calculate_correlation_significance(
        self,
        correlation: float,
        n: int,
        alpha: float = 0.05
    ) -> Dict[str, Any]:
        """
        Calculate statistical significance of a correlation coefficient
        
        Args:
            correlation: Correlation coefficient
            n: Sample size
            alpha: Significance level
        
        Returns:
            Dictionary with significance test results
        """
        # Calculate t-statistic
        if abs(correlation) == 1:
            t_stat = float('inf') if correlation > 0 else float('-inf')
            p_value = 0.0
        else:
            t_stat = correlation * np.sqrt(n - 2) / np.sqrt(1 - correlation ** 2)
            p_value = 2 * (1 - stats.t.cdf(abs(t_stat), n - 2))
        
        # Calculate confidence interval
        z = np.arctanh(correlation)
        se = 1 / np.sqrt(n - 3)
        z_critical = stats.norm.ppf(1 - alpha / 2)
        
        ci_lower = np.tanh(z - z_critical * se)
        ci_upper = np.tanh(z + z_critical * se)
        
        return {
            't_statistic': float(t_stat),
            'p_value': float(p_value),
            'is_significant': p_value < alpha,
            'confidence_interval': {
                'lower': float(ci_lower),
                'upper': float(ci_upper),
                'level': 1 - alpha
            },
            'sample_size': n,
            'correlation': float(correlation)
        }