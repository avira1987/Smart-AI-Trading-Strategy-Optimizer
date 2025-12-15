import SEO from '../components/SEO'
import Breadcrumbs from '../components/Breadcrumbs'
import ArticleSchema from '../components/ArticleSchema'
import { Link } from 'react-router-dom'

export default function Tutorial() {
  return (
    <>
      <SEO
        title="آموزش ترید با هوش مصنوعی | راهنمای استفاده از سیستم معاملات هوشمند"
        description="آموزش کامل استفاده از سامانه ترید با هوش مصنوعی و ترید به کمک هوش مصنوعی. راهنمای آپلود استراتژی، بک‌تست و معاملات هوشمند"
        keywords="آموزش ترید با هوش مصنوعی, آموزش ترید به کمک هوش مصنوعی, راهنمای معاملات هوشمند, آموزش بک‌تست, آموزش استراتژی معاملاتی"
        canonical="https://myaibaz.ir/tutorial"
        ogTitle="آموزش ترید با هوش مصنوعی"
        ogDescription="آموزش کامل استفاده از سامانه ترید با هوش مصنوعی و ترید به کمک هوش مصنوعی"
        ogUrl="https://myaibaz.ir/tutorial"
      />
      <ArticleSchema
        title="آموزش استفاده از سیستم ترید با هوش مصنوعی"
        description="آموزش کامل استفاده از سامانه ترید با هوش مصنوعی و ترید به کمک هوش مصنوعی. راهنمای آپلود استراتژی، بک‌تست و معاملات هوشمند"
        url="https://myaibaz.ir/tutorial"
        datePublished="2024-12-20"
        dateModified="2024-12-20"
      />
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 direction-rtl" style={{ direction: 'rtl', textAlign: 'right' }}>
      <Breadcrumbs />
      <div className="bg-gray-800 rounded-lg p-6 mb-6">
        <h1 className="text-3xl font-bold text-white mb-6">آموزش استفاده از سیستم ترید با هوش مصنوعی</h1>
        
        <div className="space-y-6 text-gray-300">
          {/* بخش 1: ثبت‌نام و ورود */}
          <section className="bg-gray-900 rounded-lg p-6">
            <h2 className="text-2xl font-semibold text-blue-400 mb-4">مرحله 1: ثبت‌نام و ورود به سیستم</h2>
            <div className="space-y-4">
              <p className="leading-relaxed">
                برای شروع استفاده از سیستم <strong className="text-blue-400">ترید با هوش مصنوعی</strong>، ابتدا باید در سیستم ثبت‌نام کنید.
              </p>
              <div className="bg-gray-800 rounded-lg p-4">
                <h3 className="text-xl font-semibold text-yellow-400 mb-3">روش‌های ورود:</h3>
                <ul className="list-disc list-inside space-y-2 mr-4">
                  <li><strong>ورود با شماره موبایل:</strong> شماره موبایل خود را وارد کرده و کد OTP دریافت کنید</li>
                  <li><strong>ورود با حساب Google:</strong> می‌توانید از حساب Google خود برای ورود سریع استفاده کنید</li>
                </ul>
                <div className="mt-4 p-3 bg-blue-900 border-r-4 border-blue-500 rounded">
                  <p className="text-sm">
                    💡 <strong>نکته:</strong> پس از ورود، حتماً پروفایل خود را تکمیل کنید (نام و نام خانوادگی) تا بتوانید از تمامی امکانات سیستم استفاده کنید.
                  </p>
                </div>
              </div>
            </div>
          </section>

          {/* بخش 2: آپلود استراتژی */}
          <section className="bg-gray-900 rounded-lg p-6">
            <h2 className="text-2xl font-semibold text-blue-400 mb-4">مرحله 2: آپلود و مدیریت استراتژی‌ها</h2>
            <div className="space-y-4">
              <p className="leading-relaxed">
                پس از ورود به سیستم، می‌توانید استراتژی‌های معاملاتی خود را آپلود کنید. سیستم به صورت خودکار استراتژی شما را با استفاده از <strong className="text-green-400">هوش مصنوعی</strong> تجزیه و تحلیل می‌کند.
              </p>
              
              <div className="bg-gray-800 rounded-lg p-4 space-y-4">
                <div>
                  <h3 className="text-xl font-semibold text-yellow-400 mb-2">نحوه آپلود استراتژی:</h3>
                  <ol className="list-decimal list-inside space-y-2 mr-4">
                    <li>در صفحه <Link to="/" className="text-blue-400 hover:text-blue-300 underline">داشبورد</Link>، روی دکمه <strong>"آپلود استراتژی"</strong> کلیک کنید</li>
                    <li>نام استراتژی را وارد کنید (مثلاً: "استراتژی RSI برای طلا")</li>
                    <li>توضیحات استراتژی را بنویسید (شرایط ورود، خروج، حد ضرر و حد سود)</li>
                    <li>فایل استراتژی را انتخاب کنید:
                      <ul className="list-disc list-inside mr-6 mt-2 space-y-1 text-sm">
                        <li>فرمت‌های پشتیبانی شده: <strong>Word (.docx)</strong>، <strong>PDF</strong>، <strong>Text (.txt)</strong></li>
                        <li>می‌توانید استراتژی را به صورت متن ساده نیز بنویسید</li>
                      </ul>
                    </li>
                    <li>روی دکمه <strong>"آپلود"</strong> کلیک کنید</li>
                    <li>منتظر بمانید تا سیستم استراتژی را پردازش کند (این کار معمولاً چند ثانیه طول می‌کشد)</li>
                  </ol>
                </div>

                <div>
                  <h3 className="text-xl font-semibold text-yellow-400 mb-2">تعیین استراتژی اصلی:</h3>
                  <p className="mb-2">
                    برای اجرای بک‌تست، باید یک استراتژی را به عنوان <strong className="text-green-400">استراتژی اصلی</strong> تعیین کنید:
                  </p>
                  <ul className="list-disc list-inside space-y-1 mr-4">
                    <li>در لیست استراتژی‌ها، روی دکمه <strong>"تعیین به عنوان اصلی"</strong> کلیک کنید</li>
                    <li>استراتژی اصلی با برچسب <span className="bg-green-600 text-white px-2 py-1 rounded text-sm">اصلی</span> نمایش داده می‌شود</li>
                    <li>فقط یک استراتژی می‌تواند به عنوان اصلی تعیین شود</li>
                    <li>برای تغییر استراتژی اصلی، روی همان دکمه کلیک کنید تا از حالت اصلی خارج شود، سپس استراتژی دیگری را انتخاب کنید</li>
                  </ul>
                </div>
              </div>
            </div>
          </section>

          {/* بخش 3: نحوه نوشتن استراتژی */}
          <section className="bg-gray-900 rounded-lg p-6">
            <h2 className="text-2xl font-semibold text-blue-400 mb-4">نحوه نوشتن استراتژی برای ترید به کمک هوش مصنوعی</h2>
            <div className="space-y-4">
              <div>
                <h3 className="text-xl font-semibold text-yellow-400 mb-2">فرمت پیشنهادی برای نوشتن استراتژی:</h3>
                <p className="mb-2">برای نوشتن استراتژی معاملاتی که با <strong className="text-blue-400">ترید با هوش مصنوعی</strong> کار می‌کند، می‌توانید از فرمت زیر استفاده کنید:</p>
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
                <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                  <ul className="list-disc list-inside space-y-1 mr-4">
                    <li>RSI (Relative Strength Index)</li>
                    <li>MACD (Moving Average Convergence Divergence)</li>
                    <li>Moving Average (MA, SMA, EMA)</li>
                    <li>Bollinger Bands</li>
                    <li>Support and Resistance Levels</li>
                  </ul>
                  <ul className="list-disc list-inside space-y-1 mr-4">
                    <li>Stochastic (استوکاستیک)</li>
                    <li>Williams %R</li>
                    <li>ATR (میانگین محدوده واقعی)</li>
                    <li>ADX (شاخص میانگین جهت)</li>
                    <li>CCI (شاخص کانال کالا)</li>
                  </ul>
                </div>
              </div>

              <div className="bg-blue-900 border-r-4 border-blue-500 p-4 rounded">
                <h4 className="text-lg font-semibold text-blue-300 mb-2">💡 نکات مهم در نوشتن استراتژی:</h4>
                <ul className="list-disc list-inside space-y-1 mr-4 text-sm">
                  <li>شرایط ورود و خروج را به صورت واضح و دقیق بنویسید</li>
                  <li>حد ضرر و حد سود را مشخص کنید</li>
                  <li>نماد معاملاتی و بازه زمانی را ذکر کنید</li>
                  <li>می‌توانید از زبان فارسی یا انگلیسی استفاده کنید</li>
                  <li>هر چه استراتژی دقیق‌تر باشد، نتایج بک‌تست بهتر خواهد بود</li>
                </ul>
              </div>
            </div>
          </section>

          {/* بخش 4: اجرای بک‌تست */}
          <section className="bg-gray-900 rounded-lg p-6">
            <h2 className="text-2xl font-semibold text-blue-400 mb-4">مرحله 3: اجرای بک‌تست استراتژی</h2>
            <div className="space-y-4">
              <p className="leading-relaxed">
                پس از آپلود و تعیین استراتژی اصلی، می‌توانید استراتژی خود را بر روی داده‌های تاریخی تست کنید.
              </p>
              
              <div className="bg-gray-800 rounded-lg p-4">
                <h3 className="text-xl font-semibold text-yellow-400 mb-3">مراحل اجرای بک‌تست:</h3>
                <ol className="list-decimal list-inside space-y-2 mr-4">
                  <li>به صفحه <Link to="/testing" className="text-blue-400 hover:text-blue-300 underline">"تست استراتژی"</Link> بروید</li>
                  <li>استراتژی اصلی خود را از لیست انتخاب کنید (اگر استراتژی اصلی تعیین نکرده‌اید، ابتدا باید آن را تعیین کنید)</li>
                  <li>پارامترهای بک‌تست را تنظیم کنید:
                    <ul className="list-disc list-inside mr-6 mt-2 space-y-1 text-sm">
                      <li><strong>بازه زمانی:</strong> مدت زمان تست (از 1 روز تا 1 سال)</li>
                      <li><strong>سرمایه اولیه:</strong> مبلغ اولیه برای شروع معاملات (پیش‌فرض: 10,000 دلار)</li>
                      <li><strong>نماد معاملاتی:</strong> جفت ارز یا نماد مورد نظر (مثلاً: XAUUSD، EURUSD)</li>
                      <li><strong>اندیکاتورها (اختیاری):</strong> می‌توانید اندیکاتورهای اضافی را انتخاب کنید</li>
                    </ul>
                  </li>
                  <li>روی دکمه <strong>"اجرای Backtest"</strong> کلیک کنید</li>
                  <li>منتظر بمانید تا بک‌تست تکمیل شود:
                    <ul className="list-disc list-inside mr-6 mt-2 space-y-1 text-sm">
                      <li>وضعیت بک‌تست در بالای صفحه نمایش داده می‌شود</li>
                      <li>این فرآیند ممکن است چند دقیقه طول بکشد</li>
                      <li>می‌توانید وضعیت را در صفحه <Link to="/results" className="text-blue-400 hover:text-blue-300 underline">"نتایج"</Link> مشاهده کنید</li>
                    </ul>
                  </li>
                </ol>
              </div>

              <div className="bg-yellow-900 border-r-4 border-yellow-500 p-4 rounded">
                <h4 className="text-lg font-semibold text-yellow-300 mb-2">⚠️ نکات مهم:</h4>
                <ul className="list-disc list-inside space-y-1 mr-4 text-sm">
                  <li>قبل از اجرای بک‌تست، مطمئن شوید که استراتژی اصلی تعیین شده است</li>
                  <li>بازه زمانی طولانی‌تر، نتایج دقیق‌تری ارائه می‌دهد اما زمان بیشتری می‌برد</li>
                  <li>می‌توانید چندین بک‌تست با پارامترهای مختلف اجرا کنید و نتایج را مقایسه کنید</li>
                </ul>
              </div>
            </div>
          </section>

          {/* بخش 5: مشاهده نتایج */}
          <section className="bg-gray-900 rounded-lg p-6">
            <h2 className="text-2xl font-semibold text-blue-400 mb-4">مرحله 4: مشاهده و تحلیل نتایج بک‌تست</h2>
            <div className="space-y-4">
              <p className="leading-relaxed">
                پس از تکمیل بک‌تست، می‌توانید نتایج را در صفحه <Link to="/results" className="text-blue-400 hover:text-blue-300 underline">"نتایج"</Link> مشاهده و تحلیل کنید.
              </p>
              
              <div className="bg-gray-800 rounded-lg p-4">
                <h3 className="text-xl font-semibold text-yellow-400 mb-3">اطلاعات قابل مشاهده در نتایج:</h3>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div>
                    <h4 className="text-lg font-semibold text-green-400 mb-2">متریک‌های عملکرد:</h4>
                    <ul className="list-disc list-inside space-y-1 mr-4 text-sm">
                      <li><strong>بازدهی کل (Total Return):</strong> درصد سود یا زیان کل</li>
                      <li><strong>نرخ برد (Win Rate):</strong> درصد معاملات موفق</li>
                      <li><strong>حداکثر افت سرمایه (Max Drawdown):</strong> بیشترین کاهش سرمایه</li>
                      <li><strong>تعداد معاملات:</strong> تعداد کل معاملات انجام شده</li>
                      <li><strong>Profit Factor:</strong> نسبت سود به ضرر</li>
                      <li><strong>Sharpe Ratio:</strong> نسبت بازدهی به ریسک</li>
                    </ul>
                  </div>
                  <div>
                    <h4 className="text-lg font-semibold text-green-400 mb-2">نمودارها و تحلیل‌ها:</h4>
                    <ul className="list-disc list-inside space-y-1 mr-4 text-sm">
                      <li><strong>نمودار Equity Curve:</strong> نمایش تغییرات سرمایه در طول زمان</li>
                      <li><strong>جزئیات معاملات:</strong> لیست تمام معاملات با جزئیات کامل</li>
                      <li><strong>تحلیل AI:</strong> تحلیل هوشمند نتایج توسط هوش مصنوعی</li>
                      <li><strong>توصیه‌های بهبود:</strong> پیشنهادات برای بهبود استراتژی</li>
                    </ul>
                  </div>
                </div>
              </div>

              <div className="bg-blue-900 border-r-4 border-blue-500 p-4 rounded">
                <h4 className="text-lg font-semibold text-blue-300 mb-2">📊 نحوه تفسیر نتایج:</h4>
                <ul className="list-disc list-inside space-y-1 mr-4 text-sm">
                  <li><strong>بازدهی مثبت:</strong> استراتژی در بازه زمانی تست شده سودآور بوده است</li>
                  <li><strong>نرخ برد بالا:</strong> نشان‌دهنده دقت بالای استراتژی در تشخیص نقاط ورود و خروج</li>
                  <li><strong>Drawdown کم:</strong> استراتژی ریسک کمتری دارد</li>
                  <li><strong>Profit Factor بالای 1:</strong> نشان‌دهنده سودآوری کلی استراتژی</li>
                </ul>
              </div>
            </div>
          </section>

          {/* بخش 6: بهینه‌سازی استراتژی */}
          <section className="bg-gray-900 rounded-lg p-6">
            <h2 className="text-2xl font-semibold text-blue-400 mb-4">مرحله 5: بهینه‌سازی استراتژی (اختیاری)</h2>
            <div className="space-y-4">
              <p className="leading-relaxed">
                پس از مشاهده نتایج بک‌تست، می‌توانید استراتژی خود را با استفاده از هوش مصنوعی بهینه کنید تا عملکرد بهتری داشته باشد.
              </p>
              
              <div className="bg-gray-800 rounded-lg p-4">
                <h3 className="text-xl font-semibold text-yellow-400 mb-3">روش‌های بهینه‌سازی:</h3>
                <ul className="list-disc list-inside space-y-2 mr-4">
                  <li><strong>بهینه‌سازی با Machine Learning (ML):</strong> استفاده از الگوریتم‌های یادگیری ماشین</li>
                  <li><strong>بهینه‌سازی با Deep Learning (DL):</strong> استفاده از شبکه‌های عصبی عمیق</li>
                  <li><strong>بهینه‌سازی ترکیبی (Hybrid):</strong> ترکیب ML و DL</li>
                  <li><strong>بهینه‌سازی خودکار (Auto):</strong> انتخاب خودکار بهترین روش</li>
                </ul>
                
                <div className="mt-4 p-3 bg-gray-700 rounded">
                  <p className="text-sm">
                    💡 <strong>نکته:</strong> بهینه‌سازی ممکن است زمان زیادی ببرد. پس از تکمیل، می‌توانید نتایج قبل و بعد از بهینه‌سازی را مقایسه کنید و درصد بهبود را مشاهده کنید.
                  </p>
                </div>
              </div>
            </div>
          </section>

          {/* بخش 7: معاملات زنده */}
          <section className="bg-gray-900 rounded-lg p-6">
            <h2 className="text-2xl font-semibold text-blue-400 mb-4">مرحله 6: معاملات زنده (پیشرفته)</h2>
            <div className="space-y-4">
              <p className="leading-relaxed">
                پس از اطمینان از عملکرد استراتژی در بک‌تست، می‌توانید از استراتژی خود در معاملات زنده استفاده کنید.
              </p>
              
              <div className="bg-gray-800 rounded-lg p-4">
                <h3 className="text-xl font-semibold text-yellow-400 mb-3">نکات مهم قبل از معاملات زنده:</h3>
                <ul className="list-disc list-inside space-y-2 mr-4">
                  <li>حتماً استراتژی را در چندین بازه زمانی مختلف تست کنید</li>
                  <li>از حساب دمو برای تست اولیه استفاده کنید</li>
                  <li>میزان ریسک را به درستی تنظیم کنید</li>
                  <li>همیشه از حد ضرر و حد سود استفاده کنید</li>
                  <li>وضعیت معاملات را به صورت منظم بررسی کنید</li>
                </ul>
              </div>

              <div className="bg-red-900 border-r-4 border-red-500 p-4 rounded">
                <h4 className="text-lg font-semibold text-red-300 mb-2">⚠️ هشدار:</h4>
                <p className="text-sm">
                  معاملات در بازارهای مالی همیشه با ریسک همراه است. قبل از استفاده از سرمایه واقعی، حتماً با حساب دمو تمرین کنید و از آمادگی کامل خود اطمینان حاصل کنید.
                </p>
              </div>
            </div>
          </section>

          {/* بخش 8: سوالات متداول */}
          <section className="bg-gray-900 rounded-lg p-6">
            <h2 className="text-2xl font-semibold text-blue-400 mb-4">سوالات متداول (FAQ)</h2>
            <div className="space-y-4">
              <div className="bg-gray-800 rounded-lg p-4">
                <h3 className="text-lg font-semibold text-yellow-400 mb-2">چرا نمی‌توانم بک‌تست اجرا کنم؟</h3>
                <p className="text-sm">
                  مطمئن شوید که یک استراتژی به عنوان <strong>استراتژی اصلی</strong> تعیین شده است. بدون استراتژی اصلی، امکان اجرای بک‌تست وجود ندارد.
                </p>
              </div>

              <div className="bg-gray-800 rounded-lg p-4">
                <h3 className="text-lg font-semibold text-yellow-400 mb-2">چقدر طول می‌کشد تا بک‌تست تکمیل شود؟</h3>
                <p className="text-sm">
                  زمان تکمیل بک‌تست به عوامل مختلفی بستگی دارد: بازه زمانی انتخاب شده، پیچیدگی استراتژی، و حجم داده‌ها. معمولاً بین 2 تا 10 دقیقه طول می‌کشد.
                </p>
              </div>

              <div className="bg-gray-800 rounded-lg p-4">
                <h3 className="text-lg font-semibold text-yellow-400 mb-2">چگونه می‌توانم استراتژی خود را بهبود دهم؟</h3>
                <p className="text-sm">
                  می‌توانید از بخش بهینه‌سازی استفاده کنید، یا با بررسی نتایج بک‌تست و تحلیل AI، پارامترهای استراتژی را به صورت دستی تنظیم کنید.
                </p>
              </div>

              <div className="bg-gray-800 rounded-lg p-4">
                <h3 className="text-lg font-semibold text-yellow-400 mb-2">آیا می‌توانم چندین استراتژی را همزمان تست کنم؟</h3>
                <p className="text-sm">
                  بله، می‌توانید چندین استراتژی آپلود کنید و هر کدام را به صورت جداگانه تست کنید. اما در هر زمان فقط یک استراتژی می‌تواند به عنوان اصلی تعیین شود.
                </p>
              </div>
            </div>
          </section>

          {/* بخش 9: لینک‌های مفید */}
          <section className="bg-gray-900 rounded-lg p-6">
            <h2 className="text-2xl font-semibold text-blue-400 mb-4">لینک‌های مفید</h2>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <Link to="/" className="bg-gray-800 hover:bg-gray-700 rounded-lg p-4 transition-colors">
                <h3 className="text-lg font-semibold text-blue-400 mb-2">📊 داشبورد</h3>
                <p className="text-sm text-gray-300">مدیریت استراتژی‌ها و مشاهده آمار کلی</p>
              </Link>
              <Link to="/testing" className="bg-gray-800 hover:bg-gray-700 rounded-lg p-4 transition-colors">
                <h3 className="text-lg font-semibold text-green-400 mb-2">🧪 تست استراتژی</h3>
                <p className="text-sm text-gray-300">اجرای بک‌تست و تست استراتژی‌ها</p>
              </Link>
              <Link to="/results" className="bg-gray-800 hover:bg-gray-700 rounded-lg p-4 transition-colors">
                <h3 className="text-lg font-semibold text-yellow-400 mb-2">📈 نتایج</h3>
                <p className="text-sm text-gray-300">مشاهده و تحلیل نتایج بک‌تست‌ها</p>
              </Link>
              <Link to="/profile" className="bg-gray-800 hover:bg-gray-700 rounded-lg p-4 transition-colors">
                <h3 className="text-lg font-semibold text-purple-400 mb-2">👤 پروفایل</h3>
                <p className="text-sm text-gray-300">مدیریت پروفایل و تنظیمات کاربری</p>
              </Link>
            </div>
          </section>
        </div>
      </div>
    </div>
    </>
  )
}
