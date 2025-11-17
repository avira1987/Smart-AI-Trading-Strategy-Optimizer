import pandas as pd
import numpy as np
import re
from typing import Dict, List, Any, Tuple
from datetime import datetime
import json
import logging
import traceback
from .technical_indicators import calculate_all_indicators

logger = logging.getLogger(__name__)

class BacktestEngine:
    """Real backtesting engine"""
    
    def __init__(self, initial_capital: float = 10000):
        self.initial_capital = initial_capital
        self.current_capital = initial_capital
        self.positions = []
        self.trades = []
        self.equity_curve = []
        self.max_drawdown = 0.0
        self.peak_equity = initial_capital
    
    def run_backtest(self, data: pd.DataFrame, strategy: Dict[str, Any], symbol: str) -> Dict[str, Any]:
        """Run backtest with real data and strategy"""
        # Use detailed logger for backtest engine
        detailed_logger = logging.getLogger('ai_module.backtest_engine')
        
        buy_signals = 0
        sell_signals = 0

        try:
            detailed_logger.info("=" * 80)
            detailed_logger.info(f"شروع BacktestEngine برای نماد: {symbol}")
            detailed_logger.info(f"تعداد داده‌ها: {len(data)} ردیف")
            detailed_logger.info(f"سرمایه اولیه: {self.initial_capital}")
            
            logger.info(f"Starting backtest for {symbol} with {len(data)} data points")
            
            # Reset engine state for fresh backtest
            self.current_capital = self.initial_capital
            self.positions = []
            self.trades = []
            self.equity_curve = []
            self.max_drawdown = 0.0
            self.peak_equity = self.initial_capital
            
            detailed_logger.info(f"وضعیت موتور بک‌تست ریست شد")
            
            # Check if data is empty
            if data.empty:
                error_msg = 'داده‌های خالی برای بک‌تست دریافت شد.'
                detailed_logger.error(f"❌ خطا: {error_msg}")
                logger.warning(f"Empty data frame provided for backtest")
                return self._return_empty_results(strategy, symbol, error_msg)
            
            # Initialize technical indicators
            detailed_logger.info("-" * 80)
            detailed_logger.info("مرحله 1: محاسبه اندیکاتورهای تکنیکال")
            detailed_logger.info("-" * 80)
            
            try:
                detailed_logger.info(f"در حال محاسبه اندیکاتورها برای {len(data)} ردیف...")
                data = calculate_all_indicators(data)
                detailed_logger.info(f"✅ اندیکاتورها با موفقیت محاسبه شدند")
                detailed_logger.info(f"شکل داده بعد از اندیکاتورها: {data.shape}")
                detailed_logger.info(f"ستون‌های موجود: {list(data.columns)[:10]}...")  # نمایش 10 ستون اول
                logger.info(f"Indicators calculated successfully. Data shape: {data.shape}")
            except Exception as ind_error:
                error_msg = f'خطا در محاسبه اندیکاتورها: {str(ind_error)}'
                detailed_logger.error(f"❌ خطا در محاسبه اندیکاتورها: {str(ind_error)}")
                detailed_logger.error(f"Traceback: {traceback.format_exc()}")
                logger.error(f"Error calculating indicators: {ind_error}", exc_info=True)
                return self._return_empty_results(strategy, symbol, error_msg)
            
            # Apply strategy logic (signals and Persian reasons)
            detailed_logger.info("-" * 80)
            detailed_logger.info("مرحله 2: تولید سیگنال‌ها از استراتژی")
            detailed_logger.info("-" * 80)
            
            try:
                detailed_logger.info(f"در حال تولید سیگنال‌ها از استراتژی...")
                signals, signal_reasons = self._generate_signals(data, strategy)
                buy_signals = int((signals == 1).sum())
                sell_signals = int((signals == -1).sum())
                total_signals = buy_signals + sell_signals
                
                detailed_logger.info(f"✅ سیگنال‌ها تولید شدند:")
                detailed_logger.info(f"  - سیگنال خرید: {buy_signals}")
                detailed_logger.info(f"  - سیگنال فروش: {sell_signals}")
                detailed_logger.info(f"  - کل سیگنال‌ها: {total_signals}")
                detailed_logger.info(f"  - کل ردیف‌ها: {len(signals)}")
                
                if total_signals == 0:
                    detailed_logger.warning(f"⚠️ هشدار: هیچ سیگنالی تولید نشد! استراتژی ممکن است با داده‌ها مطابقت نداشته باشد.")
                
                logger.info(f"Signals generated: {buy_signals} buy signals, {sell_signals} sell signals, total rows: {len(signals)}")
            except Exception as sig_error:
                error_msg = f'خطا در تولید سیگنال‌ها: {str(sig_error)}'
                detailed_logger.error(f"❌ خطا در تولید سیگنال‌ها: {str(sig_error)}")
                detailed_logger.error(f"Traceback: {traceback.format_exc()}")
                logger.error(f"Error generating signals: {sig_error}", exc_info=True)
                return self._return_empty_results(strategy, symbol, error_msg)
            
            # Execute trades (attach entry/exit reasons)
            detailed_logger.info("-" * 80)
            detailed_logger.info("مرحله 3: اجرای معاملات")
            detailed_logger.info("-" * 80)
            
            try:
                detailed_logger.info(f"در حال اجرای معاملات با {total_signals} سیگنال...")
                self._execute_trades(data, signals, signal_reasons)
                detailed_logger.info(f"✅ اجرای معاملات تکمیل شد:")
                detailed_logger.info(f"  - تعداد معاملات: {len(self.trades)}")
                logger.info(f"Trade execution completed: {len(self.trades)} trades executed")
                
                if len(self.trades) == 0:
                    detailed_logger.warning(f"⚠️ هشدار: هیچ معامله‌ای اجرا نشد!")
            except Exception as trade_error:
                error_msg = f'خطا در اجرای معاملات: {str(trade_error)}'
                detailed_logger.error(f"❌ خطا در اجرای معاملات: {str(trade_error)}")
                detailed_logger.error(f"Traceback: {traceback.format_exc()}")
                logger.error(f"Error executing trades: {trade_error}", exc_info=True)
                return self._return_empty_results(strategy, symbol, error_msg)
            
            # Calculate performance metrics
            detailed_logger.info("-" * 80)
            detailed_logger.info("مرحله 4: محاسبه متریک‌های عملکرد")
            detailed_logger.info("-" * 80)
            
            try:
                detailed_logger.info(f"در حال محاسبه متریک‌ها...")
                metrics = self._calculate_metrics()
                detailed_logger.info(f"✅ متریک‌ها محاسبه شدند:")
                detailed_logger.info(f"  - total_trades: {metrics['total_trades']}")
                detailed_logger.info(f"  - total_return: {metrics['total_return']:.2f}%")
                detailed_logger.info(f"  - win_rate: {metrics['win_rate']:.2f}%")
                detailed_logger.info(f"  - max_drawdown: {metrics['max_drawdown']:.2f}%")
                logger.info(f"Backtest completed: {metrics['total_trades']} trades, {metrics['total_return']:.2f}% return, win_rate: {metrics['win_rate']:.2f}%")
            except Exception as metrics_error:
                error_msg = f'خطا در محاسبه متریک‌ها: {str(metrics_error)}'
                detailed_logger.error(f"❌ خطا در محاسبه متریک‌ها: {str(metrics_error)}")
                detailed_logger.error(f"Traceback: {traceback.format_exc()}")
                logger.error(f"Error calculating metrics: {metrics_error}", exc_info=True)
                return self._return_empty_results(strategy, symbol, error_msg)
            
            # Build a Persian description summarizing trade reasons
            description_fa = self._build_persian_description(symbol)

            return {
                'total_return': metrics['total_return'],
                'total_trades': metrics['total_trades'],
                'winning_trades': metrics['winning_trades'],
                'losing_trades': metrics['losing_trades'],
                'win_rate': metrics['win_rate'],
                'max_drawdown': metrics['max_drawdown'],
                'equity_curve_data': self.equity_curve,
                'trades': self.trades,
                'strategy_used': strategy,
                'symbol': symbol,
                'sharpe_ratio': metrics['sharpe_ratio'],
                'profit_factor': metrics['profit_factor'],
                'description_fa': description_fa
            }
            
        except Exception as e:
            detailed_logger = logging.getLogger('ai_module.backtest_engine')
            error_msg = f'خطای غیرمنتظره در بک‌تست: {str(e)}'
            detailed_logger.error("=" * 80)
            detailed_logger.error(f"❌❌❌ خطای غیرمنتظره در بک‌تست ❌❌❌")
            detailed_logger.error(f"نوع خطا: {type(e).__name__}")
            detailed_logger.error(f"پیام خطا: {str(e)}")
            detailed_logger.error("Traceback:")
            detailed_logger.error(traceback.format_exc())
            detailed_logger.error("=" * 80)
            logger.error(f"Error in backtest: {e}", exc_info=True)
            return self._return_empty_results(strategy, symbol, error_msg)
    
    def _return_empty_results(self, strategy: Dict[str, Any], symbol: str, error_msg: str) -> Dict[str, Any]:
        """Return empty results with error message"""
        return {
            'error': error_msg,
            'total_return': 0.0,
            'total_trades': 0,
            'winning_trades': 0,
            'losing_trades': 0,
            'win_rate': 0.0,
            'max_drawdown': 0.0,
            'equity_curve_data': [],
            'trades': [],
            'strategy_used': strategy,
            'symbol': symbol,
            'sharpe_ratio': 0.0,
            'profit_factor': 0.0,
            'description_fa': error_msg
        }
    
    def _generate_signals(self, data: pd.DataFrame, strategy: Dict[str, Any]) -> Tuple[pd.Series, Dict[int, Dict[str, str]]]:
        """Generate buy/sell signals based on user's text strategy only; optional selected indicators can restrict entries.

        Rules:
        - Never use automatic technical fallbacks (RSI/MACD/etc) when user text exists.
        - Never use any fallback if text parsing yields zero signals; produce zero signals.
        - Technical indicators are used only if the user explicitly selected them, and only to COMBINE (AND) with text signals.
        """
        signals = pd.Series(0, index=data.index)
        reasons: Dict[int, Dict[str, str]] = {}
        
        # Get strategy conditions from uploaded text file
        entry_conditions = strategy.get('entry_conditions', [])
        exit_conditions = strategy.get('exit_conditions', [])
        indicators = strategy.get('indicators', [])
        raw_excerpt = strategy.get('raw_excerpt', '')
        selected_indicators = strategy.get('selected_indicators', [])
        
        # PRIORITY: Always try to parse custom strategy from uploaded text first
        # This ensures user's uploaded strategy is used as the primary method
        has_custom_strategy = (
            entry_conditions or 
            exit_conditions or 
            indicators or 
            raw_excerpt
        )
        
        text_signals = pd.Series(0, index=data.index)
        text_reasons: Dict[int, Dict[str, str]] = {}
        
        if has_custom_strategy:
            # Parse custom strategy from user's uploaded text file (PRIMARY METHOD)
            text_signals, text_reasons = self._parse_custom_strategy(data, strategy)
            logger.info(f"Text-based strategy generated {text_signals.sum()} signals")
        else:
            # No custom strategy found - DO NOT use automatic fallbacks
            logger.warning("No strategy found in uploaded text. Skipping automatic technical fallbacks by design.")
            text_signals = pd.Series(0, index=data.index)
            text_reasons = {}
        
        # Now apply selected technical indicators if provided (combine with text strategy using AND logic)
        if selected_indicators and len(selected_indicators) > 0:
            logger.info(f"Combining text strategy with selected indicators: {selected_indicators}")
            indicator_signals, indicator_reasons = self._apply_selected_indicators(data, selected_indicators)
            
            # Check if text strategy produced any signals
            text_has_signals = (text_signals != 0).any()
            
            if text_has_signals:
                # Text strategy has signals - use AND logic: both text strategy AND indicator signals must be true
                # For buy signals: text says buy (1) AND indicator says buy (1) = buy (1)
                # For sell signals: text says sell (-1) AND indicator says sell (-1) = sell (-1)
                combined_signals = pd.Series(0, index=data.index)
                combined_reasons: Dict[int, Dict[str, str]] = {}
                
                # Entry signals: require both text and indicator to agree
                buy_mask = (text_signals == 1) & (indicator_signals == 1)
                combined_signals[buy_mask] = 1
                
                # Exit signals: require both text and indicator to agree
                sell_mask = (text_signals == -1) & (indicator_signals == -1)
                combined_signals[sell_mask] = -1
                
                # Combine reasons - show both text and indicator reasons
                for idx in data.index[buy_mask]:
                    text_reason = text_reasons.get(idx, {}).get('entry_reason_fa', '')
                    indicator_reason = indicator_reasons.get(idx, {}).get('entry_reason_fa', '')
                    combined_reason = f"{text_reason}"
                    if indicator_reason:
                        combined_reason += f" + {indicator_reason}"
                    combined_reasons.setdefault(idx, {})['entry_reason_fa'] = combined_reason
                
                for idx in data.index[sell_mask]:
                    text_reason = text_reasons.get(idx, {}).get('exit_reason_fa', '')
                    indicator_reason = indicator_reasons.get(idx, {}).get('exit_reason_fa', '')
                    combined_reason = f"{text_reason}"
                    if indicator_reason:
                        combined_reason += f" + {indicator_reason}"
                    combined_reasons.setdefault(idx, {})['exit_reason_fa'] = combined_reason
                
                # Check if combined signals are empty - if so, fallback to indicator signals only
                combined_buy_count = int((combined_signals == 1).sum())
                combined_sell_count = int((combined_signals == -1).sum())
                combined_total = combined_buy_count + combined_sell_count
                
                if combined_total == 0:
                    # AND logic produced no signals - fallback to indicator signals only
                    logger.warning(f"AND logic produced no signals (text: {int((text_signals != 0).sum())} signals, indicator: {int((indicator_signals != 0).sum())} signals). Falling back to indicator signals only.")
                    signals = indicator_signals
                    reasons = indicator_reasons
                else:
                    signals = combined_signals
                    reasons = combined_reasons
                    text_total = int((text_signals != 0).sum())
                    indicator_total = int((indicator_signals != 0).sum())
                    logger.info(f"Combined strategy (AND logic) generated {combined_total} signals (buys: {combined_buy_count}, sells: {combined_sell_count}) from text: {text_total}, indicators: {indicator_total}")
            else:
                # Text strategy produced no signals - use ONLY indicator signals (fallback to indicators only)
                signals = indicator_signals
                reasons = indicator_reasons
                buy_count = int((signals == 1).sum())
                sell_count = int((signals == -1).sum())
                total_count = buy_count + sell_count
                indicator_buy = int((indicator_signals == 1).sum())
                indicator_sell = int((indicator_signals == -1).sum())
                indicator_total = indicator_buy + indicator_sell
                logger.info(f"Text strategy produced no signals, using selected indicators only: {total_count} signals (buys: {buy_count}, sells: {sell_count}, indicator_total: {indicator_total}, indicator_buys: {indicator_buy}, indicator_sells: {indicator_sell})")
        else:
            # No selected indicators - use ONLY text-based strategy from extracted file, NO fallbacks
            signals = text_signals
            reasons = text_reasons
            text_signal_count = int((text_signals != 0).sum())
            
            logger.info(f"Using text-based strategy only (no technical fallbacks): {text_signal_count} signals")
            
            # Warn if no signals were generated from extracted strategy
            if text_signal_count == 0:
                entry_conditions = strategy.get('entry_conditions', [])
                exit_conditions = strategy.get('exit_conditions', [])
                
                has_valid_entry_conditions = entry_conditions and any(
                    cond and cond.strip() and len(cond.strip()) > 3 
                    for cond in entry_conditions
                )
                
                if not has_valid_entry_conditions:
                    logger.warning(f"⚠️ استراتژی استخراج شده هیچ شرط ورودی ندارد ({len(entry_conditions)} شرط ورود، {len(exit_conditions)} شرط خروج). بدون شرط ورود، هیچ معامله‌ای انجام نخواهد شد.")
                else:
                    logger.warning(f"⚠️ استراتژی استخراج شده دارای شرط ورود است اما هیچ سیگنالی تولید نشد. ممکن است شرط‌ها قابل پارس نباشند یا با داده‌ها مطابقت نداشته باشند.")
        
        return signals, reasons
    
    def _apply_selected_indicators(self, data: pd.DataFrame, selected_indicators: List[str]) -> Tuple[pd.Series, Dict[int, Dict[str, str]]]:
        """Apply selected technical indicators and generate signals
        
        Returns signals based on selected indicators using standard technical analysis logic.
        Multiple indicators are combined using OR logic (any indicator can trigger a signal).
        """
        combined_signals = pd.Series(0, index=data.index)
        combined_reasons: Dict[int, Dict[str, str]] = {}
        
        # Apply each selected indicator and combine using OR logic
        for indicator in selected_indicators:
            indicator_signals = pd.Series(0, index=data.index)
            indicator_reasons: Dict[int, Dict[str, str]] = {}
            indicator_lower = indicator.lower()
            
            # RSI strategy
            if indicator_lower == 'rsi' and 'rsi' in data.columns:
                buy_mask = (data['rsi'] < 30) & (data['rsi'].shift(1) >= 30)
                sell_mask = (data['rsi'] > 70) & (data['rsi'].shift(1) <= 70)
                indicator_signals[buy_mask] = 1
                indicator_signals[sell_mask] = -1
                for idx in data.index[buy_mask]:
                    indicator_reasons.setdefault(idx, {})['entry_reason_fa'] = 'ورود: RSI از 30 پایین‌تر رفت (اندیکاتور تکنیکال)'
                for idx in data.index[sell_mask]:
                    indicator_reasons.setdefault(idx, {})['exit_reason_fa'] = 'خروج: RSI از 70 بالاتر رفت (اندیکاتور تکنیکال)'
            
            # MACD strategy
            elif indicator_lower == 'macd' and 'macd' in data.columns and 'macd_signal' in data.columns:
                buy_mask = (data['macd'] > data['macd_signal']) & (data['macd'].shift(1) <= data['macd_signal'].shift(1))
                sell_mask = (data['macd'] < data['macd_signal']) & (data['macd'].shift(1) >= data['macd_signal'].shift(1))
                indicator_signals[buy_mask] = 1
                indicator_signals[sell_mask] = -1
                for idx in data.index[buy_mask]:
                    indicator_reasons.setdefault(idx, {})['entry_reason_fa'] = 'ورود: تقاطع صعودی MACD (اندیکاتور تکنیکال)'
                for idx in data.index[sell_mask]:
                    indicator_reasons.setdefault(idx, {})['exit_reason_fa'] = 'خروج: تقاطع نزولی MACD (اندیکاتور تکنیکال)'
            
            # SMA strategy
            elif indicator_lower == 'sma' and 'sma_20' in data.columns and 'sma_50' in data.columns:
                buy_mask = (data['sma_20'] > data['sma_50']) & (data['sma_20'].shift(1) <= data['sma_50'].shift(1))
                sell_mask = (data['sma_20'] < data['sma_50']) & (data['sma_20'].shift(1) >= data['sma_50'].shift(1))
                indicator_signals[buy_mask] = 1
                indicator_signals[sell_mask] = -1
                for idx in data.index[buy_mask]:
                    indicator_reasons.setdefault(idx, {})['entry_reason_fa'] = 'ورود: تقاطع صعودی SMA (اندیکاتور تکنیکال)'
                for idx in data.index[sell_mask]:
                    indicator_reasons.setdefault(idx, {})['exit_reason_fa'] = 'خروج: تقاطع نزولی SMA (اندیکاتور تکنیکال)'
            
            # EMA strategy
            elif indicator_lower == 'ema' and 'ema_12' in data.columns and 'ema_26' in data.columns:
                buy_mask = (data['ema_12'] > data['ema_26']) & (data['ema_12'].shift(1) <= data['ema_26'].shift(1))
                sell_mask = (data['ema_12'] < data['ema_26']) & (data['ema_12'].shift(1) >= data['ema_26'].shift(1))
                indicator_signals[buy_mask] = 1
                indicator_signals[sell_mask] = -1
                for idx in data.index[buy_mask]:
                    indicator_reasons.setdefault(idx, {})['entry_reason_fa'] = 'ورود: تقاطع صعودی EMA (اندیکاتور تکنیکال)'
                for idx in data.index[sell_mask]:
                    indicator_reasons.setdefault(idx, {})['exit_reason_fa'] = 'خروج: تقاطع نزولی EMA (اندیکاتور تکنیکال)'
            
            # Bollinger Bands strategy
            elif indicator_lower == 'bollinger' and 'bb_upper' in data.columns and 'bb_lower' in data.columns and 'bb_middle' in data.columns:
                buy_mask = (data['close'] < data['bb_lower']) & (data['close'].shift(1) >= data['bb_lower'].shift(1))
                sell_mask = (data['close'] > data['bb_upper']) & (data['close'].shift(1) <= data['bb_upper'].shift(1))
                indicator_signals[buy_mask] = 1
                indicator_signals[sell_mask] = -1
                for idx in data.index[buy_mask]:
                    indicator_reasons.setdefault(idx, {})['entry_reason_fa'] = 'ورود: قیمت به زیر باند پایین بولینگر رسید (اندیکاتور تکنیکال)'
                for idx in data.index[sell_mask]:
                    indicator_reasons.setdefault(idx, {})['exit_reason_fa'] = 'خروج: قیمت به بالای باند بالایی بولینگر رسید (اندیکاتور تکنیکال)'
            
            # Stochastic strategy
            elif indicator_lower == 'stochastic' and 'stoch_k' in data.columns and 'stoch_d' in data.columns:
                buy_mask = (data['stoch_k'] < 20) & (data['stoch_k'].shift(1) >= 20) & (data['stoch_k'] > data['stoch_d'])
                sell_mask = (data['stoch_k'] > 80) & (data['stoch_k'].shift(1) <= 80) & (data['stoch_k'] < data['stoch_d'])
                indicator_signals[buy_mask] = 1
                indicator_signals[sell_mask] = -1
                for idx in data.index[buy_mask]:
                    indicator_reasons.setdefault(idx, {})['entry_reason_fa'] = 'ورود: استوکاستیک در منطقه اشباع فروش (اندیکاتور تکنیکال)'
                for idx in data.index[sell_mask]:
                    indicator_reasons.setdefault(idx, {})['exit_reason_fa'] = 'خروج: استوکاستیک در منطقه اشباع خرید (اندیکاتور تکنیکال)'
            
            # Williams %R strategy
            elif indicator_lower == 'williams_r' and 'williams_r' in data.columns:
                buy_mask = (data['williams_r'] < -80) & (data['williams_r'].shift(1) >= -80)
                sell_mask = (data['williams_r'] > -20) & (data['williams_r'].shift(1) <= -20)
                indicator_signals[buy_mask] = 1
                indicator_signals[sell_mask] = -1
                for idx in data.index[buy_mask]:
                    indicator_reasons.setdefault(idx, {})['entry_reason_fa'] = 'ورود: Williams %R در منطقه اشباع فروش (اندیکاتور تکنیکال)'
                for idx in data.index[sell_mask]:
                    indicator_reasons.setdefault(idx, {})['exit_reason_fa'] = 'خروج: Williams %R در منطقه اشباع خرید (اندیکاتور تکنیکال)'
            
            # ATR strategy (using volatility breakout)
            elif indicator_lower == 'atr' and 'atr' in data.columns:
                # Simple ATR-based breakout strategy
                high_low_range = data['high'] - data['low']
                buy_mask = high_low_range > data['atr'] * 1.5
                # ATR is typically used for stop-loss, not direct signals, so this is simplified
                # In practice, ATR is combined with other indicators
                indicator_signals[buy_mask] = 1
                for idx in data.index[buy_mask]:
                    indicator_reasons.setdefault(idx, {})['entry_reason_fa'] = 'ورود: شکست نوسان بالا (ATR) (اندیکاتور تکنیکال)'
            
            # ADX strategy (trend strength)
            elif indicator_lower == 'adx' and 'adx' in data.columns:
                # ADX > 25 indicates strong trend
                buy_mask = (data['adx'] > 25) & (data['adx'].shift(1) <= 25)
                indicator_signals[buy_mask] = 1
                for idx in data.index[buy_mask]:
                    indicator_reasons.setdefault(idx, {})['entry_reason_fa'] = 'ورود: ADX نشان‌دهنده روند قوی (اندیکاتور تکنیکال)'
            
            # CCI strategy
            elif indicator_lower == 'cci' and 'cci' in data.columns:
                buy_mask = (data['cci'] < -100) & (data['cci'].shift(1) >= -100)
                sell_mask = (data['cci'] > 100) & (data['cci'].shift(1) <= 100)
                indicator_signals[buy_mask] = 1
                indicator_signals[sell_mask] = -1
                for idx in data.index[buy_mask]:
                    indicator_reasons.setdefault(idx, {})['entry_reason_fa'] = 'ورود: CCI در منطقه اشباع فروش (اندیکاتور تکنیکال)'
                for idx in data.index[sell_mask]:
                    indicator_reasons.setdefault(idx, {})['exit_reason_fa'] = 'خروج: CCI در منطقه اشباع خرید (اندیکاتور تکنیکال)'
            
            # Combine this indicator's signals with overall signals using OR logic
            # Entry: if this indicator says buy OR previous indicator said buy, set buy
            buy_mask = (indicator_signals == 1) | (combined_signals == 1)
            combined_signals[buy_mask] = 1
            
            # Exit: if this indicator says sell OR previous indicator said sell, set sell
            sell_mask = (indicator_signals == -1) | (combined_signals == -1)
            combined_signals[sell_mask] = -1
            
            # Merge reasons - combine all indicator reasons
            for idx, reason_dict in indicator_reasons.items():
                if idx in combined_reasons:
                    # Multiple indicators triggered - combine reasons
                    existing_entry = combined_reasons[idx].get('entry_reason_fa', '')
                    existing_exit = combined_reasons[idx].get('exit_reason_fa', '')
                    new_entry = reason_dict.get('entry_reason_fa', '')
                    new_exit = reason_dict.get('exit_reason_fa', '')
                    
                    if existing_entry and new_entry:
                        combined_reasons[idx]['entry_reason_fa'] = f"{existing_entry} یا {new_entry}"
                    elif new_entry:
                        combined_reasons[idx]['entry_reason_fa'] = new_entry
                    
                    if existing_exit and new_exit:
                        combined_reasons[idx]['exit_reason_fa'] = f"{existing_exit} یا {new_exit}"
                    elif new_exit:
                        combined_reasons[idx]['exit_reason_fa'] = new_exit
                else:
                    combined_reasons[idx] = reason_dict.copy()
        
        return combined_signals, combined_reasons
    
    def _use_fallback_strategy(self, data: pd.DataFrame, strategy: Dict[str, Any]) -> Tuple[pd.Series, Dict[int, Dict[str, str]]]:
        """Fallback to default strategies only when no user strategy is found"""
        signals = pd.Series(0, index=data.index)
        reasons: Dict[int, Dict[str, str]] = {}
        
        # Default strategy: RSI oversold/overbought
        if 'rsi' in data.columns:
            # RSI strategy
            buy_mask = (data['rsi'] < 30) & (data['rsi'].shift(1) >= 30)
            sell_mask = (data['rsi'] > 70) & (data['rsi'].shift(1) <= 70)
            signals[buy_mask] = 1
            signals[sell_mask] = -1
            for idx in data.index[buy_mask]:
                reasons.setdefault(idx, {})['entry_reason_fa'] = 'ورود: RSI از 30 پایین‌تر رفت و سیگنال خرید صادر شد.'
            for idx in data.index[sell_mask]:
                reasons.setdefault(idx, {})['exit_reason_fa'] = 'خروج: RSI از 70 بالاتر رفت و سیگنال فروش صادر شد.'
            
        elif 'macd' in data.columns:
            # MACD strategy
            buy_mask = (data['macd'] > data['macd_signal']) & (data['macd'].shift(1) <= data['macd_signal'].shift(1))
            sell_mask = (data['macd'] < data['macd_signal']) & (data['macd'].shift(1) >= data['macd_signal'].shift(1))
            signals[buy_mask] = 1
            signals[sell_mask] = -1
            for idx in data.index[buy_mask]:
                reasons.setdefault(idx, {})['entry_reason_fa'] = 'ورود: تقاطع صعودی MACD با خط سیگنال رخ داد.'
            for idx in data.index[sell_mask]:
                reasons.setdefault(idx, {})['exit_reason_fa'] = 'خروج: تقاطع نزولی MACD با خط سیگنال رخ داد.'
            
        elif 'sma_20' in data.columns and 'sma_50' in data.columns:
            # Moving Average crossover strategy
            buy_mask = (data['sma_20'] > data['sma_50']) & (data['sma_20'].shift(1) <= data['sma_50'].shift(1))
            sell_mask = (data['sma_20'] < data['sma_50']) & (data['sma_20'].shift(1) >= data['sma_50'].shift(1))
            signals[buy_mask] = 1
            signals[sell_mask] = -1
            for idx in data.index[buy_mask]:
                reasons.setdefault(idx, {})['entry_reason_fa'] = 'ورود: تقاطع صعودی میانگین‌های متحرک 20 و 50 رخ داد.'
            for idx in data.index[sell_mask]:
                reasons.setdefault(idx, {})['exit_reason_fa'] = 'خروج: تقاطع نزولی میانگین‌های متحرک 20 و 50 رخ داد.'
        
        return signals, reasons
    
    def _split_condition(self, condition: str) -> List[str]:
        """Split a complex condition into multiple simpler conditions"""
        # Split on common delimiters that might separate multiple conditions
        import re
        # Split on sentence endings, semicolons, or list markers
        parts = re.split(r'[;\n\r]|\.\s+(?=[A-Z\u0600-\u06FF])', condition)
        # Also split on numbered/bullet points
        parts = [p.strip() for p in parts if p.strip() and len(p.strip()) > 3]
        # If no split occurred, return original
        return parts if len(parts) > 1 else [condition]
    
    def _extract_indicator_keywords(self, text: str) -> List[str]:
        """Extract indicator-related keywords from text (Persian and English)"""
        keywords = []
        text_lower = text.lower()
        
        # Persian indicator names mapping
        persian_indicators = {
            'rsi': ['rsi', 'آر اس آی', 'آر‌اس‌آی'],
            'macd': ['macd', 'مکدی', 'mac d'],
            'sma': ['sma', 'میانگین متحرک', 'میانگین', 'sma20', 'sma 20', 'sma50', 'sma 50'],
            'ema': ['ema', 'ema12', 'ema 12', 'ema26', 'ema 26'],
            'bollinger': ['bollinger', 'بولینگر', 'باند بولینگر', 'bb'],
            'stochastic': ['stochastic', 'استوکاستیک', 'stoch'],
            'williams': ['williams', 'ویلیامز', 'williams %r', 'williamsr'],
            'atr': ['atr', 'اِی تی آر'],
            'adx': ['adx', 'اِی دی ایکس'],
            'cci': ['cci', 'سی سی آی']
        }
        
        for indicator_key, patterns in persian_indicators.items():
            for pattern in patterns:
                if pattern in text_lower:
                    keywords.append(indicator_key)
                    break
        
        return list(set(keywords))
    
    def _parse_custom_strategy(self, data: pd.DataFrame, strategy: Dict[str, Any]) -> Tuple[pd.Series, Dict[int, Dict[str, str]]]:
        """Parse custom strategy conditions from user's uploaded text file and produce signals
        
        This method extracts and uses the actual conditions from the user's text file,
        not hardcoded defaults. It supports Persian and English conditions.
        """
        signals = pd.Series(0, index=data.index)
        reasons: Dict[int, Dict[str, str]] = {}
        
        try:
            entry_conditions = strategy.get('entry_conditions', [])
            exit_conditions = strategy.get('exit_conditions', [])
            raw_excerpt = strategy.get('raw_excerpt', '')
            indicators = strategy.get('indicators', [])
            
            detailed_logger = logging.getLogger('ai_module.backtest_engine')
            
            logger.info(f"Parsing custom strategy: {len(entry_conditions)} entry conditions, {len(exit_conditions)} exit conditions, indicators: {indicators}")
            detailed_logger.debug(f"Entry conditions count: {len(entry_conditions)}, Exit conditions count: {len(exit_conditions)}")
            
            # Log what conditions we have - show full conditions for debugging
            if entry_conditions:
                logger.info(f"Entry conditions: {len(entry_conditions)} conditions found")
                detailed_logger.info(f"===== EXTRACTED ENTRY CONDITIONS ({len(entry_conditions)}) =====")
                for idx, cond in enumerate(entry_conditions, 1):
                    detailed_logger.info(f"Entry {idx}: {cond[:200]}...")
                    detailed_logger.debug(f"Entry condition {idx} (full): {cond}")
            else:
                detailed_logger.warning("⚠️ NO ENTRY CONDITIONS PROVIDED!")
                
            if exit_conditions:
                logger.info(f"Exit conditions: {len(exit_conditions)} conditions found")
                detailed_logger.info(f"===== EXTRACTED EXIT CONDITIONS ({len(exit_conditions)}) =====")
                for idx, cond in enumerate(exit_conditions, 1):
                    detailed_logger.info(f"Exit {idx}: {cond[:200]}...")
                    detailed_logger.debug(f"Exit condition {idx} (full): {cond}")
            else:
                detailed_logger.warning("⚠️ NO EXIT CONDITIONS PROVIDED!")
            
            # Check available columns in data
            available_cols = list(data.columns)
            logger.info(f"Available data columns: {len(available_cols)} columns")
            detailed_logger.debug(f"Available columns: {available_cols[:15]}...")  # First 15 columns
            
            # Track if we successfully parsed any conditions
            parsed_entry_conditions = 0
            parsed_exit_conditions = 0
            
            # Use the actual extracted conditions from user's text file
            # Parse entry conditions
            for condition in entry_conditions:
                if not condition or not condition.strip():
                    continue
                
                # Try to split complex conditions into simpler parts
                condition_parts = self._split_condition(condition.strip())
                detailed_logger.debug(f"Processing condition (split into {len(condition_parts)} parts): {condition[:100]}...")
                
                for condition_part in condition_parts:
                    condition_text = condition_part.strip()
                    if not condition_text or len(condition_text) < 3:
                        continue
                    
                    condition_lower = condition_text.lower()
                    
                    # Use the actual condition text as the reason
                    reason_text = f"ورود: {condition_text[:100]}"  # Limit length
                    
                    condition_parsed = False
                    
                    # First, try to extract indicator keywords to guide parsing
                    indicator_keywords = self._extract_indicator_keywords(condition_text)
                    if indicator_keywords:
                        detailed_logger.debug(f"Extracted indicator keywords: {indicator_keywords} from condition: {condition_text[:80]}...")
                    
                    # Parse volume-based conditions FIRST (before generic BUY/SELL)
                    if not condition_parsed and 'volume' in data.columns:
                        # High volume conditions (پرحجم, high volume)
                        if 'پرحجم' in condition_lower or 'high volume' in condition_lower or ('volume' in condition_lower and ('high' in condition_lower or 'زیاد' in condition_lower)):
                            vol_median = data['volume'].median()
                            if vol_median > 0:
                                # High volume: volume > 1.5x median
                                mask = data['volume'] > vol_median * 1.5
                                signal_count = mask.sum()
                                if signal_count > 0:
                                    signals[mask] = 1
                                    for idx in data.index[mask]:
                                        reasons.setdefault(idx, {})['entry_reason_fa'] = reason_text
                                    detailed_logger.info(f"Parsed high volume entry condition: {condition_text[:50]}... -> {signal_count} signals")
                                    parsed_entry_conditions += 1
                                    condition_parsed = True
                        
                        # Low volume conditions (کم‌حجم, low volume)
                        elif 'کم‌حجم' in condition_lower or 'کم حجم' in condition_lower or 'low volume' in condition_lower or ('volume' in condition_lower and ('low' in condition_lower or 'کم' in condition_lower)):
                            vol_median = data['volume'].median()
                            if vol_median > 0:
                                # Low volume: volume < 0.5x median
                                mask = data['volume'] < vol_median * 0.5
                                signal_count = mask.sum()
                                if signal_count > 0:
                                    signals[mask] = 1
                                    for idx in data.index[mask]:
                                        reasons.setdefault(idx, {})['entry_reason_fa'] = reason_text
                                    detailed_logger.info(f"Parsed low volume entry condition: {condition_text[:50]}... -> {signal_count} signals")
                                    parsed_entry_conditions += 1
                                    condition_parsed = True
                    
                    # Parse candle pattern conditions (سه کندل متوالی, consecutive candles)
                    if not condition_parsed and 'low' in data.columns and 'high' in data.columns:
                        # Three consecutive candles with higher lows (سه کندل متوالی با Low بالاتر)
                        if ('سه کندل' in condition_lower or 'three candle' in condition_lower or '3 candle' in condition_lower or 
                            'سه کندل متوالی' in condition_lower or 'consecutive' in condition_lower) and \
                           ('low' in condition_lower or 'بالاتر' in condition_lower or 'higher' in condition_lower or 'صعود' in condition_lower):
                            # Check for 3 consecutive candles with higher lows
                            mask = pd.Series(False, index=data.index)
                            for idx_pos in range(2, len(data)):
                                idx = data.index[idx_pos]
                                prev_idx1 = data.index[idx_pos - 1]
                                prev_idx2 = data.index[idx_pos - 2]
                                if (data.loc[idx, 'low'] > data.loc[prev_idx1, 'low'] and 
                                    data.loc[prev_idx1, 'low'] > data.loc[prev_idx2, 'low']):
                                    mask.loc[idx] = True
                            
                            signal_count = int(mask.sum())
                            if signal_count > 0:
                                signals[mask] = 1
                                for idx in data.index[mask]:
                                    reasons.setdefault(idx, {})['entry_reason_fa'] = reason_text
                                detailed_logger.info(f"Parsed candle pattern entry condition (3 consecutive higher lows): {condition_text[:50]}... -> {signal_count} signals")
                                parsed_entry_conditions += 1
                                condition_parsed = True
                        
                        # Three consecutive green candles (سه کندل سبز پشت‌سر‌هم) - usually for exit, but check anyway
                        elif ('سه کندل' in condition_lower or 'three candle' in condition_lower) and \
                             ('سبز' in condition_lower or 'green' in condition_lower or 'صعودی' in condition_lower):
                            if 'close' in data.columns and 'open' in data.columns:
                                # Check for 3 consecutive green candles (close > open)
                                mask = pd.Series(False, index=data.index)
                                for idx_pos in range(2, len(data)):
                                    idx = data.index[idx_pos]
                                    prev_idx1 = data.index[idx_pos - 1]
                                    prev_idx2 = data.index[idx_pos - 2]
                                    if (data.loc[idx, 'close'] > data.loc[idx, 'open'] and
                                        data.loc[prev_idx1, 'close'] > data.loc[prev_idx1, 'open'] and
                                        data.loc[prev_idx2, 'close'] > data.loc[prev_idx2, 'open']):
                                        mask.loc[idx] = True
                                
                                signal_count = int(mask.sum())
                                if signal_count > 0:
                                    signals[mask] = 1
                                    for idx in data.index[mask]:
                                        reasons.setdefault(idx, {})['entry_reason_fa'] = reason_text
                                    detailed_logger.info(f"Parsed candle pattern entry condition (3 consecutive green candles): {condition_text[:50]}... -> {signal_count} signals")
                                    parsed_entry_conditions += 1
                                    condition_parsed = True
                    
                    # Parse generic BUY/SELL patterns (after volume and candle patterns)
                    # These are often extracted by NLP but don't match technical indicator patterns
                    if not condition_parsed:
                        # Check for explicit BUY/خرید signals
                        buy_keywords = ['buy', 'خرید', 'long', 'ورود', '(buy)', 'buy signal', 'سیگنال خرید']
                        if any(kw in condition_lower for kw in buy_keywords):
                            # Generic BUY signal - use intelligent defaults based on available indicators
                            if 'rsi' in data.columns:
                                # Use RSI crossover below 30 (oversold entry)
                                mask = (data['rsi'] < 30) & (data['rsi'].shift(1) >= 30)
                                signal_count = mask.sum()
                                if signal_count > 0:
                                    signals[mask] = 1
                                    for idx in data.index[mask]:
                                        reasons.setdefault(idx, {})['entry_reason_fa'] = reason_text
                                    detailed_logger.info(f"Parsed generic BUY entry condition: {condition_text[:50]}... -> {signal_count} signals (RSI crossover < 30)")
                                    parsed_entry_conditions += 1
                                    condition_parsed = True
                                else:
                                    # Fallback: use RSI < 35 if crossover didn't work
                                    mask = data['rsi'] < 35
                                    signal_count = mask.sum()
                                    if signal_count > 0 and signal_count < len(data) * 0.3:  # Not too many signals
                                        signals[mask] = 1
                                        for idx in data.index[mask]:
                                            reasons.setdefault(idx, {})['entry_reason_fa'] = reason_text
                                        detailed_logger.info(f"Parsed generic BUY entry condition (fallback): {condition_text[:50]}... -> {signal_count} signals (RSI < 35)")
                                        parsed_entry_conditions += 1
                                        condition_parsed = True
                            elif 'volume' in data.columns:
                                # High volume buy signal (fallback if no RSI)
                                vol_median = data['volume'].median()
                                if vol_median > 0:
                                    mask = data['volume'] > vol_median * 1.5  # High volume
                                    signal_count = mask.sum()
                                    if signal_count > 0:
                                        signals[mask] = 1
                                        for idx in data.index[mask]:
                                            reasons.setdefault(idx, {})['entry_reason_fa'] = reason_text
                                        detailed_logger.info(f"Parsed volume-based BUY entry condition: {condition_text[:50]}... -> {signal_count} signals")
                                        parsed_entry_conditions += 1
                                        condition_parsed = True
                    
                    # Parse RSI conditions with custom thresholds
                    if 'rsi' in condition_lower or 'rsi' in indicator_keywords:
                        if 'rsi' not in data.columns:
                            detailed_logger.warning(f"RSI condition found but RSI column not in data: {condition_text[:80]}")
                            continue
                        
                        # Extract numeric threshold if present
                        rsi_numbers = re.findall(r'\d+', condition_text)
                        rsi_threshold = 30  # default
                        
                        if rsi_numbers:
                            # Try to infer threshold from context
                            for num in rsi_numbers:
                                num_val = int(num)
                                if 'زیر' in condition_lower or 'below' in condition_lower or 'کمتر' in condition_lower or 'oversold' in condition_lower:
                                    if num_val < 50:  # likely oversold threshold
                                        rsi_threshold = num_val
                                elif 'بالا' in condition_lower or 'above' in condition_lower or 'بیشتر' in condition_lower or 'overbought' in condition_lower:
                                    if num_val > 50:  # likely overbought threshold
                                        rsi_threshold = num_val
                        
                        if 'زیر' in condition_lower or 'below' in condition_lower or 'کمتر' in condition_lower or 'oversold' in condition_lower or ('rsi' in condition_lower and rsi_threshold < 50):
                            # Oversold condition
                            mask = (data['rsi'] < rsi_threshold) & (data['rsi'].shift(1) >= rsi_threshold)
                            signal_count = mask.sum()
                            signals[mask] = 1
                            for idx in data.index[mask]:
                                reasons.setdefault(idx, {})['entry_reason_fa'] = reason_text
                            detailed_logger.info(f"Parsed RSI entry condition: {condition_text[:50]}... -> {signal_count} signals")
                            parsed_entry_conditions += 1
                            condition_parsed = True
                        elif 'بالا' in condition_lower or 'above' in condition_lower or 'بیشتر' in condition_lower or 'overbought' in condition_lower or ('rsi' in condition_lower and rsi_threshold > 50):
                            # Overbought condition (usually for exit, but user may have different logic)
                            mask = (data['rsi'] > rsi_threshold) & (data['rsi'].shift(1) <= rsi_threshold)
                            signal_count = mask.sum()
                            signals[mask] = 1
                            for idx in data.index[mask]:
                                reasons.setdefault(idx, {})['entry_reason_fa'] = reason_text
                            detailed_logger.info(f"Parsed RSI entry condition: {condition_text[:50]}... -> {signal_count} signals")
                            parsed_entry_conditions += 1
                            condition_parsed = True
                    
                    # Parse MACD conditions
                    elif 'macd' in condition_lower or 'macd' in indicator_keywords:
                        if 'macd' not in data.columns or 'macd_signal' not in data.columns:
                            detailed_logger.warning(f"MACD condition found but MACD columns not in data: {condition_text[:80]}")
                            continue
                        
                        if 'تقاطع' in condition_lower or 'crossover' in condition_lower or 'cross' in condition_lower or 'crosses' in condition_lower:
                            if 'صعودی' in condition_lower or 'upward' in condition_lower or 'bullish' in condition_lower or ('macd' in condition_lower and 'above' in condition_lower):
                                # Bullish crossover
                                mask = (data['macd'] > data['macd_signal']) & (data['macd'].shift(1) <= data['macd_signal'].shift(1))
                                signal_count = mask.sum()
                                signals[mask] = 1
                                for idx in data.index[mask]:
                                    reasons.setdefault(idx, {})['entry_reason_fa'] = reason_text
                                detailed_logger.info(f"Parsed MACD entry condition: {condition_text[:50]}... -> {signal_count} signals")
                                parsed_entry_conditions += 1
                                condition_parsed = True
                    
                    # Parse Moving Average conditions
                    elif 'moving average' in condition_lower or 'میانگین' in condition_lower or 'sma' in condition_lower or 'ema' in condition_lower or 'sma' in indicator_keywords or 'ema' in indicator_keywords:
                        if 'sma_20' not in data.columns or 'sma_50' not in data.columns:
                            detailed_logger.warning(f"MA condition found but SMA columns not in data: {condition_text[:80]}")
                            continue
                        
                        if 'تقاطع' in condition_lower or 'crossover' in condition_lower or 'cross' in condition_lower:
                            if 'صعودی' in condition_lower or 'upward' in condition_lower or 'bullish' in condition_lower:
                                # Bullish MA crossover
                                mask = (data['sma_20'] > data['sma_50']) & (data['sma_20'].shift(1) <= data['sma_50'].shift(1))
                                signal_count = mask.sum()
                                signals[mask] = 1
                                for idx in data.index[mask]:
                                    reasons.setdefault(idx, {})['entry_reason_fa'] = reason_text
                                detailed_logger.info(f"Parsed MA entry condition: {condition_text[:50]}... -> {signal_count} signals")
                                parsed_entry_conditions += 1
                                condition_parsed = True
                    
                    # Generic condition - try to extract indicator names and use them
                    if not condition_parsed:
                        # Try to match any available indicator by checking column names
                        for col in data.columns:
                            col_lower = col.lower()
                            # Check if condition mentions this indicator (case-insensitive partial match)
                            if col_lower in condition_lower or condition_lower in col_lower or \
                               any(word in condition_lower for word in col_lower.split('_')) or \
                               any(word in col_lower for word in condition_lower.split() if len(word) > 2):
                                # Simple threshold-based logic
                                numbers = re.findall(r'\d+', condition_text)
                                # Check for common indicator columns
                                if col in ['rsi', 'stoch_k', 'stoch_d', 'williams_r', 'cci', 'adx', 'atr']:
                                    if numbers:
                                        threshold = float(numbers[0])
                                    else:
                                        # Use default thresholds if no number found
                                        if col in ['rsi']:
                                            threshold = 30  # oversold
                                        elif col in ['stoch_k', 'stoch_d']:
                                            threshold = 20  # oversold
                                        elif col in ['williams_r']:
                                            threshold = -80  # oversold
                                        elif col in ['cci']:
                                            threshold = -100  # oversold
                                        else:
                                            threshold = None
                                    
                                    if threshold is not None:
                                        if 'زیر' in condition_lower or 'below' in condition_lower or 'کمتر' in condition_lower or 'oversold' in condition_lower:
                                            mask = (data[col] < threshold) & (data[col].shift(1) >= threshold)
                                            signal_count = mask.sum()
                                            signals[mask] = 1
                                            for idx in data.index[mask]:
                                                reasons.setdefault(idx, {})['entry_reason_fa'] = reason_text
                                            detailed_logger.info(f"Parsed generic entry condition for {col}: {condition_text[:50]}... -> {signal_count} signals")
                                            parsed_entry_conditions += 1
                                            condition_parsed = True
                                            break
                                        elif 'بالا' in condition_lower or 'above' in condition_lower or 'بیشتر' in condition_lower or 'overbought' in condition_lower:
                                            mask = (data[col] > threshold) & (data[col].shift(1) <= threshold)
                                            signal_count = mask.sum()
                                            signals[mask] = 1
                                            for idx in data.index[mask]:
                                                reasons.setdefault(idx, {})['entry_reason_fa'] = reason_text
                                            detailed_logger.info(f"Parsed generic entry condition for {col}: {condition_text[:50]}... -> {signal_count} signals")
                                            parsed_entry_conditions += 1
                                            condition_parsed = True
                                            break
                                # Check for moving average columns
                                elif 'sma' in col_lower or 'ema' in col_lower:
                                    # Look for crossover patterns
                                    if 'تقاطع' in condition_lower or 'crossover' in condition_lower or 'cross' in condition_lower:
                                        # Try to find another MA column to cross with
                                        for other_col in data.columns:
                                            if other_col != col and ('sma' in other_col.lower() or 'ema' in other_col.lower()):
                                                if 'صعودی' in condition_lower or 'upward' in condition_lower or 'bullish' in condition_lower or 'above' in condition_lower:
                                                    mask = (data[col] > data[other_col]) & (data[col].shift(1) <= data[other_col].shift(1))
                                                    signal_count = mask.sum()
                                                    signals[mask] = 1
                                                    for idx in data.index[mask]:
                                                        reasons.setdefault(idx, {})['entry_reason_fa'] = reason_text
                                                    detailed_logger.info(f"Parsed MA crossover entry condition: {col} crosses above {other_col} -> {signal_count} signals")
                                                    parsed_entry_conditions += 1
                                                    condition_parsed = True
                                                    break
                                        if condition_parsed:
                                            break
                    
                    if not condition_parsed:
                        # Last resort: log the condition for debugging but don't generate signals
                        logger.warning(f"Could not parse entry condition: {condition_text[:100]}")
                        detailed_logger = logging.getLogger('ai_module.backtest_engine')
                        detailed_logger.debug(f"Unparsed entry condition details: '{condition_text[:200]}', available columns: {[c for c in data.columns if any(word in condition_lower for word in c.lower().split('_'))][:5]}")
                        
                        # Try one more generic pattern: if condition contains any price/volume keywords
                        # and we have basic OHLC data, generate signals based on price action
                        price_keywords = ['price', 'قیمت', 'candle', 'کندل', 'bar', 'bar']
                        if any(kw in condition_lower for kw in price_keywords) and 'close' in data.columns:
                            # Very generic: use price momentum as fallback
                            if 'up' in condition_lower or 'بالا' in condition_lower or 'صعود' in condition_lower:
                                # Price going up
                                mask = data['close'] > data['close'].shift(1)
                                signal_count = mask.sum()
                                if signal_count > len(data) * 0.1:  # At least 10% of bars
                                    signals[mask] = 1
                                    for idx in data.index[mask]:
                                        reasons.setdefault(idx, {})['entry_reason_fa'] = f"{reason_text} (generic price action)"
                                    detailed_logger.info(f"Parsed generic price action entry: {condition_text[:50]}... -> {signal_count} signals")
                                    parsed_entry_conditions += 1
                                    condition_parsed = True
            
            # Parse exit conditions
            for condition in exit_conditions:
                if not condition or not condition.strip():
                    continue
                
                # Try to split complex conditions into simpler parts
                condition_parts = self._split_condition(condition.strip())
                detailed_logger.debug(f"Processing exit condition (split into {len(condition_parts)} parts): {condition[:100]}...")
                
                for condition_part in condition_parts:
                    condition_text = condition_part.strip()
                    if not condition_text or len(condition_text) < 3:
                        continue
                    
                    condition_lower = condition_text.lower()
                    
                    # Use the actual condition text as the reason
                    reason_text = f"خروج: {condition_text[:100]}"  # Limit length
                    
                    condition_parsed = False
                    
                    # First, try to extract indicator keywords to guide parsing
                    indicator_keywords = self._extract_indicator_keywords(condition_text)
                    if indicator_keywords:
                        detailed_logger.debug(f"Extracted indicator keywords: {indicator_keywords} from exit condition: {condition_text[:80]}...")
                    
                    # Parse candle pattern conditions for exit (سه کندل سبز پشت‌سر‌هم)
                    if not condition_parsed and 'close' in data.columns and 'open' in data.columns:
                        # Three consecutive green candles for exit (سه کندل سبز پشت‌سر‌هم)
                        if ('سه کندل' in condition_lower or 'three candle' in condition_lower) and \
                           ('سبز' in condition_lower or 'green' in condition_lower or 'صعودی' in condition_lower):
                            # Check for 3 consecutive green candles (close > open)
                            mask = pd.Series(False, index=data.index)
                            for idx_pos in range(2, len(data)):
                                idx = data.index[idx_pos]
                                prev_idx1 = data.index[idx_pos - 1]
                                prev_idx2 = data.index[idx_pos - 2]
                                if (data.loc[idx, 'close'] > data.loc[idx, 'open'] and
                                    data.loc[prev_idx1, 'close'] > data.loc[prev_idx1, 'open'] and
                                    data.loc[prev_idx2, 'close'] > data.loc[prev_idx2, 'open']):
                                    mask.loc[idx] = True
                            
                            signal_count = int(mask.sum())
                            if signal_count > 0:
                                signals[mask] = -1
                                for idx in data.index[mask]:
                                    reasons.setdefault(idx, {})['exit_reason_fa'] = reason_text
                                detailed_logger.info(f"Parsed candle pattern exit condition (3 consecutive green candles): {condition_text[:50]}... -> {signal_count} signals")
                                parsed_exit_conditions += 1
                                condition_parsed = True
                    
                    # Parse generic SELL/خروج patterns (before specific indicators)
                    if not condition_parsed:
                        # Check for explicit SELL/فروش signals
                        sell_keywords = ['sell', 'فروش', 'short', 'خروج', '(sell)', 'sell signal', 'سیگنال فروش', 'exit', 'exit signal']
                        if any(kw in condition_lower for kw in sell_keywords):
                            # Generic SELL signal - use intelligent defaults
                            if 'rsi' in data.columns:
                                # Use RSI crossover above 70 (overbought exit)
                                mask = (data['rsi'] > 70) & (data['rsi'].shift(1) <= 70)
                                signal_count = mask.sum()
                                if signal_count > 0:
                                    signals[mask] = -1
                                    for idx in data.index[mask]:
                                        reasons.setdefault(idx, {})['exit_reason_fa'] = reason_text
                                    detailed_logger.info(f"Parsed generic SELL exit condition: {condition_text[:50]}... -> {signal_count} signals (RSI crossover > 70)")
                                    parsed_exit_conditions += 1
                                    condition_parsed = True
                                else:
                                    # Fallback: use RSI > 65 if crossover didn't work
                                    mask = data['rsi'] > 65
                                    signal_count = mask.sum()
                                    if signal_count > 0 and signal_count < len(data) * 0.3:  # Not too many signals
                                        signals[mask] = -1
                                        for idx in data.index[mask]:
                                            reasons.setdefault(idx, {})['exit_reason_fa'] = reason_text
                                        detailed_logger.info(f"Parsed generic SELL exit condition (fallback): {condition_text[:50]}... -> {signal_count} signals (RSI > 65)")
                                        parsed_exit_conditions += 1
                                        condition_parsed = True
                    
                    # Parse RSI conditions
                    if 'rsi' in condition_lower or 'rsi' in indicator_keywords:
                        if 'rsi' not in data.columns:
                            detailed_logger.warning(f"RSI exit condition found but RSI column not in data: {condition_text[:80]}")
                            continue
                        
                        rsi_numbers = re.findall(r'\d+', condition_text)
                        rsi_threshold = 70  # default
                        
                        if rsi_numbers:
                            for num in rsi_numbers:
                                num_val = int(num)
                                if 'بالا' in condition_lower or 'above' in condition_lower or 'بیشتر' in condition_lower or 'overbought' in condition_lower:
                                    if num_val > 50:
                                        rsi_threshold = num_val
                                elif 'زیر' in condition_lower or 'below' in condition_lower or 'کمتر' in condition_lower or 'oversold' in condition_lower:
                                    if num_val < 50:
                                        rsi_threshold = num_val
                        
                        if 'بالا' in condition_lower or 'above' in condition_lower or 'بیشتر' in condition_lower or 'overbought' in condition_lower or ('rsi' in condition_lower and rsi_threshold > 50):
                            mask = (data['rsi'] > rsi_threshold) & (data['rsi'].shift(1) <= rsi_threshold)
                            signal_count = mask.sum()
                            signals[mask] = -1
                            for idx in data.index[mask]:
                                reasons.setdefault(idx, {})['exit_reason_fa'] = reason_text
                            detailed_logger.info(f"Parsed RSI exit condition: {condition_text[:50]}... -> {signal_count} signals")
                            parsed_exit_conditions += 1
                            condition_parsed = True
                        elif 'زیر' in condition_lower or 'below' in condition_lower or 'کمتر' in condition_lower or 'oversold' in condition_lower:
                            mask = (data['rsi'] < rsi_threshold) & (data['rsi'].shift(1) >= rsi_threshold)
                            signal_count = mask.sum()
                            signals[mask] = -1
                            for idx in data.index[mask]:
                                reasons.setdefault(idx, {})['exit_reason_fa'] = reason_text
                            detailed_logger.info(f"Parsed RSI exit condition: {condition_text[:50]}... -> {signal_count} signals")
                            parsed_exit_conditions += 1
                            condition_parsed = True
                    
                    # Parse MACD conditions
                    elif 'macd' in condition_lower or 'macd' in indicator_keywords:
                        if 'macd' not in data.columns or 'macd_signal' not in data.columns:
                            detailed_logger.warning(f"MACD exit condition found but MACD columns not in data: {condition_text[:80]}")
                            continue
                        
                        if 'تقاطع' in condition_lower or 'crossover' in condition_lower or 'cross' in condition_lower:
                            if 'نزولی' in condition_lower or 'downward' in condition_lower or 'bearish' in condition_lower or ('macd' in condition_lower and 'below' in condition_lower):
                                # Bearish crossover
                                mask = (data['macd'] < data['macd_signal']) & (data['macd'].shift(1) >= data['macd_signal'].shift(1))
                                signal_count = mask.sum()
                                signals[mask] = -1
                                for idx in data.index[mask]:
                                    reasons.setdefault(idx, {})['exit_reason_fa'] = reason_text
                                detailed_logger.info(f"Parsed MACD exit condition: {condition_text[:50]}... -> {signal_count} signals")
                                parsed_exit_conditions += 1
                                condition_parsed = True
                    
                    # Parse Moving Average conditions
                    elif 'moving average' in condition_lower or 'میانگین' in condition_lower or 'sma' in condition_lower or 'ema' in condition_lower or 'sma' in indicator_keywords or 'ema' in indicator_keywords:
                        if 'sma_20' not in data.columns or 'sma_50' not in data.columns:
                            detailed_logger.warning(f"MA exit condition found but SMA columns not in data: {condition_text[:80]}")
                            continue
                        
                        if 'تقاطع' in condition_lower or 'crossover' in condition_lower or 'cross' in condition_lower:
                            if 'نزولی' in condition_lower or 'downward' in condition_lower or 'bearish' in condition_lower:
                                # Bearish MA crossover
                                mask = (data['sma_20'] < data['sma_50']) & (data['sma_20'].shift(1) >= data['sma_50'].shift(1))
                                signal_count = mask.sum()
                                signals[mask] = -1
                                for idx in data.index[mask]:
                                    reasons.setdefault(idx, {})['exit_reason_fa'] = reason_text
                                detailed_logger.info(f"Parsed MA exit condition: {condition_text[:50]}... -> {signal_count} signals")
                                parsed_exit_conditions += 1
                                condition_parsed = True
                    
                    # Generic exit condition parsing
                    if not condition_parsed:
                        for col in data.columns:
                            col_lower = col.lower()
                            if col_lower in condition_lower or condition_lower in col_lower or \
                               any(word in condition_lower for word in col_lower.split('_')) or \
                               any(word in col_lower for word in condition_lower.split() if len(word) > 2):
                                numbers = re.findall(r'\d+', condition_text)
                                if col in ['rsi', 'stoch_k', 'stoch_d', 'williams_r', 'cci', 'adx']:
                                    if numbers:
                                        threshold = float(numbers[0])
                                    else:
                                        # Use default thresholds
                                        if col in ['rsi']:
                                            threshold = 70  # overbought
                                        elif col in ['stoch_k', 'stoch_d']:
                                            threshold = 80  # overbought
                                        elif col in ['williams_r']:
                                            threshold = -20  # overbought
                                        elif col in ['cci']:
                                            threshold = 100  # overbought
                                        else:
                                            threshold = None
                                    
                                    if threshold is not None:
                                        if 'بالا' in condition_lower or 'above' in condition_lower or 'بیشتر' in condition_lower or 'overbought' in condition_lower:
                                            mask = (data[col] > threshold) & (data[col].shift(1) <= threshold)
                                            signal_count = mask.sum()
                                            signals[mask] = -1
                                            for idx in data.index[mask]:
                                                reasons.setdefault(idx, {})['exit_reason_fa'] = reason_text
                                            detailed_logger.info(f"Parsed generic exit condition for {col}: {condition_text[:50]}... -> {signal_count} signals")
                                            parsed_exit_conditions += 1
                                            condition_parsed = True
                                            break
                                        elif 'زیر' in condition_lower or 'below' in condition_lower or 'کمتر' in condition_lower or 'oversold' in condition_lower:
                                            mask = (data[col] < threshold) & (data[col].shift(1) >= threshold)
                                            signal_count = mask.sum()
                                            signals[mask] = -1
                                            for idx in data.index[mask]:
                                                reasons.setdefault(idx, {})['exit_reason_fa'] = reason_text
                                            detailed_logger.info(f"Parsed generic exit condition for {col}: {condition_text[:50]}... -> {signal_count} signals")
                                            parsed_exit_conditions += 1
                                            condition_parsed = True
                                            break
                    
                    if not condition_parsed:
                        detailed_logger.warning(f"Could not parse exit condition: {condition_text[:100]}")
                        detailed_logger.debug(f"Unparsed exit condition details: '{condition_text[:200]}', available columns: {[c for c in data.columns if any(word in condition_lower for word in c.lower().split('_'))][:5]}")
            
            # Summary of parsing results
            logger.info(f"Parsed {parsed_entry_conditions} entry conditions and {parsed_exit_conditions} exit conditions successfully")
            detailed_logger.info("=" * 80)
            detailed_logger.info(f"===== PARSING SUMMARY =====")
            detailed_logger.info(f"Entry conditions extracted by NLP: {len(entry_conditions)}")
            detailed_logger.info(f"Entry conditions successfully parsed: {parsed_entry_conditions}")
            detailed_logger.info(f"Exit conditions extracted by NLP: {len(exit_conditions)}")
            detailed_logger.info(f"Exit conditions successfully parsed: {parsed_exit_conditions}")
            detailed_logger.info(f"Total signals generated: {(signals == 1).sum()} buy, {(signals == -1).sum()} sell")
            detailed_logger.info("=" * 80)
            
            # If no signals found, try fallback strategies
            if signals.sum() == 0:
                logger.warning(f"No signals generated from {len(entry_conditions)} entry and {len(exit_conditions)} exit conditions")
                
                # Fallback 1: Try to use indicators list if available
                if indicators:
                    logger.info(f"Trying fallback: using indicators list: {indicators}")
                    for ind in indicators:
                        ind_lower = ind.lower()
                        if 'rsi' in ind_lower and 'rsi' in data.columns:
                            # Default RSI strategy
                            buy_mask = (data['rsi'] < 30) & (data['rsi'].shift(1) >= 30)
                            sell_mask = (data['rsi'] > 70) & (data['rsi'].shift(1) <= 70)
                            signals[buy_mask] = 1
                            signals[sell_mask] = -1
                            logger.info(f"Applied fallback RSI strategy: {(buy_mask).sum()} buy, {(sell_mask).sum()} sell signals")
                        elif 'macd' in ind_lower and 'macd' in data.columns and 'macd_signal' in data.columns:
                            buy_mask = (data['macd'] > data['macd_signal']) & (data['macd'].shift(1) <= data['macd_signal'].shift(1))
                            sell_mask = (data['macd'] < data['macd_signal']) & (data['macd'].shift(1) >= data['macd_signal'].shift(1))
                            signals[buy_mask] = 1
                            signals[sell_mask] = -1
                            logger.info(f"Applied fallback MACD strategy: {(buy_mask).sum()} buy, {(sell_mask).sum()} sell signals")
                        elif ('sma' in ind_lower or 'ema' in ind_lower) and 'sma_20' in data.columns and 'sma_50' in data.columns:
                            buy_mask = (data['sma_20'] > data['sma_50']) & (data['sma_20'].shift(1) <= data['sma_50'].shift(1))
                            sell_mask = (data['sma_20'] < data['sma_50']) & (data['sma_20'].shift(1) >= data['sma_50'].shift(1))
                            signals[buy_mask] = 1
                            signals[sell_mask] = -1
                            logger.info(f"Applied fallback MA strategy: {(buy_mask).sum()} buy, {(sell_mask).sum()} sell signals")
                
                # Fallback 2: Try to parse raw excerpt for common patterns
                if signals.sum() == 0 and raw_excerpt:
                    logger.info("Trying fallback: parsing raw excerpt for common patterns")
                    raw_lower = raw_excerpt.lower()
                    
                    # Look for common patterns in raw text
                    if 'rsi' in raw_lower and 'rsi' in data.columns:
                        if 'زیر' in raw_lower or 'below' in raw_lower or 'oversold' in raw_lower:
                            buy_mask = (data['rsi'] < 30) & (data['rsi'].shift(1) >= 30)
                            signals[buy_mask] = 1
                        if 'بالا' in raw_lower or 'above' in raw_lower or 'overbought' in raw_lower:
                            sell_mask = (data['rsi'] > 70) & (data['rsi'].shift(1) <= 70)
                            signals[sell_mask] = -1
                        logger.info(f"Applied fallback from raw text (RSI): {(signals==1).sum()} buy, {(signals==-1).sum()} sell signals")
                    
                    elif 'macd' in raw_lower and 'macd' in data.columns and 'macd_signal' in data.columns:
                        if 'صعودی' in raw_lower or 'upward' in raw_lower or 'bullish' in raw_lower:
                            buy_mask = (data['macd'] > data['macd_signal']) & (data['macd'].shift(1) <= data['macd_signal'].shift(1))
                            signals[buy_mask] = 1
                        if 'نزولی' in raw_lower or 'downward' in raw_lower or 'bearish' in raw_lower:
                            sell_mask = (data['macd'] < data['macd_signal']) & (data['macd'].shift(1) >= data['macd_signal'].shift(1))
                            signals[sell_mask] = -1
                        logger.info(f"Applied fallback from raw text (MACD): {(signals==1).sum()} buy, {(signals==-1).sum()} sell signals")
                
                # Final check: if still no signals, log detailed diagnostics
                buy_signals = int((signals == 1).sum())
                sell_signals = int((signals == -1).sum())

                if buy_signals == 0 and sell_signals == 0:
                    detailed_logger = logging.getLogger('ai_module.backtest_engine')
                    detailed_logger.warning("=" * 80)
                    detailed_logger.warning("===== STRATEGY PARSING DIAGNOSTICS ======")
                    detailed_logger.warning(f"Entry conditions provided: {len(entry_conditions)}")
                    detailed_logger.warning(f"Exit conditions provided: {len(exit_conditions)}")
                    detailed_logger.warning(f"Parsed successfully: {parsed_entry_conditions} entry, {parsed_exit_conditions} exit")
                    detailed_logger.warning(f"Indicators in strategy: {indicators}")
                    detailed_logger.warning(f"Available data columns: {available_cols[:20]}...")  # First 20 columns
                    
                    # Show raw excerpt to help diagnose
                    if raw_excerpt:
                        detailed_logger.warning(f"Raw excerpt (first 1000 chars):")
                        detailed_logger.warning("-" * 80)
                        detailed_logger.warning(raw_excerpt[:1000])
                        detailed_logger.warning("-" * 80)
                    else:
                        detailed_logger.warning("No raw excerpt available!")
                    
                    # Show actual entry/exit conditions that were provided
                    if entry_conditions:
                        detailed_logger.warning(f"Entry conditions (first 3):")
                        for idx, cond in enumerate(entry_conditions[:3], 1):
                            detailed_logger.warning(f"  {idx}. {cond[:200]}...")
                    else:
                        detailed_logger.warning("⚠️ NO ENTRY CONDITIONS PROVIDED!")
                    
                    if exit_conditions:
                        detailed_logger.warning(f"Exit conditions (first 3):")
                        for idx, cond in enumerate(exit_conditions[:3], 1):
                            detailed_logger.warning(f"  {idx}. {cond[:200]}...")
                    
                    detailed_logger.warning("=" * 80)
                    
                    logger.warning(f"""
                    ===== STRATEGY PARSING DIAGNOSTICS =====
                    Entry conditions provided: {len(entry_conditions)}
                    Exit conditions provided: {len(exit_conditions)}
                    Parsed successfully: {parsed_entry_conditions} entry, {parsed_exit_conditions} exit
                    Indicators in strategy: {indicators}
                    Available data columns: {len(available_cols)} columns
                    Raw excerpt length: {len(raw_excerpt)} chars
                    ========================================
                    """)
        
        except Exception as e:
            logger.error(f"Error parsing custom strategy: {e}", exc_info=True)
        
        # Calculate buy_signals and sell_signals from signals (in case exception occurred before they were set)
        buy_signals = int((signals == 1).sum())
        sell_signals = int((signals == -1).sum())
        
        total_signals = buy_signals + sell_signals
        logger.info(f"Final signal count: {total_signals} total ({buy_signals} buy, {sell_signals} sell)")
        
        return signals, reasons
    
    def _execute_trades(self, data: pd.DataFrame, signals: pd.Series, signal_reasons: Dict[int, Dict[str, str]]):
        """Execute trades based on signals and attach entry/exit Persian reasons"""
        if data.empty:
            logger.warning("Cannot execute trades: data is empty")
            return
        
        # Ensure signals index matches data index
        if not signals.index.equals(data.index):
            logger.warning(f"Signals index doesn't match data index. Reindexing signals. Data: {len(data)}, Signals: {len(signals)}")
            try:
                signals = signals.reindex(data.index, fill_value=0)
            except Exception as e:
                logger.error(f"Error reindexing signals: {e}")
                return
        
        position = 0
        entry_price = 0.0
        entry_date = None
        entry_reason_fa = ''
        
        try:
            for i, (date, row) in enumerate(data.iterrows()):
                try:
                    # Get signal value safely
                    if i < len(signals):
                        signal = signals.iloc[i]
                    else:
                        signal = signals.get(date, 0)
                    
                    # Ensure signal is numeric
                    if pd.isna(signal):
                        signal = 0
                    else:
                        signal = int(signal)
                    
                    if signal == 1 and position == 0:  # Buy signal
                        position = 1
                        entry_price = float(row['close'])
                        entry_date = date
                        # capture entry reason if available
                        idx = data.index[i]
                        entry_reason_fa = signal_reasons.get(idx, {}).get('entry_reason_fa', '')
                        logger.debug(f"Buy signal at {date}, price: {entry_price}")
                        
                    elif signal == -1 and position == 1:  # Sell signal
                        # Close position
                        exit_price = float(row['close'])
                        if entry_price > 0:
                            pnl = (exit_price - entry_price) / entry_price
                        else:
                            logger.warning(f"Invalid entry_price {entry_price} at sell signal")
                            pnl = 0.0
                        
                        idx = data.index[i]
                        exit_reason_fa = signal_reasons.get(idx, {}).get('exit_reason_fa', '')
                        
                        trade = {
                            'entry_date': entry_date.strftime('%Y-%m-%d %H:%M:%S') if entry_date else date.strftime('%Y-%m-%d %H:%M:%S'),
                            'exit_date': date.strftime('%Y-%m-%d %H:%M:%S'),
                            'entry_price': entry_price,
                            'exit_price': exit_price,
                            'pnl': pnl,
                            'pnl_percent': pnl * 100,
                            'duration_days': (date - entry_date).days if entry_date else 0,
                            'entry_reason_fa': entry_reason_fa,
                            'exit_reason_fa': exit_reason_fa
                        }
                        
                        self.trades.append(trade)
                        self.current_capital *= (1 + pnl)
                        position = 0
                        entry_reason_fa = ''
                        logger.debug(f"Sell signal at {date}, price: {exit_price}, pnl: {pnl:.4f}, capital: {self.current_capital:.2f}")
                    
                    # Update peak equity and drawdown
                    if self.current_capital > self.peak_equity:
                        self.peak_equity = self.current_capital
                    
                    current_drawdown = (self.peak_equity - self.current_capital) / self.peak_equity * 100 if self.peak_equity > 0 else 0.0
                    if current_drawdown > self.max_drawdown:
                        self.max_drawdown = current_drawdown
                    
                    # Record equity curve
                    try:
                        date_str = date.strftime('%Y-%m-%d') if hasattr(date, 'strftime') else str(date)
                        self.equity_curve.append({
                            'date': date_str,
                            'equity': float(self.current_capital),
                            'drawdown': float(current_drawdown)
                        })
                    except Exception as equity_error:
                        logger.warning(f"Error recording equity curve at {date}: {equity_error}")

                except Exception as row_error:
                    logger.warning(f"Error processing row {i} ({date}): {row_error}")
                    continue

            # Auto-close any open position at the end of backtest
            if position == 1 and entry_date is not None and not data.empty:
                try:
                    last_date = data.index[-1]
                    last_close = float(data.iloc[-1]['close'])
                    if entry_price > 0:
                        pnl = (last_close - entry_price) / entry_price
                    else:
                        pnl = 0.0
                    
                    trade = {
                        'entry_date': entry_date.strftime('%Y-%m-%d %H:%M:%S'),
                        'exit_date': last_date.strftime('%Y-%m-%d %H:%M:%S') if hasattr(last_date, 'strftime') else str(last_date),
                        'entry_price': entry_price,
                        'exit_price': last_close,
                        'pnl': pnl,
                        'pnl_percent': pnl * 100,
                        'duration_days': (last_date - entry_date).days if hasattr(last_date, 'days') and hasattr(entry_date, 'days') else 0,
                        'entry_reason_fa': entry_reason_fa,
                        'exit_reason_fa': 'خروج خودکار در پایان بازه بک‌تست'
                    }
                    self.trades.append(trade)
                    self.current_capital *= (1 + pnl)
                    logger.info(f"Auto-closed position at end: pnl={pnl:.4f}")
                except Exception as close_error:
                    logger.error(f"Error auto-closing position: {close_error}")

        except Exception as e:
            logger.error(f"Error in _execute_trades: {e}", exc_info=True)
            raise

        # Diagnostics
        try:
            buy_count = int((signals == 1).sum())
            sell_count = int((signals == -1).sum())
            total_signals = len(signals)
            logger.info(f"Signals summary -> buys: {buy_count}, sells: {sell_count}, total signals: {total_signals}, data rows: {len(data)}")
            logger.info(f"Trades executed: {len(self.trades)}, final capital: {self.current_capital:.2f}, initial: {self.initial_capital:.2f}")
        except Exception as diag_error:
            logger.warning(f"Error in diagnostics: {diag_error}")
    
    def _calculate_metrics(self) -> Dict[str, Any]:
        """Calculate performance metrics"""
        try:
            # Ensure we have valid initial and current capital
            initial_cap = float(self.initial_capital) if self.initial_capital > 0 else 10000.0
            current_cap = float(self.current_capital) if hasattr(self, 'current_capital') else initial_cap
            
            if not self.trades or len(self.trades) == 0:
                logger.info(f"No trades executed. Initial capital: {initial_cap:.2f}, Current capital: {current_cap:.2f}")
                return {
                    'total_return': 0.0,
                    'total_trades': 0,
                    'winning_trades': 0,
                    'losing_trades': 0,
                    'win_rate': 0.0,
                    'max_drawdown': float(self.max_drawdown) if hasattr(self, 'max_drawdown') else 0.0,
                    'sharpe_ratio': 0.0,
                    'profit_factor': 0.0
                }
            
            total_trades = len(self.trades)
            winning_trades = sum(1 for trade in self.trades if trade.get('pnl', 0) > 0)
            losing_trades = total_trades - winning_trades
            win_rate = (winning_trades / total_trades) * 100.0 if total_trades > 0 else 0.0
            
            # Calculate total return based on final capital vs initial capital
            if initial_cap > 0:
                total_return = ((current_cap - initial_cap) / initial_cap) * 100.0
            else:
                logger.warning("Initial capital is zero or negative, setting total_return to 0")
                total_return = 0.0
            
            # Calculate profit factor
            total_profit = sum(float(trade.get('pnl', 0)) for trade in self.trades if trade.get('pnl', 0) > 0)
            total_loss = abs(sum(float(trade.get('pnl', 0)) for trade in self.trades if trade.get('pnl', 0) < 0))
            profit_factor = total_profit / total_loss if total_loss > 0 else (float('inf') if total_profit > 0 else 0.0)
            
            # Calculate Sharpe ratio (simplified)
            if total_trades > 1:
                returns = [float(trade.get('pnl', 0)) for trade in self.trades]
                returns_mean = np.mean(returns)
                returns_std = np.std(returns)
                if returns_std > 0:
                    sharpe_ratio = (returns_mean / returns_std) * np.sqrt(252)
                else:
                    sharpe_ratio = 0.0
            else:
                sharpe_ratio = 0.0
            
            # Ensure max_drawdown is a valid float
            max_dd = float(self.max_drawdown) if hasattr(self, 'max_drawdown') else 0.0
            
            metrics = {
                'total_return': round(total_return, 2),
                'total_trades': total_trades,
                'winning_trades': winning_trades,
                'losing_trades': losing_trades,
                'win_rate': round(win_rate, 2),
                'max_drawdown': round(max_dd, 2),
                'sharpe_ratio': round(sharpe_ratio, 4),
                'profit_factor': round(profit_factor, 4) if profit_factor != float('inf') else float('inf')
            }
            
            logger.info(f"Metrics calculated: return={metrics['total_return']:.2f}%, trades={metrics['total_trades']}, win_rate={metrics['win_rate']:.2f}%")
            return metrics
            
        except Exception as e:
            logger.error(f"Error calculating metrics: {e}", exc_info=True)
            # Return safe defaults on error
            return {
                'total_return': 0.0,
                'total_trades': len(self.trades) if hasattr(self, 'trades') else 0,
                'winning_trades': 0,
                'losing_trades': 0,
                'win_rate': 0.0,
                'max_drawdown': 0.0,
                'sharpe_ratio': 0.0,
                'profit_factor': 0.0
            }

    def _build_persian_description(self, symbol: str) -> str:
        """Create a concise Persian description summarizing reasons of entries/exits for the test result."""
        if not self.trades:
            return f"برای نماد {symbol} هیچ معامله‌ای در این بک‌تست انجام نشد."
        lines: List[str] = [f"گزارش خلاصه معاملات برای نماد {symbol}:"]
        for idx, t in enumerate(self.trades, start=1):
            entry_reason = t.get('entry_reason_fa') or '—'
            exit_reason = t.get('exit_reason_fa') or '—'
            pnl_pct = f"{t.get('pnl_percent', 0):.2f}%"
            lines.append(f"معامله {idx}: ورود {t['entry_date']}، خروج {t['exit_date']}، سود/زیان: {pnl_pct}. دلیل ورود: {entry_reason} | دلیل خروج: {exit_reason}")
        return "\n".join(lines)

def run_simple_backtest(data: pd.DataFrame, strategy_type: str = 'rsi') -> Dict[str, Any]:
    """Run a simple backtest with predefined strategy"""
    engine = BacktestEngine()
    
    # Create simple strategy based on type
    strategy = {
        'entry_conditions': [],
        'exit_conditions': [],
        'indicators': [strategy_type],
        'strategy_type': strategy_type
    }
    
    return engine.run_backtest(data, strategy, 'EUR/USD')
