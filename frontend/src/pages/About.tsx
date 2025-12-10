import { useFeatureFlags } from '../context/FeatureFlagsContext'
import { Link } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'
import SEO from '../components/SEO'
import Breadcrumbs from '../components/Breadcrumbs'

export default function About() {
  const { liveTradingEnabled } = useFeatureFlags()
  const { isAuthenticated } = useAuth()

  return (
    <>
      <SEO
        title="درباره ما | ترید با هوش مصنوعی | سامانه معاملات هوشمند"
        description="درباره سامانه ترید با هوش مصنوعی و ترید به کمک هوش مصنوعی - شرکت تک ایده پویان. اطلاعات تماس، آدرس و راهنمای استفاده از سیستم معاملات هوشمند"
        keywords="درباره ترید با هوش مصنوعی, درباره ترید به کمک هوش مصنوعی, شرکت تک ایده پویان, تماس با ما, پشتیبانی معاملات هوشمند"
        canonical="https://myaibaz.ir/about"
        ogTitle="درباره سامانه ترید با هوش مصنوعی"
        ogDescription="درباره سامانه ترید با هوش مصنوعی و ترید به کمک هوش مصنوعی - شرکت تک ایده پویان"
        ogUrl="https://myaibaz.ir/about"
      />
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 direction-rtl" style={{ direction: 'rtl', textAlign: 'right' }}>
      <Breadcrumbs />
      <div className="bg-gray-800 rounded-lg p-6 mb-6">
        <h1 className="text-3xl font-bold text-white mb-6">درباره سامانه ترید با هوش مصنوعی</h1>
        
        {/* Company Information Section */}
        <section className="mb-8">
          <h2 className="text-2xl font-semibold text-blue-400 mb-4">شرکت تک ایده پویان - پیشرو در ترید با هوش مصنوعی</h2>
          <div className="bg-gray-900 rounded-lg p-6 space-y-4">
            <p className="text-gray-300 leading-relaxed text-lg">
              شرکت <strong className="text-blue-400">تک ایده پویان</strong> یک شرکت پیشرو در زمینه توسعه نرم‌افزارهای هوشمند و راه‌حل‌های نوآورانه در حوزه فناوری اطلاعات است. ما با بهره‌گیری از تکنولوژی‌های روز دنیا و تیمی متخصص، در تلاش هستیم تا محصولات و خدمات با کیفیتی را به مشتریان خود ارائه دهیم.
            </p>
            <p className="text-gray-300 leading-relaxed">
              این وب‌سایت یک سامانه پیشرفته <strong className="text-blue-400">ترید با هوش مصنوعی</strong> و <strong className="text-blue-400">ترید به کمک هوش مصنوعی</strong> است که به کاربران امکان می‌دهد استراتژی‌های معاملاتی خود را به صورت فایل متنی آپلود کرده، با استفاده از هوش مصنوعی تجزیه و تحلیل شوند، بر روی داده‌های تاریخی تست شوند و در صورت تمایل، معاملات زنده را انجام دهند. این سامانه با استفاده از آخرین تکنولوژی‌های وب و هوش مصنوعی طراحی شده است تا تجربه کاربری بهینه و نتایج دقیقی را برای <strong className="text-green-400">ترید هوشمند</strong> ارائه دهد. برای یادگیری نحوه استفاده از سیستم، می‌توانید به صفحه <Link to="/tutorial" className="text-blue-400 hover:text-blue-300 underline">آموزش</Link> مراجعه کنید. همچنین می‌توانید <Link to="/blog" className="text-blue-400 hover:text-blue-300 underline">مقالات بلاگ</Link> ما را برای اطلاعات بیشتر مطالعه کنید.
            </p>
            <div className="bg-blue-900/30 border-r-4 border-blue-500 p-4 mt-4 rounded">
              <h3 className="text-lg font-semibold text-blue-300 mb-2">چرا ترید با هوش مصنوعی؟</h3>
              <p className="text-gray-300 leading-relaxed">
                <strong className="text-blue-400">ترید با هوش مصنوعی</strong> و <strong className="text-blue-400">ترید به کمک هوش مصنوعی</strong> به شما امکان می‌دهد تا از قدرت یادگیری ماشین و الگوریتم‌های پیشرفته برای تحلیل بازار استفاده کنید. سیستم ما با استفاده از هوش مصنوعی، الگوهای معاملاتی را شناسایی کرده و بهترین استراتژی‌ها را برای شما پیشنهاد می‌دهد. این رویکرد باعث می‌شود تا تصمیمات معاملاتی شما بر اساس داده‌ها و تحلیل‌های دقیق باشد، نه احساسات.
              </p>
            </div>
          </div>
        </section>

        {/* Contact Us Section */}
        <section className="mb-8">
          <h2 className="text-2xl font-semibold text-blue-400 mb-4">تماس با ما</h2>
          <div className="bg-gray-900 rounded-lg p-6">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              {/* Address */}
              <div className="space-y-2">
                <h3 className="text-lg font-semibold text-yellow-400 flex items-center gap-2">
                  <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17.657 16.657L13.414 20.9a1.998 1.998 0 01-2.827 0l-4.244-4.243a8 8 0 1111.314 0z" />
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 11a3 3 0 11-6 0 3 3 0 016 0z" />
                  </svg>
                  آدرس
                </h3>
                <p className="text-gray-300 leading-relaxed">
                  گلستان - گرگان - گرگانپارس<br />
                  خیابان آذر، نبش خیابان آبان شرقی
                </p>
              </div>

              {/* Phone Numbers */}
              <div className="space-y-2">
                <h3 className="text-lg font-semibold text-yellow-400 flex items-center gap-2">
                  <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 5a2 2 0 012-2h3.28a1 1 0 01.948.684l1.498 4.493a1 1 0 01-.502 1.21l-2.257 1.13a11.042 11.042 0 005.516 5.516l1.13-2.257a1 1 0 011.21-.502l4.493 1.498a1 1 0 01.684.949V19a2 2 0 01-2 2h-1C9.716 21 3 14.284 3 6V5z" />
                  </svg>
                  تماس
                </h3>
                <div className="space-y-2">
                  <p className="text-gray-300">
                    <span className="text-gray-400">تلفن:</span>{' '}
                    <a href="tel:0173256465" className="text-blue-400 hover:text-blue-300 transition" dir="ltr">
                      0173256465
                    </a>
                  </p>
                  <p className="text-gray-300">
                    <span className="text-gray-400">همراه:</span>{' '}
                    <a href="tel:09035760718" className="text-blue-400 hover:text-blue-300 transition" dir="ltr">
                      09035760718
                    </a>
                  </p>
                </div>
              </div>

              {/* Email */}
              <div className="space-y-2">
                <h3 className="text-lg font-semibold text-yellow-400 flex items-center gap-2">
                  <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 8l7.89 5.26a2 2 0 002.22 0L21 8M5 19h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z" />
                  </svg>
                  ایمیل
                </h3>
                <p className="text-gray-300">
                  <a href="mailto:amiravira1987@gmail.com" className="text-blue-400 hover:text-blue-300 transition" dir="ltr">
                    amiravira1987@gmail.com
                  </a>
                </p>
              </div>

              {/* Telegram */}
              <div className="space-y-2">
                <h3 className="text-lg font-semibold text-yellow-400 flex items-center gap-2">
                  <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 24 24">
                    <path d="M11.944 0A12 12 0 0 0 0 12a12 12 0 0 0 12 12 12 12 0 0 0 12-12A12 12 0 0 0 12 0a12 12 0 0 0-.056 0zm4.962 7.224c.1-.002.321.023.465.14a.506.506 0 0 1 .171.325c.016.093.036.306.02.472-.18 1.898-.962 6.502-1.36 8.627-.168.9-.499 1.201-.82 1.23-.696.065-1.225-.46-1.9-.902-1.056-.693-1.653-1.124-2.678-1.8-1.185-.78-.417-1.21.258-1.91.177-.184 3.247-2.977 3.307-3.23.007-.032.014-.15-.056-.212s-.174-.041-.249-.024c-.106.024-1.793 1.14-5.061 3.345-.48.33-.913.49-1.302.48-.428-.008-1.252-.241-1.865-.44-.752-.245-1.349-.374-1.297-.789.027-.216.325-.437.893-.663 3.498-1.524 5.83-2.529 6.998-3.014 3.332-1.386 4.025-1.627 4.476-1.635z"/>
                  </svg>
                  تلگرام پشتیبانی
                </h3>
                <p className="text-gray-300">
                  <a href="https://t.me/avxsupport" target="_blank" rel="noopener noreferrer" className="text-blue-400 hover:text-blue-300 transition inline-flex items-center gap-2">
                    <span>@avxsupport</span>
                    <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 6H6a2 2 0 00-2 2v10a2 2 0 002 2h10a2 2 0 002-2v-4M14 4h6m0 0v6m0-6L10 14" />
                    </svg>
                  </a>
                </p>
              </div>

              {/* Ticket System */}
              <div className="space-y-2">
                <h3 className="text-lg font-semibold text-yellow-400 flex items-center gap-2">
                  <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 10h.01M12 10h.01M16 10h.01M9 16H5a2 2 0 01-2-2V6a2 2 0 012-2h14a2 2 0 012 2v8a2 2 0 01-2 2h-5l-5 5v-5z" />
                  </svg>
                  درخواست تماس
                </h3>
                {isAuthenticated ? (
                  <p className="text-gray-300 mb-3">
                    برای ارسال درخواست تماس و پشتیبانی، می‌توانید از سیستم تیکت استفاده کنید.
                  </p>
                ) : (
                  <p className="text-gray-300 mb-3">
                    برای ارسال درخواست تماس و پشتیبانی، ابتدا وارد حساب کاربری خود شوید و سپس از سیستم تیکت استفاده کنید.
                  </p>
                )}
                {isAuthenticated ? (
                  <Link
                    to="/tickets"
                    className="inline-flex items-center gap-2 px-4 py-2 bg-blue-500 text-white rounded-lg hover:bg-blue-600 transition font-medium"
                  >
                    <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
                    </svg>
                    ایجاد تیکت جدید
                  </Link>
                ) : (
                  <Link
                    to="/login"
                    className="inline-flex items-center gap-2 px-4 py-2 bg-blue-500 text-white rounded-lg hover:bg-blue-600 transition font-medium"
                  >
                    ورود به حساب کاربری
                  </Link>
                )}
              </div>
            </div>
          </div>
        </section>

        <h1 className="text-3xl font-bold text-white mb-6 mt-8">درباره سیستم ترید با هوش مصنوعی</h1>
        
        <div className="space-y-6 text-gray-300">
          <section>
            <h2 className="text-2xl font-semibold text-blue-400 mb-4">منطق و عملکرد سیستم ترید با هوش مصنوعی</h2>
            <div className="bg-gray-900 rounded-lg p-4 space-y-4">
              <p className="leading-relaxed">
                این سامانه یک سیستم پیشرفته <strong className="text-blue-400">ترید با هوش مصنوعی</strong> و <strong className="text-blue-400">ترید به کمک هوش مصنوعی</strong> است که به شما امکان می‌دهد:
              </p>
              <ul className="list-disc list-inside space-y-2 mr-4">
                <li>استراتژی‌های معاملاتی را به صورت فایل متنی آپلود کنید</li>
                <li>از هوش مصنوعی برای تجزیه و تحلیل و تبدیل استراتژی‌های متنی به کد استفاده کنید - <strong className="text-green-400">ترید به کمک هوش مصنوعی</strong></li>
                <li>استراتژی‌های خود را بر روی داده‌های تاریخی تست کنید (Backtest) با استفاده از <strong className="text-green-400">ترید با هوش مصنوعی</strong></li>
                {liveTradingEnabled && (
                  <li>معاملات زنده هوشمند را با استفاده از حساب معاملاتی Litefinex انجام دهید</li>
                )}
                <li>عملکرد استراتژی‌ها را با نمودارها و آمارهای دقیق بررسی کنید - تحلیل‌های ارائه شده توسط هوش مصنوعی</li>
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
    </>
  )
}

