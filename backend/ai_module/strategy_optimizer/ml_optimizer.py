"""
Machine Learning based strategy optimizer
Uses various ML algorithms for parameter optimization
"""

from typing import Dict, List, Any, Optional
import pandas as pd
import numpy as np
import logging
from .base_optimizer import BaseOptimizer

logger = logging.getLogger(__name__)


class MLOptimizer(BaseOptimizer):
    """
    Machine Learning optimizer using various algorithms:
    - Random Forest for feature importance
    - Gradient Boosting for parameter optimization
    - Bayesian Optimization for efficient search
    """
    
    def __init__(self, strategy: Dict[str, Any], historical_data: pd.DataFrame):
        super().__init__(strategy, historical_data)
        self.ml_model = None
        self.feature_importance: Dict[str, float] = {}
        
    def optimize(self, 
                 objective: str = 'sharpe_ratio',
                 n_trials: int = 50,
                 method: str = 'bayesian',
                 **kwargs) -> Dict[str, Any]:
        """
        Optimize strategy using ML methods
        
        Args:
            objective: Objective function to optimize
            n_trials: Number of optimization trials
            method: Optimization method ('bayesian', 'random_search', 'grid_search')
            **kwargs: Additional parameters
            
        Returns:
            Optimization results
        """
        logger.info(f"Starting ML optimization with method: {method}, objective: {objective}")
        
        search_space = self.get_search_space()
        
        if method == 'bayesian':
            return self._bayesian_optimization(search_space, objective, n_trials)
        elif method == 'random_search':
            return self._random_search(search_space, objective, n_trials)
        elif method == 'grid_search':
            return self._grid_search(search_space, objective, **kwargs)
        else:
            raise ValueError(f"Unknown optimization method: {method}")
    
    def get_search_space(self) -> Dict[str, Any]:
        """Define parameter search space for ML optimization"""
        search_space = {
            'stop_loss': {
                'type': 'range',
                'min': 20,
                'max': 200,
                'step': 10
            },
            'take_profit': {
                'type': 'range',
                'min': 40,
                'max': 400,
                'step': 20
            },
            'risk_per_trade': {
                'type': 'range',
                'min': 0.5,
                'max': 5.0,
                'step': 0.5
            }
        }
        
        # Add indicator parameters if available
        if 'indicators' in self.strategy:
            for ind_name, ind_params in self.strategy['indicators'].items():
                if ind_name.lower() == 'rsi':
                    search_space['indicators'] = search_space.get('indicators', {})
                    search_space['indicators']['rsi'] = {
                        'period': {'type': 'range', 'min': 7, 'max': 21, 'step': 2}
                    }
                elif ind_name.lower() == 'macd':
                    search_space['indicators'] = search_space.get('indicators', {})
                    search_space['indicators']['macd'] = {
                        'fast': {'type': 'range', 'min': 8, 'max': 16, 'step': 2},
                        'slow': {'type': 'range', 'min': 20, 'max': 30, 'step': 2},
                        'signal': {'type': 'range', 'min': 7, 'max': 11, 'step': 1}
                    }
        
        return search_space
    
    def _bayesian_optimization(self, 
                               search_space: Dict[str, Any],
                               objective: str,
                               n_trials: int) -> Dict[str, Any]:
        """Bayesian optimization using Gaussian Process"""
        try:
            # Try to import Optuna for Bayesian optimization
            try:
                import optuna
            except ImportError:
                logger.warning("Optuna not available, falling back to random search")
                return self._random_search(search_space, objective, n_trials)
            
            def objective_function(trial):
                params = {}
                
                # Sample parameters
                if 'stop_loss' in search_space:
                    params['stop_loss'] = {
                        'type': 'pips',
                        'value': trial.suggest_int('stop_loss', 
                                                   search_space['stop_loss']['min'],
                                                   search_space['stop_loss']['max'],
                                                   step=search_space['stop_loss']['step'])
                    }
                
                if 'take_profit' in search_space:
                    params['take_profit'] = {
                        'type': 'pips',
                        'value': trial.suggest_int('take_profit',
                                                   search_space['take_profit']['min'],
                                                   search_space['take_profit']['max'],
                                                   step=search_space['take_profit']['step'])
                    }
                
                if 'risk_per_trade' in search_space:
                    params['risk_per_trade'] = trial.suggest_float('risk_per_trade',
                                                                   search_space['risk_per_trade']['min'],
                                                                   search_space['risk_per_trade']['max'],
                                                                   step=search_space['risk_per_trade']['step'])
                
                # Sample indicator parameters
                if 'indicators' in search_space:
                    params['indicators'] = {}
                    for ind_name, ind_config in search_space['indicators'].items():
                        params['indicators'][ind_name] = {}
                        for param_name, param_config in ind_config.items():
                            if param_config['type'] == 'range':
                                params['indicators'][ind_name][param_name] = trial.suggest_int(
                                    f'{ind_name}_{param_name}',
                                    param_config['min'],
                                    param_config['max'],
                                    step=param_config['step']
                                )
                
                # Evaluate
                score = self.evaluate_params(params, objective)
                return score
            
            # Create study
            study = optuna.create_study(direction='maximize')
            study.optimize(objective_function, n_trials=n_trials, show_progress_bar=False)
            
            # Extract best parameters
            best_params = {}
            for param_name, param_value in study.best_params.items():
                if param_name == 'stop_loss':
                    best_params['stop_loss'] = {'type': 'pips', 'value': param_value}
                elif param_name == 'take_profit':
                    best_params['take_profit'] = {'type': 'pips', 'value': param_value}
                elif param_name == 'risk_per_trade':
                    best_params['risk_per_trade'] = param_value
                elif '_' in param_name:
                    # Indicator parameter
                    parts = param_name.split('_', 1)
                    if len(parts) == 2:
                        ind_name, param = parts
                        if 'indicators' not in best_params:
                            best_params['indicators'] = {}
                        if ind_name not in best_params['indicators']:
                            best_params['indicators'][ind_name] = {}
                        best_params['indicators'][ind_name][param] = param_value
            
            return {
                'method': 'bayesian',
                'best_params': best_params,
                'best_score': study.best_value,
                'n_trials': n_trials,
                'optimization_history': self.optimization_history
            }
            
        except Exception as e:
            logger.error(f"Bayesian optimization failed: {str(e)}")
            return self._random_search(search_space, objective, n_trials)
    
    def _random_search(self, 
                      search_space: Dict[str, Any],
                      objective: str,
                      n_trials: int) -> Dict[str, Any]:
        """Random search optimization"""
        logger.info(f"Running random search with {n_trials} trials")
        
        for i in range(n_trials):
            params = {}
            
            # Randomly sample parameters
            if 'stop_loss' in search_space:
                stop_loss_space = search_space['stop_loss']
                stop_loss_val = np.random.randint(
                    stop_loss_space['min'],
                    stop_loss_space['max'] + 1,
                    step=stop_loss_space['step']
                )
                params['stop_loss'] = {'type': 'pips', 'value': stop_loss_val}
            
            if 'take_profit' in search_space:
                take_profit_space = search_space['take_profit']
                take_profit_val = np.random.randint(
                    take_profit_space['min'],
                    take_profit_space['max'] + 1,
                    step=take_profit_space['step']
                )
                params['take_profit'] = {'type': 'pips', 'value': take_profit_val}
            
            if 'risk_per_trade' in search_space:
                risk_space = search_space['risk_per_trade']
                params['risk_per_trade'] = np.random.choice(
                    np.arange(risk_space['min'], risk_space['max'] + risk_space['step'], risk_space['step'])
                )
            
            # Randomly sample indicator parameters
            if 'indicators' in search_space:
                params['indicators'] = {}
                for ind_name, ind_config in search_space['indicators'].items():
                    params['indicators'][ind_name] = {}
                    for param_name, param_config in ind_config.items():
                        if param_config['type'] == 'range':
                            param_val = np.random.randint(
                                param_config['min'],
                                param_config['max'] + 1,
                                step=param_config['step']
                            )
                            params['indicators'][ind_name][param_name] = param_val
            
            # Evaluate
            self.evaluate_params(params, objective)
            
            if (i + 1) % 10 == 0:
                logger.info(f"Completed {i + 1}/{n_trials} trials. Best score: {self.best_score:.4f}")
        
        return {
            'method': 'random_search',
            'best_params': self.best_params,
            'best_score': self.best_score,
            'n_trials': n_trials,
            'optimization_history': self.optimization_history
        }
    
    def _grid_search(self, 
                    search_space: Dict[str, Any],
                    objective: str,
                    **kwargs) -> Dict[str, Any]:
        """Grid search optimization (exhaustive)"""
        logger.warning("Grid search can be very slow. Consider using fewer parameter values.")
        
        # This is a simplified version - full grid search would be too slow
        # We'll do a limited grid search
        max_combinations = kwargs.get('max_combinations', 100)
        
        # Generate parameter combinations
        param_combinations = []
        
        # For simplicity, limit to most important parameters
        if 'stop_loss' in search_space and 'take_profit' in search_space:
            stop_loss_vals = np.arange(
                search_space['stop_loss']['min'],
                search_space['stop_loss']['max'] + 1,
                search_space['stop_loss']['step'] * 2  # Skip some for speed
            )
            take_profit_vals = np.arange(
                search_space['take_profit']['min'],
                search_space['take_profit']['max'] + 1,
                search_space['take_profit']['step'] * 2
            )
            
            for sl in stop_loss_vals[:10]:  # Limit to 10 values
                for tp in take_profit_vals[:10]:
                    if len(param_combinations) >= max_combinations:
                        break
                    params = {
                        'stop_loss': {'type': 'pips', 'value': int(sl)},
                        'take_profit': {'type': 'pips', 'value': int(tp)}
                    }
                    param_combinations.append(params)
                if len(param_combinations) >= max_combinations:
                    break
        
        # Evaluate all combinations
        for params in param_combinations:
            self.evaluate_params(params, objective)
        
        return {
            'method': 'grid_search',
            'best_params': self.best_params,
            'best_score': self.best_score,
            'n_trials': len(param_combinations),
            'optimization_history': self.optimization_history
        }

