"""
Test script to verify GapGPT conversion works with backtest
"""
import os
import sys
import django

# Setup Django
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django.contrib.auth.models import User
from core.models import TradingStrategy, Job
from ai_module.gapgpt_client import convert_strategy_with_gapgpt, get_gapgpt_api_key
from api.tasks import run_backtest_task
from django.utils import timezone
import json

def test_gapgpt_backtest():
    """Test backtest with GapGPT converted strategy"""
    
    print("=" * 80)
    print("Test: GapGPT Conversion + Backtest")
    print("=" * 80)
    
    # 1. Get or create a test user
    try:
        user = User.objects.filter(is_superuser=True).first()
        if not user:
            user = User.objects.create_user(
                username='test_gapgpt',
                email='test@example.com',
                password='test123'
            )
        print(f"✓ Using user: {user.username}")
    except Exception as e:
        print(f"✗ Error creating user: {e}")
        return
    
    # 2. Check if GapGPT API key is available
    api_key = get_gapgpt_api_key(user=user)
    if not api_key:
        print("✗ GapGPT API key not found. Please add it via API Configurations.")
        return
    print(f"✓ GapGPT API key found")
    
    # 3. Create a test strategy with text
    strategy_text = """
    استراتژی معاملاتی:
    - ورود: وقتی RSI کمتر از 30 باشد و قیمت بالاتر از میانگین متحرک 20 روزه باشد
    - خروج: وقتی RSI بیشتر از 70 باشد یا سود 5 درصد باشد
    - سمبل: XAU/USD
    - تایم فریم: M15
    """
    
    try:
        strategy = TradingStrategy.objects.create(
            user=user,
            name="Test GapGPT Strategy",
            description=strategy_text,
            processing_status='pending'
        )
        print(f"✓ Created strategy: {strategy.id}")
    except Exception as e:
        print(f"✗ Error creating strategy: {e}")
        return
    
    # 4. Convert strategy with GapGPT
    print("\n" + "-" * 80)
    print("Step 1: Converting strategy with GapGPT...")
    print("-" * 80)
    
    try:
        conversion_result = convert_strategy_with_gapgpt(
            strategy_text=strategy_text,
            model_id=None,  # Use default
            user=user,
            temperature=0.3,
            max_tokens=2000
        )
        
        if not conversion_result.get('success'):
            print(f"✗ GapGPT conversion failed: {conversion_result.get('error', 'Unknown error')}")
            strategy.delete()
            return
        
        converted_strategy = conversion_result.get('converted_strategy')
        print(f"✓ GapGPT conversion successful")
        print(f"  - Model used: {conversion_result.get('model_used', 'unknown')}")
        print(f"  - Tokens used: {conversion_result.get('tokens_used', 0)}")
        
        # Print structure of converted strategy
        print("\nConverted strategy structure:")
        print(json.dumps(converted_strategy, indent=2, ensure_ascii=False)[:1000])
        print("...")
        
    except Exception as e:
        print(f"✗ Error in GapGPT conversion: {e}")
        import traceback
        traceback.print_exc()
        strategy.delete()
        return
    
    # 5. Save converted strategy to database
    print("\n" + "-" * 80)
    print("Step 2: Saving converted strategy to database...")
    print("-" * 80)
    
    try:
        # Add metadata
        converted_strategy_with_meta = converted_strategy.copy()
        converted_strategy_with_meta['conversion_source'] = 'gapgpt'
        converted_strategy_with_meta['converted_at'] = timezone.now().isoformat()
        converted_strategy_with_meta['model_used'] = conversion_result.get('model_used', 'unknown')
        converted_strategy_with_meta['tokens_used'] = conversion_result.get('tokens_used', 0)
        
        # Ensure confidence_score exists
        if 'confidence_score' not in converted_strategy_with_meta:
            score = 0.0
            if converted_strategy_with_meta.get('entry_conditions'):
                score += 0.3
            if converted_strategy_with_meta.get('exit_conditions'):
                score += 0.3
            if converted_strategy_with_meta.get('indicators'):
                score += 0.2
            if converted_strategy_with_meta.get('risk_management'):
                score += 0.2
            converted_strategy_with_meta['confidence_score'] = min(score, 1.0)
        
        # Save to strategy
        strategy.parsed_strategy_data = converted_strategy_with_meta
        strategy.processing_status = 'processed'
        strategy.processed_at = timezone.now()
        strategy.save()
        
        print(f"✓ Saved converted strategy to database")
        print(f"  - processing_status: {strategy.processing_status}")
        print(f"  - parsed_strategy_data keys: {list(strategy.parsed_strategy_data.keys()) if strategy.parsed_strategy_data else 'None'}")
        
        # Check required fields
        required_fields = ['entry_conditions', 'exit_conditions']
        missing_fields = [field for field in required_fields if not converted_strategy_with_meta.get(field)]
        if missing_fields:
            print(f"⚠ Warning: Missing fields: {missing_fields}")
        else:
            print(f"✓ All required fields present")
            
    except Exception as e:
        print(f"✗ Error saving converted strategy: {e}")
        import traceback
        traceback.print_exc()
        strategy.delete()
        return
    
    # 6. Create a backtest job
    print("\n" + "-" * 80)
    print("Step 3: Creating backtest job...")
    print("-" * 80)
    
    try:
        job = Job.objects.create(
            user=user,
            strategy=strategy,
            job_type='backtest',
            status='pending'
        )
        print(f"✓ Created job: {job.id}")
    except Exception as e:
        print(f"✗ Error creating job: {e}")
        strategy.delete()
        return
    
    # 7. Run backtest
    print("\n" + "-" * 80)
    print("Step 4: Running backtest...")
    print("-" * 80)
    
    try:
        result = run_backtest_task(
            job.id,
            timeframe_days=7,  # Short timeframe for testing
            symbol_override='XAUUSD',
            initial_capital=10000,
            selected_indicators=None,
            ai_provider='gapgpt'
        )
        
        # Refresh job
        job.refresh_from_db()
        
        print(f"\n✓ Backtest completed")
        print(f"  - Job status: {job.status}")
        print(f"  - Error message: {job.error_message or 'None'}")
        
        if job.result_id:
            from core.models import Result
            result_obj = job.result
            print(f"  - Result ID: {result_obj.id}")
            print(f"  - Total trades: {result_obj.total_trades}")
            print(f"  - Win rate: {result_obj.win_rate:.2f}%")
            print(f"  - Total return: {result_obj.total_return:.2f}%")
            print(f"✓ BACKTEST SUCCESSFUL!")
        else:
            print(f"✗ BACKTEST FAILED - No result created")
            print(f"  Error: {job.error_message}")
            
    except Exception as e:
        print(f"\n✗ Error running backtest: {e}")
        import traceback
        traceback.print_exc()
        job.refresh_from_db()
        print(f"  - Job status: {job.status}")
        print(f"  - Error message: {job.error_message or str(e)}")
    
    # 8. Cleanup (optional)
    print("\n" + "-" * 80)
    print("Cleanup")
    print("-" * 80)
    print("Test objects created:")
    print(f"  - Strategy ID: {strategy.id}")
    print(f"  - Job ID: {job.id}")
    print("\nTo cleanup, run:")
    print(f"  Strategy.objects.filter(id={strategy.id}).delete()")
    print(f"  Job.objects.filter(id={job.id}).delete()")

if __name__ == '__main__':
    test_gapgpt_backtest()




