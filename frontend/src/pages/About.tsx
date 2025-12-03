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
            <h2 className="text-2xl font-semibold text-blue-400 mb-4">سبک‌های استراتژی قابل بک‌تست</h2>
            <div className="bg-gray-900 rounded-lg p-6 space-y-6">
              <p className="text-gray-300 leading-relaxed mb-4">
                این سیستم از انواع مختلف استراتژی‌های معاملاتی پشتیبانی می‌کند. شما می‌توانید استراتژی‌های خود را به صورت فایل متنی (فارسی یا انگلیسی) آپلود کنید و سیستم به صورت خودکار آن‌ها را تجزیه و تحلیل کرده و بک‌تست کند.
              </p>

              {/* استراتژی‌های مبتنی بر اندیکاتور */}
              <div>
                <h3 className="text-xl font-semibold text-yellow-400 mb-3">1. استراتژی‌های مبتنی بر اندیکاتورهای تکنیکال</h3>
                <p className="text-gray-300 mb-3">سیستم از 10+ اندیکاتور تکنیکال پیشرفته پشتیبانی می‌کند:</p>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mr-4">
                  <div className="bg-gray-800 rounded-lg p-4">
                    <h4 className="text-lg font-semibold text-blue-300 mb-2">RSI (Relative Strength Index)</h4>
                    <ul className="text-gray-300 text-sm space-y-1 list-disc list-inside">
                      <li>ورود: RSI زیر 30 (اشباع فروش)</li>
                      <li>خروج: RSI بالای 70 (اشباع خرید)</li>
                    </ul>
                  </div>
                  <div className="bg-gray-800 rounded-lg p-4">
                    <h4 className="text-lg font-semibold text-blue-300 mb-2">MACD</h4>
                    <ul className="text-gray-300 text-sm space-y-1 list-disc list-inside">
                      <li>ورود: تقاطع صعودی MACD با خط سیگنال</li>
                      <li>خروج: تقاطع نزولی MACD با خط سیگنال</li>
                    </ul>
                  </div>
                  <div className="bg-gray-800 rounded-lg p-4">
                    <h4 className="text-lg font-semibold text-blue-300 mb-2">Moving Averages</h4>
                    <ul className="text-gray-300 text-sm space-y-1 list-disc list-inside">
                      <li>SMA: تقاطع SMA 20 و SMA 50</li>
                      <li>EMA: تقاطع EMA 12 و EMA 26</li>
                    </ul>
                  </div>
                  <div className="bg-gray-800 rounded-lg p-4">
                    <h4 className="text-lg font-semibold text-blue-300 mb-2">Bollinger Bands</h4>
                    <ul className="text-gray-300 text-sm space-y-1 list-disc list-inside">
                      <li>ورود: قیمت به زیر باند پایین</li>
                      <li>خروج: قیمت به بالای باند بالایی</li>
                    </ul>
                  </div>
                  <div className="bg-gray-800 rounded-lg p-4">
                    <h4 className="text-lg font-semibold text-blue-300 mb-2">Stochastic Oscillator</h4>
                    <ul className="text-gray-300 text-sm space-y-1 list-disc list-inside">
                      <li>ورود: استوکاستیک در منطقه اشباع فروش (&lt; 20)</li>
                      <li>خروج: استوکاستیک در منطقه اشباع خرید (&gt; 80)</li>
                    </ul>
                  </div>
                  <div className="bg-gray-800 rounded-lg p-4">
                    <h4 className="text-lg font-semibold text-blue-300 mb-2">سایر اندیکاتورها</h4>
                    <ul className="text-gray-300 text-sm space-y-1 list-disc list-inside">
                      <li>Williams %R</li>
                      <li>ATR (Average True Range)</li>
                      <li>ADX (Average Directional Index)</li>
                      <li>CCI (Commodity Channel Index)</li>
                    </ul>
                  </div>
                </div>
              </div>

              {/* استراتژی‌های متنی */}
              <div>
                <h3 className="text-xl font-semibold text-yellow-400 mb-3">2. استراتژی‌های متنی سفارشی</h3>
                <div className="bg-gray-800 rounded-lg p-4">
                  <p className="text-gray-300 mb-3">شما می‌توانید استراتژی‌های خود را به صورت فایل Word/Docx/TXT آپلود کنید:</p>
                  <ul className="text-gray-300 space-y-2 list-disc list-inside mr-4">
                    <li>پشتیبانی کامل از فارسی و انگلیسی</li>
                    <li>استخراج خودکار شرایط ورود/خروج با NLP و AI</li>
                    <li>ترکیب چند شرط با AND/OR</li>
                    <li>مثال: "ورود زمانی که RSI زیر 30 باشد و MACD تقاطع صعودی داشته باشد"</li>
                  </ul>
                </div>
              </div>

              {/* استراتژی‌های ترکیبی */}
              <div>
                <h3 className="text-xl font-semibold text-yellow-400 mb-3">3. استراتژی‌های ترکیبی</h3>
                <div className="bg-gray-800 rounded-lg p-4">
                  <ul className="text-gray-300 space-y-2 list-disc list-inside mr-4">
                    <li>ترکیب استراتژی متنی با اندیکاتورها (AND)</li>
                    <li>ترکیب چند اندیکاتور (OR)</li>
                    <li>ترکیب شرایط قیمت با اندیکاتورها</li>
                  </ul>
                </div>
              </div>

              {/* Price Action */}
              <div>
                <h3 className="text-xl font-semibold text-yellow-400 mb-3">4. استراتژی‌های مبتنی بر Price Action</h3>
                <div className="bg-gray-800 rounded-lg p-4">
                  <ul className="text-gray-300 space-y-2 list-disc list-inside mr-4">
                    <li>شرایط مبتنی بر قیمت (مثل "قیمت بالای 2000")</li>
                    <li>الگوهای کندل استیک (در صورت تعریف در متن)</li>
                    <li>شکست سطوح حمایت/مقاومت</li>
                  </ul>
                </div>
              </div>

              {/* مدیریت ریسک */}
              <div>
                <h3 className="text-xl font-semibold text-yellow-400 mb-3">5. استراتژی‌های مدیریت ریسک</h3>
                <div className="bg-gray-800 rounded-lg p-4">
                  <ul className="text-gray-300 space-y-2 list-disc list-inside mr-4">
                    <li>Stop Loss (پیپ، درصد، یا قیمت)</li>
                    <li>Take Profit (پیپ، درصد، یا قیمت)</li>
                    <li>Risk per Trade (درصد سرمایه)</li>
                    <li>مدیریت حجم معامله</li>
                  </ul>
                </div>
              </div>

              {/* چند نماد */}
              <div>
                <h3 className="text-xl font-semibold text-yellow-400 mb-3">6. استراتژی‌های چند نماد</h3>
                <div className="bg-gray-800 rounded-lg p-4">
                  <p className="text-gray-300 mb-2">پشتیبانی از نمادهای مختلف:</p>
                  <ul className="text-gray-300 space-y-1 list-disc list-inside mr-4">
                    <li>XAU/USD (طلا)</li>
                    <li>EUR/USD</li>
                    <li>GBP/USD</li>
                    <li>و سایر نمادهای فارکس</li>
                  </ul>
                </div>
              </div>

              {/* ویژگی‌های بک‌تست */}
              <div>
                <h3 className="text-xl font-semibold text-yellow-400 mb-3">متریک‌های عملکرد بک‌تست</h3>
                <div className="bg-gray-800 rounded-lg p-4">
                  <ul className="text-gray-300 space-y-2 list-disc list-inside mr-4">
                    <li><strong>Total Return:</strong> بازده کل استراتژی</li>
                    <li><strong>Win Rate:</strong> نرخ برد معاملات</li>
                    <li><strong>Max Drawdown:</strong> حداکثر افت سرمایه</li>
                    <li><strong>Sharpe Ratio:</strong> نسبت بازده به ریسک</li>
                    <li><strong>Profit Factor:</strong> نسبت سود به ضرر</li>
                    <li><strong>Equity Curve:</strong> نمودار رشد سرمایه</li>
                    <li><strong>تحلیل AI:</strong> تحلیل هوشمند از نتایج</li>
                  </ul>
                </div>
              </div>
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

