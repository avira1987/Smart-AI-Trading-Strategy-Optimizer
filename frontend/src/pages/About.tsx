import React from 'react'
import { useFeatureFlags } from '../context/FeatureFlagsContext'

export default function About() {
  const { liveTradingEnabled } = useFeatureFlags()

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 direction-rtl" style={{ direction: 'rtl', textAlign: 'right' }}>
      <div className="bg-gray-800 rounded-lg p-6 mb-6">
        <h1 className="text-3xl font-bold text-white mb-6">درباره سیستم مدیریت هوشمند معاملات</h1>
        
        <div className="space-y-6 text-gray-300">
          <section>
            <h2 className="text-2xl font-semibold text-blue-400 mb-4">منطق و عملکرد سیستم</h2>
            <div className="bg-gray-900 rounded-lg p-4 space-y-4">
              <p className="leading-relaxed">
                این سامانه یک سیستم مدیریت استراتژی‌های معاملاتی با استفاده از هوش مصنوعی است که به شما امکان می‌دهد:
              </p>
              <ul className="list-disc list-inside space-y-2 mr-4">
                <li>استراتژی‌های معاملاتی را به صورت فایل متنی آپلود کنید</li>
                <li>از هوش مصنوعی برای تجزیه و تحلیل و تبدیل استراتژی‌های متنی به کد استفاده کنید</li>
                <li>استراتژی‌های خود را بر روی داده‌های تاریخی تست کنید (Backtest)</li>
                {liveTradingEnabled && (
                  <li>معاملات زنده را با استفاده از حساب معاملاتی Litefinex انجام دهید</li>
                )}
                <li>عملکرد استراتژی‌ها را با نمودارها و آمارهای دقیق بررسی کنید</li>
              </ul>
            </div>
          </section>

          <section>
            <h2 className="text-2xl font-semibold text-blue-400 mb-4">روش استفاده از سیستم</h2>
            <div className="bg-gray-900 rounded-lg p-4 space-y-6">
              <div>
                <h3 className="text-xl font-semibold text-yellow-400 mb-3">مرحله 1: تنظیمات اولیه</h3>
                <ol className="list-decimal list-inside space-y-2 mr-4">
                  <li>به بخش <strong>"تنظیمات API"</strong> در داشبورد بروید</li>
                  <li>API Key های مورد نیاز را اضافه کنید (TwelveData، MetalsAPI، و غیره)</li>
                  <li>اطمینان حاصل کنید که حساب معاملاتی Litefinex خود را متصل کرده‌اید</li>
                </ol>
              </div>

              <div>
                <h3 className="text-xl font-semibold text-yellow-400 mb-3">مرحله 2: آپلود استراتژی</h3>
                <ol className="list-decimal list-inside space-y-2 mr-4">
                  <li>در صفحه داشبورد، روی <strong>"آپلود استراتژی"</strong> کلیک کنید</li>
                  <li>نام و توضیحات استراتژی را وارد کنید</li>
                  <li>فایل استراتژی (Word, PDF, یا Text) را انتخاب و آپلود کنید</li>
                  <li>سیستم به صورت خودکار استراتژی را با AI تجزیه می‌کند</li>
                </ol>
              </div>

              <div>
                <h3 className="text-xl font-semibold text-yellow-400 mb-3">مرحله 3: تست استراتژی</h3>
                <ol className="list-decimal list-inside space-y-2 mr-4">
                  <li>به صفحه <strong>"تست استراتژی"</strong> بروید</li>
                  <li>استراتژی مورد نظر را انتخاب کنید</li>
                  <li>پارامترهای تست را تنظیم کنید:
                    <ul className="list-disc list-inside mr-6 mt-2 space-y-1">
                      <li>بازه زمانی (1 روز تا 1 سال)</li>
                      <li>سرمایه اولیه</li>
                      <li>نماد معاملاتی (EUR/USD، XAUUSD، و غیره)</li>
                    </ul>
                  </li>
                  <li>روی <strong>"اجرای Backtest"</strong> کلیک کنید</li>
                  <li>منتظر بمانید تا تست تکمیل شود (این کار ممکن است چند دقیقه طول بکشد)</li>
                </ol>
              </div>

              <div>
                <h3 className="text-xl font-semibold text-yellow-400 mb-3">مرحله 4: بررسی نتایج</h3>
                <ol className="list-decimal list-inside space-y-2 mr-4">
                  <li>به صفحه <strong>"نتایج"</strong> بروید</li>
                  <li>نتایج تست‌های انجام شده را مشاهده کنید</li>
                  <li>معیارهای عملکرد را بررسی کنید:
                    <ul className="list-disc list-inside mr-6 mt-2 space-y-1">
                      <li>بازدهی کل (Total Return)</li>
                      <li>نرخ برد (Win Rate)</li>
                      <li>حداکثر افت سرمایه (Max Drawdown)</li>
                      <li>تعداد معاملات</li>
                    </ul>
                  </li>
                  <li>نمودار منحنی سودآوری را بررسی کنید</li>
                </ol>
              </div>

              {liveTradingEnabled && (
                <div>
                  <h3 className="text-xl font-semibold text-yellow-400 mb-3">مرحله 5: معاملات زنده</h3>
                  <ol className="list-decimal list-inside space-y-2 mr-4">
                    <li>پس از اطمینان از عملکرد استراتژی، به صفحه <strong>"معاملات زنده"</strong> بروید</li>
                    <li>اطلاعات حساب معاملاتی Litefinex را بررسی کنید</li>
                    <li>استراتژی مورد نظر را انتخاب کنید</li>
                    <li>معامله را با تنظیمات مناسب باز کنید:
                      <ul className="list-disc list-inside mr-6 mt-2 space-y-1">
                        <li>نماد معاملاتی</li>
                        <li>نوع معامله (خرید یا فروش)</li>
                        <li>حجم معامله</li>
                        <li>حد ضرر و حد سود</li>
                      </ul>
                    </li>
                    <li>وضعیت معاملات باز را به صورت زنده نظارت کنید</li>
                  </ol>
                </div>
              )}
            </div>
          </section>

          <section>
            <h2 className="text-2xl font-semibold text-blue-400 mb-4">نکات مهم</h2>
            <div className="bg-gray-900 rounded-lg p-4 space-y-3">
              {liveTradingEnabled ? (
                <div className="flex items-start space-x-3 space-x-reverse">
                  <span className="text-yellow-400 font-bold">⚠️</span>
                  <p>همیشه قبل از معاملات زنده، استراتژی را بر روی داده‌های تاریخی تست کنید</p>
                </div>
              ) : (
                <div className="flex items-start space-x-3 space-x-reverse">
                  <span className="text-blue-400 font-bold">ℹ️</span>
                  <p>ویژگی معاملات زنده در حال حاضر غیرفعال است و به زودی در دسترس قرار می‌گیرد.</p>
                </div>
              )}
              <div className="flex items-start space-x-3 space-x-reverse">
                <span className="text-yellow-400 font-bold">⚠️</span>
                <p>از حد ضرر و حد سود استفاده کنید تا ریسک معاملات را مدیریت کنید</p>
              </div>
              <div className="flex items-start space-x-3 space-x-reverse">
                <span className="text-yellow-400 font-bold">⚠️</span>
                <p>اطمینان حاصل کنید که حساب معاملاتی Litefinex شما به درستی متصل شده است</p>
              </div>
              <div className="flex items-start space-x-3 space-x-reverse">
                <span className="text-green-400 font-bold">✅</span>
                <p>داده‌های بازار به صورت خودکار کش می‌شوند تا هزینه‌های API کاهش یابد</p>
              </div>
            </div>
          </section>
        </div>
      </div>
    </div>
  )
}

