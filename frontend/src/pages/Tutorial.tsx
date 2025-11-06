import React from 'react'

export default function Tutorial() {
  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 direction-rtl" style={{ direction: 'rtl', textAlign: 'right' }}>
      <div className="bg-gray-800 rounded-lg p-6 mb-6">
        <h1 className="text-3xl font-bold text-white mb-6">آموزش استفاده از سیستم</h1>
        
        <div className="space-y-6 text-gray-300">
          <section className="bg-gray-900 rounded-lg p-6">
            <h2 className="text-2xl font-semibold text-blue-400 mb-4">آموزش دریافت IP های رایگان</h2>
            <div className="space-y-4">
              <p className="leading-relaxed">
                برای اتصال به صرافی Litefinex و انجام معاملات، ممکن است به IP های اختصاصی نیاز داشته باشید. 
                در ادامه روش‌های دریافت IP های رایگان را به صورت خلاصه بررسی می‌کنیم:
              </p>

              <div className="bg-gray-800 rounded-lg p-4 space-y-4">
                <div>
                  <h3 className="text-xl font-semibold text-green-400 mb-2">1. استفاده از VPN های رایگان</h3>
                  <ul className="list-disc list-inside space-y-1 mr-4">
                    <li>VPN های رایگان مانند <strong>ProtonVPN</strong>، <strong>Windscribe</strong> گزینه‌های خوبی هستند</li>
                    <li>این VPN ها IP های عمومی ارائه می‌دهند که برای برخی معاملات مناسب هستند</li>
                    <li>محدودیت: IP ها ممکن است توسط دیگران استفاده شوند</li>
                  </ul>
                </div>

                <div>
                  <h3 className="text-xl font-semibold text-green-400 mb-2">2. استفاده از Proxy های رایگان</h3>
                  <ul className="list-disc list-inside space-y-1 mr-4">
                    <li>وب‌سایت‌هایی مانند <strong>FreeProxyList</strong> لیست Proxy های رایگان ارائه می‌دهند</li>
                    <li>می‌توانید از Proxy های HTTP/HTTPS رایگان استفاده کنید</li>
                    <li>هشدار: بسیاری از Proxy های رایگان ناپایدار یا ناامن هستند</li>
                  </ul>
                </div>

                <div>
                  <h3 className="text-xl font-semibold text-green-400 mb-2">3. استفاده از Tor Browser</h3>
                  <ul className="list-disc list-inside space-y-1 mr-4">
                    <li>Tor شبکه‌ای از نودهای داوطلبانه است که IP شما را تغییر می‌دهد</li>
                    <li>کاملاً رایگان و متن‌باز است</li>
                    <li>محدودیت: سرعت کم و ممکن است برای معاملات سریع مناسب نباشد</li>
                  </ul>
                </div>

                <div>
                  <h3 className="text-xl font-semibold text-green-400 mb-2">4. استفاده از Cloud Platforms رایگان</h3>
                  <ul className="list-disc list-inside space-y-1 mr-4">
                    <li><strong>Google Cloud Platform:</strong> 300 دلار اعتبار رایگان برای 90 روز</li>
                    <li><strong>AWS Free Tier:</strong> 12 ماه رایگان برای برخی سرویس‌ها</li>
                    <li><strong>Oracle Cloud:</strong> همیشه رایگان برای برخی منابع</li>
                    <li>می‌توانید یک سرور مجازی ایجاد کنید و IP اختصاصی دریافت کنید</li>
                  </ul>
                </div>

                <div>
                  <h3 className="text-xl font-semibold text-green-400 mb-2">5. استفاده از VPS رایگان</h3>
                  <ul className="list-disc list-inside space-y-1 mr-4">
                    <li>برخی ارائه‌دهندگان VPS رایگان مانند <strong>Vultr</strong> یا <strong>DigitalOcean</strong> اعتبار آزمایشی ارائه می‌دهند</li>
                    <li>می‌توانید از کدهای تخفیف استفاده کنید</li>
                    <li>VPS های رایگان معمولاً محدودیت منابع دارند</li>
                  </ul>
                </div>
              </div>

              <div className="bg-yellow-900 border-r-4 border-yellow-500 p-4 mt-4">
                <h4 className="text-lg font-semibold text-yellow-300 mb-2">⚠️ نکات امنیتی مهم:</h4>
                <ul className="list-disc list-inside space-y-1 mr-4 text-gray-200">
                  <li>IP های رایگان ممکن است توسط دیگران استفاده شده باشند و در لیست سیاه قرار گیرند</li>
                  <li>برای معاملات واقعی، استفاده از IP اختصاصی پرداخت‌شده توصیه می‌شود</li>
                  <li>همیشه IP خود را از طریق سرویس‌هایی مانند <strong>ipinfo.io</strong> بررسی کنید</li>
                  <li>از VPN/Proxy های معتبر استفاده کنید تا امنیت داده‌های شما حفظ شود</li>
                </ul>
              </div>
            </div>
          </section>

          <section className="bg-gray-900 rounded-lg p-6">
            <h2 className="text-2xl font-semibold text-blue-400 mb-4">نحوه اتصال به Litefinex</h2>
            <div className="space-y-4">
              <div>
                <h3 className="text-xl font-semibold text-yellow-400 mb-2">مراحل اتصال:</h3>
                <ol className="list-decimal list-inside space-y-2 mr-4">
                  <li>حساب معاملاتی خود را در صرافی Litefinex ایجاد کنید</li>
                  <li>اطلاعات اتصال MT5 را از پنل کاربری Litefinex دریافت کنید:
                    <ul className="list-disc list-inside mr-6 mt-2 space-y-1">
                      <li>سرور معاملاتی (Server)</li>
                      <li>نام کاربری (Login)</li>
                      <li>رمز عبور (Password)</li>
                    </ul>
                  </li>
                  <li>نرم‌افزار MetaTrader 5 را نصب کنید</li>
                  <li>با استفاده از اطلاعات دریافت شده به سرور Litefinex متصل شوید</li>
                  <li>در این سیستم، اتصال به صورت خودکار از طریق MT5 انجام می‌شود</li>
                </ol>
              </div>
            </div>
          </section>

          <section className="bg-gray-900 rounded-lg p-6">
            <h2 className="text-2xl font-semibold text-blue-400 mb-4">راهنمای استفاده از استراتژی‌ها</h2>
            <div className="space-y-4">
              <div>
                <h3 className="text-xl font-semibold text-yellow-400 mb-2">نحوه نوشتن استراتژی:</h3>
                <p className="mb-2">برای نوشتن استراتژی معاملاتی، می‌توانید از فرمت زیر استفاده کنید:</p>
                <div className="bg-gray-800 rounded p-4 font-mono text-sm overflow-x-auto">
                  <pre className="text-green-400">{`نماد معاملاتی: XAUUSD
بازه زمانی: M15

شرایط ورود:
- زمانی که RSI زیر 30 باشد
- و قیمت به خط حمایت برسد

حد ضرر: 50 پیپ
حد سود: 100 پیپ`}</pre>
                </div>
              </div>

              <div>
                <h3 className="text-xl font-semibold text-yellow-400 mb-2">اندیکاتورهای پشتیبانی شده:</h3>
                <ul className="list-disc list-inside space-y-1 mr-4">
                  <li>RSI (Relative Strength Index)</li>
                  <li>MACD (Moving Average Convergence Divergence)</li>
                  <li>Moving Average (MA, SMA, EMA)</li>
                  <li>Bollinger Bands</li>
                  <li>Support and Resistance Levels</li>
                </ul>
              </div>
            </div>
          </section>
        </div>
      </div>
    </div>
  )
}

