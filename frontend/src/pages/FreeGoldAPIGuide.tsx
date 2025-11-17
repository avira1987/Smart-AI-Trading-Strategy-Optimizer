import { Link } from 'react-router-dom'

const providers = [
  {
    name: 'TwelveData',
    url: 'https://twelvedata.com',
    steps: [
      'در وب‌سایت TwelveData ثبت نام کنید و ایمیل خود را تایید نمایید.',
      'در داشبورد کاربری، از بخش API Keys یک کلید جدید ایجاد کنید.',
      'پلن رایگان قادر به ارائه 800 درخواست روزانه است که برای بک‌تست کافی است.',
      'کلید دریافت شده را در بخش پروفایل > دسترسی به قیمت طلا وارد کنید.',
    ],
  },
  {
    name: 'Financial Modeling Prep',
    url: 'https://site.financialmodelingprep.com/developer',
    steps: [
      'یک حساب رایگان ایجاد کنید و وارد داشبورد شوید.',
      'در بخش API Key، کلید عمومی خود را دریافت کنید.',
      'برای نماد طلا از Endpoint های XAUUSD یا commodities استفاده کنید.',
      'کلید را در پروفایل سامانه ثبت کنید تا برای بک‌تست‌ها آماده شود.',
    ],
  },
  {
    name: 'MetalsAPI',
    url: 'https://metals-api.com',
    steps: [
      'پس از ثبت‌نام، یک پلن رایگان انتخاب کنید.',
      'از بخش Dashboard کلید API را کپی کنید.',
      'برای دریافت قیمت طلا از Endpoint مربوط به XAU/USD استفاده نمایید.',
      'در صورت نیاز به محدوده تاریخی بزرگ‌تر، از پلن پولی استفاده کنید.',
    ],
  },
]

export default function FreeGoldAPIGuide() {
  return (
    <div className="max-w-5xl mx-auto px-4 sm:px-6 lg:px-8 py-10 direction-rtl" style={{ direction: 'rtl', textAlign: 'right' }}>
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-white mb-3">راهنمای دریافت API رایگان برای قیمت طلا</h1>
        <p className="text-gray-300 text-sm leading-7">
          برای اجرای بک‌تست‌های استراتژی در سامانه، به دسترسی لحظه‌ای قیمت طلا نیاز دارید. ساده‌ترین راه، ثبت‌نام در سرویس‌های ارائه‌دهنده
          داده‌های مالی و استفاده از پلن رایگان آن‌ها است. در این صفحه مراحل تهیه و ثبت API شرح داده شده است.
        </p>
      </div>

      <div className="bg-gray-800 rounded-lg border border-gray-700 p-6 mb-8">
        <h2 className="text-xl font-semibold text-white mb-3">مراحل کلی</h2>
        <ol className="list-decimal pr-5 text-gray-300 text-sm space-y-2">
          <li>در یکی از سرویس‌های معرفی شده ثبت نام کنید و ایمیل خود را تایید نمایید.</li>
          <li>در داشبورد حساب کاربری سرویس، کلید API اختصاصی خود را ایجاد یا مشاهده کنید.</li>
          <li>در سامانه استراتژی، به صفحه <Link to="/profile" className="text-blue-400 hover:text-blue-300">پروفایل &gt; دسترسی به قیمت طلا</Link> بروید.</li>
          <li>کلید و نام ارائه‌دهنده را وارد کرده و روی «ذخیره تنظیمات» کلیک کنید.</li>
          <li>پس از ثبت، بک‌تست‌ها و تحلیل‌ها از API شخصی شما استفاده خواهند کرد.</li>
        </ol>
      </div>

      <div className="space-y-6">
        {providers.map((provider) => (
          <div key={provider.name} className="bg-gray-800 border border-gray-700 rounded-lg p-6">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-lg font-semibold text-white">{provider.name}</h3>
              <a
                href={provider.url}
                target="_blank"
                rel="noopener noreferrer"
                className="text-sm text-blue-400 hover:text-blue-300"
              >
                ورود به وب‌سایت
              </a>
            </div>
            <ul className="list-disc pr-5 text-sm text-gray-300 space-y-2 leading-6">
              {provider.steps.map((step, index) => (
                <li key={index}>{step}</li>
              ))}
            </ul>
          </div>
        ))}
      </div>

      <div className="bg-gray-800 border border-yellow-600 rounded-lg p-5 mt-8">
        <h3 className="text-lg font-semibold text-yellow-300 mb-2">نکات مهم</h3>
        <ul className="list-disc pr-5 text-sm text-gray-300 space-y-2 leading-6">
          <li>پلن‌های رایگان معمولاً محدودیت تعداد درخواست یا تأخیر در داده‌ها دارند؛ برای معاملات زنده به پلن حرفه‌ای نیاز خواهید داشت.</li>
          <li>کلید API خود را در اختیار افراد ناشناس قرار ندهید. در صورت لو رفتن کلید، آن را از داشبورد سرویس لغو کنید.</li>
          <li>در صورت نیاز به راهنمایی سریع، می‌توانید از بخش پروفایل درخواست «دریافت API توسط تیم» ثبت کنید.</li>
        </ul>
      </div>
    </div>
  )
}

