"""
Base optimizer class with common functionality
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Any, Optional, Tuple
import pandas as pd
import numpy as np
import logging

logger = logging.getLogger(__name__)


class BaseOptimizer(ABC):
    """Base class for all optimization strategies"""
    
    def __init__(self, strategy: Dict[str, Any], historical_data: pd.DataFrame):
        """
        Initialize optimizer
        
        Args:
            strategy: Strategy dictionary with entry/exit conditions
            historical_data: Historical price data
        """
        self.strategy = strategy
        self.historical_data = historical_data
        self.optimization_history: List[Dict[str, Any]] = []
        self.best_params: Optional[Dict[str, Any]] = None
        self.best_score: float = -np.inf
        
    @abstractmethod
    def optimize(self, objective: str = 'sharpe_ratio', **kwargs) -> Dict[str, Any]:
        """
        Run optimization
        
        Args:
            objective: Objective function to optimize ('sharpe_ratio', 'total_return', 'win_rate', etc.)
            **kwargs: Additional optimization parameters
            
        Returns:
            Dictionary with optimized parameters and results
        """
        pass
    
    @abstractmethod
    def get_search_space(self) -> Dict[str, Any]:
        """
        Define parameter search space
        
        Returns:
            Dictionary defining parameter ranges
        """
        pass
    
    def evaluate_params(self, params: Dict[str, Any], objective: str = 'sharpe_ratio') -> float:
        """
        Evaluate strategy with given parameters
        
        Args:
            params: Parameters to test
            objective: Objective function to maximize
            
        Returns:
            Score value
        """
        try:
            # Create modified strategy with new parameters
            modified_strategy = self._apply_params_to_strategy(params)
            
            # Run backtest
            from ..backtest_engine import BacktestEngine
            engine = BacktestEngine()
            results = engine.run_backtest(
                self.historical_data,
                modified_strategy,
                symbol='OPTIMIZED'
            )
            
            # Calculate objective score
            if objective == 'sharpe_ratio':
                score = results.get('sharpe_ratio', 0.0)
            elif objective == 'total_return':
                score = results.get('total_return', 0.0)
            elif objective == 'win_rate':
                score = results.get('win_rate', 0.0)
            elif objective == 'profit_factor':
                score = results.get('profit_factor', 0.0)
            elif objective == 'combined':
                # Combined objective: weighted combination
                sharpe = results.get('sharpe_ratio', 0.0)
                ret = results.get('total_return', 0.0)
                wr = results.get('win_rate', 0.0)
                pf = results.get('profit_factor', 0.0)
                score = (sharpe * 0.4 + ret * 0.3 + wr * 0.2 + pf * 0.1)
            else:
                score = results.get('total_return', 0.0)
            
            # Store in history
            self.optimization_history.append({
                'params': params,
                'score': score,
                'results': results
            })
            
            # Update best if better
            if score > self.best_score:
                self.best_score = score
                self.best_params = params.copy()
            
            return score
            
        except Exception as e:
            logger.error(f"Error evaluating parameters: {str(e)}")
            return -np.inf
    
    def _apply_params_to_strategy(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Apply parameters to strategy
        
        Args:
            params: Parameters to apply
            
        Returns:
            Modified strategy dictionary
        """
        modified_strategy = self.strategy.copy()
        
        # Update risk management parameters
        if 'risk_management' not in modified_strategy:
            modified_strategy['risk_management'] = {}
        
        if 'stop_loss' in params:
            modified_strategy['risk_management']['stop_loss'] = params['stop_loss']
        if 'take_profit' in params:
            modified_strategy['risk_management']['take_profit'] = params['take_profit']
        if 'risk_per_trade' in params:
            modified_strategy['risk_management']['risk_per_trade'] = params['risk_per_trade']
        
        # Update indicator parameters
        if 'indicators' not in modified_strategy:
            modified_strategy['indicators'] = {}
        
        for indicator_name, indicator_params in params.get('indicators', {}).items():
            if indicator_name not in modified_strategy['indicators']:
                modified_strategy['indicators'][indicator_name] = {}
            modified_strategy['indicators'][indicator_name].update(indicator_params)
        
        # Update entry/exit conditions
        if 'entry_conditions' in params:
            modified_strategy['entry_conditions'] = params['entry_conditions']
        if 'exit_conditions' in params:
            modified_strategy['exit_conditions'] = params['exit_conditions']
        
        return modified_strategy
    
    def get_optimization_summary(self) -> Dict[str, Any]:
        """
        Get summary of optimization results
        
        Returns:
            Dictionary with optimization summary
        """
        return {
            'best_params': self.best_params,
            'best_score': self.best_score,
            'total_trials': len(self.optimization_history),
            'history': self.optimization_history[-10:]  # Last 10 trials
        }

