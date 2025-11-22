import os, sys, json
sys.path.append('backend')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
import django
django.setup()
from ai_module.providers import OpenAIProvider
provider = OpenAIProvider()
print('provider_available', provider.is_available())
result = provider.generate(
    'Respond with {"status":"ok"}',
    {'temperature': 0.1, 'max_output_tokens': 64},
    metadata={'use_json_response_format': True}
)
print('success', result.success)
print('status_code', result.status_code)
print('error', result.error)
print('text', (result.text or '')[:400])
raw = result.raw_response
if isinstance(raw, dict):
    print('raw_response', json.dumps(raw)[:400])
else:
    print('raw_response', raw)
