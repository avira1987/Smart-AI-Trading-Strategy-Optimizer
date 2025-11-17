#!/bin/bash
# Test SMS and Google OAuth on specific IP
# Usage: ./test_on_ip.sh

BACKEND_IP="192.168.100.9"
BACKEND_PORT="8000"
BACKEND_URL="http://${BACKEND_IP}:${BACKEND_PORT}"

echo ""
echo "========================================="
echo "  تست Backend روی IP: $BACKEND_IP:$BACKEND_PORT"
echo "========================================="
echo ""

# Test 1: Backend Status
echo "[1/3] تست وضعیت Backend..."
if response=$(curl -s "${BACKEND_URL}/api/test/backend-status/"); then
    echo "  ✓ Backend در حال اجرا است"
    echo "$response" | python3 -m json.tool 2>/dev/null || echo "$response"
else
    echo "  ✗ Backend در دسترس نیست"
    echo "لطفاً مطمئن شوید که Backend روی $BACKEND_IP:$BACKEND_PORT در حال اجرا است."
    exit 1
fi

echo ""

# Test 2: Google OAuth Configuration
echo "[2/3] تست تنظیمات Google OAuth..."
if response=$(curl -s "${BACKEND_URL}/api/test/google-oauth/"); then
    echo "  ✓ تست Google OAuth انجام شد"
    echo "$response" | python3 -m json.tool 2>/dev/null || echo "$response"
else
    echo "  ✗ خطا در تست Google OAuth"
fi

echo ""

# Test 3: SMS Test
echo "[3/3] تست ارسال SMS..."
read -p "  لطفاً شماره موبایل خود را وارد کنید (مثلاً 09123456789): " phoneNumber

if [[ $phoneNumber =~ ^09[0-9]{9}$ ]]; then
    echo "  در حال ارسال SMS..."
    response=$(curl -s -X POST "${BACKEND_URL}/api/test/sms/" \
        -H "Content-Type: application/json" \
        -d "{\"phone_number\": \"$phoneNumber\"}")
    
    if echo "$response" | grep -q '"success": true'; then
        echo "  ✓ SMS با موفقیت ارسال شد!"
        echo "$response" | python3 -m json.tool 2>/dev/null || echo "$response"
    else
        echo "  ✗ خطا در ارسال SMS"
        echo "$response" | python3 -m json.tool 2>/dev/null || echo "$response"
    fi
else
    echo "  ✗ شماره موبایل نامعتبر است (باید به فرمت 09123456789 باشد)"
fi

echo ""
echo "========================================="
echo "  تست کامل شد!"
echo "========================================="
echo ""
echo "📋 خلاصه:"
echo "  Backend URL: $BACKEND_URL"
echo "  برای تست دستی:"
echo "    - تست SMS: POST $BACKEND_URL/api/test/sms/ با body: {\"phone_number\": \"09123456789\"}"
echo "    - تست Google OAuth: GET $BACKEND_URL/api/test/google-oauth/"
echo "    - وضعیت Backend: GET $BACKEND_URL/api/test/backend-status/"
echo ""

