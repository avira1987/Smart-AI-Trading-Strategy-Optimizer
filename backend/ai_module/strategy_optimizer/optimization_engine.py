"""
Main optimization engine that coordinates different optimization methods
"""

from typing import Dict, List, Any, Optional, Tuple
import pandas as pd
import numpy as np
import logging
from .ml_optimizer import MLOptimizer
from .dl_optimizer import DLOptimizer

logger = logging.getLogger(__name__)


class OptimizationEngine:
    """
    Main engine for strategy optimization
    Coordinates ML and DL optimizers
    """
    
    def __init__(self, strategy: Dict[str, Any], historical_data: pd.DataFrame):
        """
        Initialize optimization engine
        
        Args:
            strategy: Strategy dictionary
            historical_data: Historical price data
        """
        self.strategy = strategy
        self.historical_data = historical_data
        self.ml_optimizer = MLOptimizer(strategy, historical_data)
        self.dl_optimizer = DLOptimizer(strategy, historical_data)
        self.optimization_results: List[Dict[str, Any]] = []
        
    def optimize(self,
                 method: str = 'auto',
                 optimizer_type: str = 'ml',
                 objective: str = 'sharpe_ratio',
                 **kwargs) -> Dict[str, Any]:
        """
        Run optimization with specified method
        
        Args:
            method: Optimization method
                - 'auto': Automatically choose best method
                - 'ml': Use machine learning methods
                - 'dl': Use deep learning methods
                - 'hybrid': Combine ML and DL
            optimizer_type: Type of optimizer ('ml' or 'dl')
            objective: Objective function ('sharpe_ratio', 'total_return', 'win_rate', 'combined')
            **kwargs: Additional optimization parameters
            
        Returns:
            Optimization results
        """
        logger.info(f"Starting optimization with method: {method}, optimizer: {optimizer_type}, objective: {objective}")
        
        if method == 'auto':
            return self._auto_optimize(objective, **kwargs)
        elif method == 'ml':
            return self._ml_optimize(objective, **kwargs)
        elif method == 'dl':
            return self._dl_optimize(objective, **kwargs)
        elif method == 'hybrid':
            return self._hybrid_optimize(objective, **kwargs)
        else:
            raise ValueError(f"Unknown optimization method: {method}")
    
    def _auto_optimize(self, objective: str, **kwargs) -> Dict[str, Any]:
        """Automatically choose and run best optimization method"""
        # Start with ML (faster)
        logger.info("Auto mode: Starting with ML optimization")
        ml_results = self._ml_optimize(objective, **kwargs)
        
        # If ML results are promising, try DL for refinement
        if ml_results.get('best_score', 0) > 0:
            logger.info("Auto mode: Refining with DL optimization")
            dl_results = self._dl_optimize(objective, n_episodes=20, **kwargs)
            
            # Compare and return best
            if dl_results.get('best_score', 0) > ml_results.get('best_score', 0):
                return {
                    'method': 'auto_hybrid',
                    'best_optimizer': 'dl',
                    **dl_results,
                    'ml_results': ml_results
                }
            else:
                return {
                    'method': 'auto_hybrid',
                    'best_optimizer': 'ml',
                    **ml_results,
                    'dl_results': dl_results
                }
        
        return {
            'method': 'auto',
            'best_optimizer': 'ml',
            **ml_results
        }
    
    def _ml_optimize(self, objective: str, **kwargs) -> Dict[str, Any]:
        """Run ML optimization"""
        ml_method = kwargs.get('ml_method', 'bayesian')
        n_trials = kwargs.get('n_trials', 50)
        
        results = self.ml_optimizer.optimize(
            objective=objective,
            method=ml_method,
            n_trials=n_trials,
            **kwargs
        )
        
        self.optimization_results.append({
            'optimizer_type': 'ml',
            'results': results
        })
        
        return results
    
    def _dl_optimize(self, objective: str, **kwargs) -> Dict[str, Any]:
        """Run DL optimization"""
        dl_method = kwargs.get('dl_method', 'reinforcement_learning')
        n_episodes = kwargs.get('n_episodes', 50)
        
        results = self.dl_optimizer.optimize(
            objective=objective,
            method=dl_method,
            n_episodes=n_episodes,
            **kwargs
        )
        
        self.optimization_results.append({
            'optimizer_type': 'dl',
            'results': results
        })
        
        return results
    
    def _hybrid_optimize(self, objective: str, **kwargs) -> Dict[str, Any]:
        """Run hybrid ML + DL optimization"""
        logger.info("Running hybrid optimization (ML + DL)")
        
        # Phase 1: ML optimization for quick exploration
        logger.info("Phase 1: ML optimization")
        ml_results = self._ml_optimize(objective, n_trials=kwargs.get('ml_trials', 30), **kwargs)
        
        # Phase 2: Use ML results as initialization for DL
        logger.info("Phase 2: DL optimization with ML initialization")
        
        # Update DL optimizer with ML best params if available
        if ml_results.get('best_params'):
            # Start DL from ML best point
            dl_results = self._dl_optimize(
                objective,
                n_episodes=kwargs.get('dl_episodes', 30),
                initial_params=ml_results['best_params'],
                **kwargs
            )
        else:
            dl_results = self._dl_optimize(
                objective,
                n_episodes=kwargs.get('dl_episodes', 30),
                **kwargs
            )
        
        # Combine results
        best_score = max(ml_results.get('best_score', 0), dl_results.get('best_score', 0))
        
        if ml_results.get('best_score', 0) >= dl_results.get('best_score', 0):
            best_params = ml_results.get('best_params')
            best_optimizer = 'ml'
        else:
            best_params = dl_results.get('best_params')
            best_optimizer = 'dl'
        
        return {
            'method': 'hybrid',
            'best_optimizer': best_optimizer,
            'best_params': best_params,
            'best_score': best_score,
            'ml_results': ml_results,
            'dl_results': dl_results,
            'optimization_history': ml_results.get('optimization_history', []) + 
                                   dl_results.get('optimization_history', [])
        }
    
    def compare_optimizers(self, objective: str = 'sharpe_ratio', **kwargs) -> Dict[str, Any]:
        """
        Compare ML and DL optimizers side by side
        
        Args:
            objective: Objective function
            **kwargs: Additional parameters
            
        Returns:
            Comparison results
        """
        logger.info("Comparing ML vs DL optimizers")
        
        ml_results = self._ml_optimize(objective, **kwargs)
        dl_results = self._dl_optimize(objective, **kwargs)
        
        return {
            'comparison': {
                'ml': {
                    'best_score': ml_results.get('best_score', 0),
                    'best_params': ml_results.get('best_params'),
                    'n_trials': ml_results.get('n_trials', 0)
                },
                'dl': {
                    'best_score': dl_results.get('best_score', 0),
                    'best_params': dl_results.get('best_params'),
                    'n_episodes': dl_results.get('n_episodes', 0)
                }
            },
            'winner': 'ml' if ml_results.get('best_score', 0) >= dl_results.get('best_score', 0) else 'dl',
            'ml_results': ml_results,
            'dl_results': dl_results
        }
    
    def get_optimization_summary(self) -> Dict[str, Any]:
        """Get summary of all optimization runs"""
        return {
            'total_optimizations': len(self.optimization_results),
            'results': self.optimization_results,
            'best_overall': self._get_best_overall()
        }
    
    def _get_best_overall(self) -> Optional[Dict[str, Any]]:
        """Get best result across all optimization runs"""
        best = None
        best_score = -np.inf
        
        for result_dict in self.optimization_results:
            results = result_dict.get('results', {})
            score = results.get('best_score', -np.inf)
            if score > best_score:
                best_score = score
                best = results
        
        return best

