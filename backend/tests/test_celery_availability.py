"""
Tests for the lightweight Celery availability probe used before starting jobs.
"""
import os
import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')

import django  # noqa: E402

django.setup()

import celery  # noqa: E402
import pytest  # noqa: E402
from redis.exceptions import RedisError  # noqa: E402

from backend.api import views  # noqa: E402


class DummyConf:
    def __init__(self, *, eager: bool, broker_url: str):
        self.task_always_eager = eager
        self.broker_url = broker_url


class DummyApp:
    def __init__(self, *, eager: bool, broker_url: str):
        self.conf = DummyConf(eager=eager, broker_url=broker_url)


def reset_cache():
    views.CELERY_CHECK_CACHE['timestamp'] = 0.0
    views.CELERY_CHECK_CACHE['available'] = False


@pytest.fixture(autouse=True)
def _reset_cache_each_test():
    reset_cache()
    yield
    reset_cache()


def test_celery_probe_returns_false_when_task_always_eager(monkeypatch):
    """If Celery runs eagerly, async availability should be reported as False."""
    dummy_app = DummyApp(eager=True, broker_url='redis://localhost:6379/0')
    monkeypatch.setattr(celery, 'current_app', dummy_app)

    available = views._is_celery_available_quick()

    assert available is False
    assert views.CELERY_CHECK_CACHE['available'] is False


def test_celery_probe_returns_false_when_redis_unreachable(monkeypatch):
    """If Redis ping fails, availability should be False."""
    dummy_app = DummyApp(eager=False, broker_url='redis://localhost:6379/0')
    monkeypatch.setattr(celery, 'current_app', dummy_app)

    def failing_from_url(*args, **kwargs):
        raise RedisError("redis down")

    monkeypatch.setattr(views.redis.Redis, 'from_url', staticmethod(failing_from_url))

    available = views._is_celery_available_quick()

    assert available is False
    assert views.CELERY_CHECK_CACHE['available'] is False


def test_celery_probe_caches_success_result(monkeypatch):
    """A successful probe should be cached to avoid repeated Redis pings."""
    dummy_app = DummyApp(eager=False, broker_url='redis://localhost:6379/0')
    monkeypatch.setattr(celery, 'current_app', dummy_app)

    ping_calls = {'count': 0}

    class DummyRedisClient:
        def ping(self):
            pass

    def successful_from_url(*args, **kwargs):
        ping_calls['count'] += 1
        return DummyRedisClient()

    monkeypatch.setattr(views.redis.Redis, 'from_url', staticmethod(successful_from_url))

    first_available = views._is_celery_available_quick()
    assert first_available is True
    assert ping_calls['count'] == 1

    # Swap the Redis factory to one that would fail; cache should prevent new calls.
    def failing_from_url(*args, **kwargs):
        ping_calls['count'] += 1
        raise RedisError("should not be reached due to cache")

    monkeypatch.setattr(views.redis.Redis, 'from_url', staticmethod(failing_from_url))

    second_available = views._is_celery_available_quick()
    assert second_available is True
    assert ping_calls['count'] == 1  # no additional attempt thanks to cache

