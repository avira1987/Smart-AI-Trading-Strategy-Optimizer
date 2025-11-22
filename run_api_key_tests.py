"""
Run API key priority tests
"""
import os
import sys
import subprocess
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
os.chdir(BASE_DIR / "backend")

# Run Django tests
result = subprocess.run(
    [sys.executable, "manage.py", "test", "tests.test_api_key_priority", "-v", "2"],
    capture_output=True,
    text=True,
    encoding="utf-8"
)

print("STDOUT:")
print(result.stdout)
print("\nSTDERR:")
print(result.stderr)
print(f"\nReturn code: {result.returncode}")

if result.returncode == 0:
    print("\n✅ All tests passed!")
else:
    print("\n❌ Some tests failed!")

