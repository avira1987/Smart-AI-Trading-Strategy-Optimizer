from celery import shared_task
from django.utils import timezone
from datetime import timedelta
from core.models import Job, Result, TradingStrategy
from api.data_providers import DataProviderManager
from ai_module.nlp_parser import parse_strategy_file
from ai_module.backtest_engine import BacktestEngine
from .mt5_client import fetch_mt5_candles, is_mt5_available
import time
import os
import logging
from typing import Any, List

logger = logging.getLogger(__name__)


def _mt5_symbol_from(symbol: Any) -> str:
    """Convert arbitrary symbol input to MT5 format (e.g., 'EUR/USD' -> 'EURUSD')."""
    try:
        s = str(symbol) if symbol is not None else 'EUR/USD'
    except Exception:
        s = 'EUR/USD'
    return s.replace('/', '')

@shared_task
def run_backtest_task(job_id, timeframe_days: int = 365, symbol_override: str = None, initial_capital: float = 10000, selected_indicators: List[str] = None):
    """Run backtest for a job with real data"""
    import time
    import traceback
    start_time = time.time()
    job = Job.objects.get(id=job_id)
    
    # Create detailed logger for this specific backtest
    detailed_logger = logging.getLogger('api.tasks')
    
    try:
        job.status = 'running'
        job.started_at = timezone.now()
        job.save()
        
        # Clean up any previous results for this job before creating a new one
        # Reset direct result reference and delete related historical results
        if job.result_id:
            job.result = None
            job.save(update_fields=['result'])
        job.results.all().delete()
        
        detailed_logger.info("=" * 80)
        detailed_logger.info(f"========== شروع بک‌تست برای Job ID: {job_id} ==========")
        detailed_logger.info(f"زمان شروع: {timezone.now().strftime('%Y-%m-%d %H:%M:%S')}")
        detailed_logger.info(f"پارامترها:")
        detailed_logger.info(f"  - timeframe_days: {timeframe_days}")
        detailed_logger.info(f"  - symbol_override: {symbol_override}")
        detailed_logger.info(f"  - initial_capital: {initial_capital}")
        detailed_logger.info(f"  - selected_indicators: {selected_indicators}")
        detailed_logger.info("=" * 80)
        
        logger.info(f"========== Starting backtest for job {job_id} ==========")
        logger.info(f"Parameters: timeframe_days={timeframe_days}, symbol_override={symbol_override}, initial_capital={initial_capital}, selected_indicators={selected_indicators}")
        print(f"[BACKTEST] Starting job {job_id} at {timezone.now()}")
        
        # Get strategy file
        strategy = job.strategy
        if not strategy or not strategy.strategy_file:
            error_msg = "No strategy file found"
            detailed_logger.error(f"خطا: {error_msg}")
            raise ValueError(error_msg)
        
        detailed_logger.info(f"استراتژی: ID={strategy.id}, Name={strategy.name}")
        detailed_logger.info(f"فایل استراتژی: {strategy.strategy_file.name if strategy.strategy_file else 'None'}")
        detailed_logger.info(f"وضعیت پردازش: {strategy.processing_status}")
        
        # Use pre-processed strategy data if available, otherwise parse on the fly
        if strategy.parsed_strategy_data and strategy.processing_status == 'processed':
            parsed_strategy = strategy.parsed_strategy_data
            detailed_logger.info(f"استفاده از داده‌های از پیش پردازش شده استراتژی")
            detailed_logger.info(f"  - confidence_score: {parsed_strategy.get('confidence_score', 0):.2f}")
            detailed_logger.info(f"  - entry_conditions: {len(parsed_strategy.get('entry_conditions', []))} شرط")
            detailed_logger.info(f"  - exit_conditions: {len(parsed_strategy.get('exit_conditions', []))} شرط")
            detailed_logger.info(f"  - indicators: {parsed_strategy.get('indicators', [])}")
            detailed_logger.info(f"  - symbol: {parsed_strategy.get('symbol', 'N/A')}")
            logger.info(f"Using pre-processed strategy data for strategy {strategy.id} (confidence: {parsed_strategy.get('confidence_score', 0):.2f})")
        else:
            # Parse strategy file on the fly (backward compatibility)
            strategy_file_path = strategy.strategy_file.path
            detailed_logger.info(f"در حال پارس فایل استراتژی: {strategy_file_path}")
            parsed_strategy = parse_strategy_file(strategy_file_path)
            detailed_logger.info(f"پارس استراتژی انجام شد:")
            detailed_logger.info(f"  - confidence_score: {parsed_strategy.get('confidence_score', 0):.2f}")
            detailed_logger.info(f"  - entry_conditions: {len(parsed_strategy.get('entry_conditions', []))} شرط")
            detailed_logger.info(f"  - exit_conditions: {len(parsed_strategy.get('exit_conditions', []))} شرط")
            detailed_logger.info(f"  - indicators: {parsed_strategy.get('indicators', [])}")
            
            # Log actual conditions if available
            if parsed_strategy.get('entry_conditions'):
                detailed_logger.info(f"شرایط ورود:")
                for idx, condition in enumerate(parsed_strategy.get('entry_conditions', [])[:5], 1):
                    detailed_logger.info(f"  {idx}. {condition[:100]}...")
            if parsed_strategy.get('exit_conditions'):
                detailed_logger.info(f"شرایط خروج:")
                for idx, condition in enumerate(parsed_strategy.get('exit_conditions', [])[:5], 1):
                    detailed_logger.info(f"  {idx}. {condition[:100]}...")
            
            logger.info(f"Parsed strategy on the fly: {parsed_strategy.get('confidence_score', 0):.2f} confidence")
        
        # Get data provider
        detailed_logger.info("-" * 80)
        detailed_logger.info("مرحله 1: دریافت داده‌های بازار")
        detailed_logger.info("-" * 80)
        
        data_manager = DataProviderManager()
        available_providers = data_manager.get_available_providers()
        detailed_logger.info(f"ارائه‌دهندگان داده موجود: {available_providers}")
        
        # If no providers found, API key should be set via environment variable or APIConfiguration
        # Do not set default API keys here for security reasons
        if not available_providers:
            pass  # Provider configuration should be done via APIConfiguration model
        
        if not available_providers:
            error_msg = (
                "هیچ ارائه‌دهنده داده‌ای تنظیم نشده است. "
                "لطفاً حداقل یکی از API keys زیر را تنظیم کنید:\n"
                "- FINANCIALMODELINGPREP_API_KEY\n"
                "- TWELVEDATA_API_KEY\n"
                "یا MetaTrader 5 را نصب کنید (اختیاری)"
            )
            detailed_logger.error(f"خطا: {error_msg}")
            logger.error(error_msg)
            job.status = 'failed'
            job.error_message = error_msg
            job.completed_at = timezone.now()
            job.save()
            return f"Backtest failed for job {job_id}: {error_msg}"
        
        # Get historical data window and symbol
        symbol = (symbol_override or parsed_strategy.get('symbol') or 'EUR/USD')
        days = int(timeframe_days) if timeframe_days else 365
        start_date = (timezone.now() - timezone.timedelta(days=days)).strftime('%Y-%m-%d')
        end_date = timezone.now().strftime('%Y-%m-%d')
        
        detailed_logger.info(f"پارامترهای دریافت داده:")
        detailed_logger.info(f"  - symbol: {symbol}")
        detailed_logger.info(f"  - start_date: {start_date}")
        detailed_logger.info(f"  - end_date: {end_date}")
        detailed_logger.info(f"  - days: {days}")
        
        # Get user from job if available
        user = None
        try:
            # Try to get user from job
            if hasattr(job, 'user') and job.user:
                user = job.user
            # Fallback: try to get from strategy if it has user field
            elif hasattr(strategy, 'user') and strategy.user:
                user = strategy.user
        except Exception:
            pass
        
        # Try to get data from any available provider
        detailed_logger.info(f"در حال دریافت داده از ارائه‌دهندگان موجود...")
        data, provider_used = data_manager.get_data_from_any_provider(symbol, start_date, end_date, user=user)
        
        if not data.empty:
            detailed_logger.info(f"✅ دریافت داده انجام شد از {provider_used}: {len(data)} ردیف")
            logger.info(f"Backtest job {job_id}: Received {len(data)} rows from {provider_used} for symbol={symbol}")
        else:
            # If no provider worked, try MT5 as last resort (only if available)
            detailed_logger.warning("هیچ ارائه‌دهنده API داده برنگرداند؛ در حال تلاش MT5 به عنوان آخرین راه...")
            logger.warning("No API provider returned data; attempting MT5 fallback as last resort")
            mt5_ok, mt5_msg = is_mt5_available()
            if mt5_ok:
                mt5_symbol = _mt5_symbol_from(symbol)
                # Calculate dynamic count based on timeframe days
                minutes_in_day = 24 * 60
                bars_per_day = minutes_in_day // 15  # tf = M15
                count = days * bars_per_day
                detailed_logger.info(f"MT5 fallback: درخواست {count} کندل برای {days} روز برای نماد {mt5_symbol}")
                logger.info(f"MT5 fallback: requesting count={count} for days={days} symbol={mt5_symbol}")
                mt5_df, mt5_err = fetch_mt5_candles(mt5_symbol, timeframe='M15', count=count)
                if mt5_err is None and not mt5_df.empty:
                    data = mt5_df
                    provider_used = 'mt5'
                    detailed_logger.info(f"✅ MT5 fallback موفق: {len(data)} کندل برای {mt5_symbol}")
                    logger.info(f"MT5 fallback succeeded with {len(data)} candles for {mt5_symbol}")
                    
                    # لاگ استفاده از MT5
                    try:
                        import time
                        from api.api_usage_tracker import log_api_usage
                        log_api_usage(
                            provider='mt5',
                            endpoint=f"fetch_mt5_candles/{mt5_symbol}",
                            request_type='GET',
                            status_code=200,
                            success=True,
                            user=user,
                            metadata={
                                'symbol': mt5_symbol,
                                'timeframe': 'M15',
                                'count': count,
                                'data_points': len(mt5_df)
                            }
                        )
                    except Exception as log_error:
                        logger.warning(f"Failed to log MT5 API usage: {log_error}")
                else:
                    logger.error(f"MT5 fallback failed or returned empty data: {mt5_err}")
                    # Continue to error handling below
            else:
                logger.warning(f"MT5 not available: {mt5_msg}")
            
            # If still no data, return clear error message
            if data.empty:
                error_msg = (
                    f"نمی‌توان داده بازار را دریافت کرد. "
                    f"لطفاً مطمئن شوید که حداقل یک API key تنظیم شده است: "
                    f"Financial Modeling Prep (FINANCIALMODELINGPREP_API_KEY) یا "
                    f"Twelve Data (TWELVEDATA_API_KEY). "
                    f"MT5 در دسترس نیست: {mt5_msg if not mt5_ok else 'N/A'}"
                )
                detailed_logger.error(f"❌ خطا: {error_msg}")
                logger.error(f"[BACKTEST] {error_msg}")
                job.status = 'failed'
                job.error_message = error_msg
                job.completed_at = timezone.now()
                job.save()
                return f"Backtest failed for job {job_id}: {error_msg}"
        
        detailed_logger.info(f"جزئیات داده دریافتی:")
        detailed_logger.info(f"  - تعداد ردیف‌ها: {len(data)}")
        detailed_logger.info(f"  - ستون‌ها: {list(data.columns)}")
        
        if data.empty:
            detailed_logger.error(f"❌ خطا: داده خالی است!")
            logger.error(f"[BACKTEST] ERROR: Data is empty after all attempts!")
            print(f"[BACKTEST] ERROR: Data is empty after all attempts!")
        else:
            detailed_logger.info(f"  - اولین تاریخ: {data.index[0]}")
            detailed_logger.info(f"  - آخرین تاریخ: {data.index[-1]}")
            detailed_logger.info(f"  - نمونه داده (5 ردیف اول):")
            try:
                sample = data.head(5)
                for idx, row in sample.iterrows():
                    detailed_logger.info(f"    {idx}: O={row.get('open', 'N/A'):.4f}, H={row.get('high', 'N/A'):.4f}, L={row.get('low', 'N/A'):.4f}, C={row.get('close', 'N/A'):.4f}")
            except Exception as e:
                detailed_logger.warning(f"نمی‌توان نمونه داده را نمایش داد: {e}")
            
            logger.info(f"[BACKTEST] Data sample: first={data.index[0]}, last={data.index[-1]}, columns={list(data.columns)}")
            print(f"[BACKTEST] Data sample: first={data.index[0]}, last={data.index[-1]}, columns={list(data.columns)}")

        # Detect flat/constant price series which breaks indicators and signals
        # Only try MT5 fallback if MT5 is available and we haven't already used it
        try:
            if 'close' in data.columns and data['close'].std(skipna=True) == 0:
                logger.warning("Detected flat price series from provider; attempting alternative providers or MT5 fallback")
                # First try other API providers
                if provider_used != 'mt5':
                    alt_data, alt_provider = data_manager.get_data_from_any_provider(symbol, start_date, end_date, user=user)
                    if not alt_data.empty and alt_provider != provider_used:
                        data = alt_data
                        provider_used = alt_provider
                        logger.info(f"Alternative provider {alt_provider} succeeded with {len(data)} rows")
                    else:
                        # Only try MT5 if no API provider worked
                        mt5_ok, mt5_msg = is_mt5_available()
                        if mt5_ok:
                            mt5_symbol = _mt5_symbol_from(symbol)
                            minutes_in_day = 24 * 60
                            bars_per_day = minutes_in_day // 15  # tf = M15
                            count = days * bars_per_day
                            logger.info(f"MT5 flat-series fallback: requesting count={count} for days={days} symbol={mt5_symbol}")
                            mt5_df, mt5_err = fetch_mt5_candles(mt5_symbol, timeframe='M15', count=count)
                            if mt5_err is None and not mt5_df.empty:
                                data = mt5_df
                                provider_used = 'mt5'
                                logger.info(f"MT5 fallback succeeded with {len(data)} candles for {mt5_symbol}")
                            else:
                                logger.warning(f"MT5 fallback failed or returned empty data: {mt5_err}")
                        else:
                            logger.warning("Flat price series detected but MT5 not available; using API data anyway")
        except Exception as e:
            logger.warning(f"Error while checking for flat series / MT5 fallback: {e}")
        
        # Add selected indicators to parsed strategy if provided
        if selected_indicators:
            parsed_strategy['selected_indicators'] = selected_indicators
        else:
            parsed_strategy['selected_indicators'] = []
        
        detailed_logger.info("-" * 80)
        detailed_logger.info("خلاصه استراتژی قبل از اجرای بک‌تست:")
        detailed_logger.info(f"  - entry_conditions: {len(parsed_strategy.get('entry_conditions', []))} شرط")
        detailed_logger.info(f"  - exit_conditions: {len(parsed_strategy.get('exit_conditions', []))} شرط")
        detailed_logger.info(f"  - indicators: {parsed_strategy.get('indicators', [])}")
        detailed_logger.info(f"  - selected_indicators: {selected_indicators or []}")
        logger.info(f"[BACKTEST] Strategy summary: entry_conditions={len(parsed_strategy.get('entry_conditions', []))}, exit_conditions={len(parsed_strategy.get('exit_conditions', []))}, indicators={parsed_strategy.get('indicators', [])}")
        print(f"[BACKTEST] Strategy summary: entry_conditions={len(parsed_strategy.get('entry_conditions', []))}, exit_conditions={len(parsed_strategy.get('exit_conditions', []))}")
        
        # Validate data before running backtest
        if data.empty:
            error_msg = f"No market data available for symbol {symbol} and timeframe {timeframe_days} days. Please check your data provider configuration."
            detailed_logger.error(f"❌ خطا: {error_msg}")
            logger.error(f"[BACKTEST] Cannot run backtest: {error_msg}")
            print(f"[BACKTEST] ERROR: {error_msg}")
            job.status = 'failed'
            job.error_message = error_msg
            job.completed_at = timezone.now()
            job.save()
            return f"Backtest failed for job {job_id}: {error_msg}"
        
        # Validate that we have enough data points (at least 100 for meaningful backtest)
        if len(data) < 100:
            detailed_logger.warning(f"⚠️ هشدار: تعداد داده‌ها کم است ({len(data)}), نتایج ممکن است قابل اعتماد نباشد")
            logger.warning(f"[BACKTEST] Very few data points ({len(data)}), backtest results may not be meaningful")
            print(f"[BACKTEST] WARNING: Only {len(data)} data points available")
        
        # Run backtest
        detailed_logger.info("-" * 80)
        detailed_logger.info("مرحله 2: اجرای بک‌تست")
        detailed_logger.info("-" * 80)
        detailed_logger.info(f"شروع BacktestEngine با {len(data)} ردیف داده")
        detailed_logger.info(f"سرمایه اولیه: {initial_capital}")
        
        logger.info(f"[BACKTEST] Starting BacktestEngine with {len(data)} rows of data")
        print(f"[BACKTEST] Starting BacktestEngine with {len(data)} rows of data")
        engine = BacktestEngine(initial_capital=initial_capital or 10000)
        backtest_start = time.time()
        
        try:
            result_data = engine.run_backtest(data, parsed_strategy, symbol)
        except Exception as backtest_error:
            detailed_logger.error(f"❌ خطا در اجرای BacktestEngine: {str(backtest_error)}")
            detailed_logger.error(traceback.format_exc())
            raise
        
        backtest_duration = time.time() - backtest_start
        detailed_logger.info(f"✅ BacktestEngine تکمیل شد در {backtest_duration:.2f} ثانیه")
        logger.info(f"[BACKTEST] BacktestEngine completed in {backtest_duration:.2f} seconds")
        print(f"[BACKTEST] BacktestEngine completed in {backtest_duration:.2f} seconds")
        
        # Log detailed results
        detailed_logger.info("-" * 80)
        detailed_logger.info("نتایج بک‌تست:")
        detailed_logger.info(f"  - total_trades: {result_data.get('total_trades', 0)}")
        detailed_logger.info(f"  - winning_trades: {result_data.get('winning_trades', 0)}")
        detailed_logger.info(f"  - losing_trades: {result_data.get('losing_trades', 0)}")
        detailed_logger.info(f"  - win_rate: {result_data.get('win_rate', 0):.2f}%")
        detailed_logger.info(f"  - total_return: {result_data.get('total_return', 0):.2f}%")
        detailed_logger.info(f"  - max_drawdown: {result_data.get('max_drawdown', 0):.2f}%")
        detailed_logger.info(f"  - sharpe_ratio: {result_data.get('sharpe_ratio', 0):.4f}")
        detailed_logger.info(f"  - profit_factor: {result_data.get('profit_factor', 0):.4f}")
        
        if result_data.get('error'):
            detailed_logger.warning(f"⚠️ هشدار در نتایج: {result_data['error']}")
        
        logger.info(f"[BACKTEST] Backtest results: trades={result_data.get('total_trades', 0)}, return={result_data.get('total_return', 0):.2f}%, signals generated")
        print(f"[BACKTEST] Results: {result_data.get('total_trades', 0)} trades, {result_data.get('total_return', 0):.2f}% return")
        
        # Check if there was an error in the result
        if 'error' in result_data and result_data.get('error'):
            logger.warning(f"Backtest completed with error: {result_data['error']}")
            job.status = 'completed'  # Still mark as completed but with error in description
            job.error_message = result_data['error']
        
        # Extract values safely with defaults
        try:
            # Generate AI analysis of backtest results
            detailed_logger.info("-" * 80)
            detailed_logger.info("مرحله 3: تولید تحلیل هوش مصنوعی از نتایج")
            detailed_logger.info("-" * 80)
            
            # Provider names mapping for display
            provider_names = {
                'financialmodelingprep': 'Financial Modeling Prep',
                'twelvedata': 'TwelveData',
                'alphavantage': 'Alpha Vantage',
                'oanda': 'OANDA',
                'metalsapi': 'MetalsAPI',
                'mt5': 'MetaTrader 5',
                'unknown': 'نامشخص'
            }
            provider_display = provider_names.get(provider_used or 'unknown', provider_used or 'نامشخص')
            
            ai_analysis = None
            try:
                from ai_module.gemini_client import analyze_backtest_trades_with_ai, generate_basic_backtest_analysis
                
                detailed_logger.info("در حال درخواست تحلیل از هوش مصنوعی...")
                ai_analysis_result = analyze_backtest_trades_with_ai(
                    backtest_results=result_data,
                    strategy=parsed_strategy,
                    symbol=symbol,
                    data_provider=provider_display,
                    data_points=len(data) if not data.empty else 0,
                    date_range=f"{start_date} تا {end_date}",
                    user=user
                )
                ai_analysis = None
                if ai_analysis_result.get('ai_status') == 'ok':
                    ai_analysis = ai_analysis_result.get('analysis_text') or ai_analysis_result.get('raw_output', '')
                    detailed_logger.info("✅ تحلیل هوش مصنوعی با موفقیت تولید شد")
                    if ai_analysis:
                        logger.info(f"[AI ANALYSIS] Generated AI analysis for backtest: {len(ai_analysis)} characters")
                else:
                    message = ai_analysis_result.get(
                        'message',
                        "AI analysis unavailable. Please configure your AI provider (OpenAI ChatGPT or Gemini) in Settings."
                    )
                    detailed_logger.warning(f"⚠️ تحلیل هوش مصنوعی در دسترس نبود: {message}")
                    logger.warning(f"AI analysis unavailable: {message}")
                    detailed_logger.warning("⚠️ تحلیل هوش مصنوعی در دسترس نبود، استفاده از تحلیل پایه")
                    # Fallback to basic analysis
                    ai_analysis = generate_basic_backtest_analysis(
                        backtest_results=result_data,
                        strategy=parsed_strategy,
                        symbol=symbol,
                        data_provider=provider_display,
                        data_points=len(data) if not data.empty else 0,
                        date_range=f"{start_date} تا {end_date}"
                    )
                    logger.info(f"[AI ANALYSIS] Generated basic analysis (AI not available): {len(ai_analysis)} characters")
            except Exception as ai_error:
                detailed_logger.error(f"❌ خطا در تولید تحلیل هوش مصنوعی: {str(ai_error)}")
                detailed_logger.error(traceback.format_exc())
                logger.warning(f"AI analysis failed: {ai_error}", exc_info=True)
                # Fallback to basic analysis
                try:
                    from ai_module.gemini_client import generate_basic_backtest_analysis
                    ai_analysis = generate_basic_backtest_analysis(
                        backtest_results=result_data,
                        strategy=parsed_strategy,
                        symbol=symbol,
                        data_provider=provider_display,
                        data_points=len(data) if not data.empty else 0,
                        date_range=f"{start_date} تا {end_date}"
                    )
                    logger.info(f"[AI ANALYSIS] Fallback to basic analysis due to error")
                except Exception:
                    ai_analysis = None
            
            # Prepare data sources information
            data_sources_info = {
                'provider': provider_used or 'unknown',
                'symbol': symbol,
                'start_date': start_date,
                'end_date': end_date,
                'data_points': len(data) if not data.empty else 0,
                'available_providers': available_providers,
                'timeframe_days': days,
                'data_range': {
                    'first_date': str(data.index[0]) if not data.empty else None,
                    'last_date': str(data.index[-1]) if not data.empty else None,
                }
            }
            
            # Build data sources description text (provider_display already defined above)
            data_sources_text = f"\n\n{'=' * 80}\n\n📊 منابع داده استفاده شده:\n\n"
            data_sources_text += f"• ارائه‌دهنده داده: {provider_display}\n"
            data_sources_text += f"• نماد معاملاتی: {symbol}\n"
            data_sources_text += f"• بازه زمانی: {start_date} تا {end_date} ({days} روز)\n"
            if not data.empty:
                data_sources_text += f"• تعداد نقاط داده: {len(data):,}\n"
                if data_sources_info['data_range']['first_date'] and data_sources_info['data_range']['last_date']:
                    data_sources_text += f"• محدوده داده‌ها: {data_sources_info['data_range']['first_date']} تا {data_sources_info['data_range']['last_date']}\n"
            if available_providers and len(available_providers) > 1:
                providers_display = [provider_names.get(p, p) for p in available_providers]
                data_sources_text += f"• ارائه‌دهندگان در دسترس: {', '.join(providers_display)}\n"
            data_sources_text += "\n"
            
            # Combine original description with AI analysis and data sources
            # Ensure original_description is always a string (not dict/JSON)
            original_description_raw = result_data.get('description_fa', result_data.get('error', ''))
            original_description = ''
            
            # Convert to string if it's not already - always ensure it's a readable text, not JSON
            if original_description_raw:
                if isinstance(original_description_raw, dict):
                    # If it's a dict, convert to readable Persian text format
                    # This should not happen normally, but handle it gracefully
                    lines = []
                    for key, value in original_description_raw.items():
                        if isinstance(value, (dict, list)):
                            import json
                            value_str = json.dumps(value, ensure_ascii=False, indent=2)
                        else:
                            value_str = str(value)
                        lines.append(f"{key}: {value_str}")
                    original_description = '\n'.join(lines)
                elif isinstance(original_description_raw, (list, tuple)):
                    # If it's a list, join it with newlines
                    original_description = '\n'.join(str(item) for item in original_description_raw)
                else:
                    # It's already a string or can be converted
                    original_description = str(original_description_raw).strip()
            
            # Ensure ai_analysis is always a string (not dict/JSON)
            ai_analysis_str = ''
            if ai_analysis:
                if isinstance(ai_analysis, dict):
                    # Convert dict to readable text format
                    lines = []
                    for key, value in ai_analysis.items():
                        if isinstance(value, (dict, list)):
                            import json
                            value_str = json.dumps(value, ensure_ascii=False, indent=2)
                        else:
                            value_str = str(value)
                        lines.append(f"{key}: {value_str}")
                    ai_analysis_str = '\n'.join(lines)
                elif isinstance(ai_analysis, (list, tuple)):
                    ai_analysis_str = '\n'.join(str(item) for item in ai_analysis)
                else:
                    ai_analysis_str = str(ai_analysis).strip()
            
            # Build final description consistently - always in readable Persian text format
            if ai_analysis_str:
                if original_description:
                    final_description = f"{original_description}\n\n{'=' * 80}\n\n📊 تحلیل هوش مصنوعی نتایج بک‌تست:\n\n{ai_analysis_str}{data_sources_text}"
                else:
                    final_description = f"📊 تحلیل هوش مصنوعی نتایج بک‌تست:\n\n{ai_analysis_str}{data_sources_text}"
            else:
                final_description = f"{original_description}{data_sources_text}" if original_description else data_sources_text.strip()
            
            # Create result with error handling
            result = Result.objects.create(
                job=job,
                total_return=float(result_data.get('total_return', 0.0)),
                total_trades=int(result_data.get('total_trades', 0)),
                winning_trades=int(result_data.get('winning_trades', 0)),
                losing_trades=int(result_data.get('losing_trades', 0)),
                win_rate=float(result_data.get('win_rate', 0.0)),
                max_drawdown=float(result_data.get('max_drawdown', 0.0)),
                equity_curve_data=result_data.get('equity_curve_data', []),
                description=final_description,
                trades_details=result_data.get('trades', []),
                data_sources=data_sources_info
            )
            
            job.result = result
            job.status = 'completed'
            job.completed_at = timezone.now()
            job.save()
            
            total_duration = time.time() - start_time
            logger.info(f"========== Backtest completed for job {job_id} in {total_duration:.2f} seconds ==========")
            logger.info(f"Results: {result_data.get('total_return', 0):.2f}% return, {result_data.get('total_trades', 0)} trades, {result_data.get('win_rate', 0):.2f}% win rate")
            print(f"[BACKTEST] ========== Backtest completed for job {job_id} in {total_duration:.2f} seconds ==========")
            print(f"[BACKTEST] Results: {result_data.get('total_return', 0):.2f}% return, {result_data.get('total_trades', 0)} trades")
            
            if result_data.get('error'):
                logger.warning(f"Backtest completed with warnings: {result_data['error']}")
                return f"Backtest completed for job {job_id} with warnings: {result_data['error']}"
            return f"Backtest completed for job {job_id}"
            
        except Exception as result_error:
            logger.error(f"Error creating result for job {job_id}: {result_error}", exc_info=True)
            # Still try to create a minimal result
            try:
                # Prepare minimal data sources info for error case
                data_sources_info = {
                    'provider': provider_used if 'provider_used' in locals() else 'unknown',
                    'symbol': symbol if 'symbol' in locals() else 'unknown',
                    'error': str(result_error)
                }
                result = Result.objects.create(
                    job=job,
                    total_return=0.0,
                    total_trades=0,
                    winning_trades=0,
                    losing_trades=0,
                    win_rate=0.0,
                    max_drawdown=0.0,
                    equity_curve_data=[],
                    description=f'خطا در ذخیره نتایج: {str(result_error)}',
                    trades_details=[],
                    data_sources=data_sources_info
                )
                job.result = result
                job.status = 'completed'
                job.error_message = f"Result creation error: {str(result_error)}"
            except Exception as final_error:
                logger.error(f"Failed to create even minimal result: {final_error}")
            
            job.completed_at = timezone.now()
            job.save()
            return f"Backtest completed for job {job_id} with errors"
        
    except Exception as e:
        import traceback
        total_duration = time.time() - start_time if 'start_time' in locals() else 0
        detailed_logger = logging.getLogger('api.tasks')
        
        detailed_logger.error("=" * 80)
        detailed_logger.error(f"❌❌❌ بک‌تست با خطا مواجه شد برای Job ID: {job_id} ❌❌❌")
        detailed_logger.error(f"زمان اجرا تا خطا: {total_duration:.2f} ثانیه")
        detailed_logger.error(f"نوع خطا: {type(e).__name__}")
        detailed_logger.error(f"پیام خطا: {str(e)}")
        detailed_logger.error("=" * 80)
        detailed_logger.error("جزئیات کامل خطا (Traceback):")
        detailed_logger.error(traceback.format_exc())
        detailed_logger.error("=" * 80)
        
        logger.error(f"========== Backtest FAILED for job {job_id} after {total_duration:.2f} seconds ==========")
        logger.error(f"Error details: {str(e)}", exc_info=True)
        print(f"[BACKTEST] ========== Backtest FAILED for job {job_id} ==========")
        print(f"[BACKTEST] Error: {str(e)}")
        job.status = 'failed'
        job.error_message = str(e)
        job.completed_at = timezone.now()
        job.save()
        return f"Backtest failed for job {job_id}: {str(e)}"

@shared_task
def run_demo_trade_task(job_id):
    """Run demo trade for a job"""
    job = Job.objects.get(id=job_id)
    
    try:
        job.status = 'running'
        job.started_at = timezone.now()
        job.save()
        
        # Clean up any previous results for this job before creating a new one
        if job.result_id:
            job.result = None
            job.save(update_fields=['result'])
        job.results.all().delete()
        
        logger.info(f"Starting demo trade for job {job_id}")
        
        # For demo trading, we'll simulate real-time data
        # This is a placeholder for future implementation
        
        # Disable fixed demo outputs; mark as not implemented
        logger.error("Demo trading is not implemented without real-time data source")
        job.status = 'failed'
        job.error_message = 'Demo trading not implemented without real-time data source'
        job.completed_at = timezone.now()
        job.save()
        return f"Demo trade failed for job {job_id}: Not implemented"
        
    except Exception as e:
        logger.error(f"Demo trade failed for job {job_id}: {str(e)}")
        job.status = 'failed'
        job.error_message = str(e)
        job.completed_at = timezone.now()
        job.save()
        return f"Demo trade failed for job {job_id}: {str(e)}"


@shared_task
def update_demo_trades_prices_task():
    """
    Periodic task to update prices of open demo trades
    Should be scheduled to run every few seconds (e.g., every 5-10 seconds)
    """
    try:
        from api.demo_trading import update_demo_trades_prices
        
        logger.debug("Running demo trades price update task...")
        result = update_demo_trades_prices()
        
        if result['updated'] > 0 or result['closed'] > 0:
            logger.info(f"Demo trades updated: {result['updated']} updated, {result['closed']} closed")
        
        return result
    except Exception as e:
        logger.error(f"Error in update_demo_trades_prices_task: {e}")
        return {'updated': 0, 'closed': 0, 'errors': 1}


@shared_task
def run_auto_trading():
    """
    Periodic task to check all active auto-trading strategies and execute trades.
    This task should be scheduled to run every few minutes (e.g., every 5 minutes).
    """
    from core.models import AutoTradingSettings
    from api.auto_trader import execute_auto_trade, manage_open_trades
    
    logger.info("Starting auto trading cycle")
    
    results = []
    
    # Manage existing open trades (update prices, etc.)
    management_result = manage_open_trades()
    logger.info(f"Trade management result: {management_result}")
    
    # Get all enabled auto trading settings
    enabled_settings = AutoTradingSettings.objects.filter(
        is_enabled=True,
        strategy__is_active=True,
        strategy__processing_status='processed'
    )
    
    logger.info(f"Found {enabled_settings.count()} enabled auto trading strategies")
    
    for settings in enabled_settings:
        # Check if enough time has passed since last check
        if settings.last_check_time:
            time_since_last_check = timezone.now() - settings.last_check_time
            required_interval = timedelta(minutes=settings.check_interval_minutes)
            
            if time_since_last_check < required_interval:
                logger.debug(f"Skipping {settings.strategy.name} (ID: {settings.id}) - only {time_since_last_check.total_seconds()/60:.1f} minutes passed, need {settings.check_interval_minutes} minutes")
                continue
            else:
                logger.info(f"Processing {settings.strategy.name} (ID: {settings.id}) - {time_since_last_check.total_seconds()/60:.1f} minutes since last check")
        else:
            logger.info(f"Processing {settings.strategy.name} (ID: {settings.id}) - first check (no last_check_time)")
        
        try:
            result = execute_auto_trade(settings)
            results.append({
                'strategy': settings.strategy.name,
                'result': result
            })
            logger.info(f"Auto trading result for {settings.strategy.name}: status={result.get('status')}, message={result.get('message')}")
        except Exception as e:
            logger.exception(f"Error executing auto trade for {settings.id}: {e}")
            results.append({
                'strategy': settings.strategy.name,
                'result': {'status': 'error', 'message': str(e)}
            })
    
    logger.info(f"Auto trading cycle completed. Processed {len(results)} strategies")
    
    return {
        'status': 'completed',
        'results': results,
        'management': management_result
    }

# Removed hardcoded mock result helper to avoid fixed outputs.


@shared_task
def run_optimization_task(optimization_id):
    """Run strategy optimization task"""
    from django.utils import timezone
    from core.models import StrategyOptimization
    from ai_module.strategy_optimizer import OptimizationEngine
    from api.data_providers import DataProviderManager
    from ai_module.backtest_engine import BacktestEngine
    import traceback
    
    logger.info(f"Starting optimization task for optimization ID: {optimization_id}")
    
    try:
        optimization = StrategyOptimization.objects.get(id=optimization_id)
        strategy = optimization.strategy
        
        if not strategy.parsed_strategy_data:
            optimization.status = 'failed'
            optimization.error_message = 'استراتژی پردازش نشده است'
            optimization.save(update_fields=['status', 'error_message'])
            return
        
        # Check if cancelled before starting
        optimization.refresh_from_db()
        if optimization.status == 'cancelled':
            logger.info(f"Optimization {optimization_id} was cancelled before starting")
            return
        
        optimization.status = 'running'
        optimization.started_at = timezone.now()
        optimization.save(update_fields=['status', 'started_at'])
        
        # Get historical data
        settings = optimization.optimization_settings or {}
        symbol = settings.get('symbol') or strategy.parsed_strategy_data.get('symbol', 'EURUSD')
        timeframe_days = settings.get('timeframe_days', 365)
        
        logger.info(f"Fetching historical data: symbol={symbol}, days={timeframe_days}")
        data_provider = DataProviderManager()
        historical_data = data_provider.get_historical_data(
            symbol=symbol,
            timeframe_days=timeframe_days
        )
        
        if historical_data is None or historical_data.empty:
            optimization.status = 'failed'
            optimization.error_message = 'داده تاریخی در دسترس نیست'
            optimization.save(update_fields=['status', 'error_message'])
            return
        
        logger.info(f"Historical data shape: {historical_data.shape}")
        
        # Initialize optimization engine
        engine = OptimizationEngine(
            strategy.parsed_strategy_data,
            historical_data
        )
        
        # Run optimization
        method = optimization.method
        objective = optimization.objective
        optimizer_type = optimization.optimizer_type
        
        kwargs = {
            'n_trials': settings.get('n_trials', 50),
            'n_episodes': settings.get('n_episodes', 50),
            'ml_method': settings.get('ml_method', 'bayesian'),
            'dl_method': settings.get('dl_method', 'reinforcement_learning'),
        }
        
        logger.info(f"Running optimization: method={method}, objective={objective}")
        
        # Create a thread to periodically save progress
        import threading
        import time
        
        # Flag to track cancellation
        cancelled_flag = {'cancelled': False}
        
        def save_progress_periodically():
            """Periodically save optimization history to database"""
            while True:
                try:
                    optimization.refresh_from_db()
                    if optimization.status != 'running':
                        if optimization.status == 'cancelled':
                            cancelled_flag['cancelled'] = True
                        break
                    
                    # Check if cancelled
                    if optimization.status == 'cancelled':
                        cancelled_flag['cancelled'] = True
                        logger.info(f"Optimization {optimization_id} was cancelled")
                        break
                    
                    # Get current history from the active optimizer
                    history = []
                    best_score = 0.0
                    
                    if optimizer_type == 'ml' or method in ['ml', 'hybrid', 'auto']:
                        if hasattr(engine, 'ml_optimizer') and hasattr(engine.ml_optimizer, 'optimization_history'):
                            history = engine.ml_optimizer.optimization_history
                            if hasattr(engine.ml_optimizer, 'best_score'):
                                best_score = engine.ml_optimizer.best_score
                    
                    if optimizer_type == 'dl' or method in ['dl', 'hybrid', 'auto']:
                        if hasattr(engine, 'dl_optimizer') and hasattr(engine.dl_optimizer, 'optimization_history'):
                            if len(engine.dl_optimizer.optimization_history) > len(history):
                                history = engine.dl_optimizer.optimization_history
                            if hasattr(engine.dl_optimizer, 'best_score'):
                                best_score = max(best_score, engine.dl_optimizer.best_score)
                    
                    if history:
                        optimization.optimization_history = history
                        optimization.best_score = best_score
                        optimization.save(update_fields=['optimization_history', 'best_score'])
                    
                    time.sleep(5)  # Save every 5 seconds
                except Exception as e:
                    logger.warning(f"Error saving progress: {str(e)}")
                    time.sleep(5)
        
        # Start progress saving thread
        progress_thread = threading.Thread(target=save_progress_periodically, daemon=True)
        progress_thread.start()
        
        # Run optimization
        try:
            results = engine.optimize(
                method=method,
                optimizer_type=optimizer_type,
                objective=objective,
                **kwargs
            )
        except Exception as opt_error:
            # Check if cancelled
            optimization.refresh_from_db()
            if optimization.status == 'cancelled' or cancelled_flag['cancelled']:
                logger.info(f"Optimization {optimization_id} was cancelled during execution")
                optimization.status = 'cancelled'
                optimization.completed_at = timezone.now()
                optimization.error_message = 'بهینه‌سازی توسط کاربر لغو شد'
                optimization.save(update_fields=['status', 'completed_at', 'error_message'])
                return
            raise opt_error
        
        # Check if cancelled before final update
        optimization.refresh_from_db()
        if optimization.status == 'cancelled' or cancelled_flag['cancelled']:
            logger.info(f"Optimization {optimization_id} was cancelled before final update")
            optimization.status = 'cancelled'
            optimization.completed_at = timezone.now()
            optimization.error_message = 'بهینه‌سازی توسط کاربر لغو شد'
            optimization.save(update_fields=['status', 'completed_at', 'error_message'])
            return
        
        # Final update
        optimization.optimized_params = results.get('best_params')
        optimization.best_score = results.get('best_score', 0.0)
        optimization.optimization_history = results.get('optimization_history', [])
        optimization.status = 'completed'
        optimization.completed_at = timezone.now()
        
        # Calculate improvement
        optimization.calculate_improvement()
        
        optimization.save()
        
        logger.info(f"Optimization completed successfully. Best score: {optimization.best_score:.4f}")
        
    except StrategyOptimization.DoesNotExist:
        logger.error(f"Optimization {optimization_id} not found")
    except Exception as e:
        error_trace = traceback.format_exc()
        logger.error(f"Optimization task failed: {str(e)}\n{error_trace}")
        
        try:
            optimization = StrategyOptimization.objects.get(id=optimization_id)
            optimization.status = 'failed'
            optimization.error_message = f"{str(e)}\n{error_trace[:500]}"
            optimization.save(update_fields=['status', 'error_message'])
        except Exception:
            pass