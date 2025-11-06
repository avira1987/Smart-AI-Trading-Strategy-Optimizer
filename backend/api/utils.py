def get_user_friendly_api_error_message(error_msg: str) -> str:
    """
    Map raw API error messages to user-friendly texts for dashboard.
    """
    msg = error_msg.lower()
    
    # اتصال اینترنت/سرور/API
    if any(x in msg for x in [
        'name or service not known', 'failed to resolve', 'getaddrinfo failed', 'max retries exceeded', 'could not resolve host', 'timeout', 'timed out', 'network is unreachable', 'connection refused', 'temporary failure in name resolution', 'httpsconnectionpool'
    ]):
        return 'ارتباط با سرور ارائه‌دهنده داده برقرار نشد. اینترنت یا سرور ارائه‌دهنده را بررسی کنید.'

    # کلید API نادرست یا بدون دسترسی
    if any(x in msg for x in [
        'api key not found', 'invalid api key', 'unauthorized', 'access denied', 'api key is invalid', 'no api key', 'api_key is invalid', 'missing api key'
    ]):
        return 'کلید API اشتباه است یا دسترسی به سرویس ندارید.'
    
    # سهمیه مصرفی (quota)
    if any(x in msg for x in [
        'quota', 'limit', 'call frequency', 'maximum number of', 'rate limit', 'temporarily blocked', 'you have reached', 'exceeded', 'please try again later', 'allowed requests', 'your monthly usage'
    ]):
        return 'سهمیه استفاده از سرویس داده (API) به پایان رسیده یا محدودیت فراخوانی اعمال شده است.'

    # فرمت نامعتبر یا خروجی غیرمنتظره
    if any(x in msg for x in ['unexpected format', 'could not extract', 'parsing', 'invalid response']):
        return 'فرمت داده بازگشتی از ارائه‌دهنده نامعتبراست. لطفا ورودی/خروجی یا کلید را بررسی کنید.'

    # خطای سمت ارائه‌دهنده (سرور مقصد)
    if 'internal server error' in msg or '503 service unavailable' in msg or 'server error' in msg:
        return 'خطا از سمت سرور ارائه‌دهنده داده رخ داده است. کمی بعد دوباره تلاش کنید.'

    # مسدودی یا تحریم جغرافیایی
    if any(x in msg for x in ['forbidden', 'blocked', 'blacklist', 'georestricted', 'geographical restriction']):
        return 'دسترسی به این سرویس از موقعیت جغرافیایی یا آی‌پی شما امکان‌پذیر نیست.'

    # خطای ناشناخته (fallback)
    return 'خطایی هنگام ارتباط با سرویس داده رخ داده است. لطفاً جزئیات را در تنظیمات و کلید API بررسی کنید.'
