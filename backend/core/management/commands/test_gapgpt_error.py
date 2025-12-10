"""
دستور مدیریتی Django برای تست خطای GapGPT
استفاده: python manage.py test_gapgpt_error
"""

from django.core.management.base import BaseCommand
import requests
import json
from ai_module.gapgpt_client import get_gapgpt_api_key
from ai_module.provider_manager import get_provider_manager
from ai_module.gemini_client import parse_with_gemini
from django.contrib.auth.models import User


class Command(BaseCommand):
    help = 'تست خطای GapGPT و نمایش جزئیات دقیق'

    def add_arguments(self, parser):
        parser.add_argument(
            '--user-id',
            type=int,
            help='ID کاربر برای تست (اختیاری)',
        )

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('\n' + '=' * 80))
        self.stdout.write(self.style.SUCCESS('🧪 تست GapGPT Error'))
        self.stdout.write(self.style.SUCCESS('=' * 80 + '\n'))

        user_id = options.get('user_id')
        user = None
        if user_id:
            try:
                user = User.objects.get(id=user_id)
                self.stdout.write(f'👤 استفاده از کاربر: {user.username} (ID: {user.id})')
            except User.DoesNotExist:
                self.stdout.write(self.style.WARNING(f'⚠️  کاربر با ID {user_id} یافت نشد'))
        else:
            user = User.objects.first()
            if user:
                self.stdout.write(f'👤 استفاده از کاربر: {user.username} (ID: {user.id})')
            else:
                self.stdout.write(self.style.WARNING('⚠️  کاربری یافت نشد، استفاده از None'))

        # تست 1: تست مستقیم API
        self.test_direct_api()

        # تست 2: تست Provider Manager
        self.test_provider_manager(user)

        # تست 3: تست parse_with_gemini
        self.test_parse_with_gemini(user)

        self.stdout.write(self.style.SUCCESS('\n' + '=' * 80))
        self.stdout.write(self.style.SUCCESS('✅ تست‌ها کامل شدند'))
        self.stdout.write(self.style.SUCCESS('=' * 80 + '\n'))

    def test_direct_api(self):
        """تست مستقیم API GapGPT"""
        self.stdout.write('\n' + '-' * 80)
        self.stdout.write('📡 تست مستقیم API GapGPT')
        self.stdout.write('-' * 80 + '\n')

        api_key = get_gapgpt_api_key()
        if not api_key:
            self.stdout.write(self.style.ERROR('❌ کلید API GapGPT یافت نشد!'))
            return

        self.stdout.write(f'✅ کلید API یافت شد: {api_key[:20]}... (طول: {len(api_key)})')

        endpoint = "https://api.gapgpt.app/v1/chat/completions"
        payload = {
            "model": "gpt-4o",
            "messages": [
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": "Say 'test'"}
            ],
            "temperature": 0.3,
            "max_tokens": 50
        }

        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }

        self.stdout.write(f'\n📤 ارسال درخواست به: {endpoint}')
        self.stdout.write(f'📤 Model: {payload["model"]}')

        try:
            response = requests.post(endpoint, headers=headers, json=payload, timeout=30)

            self.stdout.write(f'\n📥 Status Code: {response.status_code}')

            if response.status_code == 200:
                data = response.json()
                self.stdout.write(self.style.SUCCESS('✅ درخواست موفق بود!'))
                if 'choices' in data and len(data['choices']) > 0:
                    content = data['choices'][0].get('message', {}).get('content', '')
                    self.stdout.write(f'📄 Response: {content}')
            else:
                self.stdout.write(self.style.ERROR(f'❌ خطا دریافت شد: {response.status_code}'))

                try:
                    response.encoding = 'utf-8'
                    error_data = response.json()
                    self.stdout.write(f'\n📄 Error Response (JSON):')
                    self.stdout.write(json.dumps(error_data, indent=2, ensure_ascii=False))

                    error_detail = error_data.get('error', {})
                    if isinstance(error_detail, dict):
                        error_message = error_detail.get('message', '')
                        error_code = error_detail.get('code', '')
                        error_type = error_detail.get('type', '')

                        self.stdout.write(f'\n🔍 جزئیات خطا:')
                        self.stdout.write(f'   Message: {error_message}')
                        self.stdout.write(f'   Code: {error_code}')
                        self.stdout.write(f'   Type: {error_type}')

                        # بررسی quota error
                        is_quota = False
                        if error_message and any(char in error_message for char in ['预扣费', '额度', '剩余额度', '需要']):
                            is_quota = True
                            self.stdout.write(self.style.WARNING('\n⚠️  این خطا مربوط به QUOTA است!'))
                        elif error_message and ('额度' in error_message or 'quota' in error_message.lower() or 'insufficient' in error_message.lower()):
                            is_quota = True
                            self.stdout.write(self.style.WARNING('\n⚠️  این خطا مربوط به QUOTA است!'))
                        else:
                            self.stdout.write(self.style.WARNING('\n⚠️  این خطا مربوط به QUOTA نیست!'))
                            self.stdout.write('   احتمالاً مشکل دیگری است (مدل، دسترسی، و غیره)')

                    elif isinstance(error_detail, str):
                        self.stdout.write(f'\n🔍 Error Message: {error_detail}')

                except Exception as e:
                    self.stdout.write(f'\n📄 Error Response (Text):')
                    self.stdout.write(response.text[:500])
                    self.stdout.write(self.style.ERROR(f'\n⚠️  خطا در خواندن JSON: {e}'))

        except requests.exceptions.Timeout:
            self.stdout.write(self.style.ERROR('❌ Timeout: درخواست بیش از 30 ثانیه طول کشید'))
        except requests.exceptions.ConnectionError as e:
            self.stdout.write(self.style.ERROR(f'❌ Connection Error: {e}'))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'❌ Unexpected Error: {e}'))
            import traceback
            self.stdout.write(traceback.format_exc())

    def test_provider_manager(self, user):
        """تست Provider Manager"""
        self.stdout.write('\n' + '-' * 80)
        self.stdout.write('🔧 تست Provider Manager')
        self.stdout.write('-' * 80 + '\n')

        manager = get_provider_manager(user=user)

        self.stdout.write(f'📋 Providers موجود: {list(manager.providers.keys())}')
        self.stdout.write(f'📋 Priority List: {manager._get_priority_list()}')
        self.stdout.write(f'📋 Has Available Provider: {manager.has_available_provider()}')

        gapgpt_provider = manager.providers.get('gapgpt')
        if gapgpt_provider:
            self.stdout.write(f'\n🔍 GapGPT Provider:')
            self.stdout.write(f'   Available: {gapgpt_provider.is_available()}')
            api_key = gapgpt_provider.get_api_key()
            if api_key:
                self.stdout.write(f'   API Key: {api_key[:20]}... (length: {len(api_key)})')
            else:
                self.stdout.write(f'   API Key: None')

        self.stdout.write(f'\n🧪 تست generate با prompt ساده...')
        test_prompt = "Say 'test' and return {\"status\": \"ok\"} as JSON."

        try:
            result = manager.generate(
                test_prompt,
                {
                    'temperature': 0.3,
                    'max_output_tokens': 50,
                },
                metadata={'use_json_response_format': True}
            )

            self.stdout.write(f'\n📊 Result:')
            self.stdout.write(f'   Success: {result.success}')
            self.stdout.write(f'   Provider: {result.provider}')
            self.stdout.write(f'   Status Code: {result.status_code}')
            self.stdout.write(f'   Tokens Used: {result.tokens_used}')

            if result.success:
                self.stdout.write(self.style.SUCCESS(f'   ✅ Text: {result.text[:200]}'))
            else:
                self.stdout.write(self.style.ERROR(f'   ❌ Error: {result.error}'))
                self.stdout.write(f'   Attempts: {len(result.attempts)}')
                for i, attempt in enumerate(result.attempts, 1):
                    self.stdout.write(f'\n   Attempt {i}:')
                    self.stdout.write(f'      Provider: {attempt.provider}')
                    self.stdout.write(f'      Success: {attempt.success}')
                    self.stdout.write(f'      Status Code: {attempt.status_code}')
                    self.stdout.write(f'      Error: {attempt.error}')
                    self.stdout.write(f'      Latency: {attempt.latency_ms}ms')

        except Exception as e:
            self.stdout.write(self.style.ERROR(f'❌ Error in generate: {e}'))
            import traceback
            self.stdout.write(traceback.format_exc())

    def test_parse_with_gemini(self, user):
        """تست parse_with_gemini"""
        self.stdout.write('\n' + '-' * 80)
        self.stdout.write('📝 تست parse_with_gemini')
        self.stdout.write('-' * 80 + '\n')

        test_text = """
        استراتژی معاملاتی:
        - ورود: وقتی RSI زیر 30 باشد
        - خروج: وقتی RSI بالای 70 باشد
        - Stop Loss: 50 پیپ
        - Take Profit: 100 پیپ
        - نماد: EURUSD
        - تایم‌فریم: H1
        """

        self.stdout.write(f'🧪 تست parse_with_gemini...')

        try:
            result = parse_with_gemini(test_text, user=user)

            self.stdout.write(f'\n📊 Result:')
            self.stdout.write(f'   AI Status: {result.get("ai_status")}')
            self.stdout.write(f'   Message: {result.get("message")}')
            self.stdout.write(f'   Provider: {result.get("provider")}')
            self.stdout.write(f'   Status Code: {result.get("status_code")}')

            if result.get('ai_status') == 'ok':
                self.stdout.write(self.style.SUCCESS('   ✅ موفق بود!'))
                self.stdout.write(f'   Entry Conditions: {result.get("entry_conditions", [])}')
                self.stdout.write(f'   Exit Conditions: {result.get("exit_conditions", [])}')
            else:
                self.stdout.write(self.style.ERROR('   ❌ خطا:'))
                self.stdout.write(f'   Error: {result.get("error")}')
                self.stdout.write(f'   Provider Attempts: {len(result.get("provider_attempts", []))}')

                for i, attempt in enumerate(result.get('provider_attempts', []), 1):
                    self.stdout.write(f'\n   Attempt {i}:')
                    if isinstance(attempt, dict):
                        self.stdout.write(f'      Provider: {attempt.get("provider")}')
                        self.stdout.write(f'      Success: {attempt.get("success")}')
                        self.stdout.write(f'      Status Code: {attempt.get("status_code")}')
                        self.stdout.write(f'      Error: {attempt.get("error")}')
                        self.stdout.write(f'      Latency: {attempt.get("latency_ms")}ms')
                    else:
                        self.stdout.write(f'      {attempt}')

        except Exception as e:
            self.stdout.write(self.style.ERROR(f'❌ Error in parse_with_gemini: {e}'))
            import traceback
            self.stdout.write(traceback.format_exc())
