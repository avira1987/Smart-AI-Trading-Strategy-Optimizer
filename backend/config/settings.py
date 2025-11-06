import os
import sys
import logging
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

# Fix console encoding for Windows to support Persian/Farsi characters
if sys.platform == 'win32':
    try:
        # Try to set stdout encoding to UTF-8
        if hasattr(sys.stdout, 'reconfigure'):
            sys.stdout.reconfigure(encoding='utf-8', errors='replace')
        if hasattr(sys.stderr, 'reconfigure'):
            sys.stderr.reconfigure(encoding='utf-8', errors='replace')
    except Exception:
        # If reconfiguration fails, we'll use a safe handler
        pass

BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = os.environ.get('SECRET_KEY', 'django-insecure-please-change-in-production')
DEBUG = os.environ.get('DEBUG', 'True') == 'True'
ENV = os.environ.get('ENV', 'LOCAL')

# Helper function to get API key from environment or APIConfiguration
def get_api_key_from_db_or_env(provider_name: str, env_var_name: str = None) -> str:
    """Get API key from APIConfiguration model or environment variable"""
    # First try environment variable
    if env_var_name:
        api_key = os.environ.get(env_var_name, '')
        if api_key:
            return api_key
    
    # Then try APIConfiguration model
    try:
        from core.models import APIConfiguration
        api_config = APIConfiguration.objects.filter(provider=provider_name, is_active=True).first()
        if api_config:
            return api_config.api_key
    except Exception:
        # If models are not loaded yet (during initial setup), just return empty
        pass
    
    return ''

GEMINI_API_KEY = get_api_key_from_db_or_env('gemini', 'GEMINI_API_KEY')
GEMINI_MODEL = os.environ.get('GEMINI_MODEL', 'gemini-2.0-flash')
GEMINI_MAX_OUTPUT_TOKENS = int(os.environ.get('GEMINI_MAX_OUTPUT_TOKENS', '2048'))
# Default to True if not explicitly set to False
GEMINI_ENABLED = os.environ.get('GEMINI_ENABLED', 'True') == 'True'

# Zarinpal Payment Gateway Settings
ZARINPAL_MERCHANT_ID = get_api_key_from_db_or_env('zarinpal', 'ZARINPAL_MERCHANT_ID')
if not ZARINPAL_MERCHANT_ID:
    # Only raise error in production, allow empty in development
    if ENV != 'LOCAL' and not DEBUG:
        raise ValueError("ZARINPAL_MERCHANT_ID environment variable or APIConfiguration is required in production")
ZARINPAL_SANDBOX = os.environ.get('ZARINPAL_SANDBOX', 'False') == 'True'  # Set to 'True' for sandbox, 'False' for production

# Kavenegar SMS Settings
KAVENEGAR_API_KEY = get_api_key_from_db_or_env('kavenegar', 'KAVENEGAR_API_KEY')
KAVENEGAR_SENDER = os.environ.get('KAVENEGAR_SENDER', '')

# Google OAuth Settings
GOOGLE_CLIENT_ID = get_api_key_from_db_or_env('google_oauth', 'GOOGLE_CLIENT_ID')

# Frontend URL for payment callbacks
FRONTEND_URL = os.environ.get('FRONTEND_URL', 'http://localhost:3000')

# Allow access from local network
# In development, allow all hosts for local network access
# In production, set ALLOWED_HOSTS environment variable with specific hosts
default_allowed_hosts = 'localhost,127.0.0.1,0.0.0.0'

def get_local_network_hosts():
    """Get local network IP addresses for ALLOWED_HOSTS"""
    hosts = ['localhost', '127.0.0.1', '0.0.0.0']
    try:
        import socket
        # Get local IP address
        hostname = socket.gethostname()
        local_ip = socket.gethostbyname(hostname)
        hosts.append(local_ip)
        
        # Try to get all network interfaces
        import subprocess
        if sys.platform == 'win32':
            # Windows: Get IP addresses using ipconfig
            result = subprocess.run(['ipconfig'], capture_output=True, text=True, timeout=2)
            for line in result.stdout.split('\n'):
                if 'IPv4' in line or 'IP Address' in line:
                    ip = line.split(':')[-1].strip()
                    if ip and ip not in hosts and ip.startswith(('192.168.', '10.', '172.')):
                        hosts.append(ip)
        else:
            # Linux/Mac: Get IP addresses
            result = subprocess.run(['hostname', '-I'], capture_output=True, text=True, timeout=2)
            if result.returncode == 0:
                for ip in result.stdout.strip().split():
                    if ip and ip not in hosts:
                        hosts.append(ip)
    except Exception:
        # If we can't detect IPs, just use defaults
        pass
    return hosts

if DEBUG:
    # In debug mode, allow local network access
    ALLOWED_HOSTS = get_local_network_hosts()
    # Note: We can't use '*' in ALLOWED_HOSTS, but we'll handle it in middleware
else:
    ALLOWED_HOSTS = os.environ.get('ALLOWED_HOSTS', default_allowed_hosts).split(',')

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'rest_framework',
    'corsheaders',
    'core',
    'api',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'corsheaders.middleware.CorsMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'config.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'config.wsgi.application'

# Database
if ENV == 'LOCAL':
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': BASE_DIR / 'db.sqlite3',
        }
    }
else:
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.postgresql',
            'NAME': os.environ.get('DB_NAME'),
            'USER': os.environ.get('DB_USER'),
            'PASSWORD': os.environ.get('DB_PASSWORD'),
            'HOST': os.environ.get('DB_HOST'),
            'PORT': os.environ.get('DB_PORT', '5432'),
        }
    }

# Password validation
AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

# Internationalization
LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_TZ = True

# Static files
STATIC_URL = '/static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'
MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'
CACHE_DIR = BASE_DIR / 'cache'

# Create directories
for directory in [STATIC_ROOT, MEDIA_ROOT, CACHE_DIR]:
    directory.mkdir(parents=True, exist_ok=True)

# Default primary key field type
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# REST Framework
REST_FRAMEWORK = {
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.AllowAny',  # Default to AllowAny, override in views
    ],
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework.authentication.SessionAuthentication',
    ],
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
    'PAGE_SIZE': 20,
}

# CORS
# Allow CORS from local network in development
if DEBUG:
    # In debug mode, allow all origins for local network access
    CORS_ALLOW_ALL_ORIGINS = True
else:
    CORS_ALLOWED_ORIGINS = [
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost",
        "http://127.0.0.1",
    ]

CORS_ALLOW_CREDENTIALS = True

# CSRF settings - exempt API endpoints from CSRF protection
# Allow CSRF from local network in development
def get_local_network_origins():
    """Get all local network origins for CSRF_TRUSTED_ORIGINS"""
    origins = [
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost",
        "http://127.0.0.1",
    ]
    
    try:
        import socket
        import subprocess
        
        # Get all local network IPs
        all_ips = set()
        
        # Method 1: Get hostname IP
        try:
            hostname = socket.gethostname()
            local_ip = socket.gethostbyname(hostname)
            all_ips.add(local_ip)
        except Exception:
            pass
        
        # Method 2: Get all network interfaces
        if sys.platform == 'win32':
            # Windows: Parse ipconfig output
            try:
                result = subprocess.run(['ipconfig'], capture_output=True, text=True, timeout=2)
                for line in result.stdout.split('\n'):
                    if 'IPv4' in line or 'IP Address' in line:
                        parts = line.split(':')
                        if len(parts) > 1:
                            ip = parts[-1].strip()
                            if ip and ip.startswith(('192.168.', '10.', '172.16.', '172.17.', '172.18.', '172.19.', '172.20.', '172.21.', '172.22.', '172.23.', '172.24.', '172.25.', '172.26.', '172.27.', '172.28.', '172.29.', '172.30.', '172.31.')):
                                all_ips.add(ip)
            except Exception:
                pass
        else:
            # Linux/Mac: Use hostname -I
            try:
                result = subprocess.run(['hostname', '-I'], capture_output=True, text=True, timeout=2)
                if result.returncode == 0:
                    for ip in result.stdout.strip().split():
                        if ip and ip.startswith(('192.168.', '10.', '172.16.', '172.17.', '172.18.', '172.19.', '172.20.', '172.21.', '172.22.', '172.23.', '172.24.', '172.25.', '172.26.', '172.27.', '172.28.', '172.29.', '172.30.', '172.31.')):
                            all_ips.add(ip)
            except Exception:
                pass
        
        # Method 3: Try to connect to external IP to determine local network
        try:
            # Connect to a public DNS to determine local IP
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(('8.8.8.8', 80))
            local_ip = s.getsockname()[0]
            s.close()
            if local_ip:
                all_ips.add(local_ip)
        except Exception:
            pass
        
        # Add all detected IPs with common ports
        for ip in all_ips:
            for port in [3000, 8000, 3001, 8080]:
                origin = f"http://{ip}:{port}"
                if origin not in origins:
                    origins.append(origin)
            # Also add without port
            origin_no_port = f"http://{ip}"
            if origin_no_port not in origins:
                origins.append(origin_no_port)
        
        # Add common local network subnets (first 50 IPs of common subnets)
        # This allows access from any device on the same subnet
        # Detect and add IPs from detected subnets
        detected_subnets = set()
        for ip in all_ips:
            parts = ip.split('.')
            if len(parts) == 4:
                # Extract subnet (first 3 octets)
                subnet = '.'.join(parts[:3])
                detected_subnets.add(subnet)
        
        # Also include common subnets that might be used
        common_subnets = [
            '192.168.0', '192.168.1', '192.168.100', '192.168.10', '192.168.20',
            '10.0.0', '10.0.1', '172.16.0', '172.17.0', '172.18.0'
        ]
        for subnet in common_subnets:
            detected_subnets.add(subnet)
        
        # Add first 50 IPs from each detected subnet
        for subnet in detected_subnets:
            for i in range(1, 51):
                ip = f"{subnet}.{i}"
                for port in [3000, 8000]:
                    origin = f"http://{ip}:{port}"
                    if origin not in origins:
                        origins.append(origin)
    
    except Exception:
        pass
    
    return origins

if DEBUG:
    # In debug mode, allow all local network IPs
    CSRF_TRUSTED_ORIGINS = get_local_network_origins()
else:
    CSRF_TRUSTED_ORIGINS = [
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost",
        "http://127.0.0.1",
    ]

# Disable CSRF for API endpoints (handled by DRF)
CSRF_COOKIE_SECURE = False  # Set to True in production with HTTPS
CSRF_COOKIE_HTTPONLY = False

# Celery
CELERY_BROKER_URL = os.environ.get('CELERY_BROKER_URL', 'redis://localhost:6379/0')
CELERY_RESULT_BACKEND = os.environ.get('REDIS_URL', 'redis://localhost:6379/0')
CELERY_ACCEPT_CONTENT = ['json']
CELERY_TASK_SERIALIZER = 'json'
CELERY_RESULT_SERIALIZER = 'json'
CELERY_TIMEZONE = TIME_ZONE

# Windows-specific Celery configuration
# Use 'solo' pool on Windows (prefork doesn't work on Windows)
if sys.platform == 'win32':
    CELERY_WORKER_POOL = 'solo'
    # Also set task_always_eager to False for async execution
    CELERY_TASK_ALWAYS_EAGER = False

# Celery Beat Schedule for periodic tasks
from celery.schedules import crontab
CELERY_BEAT_SCHEDULE = {
    'run-auto-trading': {
        'task': 'api.tasks.run_auto_trading',
        'schedule': crontab(minute='*/5'),  # Every 5 minutes
    },
    'update-ddns': {
        'task': 'api.tasks.update_ddns_task',
        'schedule': crontab(minute='*/5'),  # Every 5 minutes
    },
    'update-demo-trades-prices': {
        'task': 'api.tasks.update_demo_trades_prices_task',
        'schedule': 10.0,  # Every 10 seconds (for real-time price updates)
    },
}

# Logging
LOG_DIR = BASE_DIR / 'logs'
LOG_DIR.mkdir(exist_ok=True)

# Custom console handler that safely handles Unicode characters
class SafeUnicodeStreamHandler(logging.StreamHandler):
    """StreamHandler that safely encodes Unicode characters for console output
    
    On Windows, console may not support UTF-8, so we replace Persian/Arabic characters
    with ASCII-safe placeholders to prevent UnicodeEncodeError crashes.
    """
    def emit(self, record):
        try:
            msg = self.format(record)
            stream = self.stream
            
            # On Windows, console encoding is often cp1252 which can't handle Persian/Arabic
            # Replace non-ASCII characters with safe placeholders for console output
            # (File handlers will still receive full Unicode)
            safe_msg = msg
            try:
                # Try to encode to ASCII - if this fails, we'll replace non-ASCII chars
                safe_msg.encode('ascii')
            except UnicodeEncodeError:
                # Replace Persian/Arabic characters and other non-ASCII with placeholders
                import re
                # Replace Persian/Arabic characters with [FA] placeholder
                safe_msg = re.sub(r'[\u0600-\u06FF\u0750-\u077F\u08A0-\u08FF\uFB50-\uFDFF\uFE70-\uFEFF]+', '[FA]', msg)
                # Replace any remaining non-ASCII with [?]
                safe_msg = safe_msg.encode('ascii', errors='replace').decode('ascii')
            
            # Write to stream (console)
            try:
                if hasattr(stream, 'buffer'):
                    # Try UTF-8 first
                    try:
                        stream.buffer.write(safe_msg.encode('utf-8', errors='replace'))
                        stream.buffer.write(b'\n')
                        stream.buffer.flush()
                    except (UnicodeEncodeError, AttributeError):
                        # Final fallback: ASCII
                        stream.write(safe_msg + '\n')
                        stream.flush()
                else:
                    stream.write(safe_msg + '\n')
                    stream.flush()
            except (UnicodeEncodeError, AttributeError, OSError):
                # Silently ignore - file handlers will still log the full message
                pass
        except Exception:
            # Silently handle all errors - don't break logging
            pass

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'standard': {
            'format': '%(asctime)s [%(levelname)s] %(name)s: %(message)s',
            'datefmt': '%Y-%m-%d %H:%M:%S'
        },
        'detailed': {
            'format': '%(asctime)s [%(levelname)s] %(name)s [%(filename)s:%(lineno)d]: %(message)s',
            'datefmt': '%Y-%m-%d %H:%M:%S'
        },
    },
    'handlers': {
        'console': {
            '()': SafeUnicodeStreamHandler,
            'formatter': 'standard',
            'level': 'INFO',
        },
        'backtest_file': {
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': LOG_DIR / 'backtest.log',
            'maxBytes': 10 * 1024 * 1024,  # 10MB
            'backupCount': 5,
            'encoding': 'utf-8',
            'formatter': 'detailed',
            'level': 'DEBUG',
        },
        'api_file': {
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': LOG_DIR / 'api.log',
            'maxBytes': 10 * 1024 * 1024,  # 10MB
            'backupCount': 5,
            'encoding': 'utf-8',
            'formatter': 'detailed',
            'level': 'DEBUG',
        },
    },
    'loggers': {
        'api': {
            'handlers': ['console', 'api_file'],
            'level': 'DEBUG' if DEBUG else 'INFO',
            'propagate': False,
        },
        'api.tasks': {
            'handlers': ['console', 'backtest_file'],
            'level': 'DEBUG',
            'propagate': False,
        },
        'ai_module.backtest_engine': {
            'handlers': ['console', 'backtest_file'],
            'level': 'DEBUG',
            'propagate': False,
        },
        'core': {
            'handlers': ['console', 'api_file'],
            'level': 'DEBUG' if DEBUG else 'INFO',
            'propagate': False,
        },
        # capture third-party if needed
        '': {
            'handlers': ['console'],
            'level': 'INFO',
        },
    },
}

