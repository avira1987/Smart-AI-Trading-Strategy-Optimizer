import React from 'react'

export default function Terms() {
  return (
    <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-12 direction-rtl" style={{ direction: 'rtl', textAlign: 'right' }}>
      <div className="bg-gray-800 rounded-xl shadow-2xl p-8 space-y-6">
        <div>
          <h1 className="text-3xl font-bold text-white mb-4">قوانین و مقررات استفاده از سامانه</h1>
          <p className="text-gray-300 leading-relaxed">
            مطالعه و رعایت قوانین زیر برای استفاده از سامانه مدیریت هوشمند معاملات الزامی است. استفاده شما از سامانه به معنی قبول کامل
            تمامی بندهای این توافق‌نامه است.
          </p>
        </div>

        <section className="space-y-3 text-gray-300 leading-relaxed">
          <h2 className="text-2xl font-semibold text-blue-400">۱. شرایط عمومی</h2>
          <ul className="list-disc list-inside space-y-2">
            <li>کاربر موظف است اطلاعات هویتی و تماس خود را به صورت صحیح و به‌روز ثبت کند.</li>
            <li>هر حساب کاربری مختص یک شخص است و واگذاری آن به دیگران مجاز نیست.</li>
            <li>هرگونه استفاده از سامانه در راستای قوانین کشور جمهوری اسلامی ایران انجام می‌شود.</li>
          </ul>
        </section>

        <section className="space-y-3 text-gray-300 leading-relaxed">
          <h2 className="text-2xl font-semibold text-blue-400">۲. مسئولیت‌ها و محدودیت‌ها</h2>
          <ul className="list-disc list-inside space-y-2">
            <li>پیش از انجام معاملات واقعی، مسئولیت بررسی و صحت‌سنجی نتایج تحلیل‌ها بر عهده کاربر است.</li>
            <li>سامانه هیچ‌گونه تضمینی بابت سودآوری یا عملکرد مثبت استراتژی‌های معاملاتی ارائه نمی‌دهد.</li>
            <li>کاربر مسئول حفاظت از اطلاعات ورود و عدم افشای آن به اشخاص ثالث است.</li>
          </ul>
        </section>

        <section className="space-y-3 text-gray-300 leading-relaxed">
          <h2 className="text-2xl font-semibold text-blue-400">۳. حریم خصوصی و امنیت</h2>
          <ul className="list-disc list-inside space-y-2">
            <li>اطلاعات شخصی کاربران مطابق سیاست‌های امنیتی سامانه محافظت می‌شود.</li>
            <li>در صورت مشاهده هرگونه فعالیت مشکوک، کاربر موظف است مراتب را به تیم پشتیبانی اطلاع دهد.</li>
            <li>سامانه برای بهبود امنیت دسترسی، از روش‌های احراز هویت چندمرحله‌ای استفاده می‌کند.</li>
          </ul>
        </section>

        <section className="space-y-3 text-gray-300 leading-relaxed">
          <h2 className="text-2xl font-semibold text-blue-400">۴. تغییرات و به‌روزرسانی‌ها</h2>
          <ul className="list-disc list-inside space-y-2">
            <li>سامانه می‌تواند در هر زمان نسبت به به‌روزرسانی قوانین اقدام کند.</li>
            <li>ادامه استفاده شما پس از اعمال تغییرات، به منزله قبول نسخه جدید قوانین خواهد بود.</li>
            <li>آخرین به‌روزرسانی قوانین در تاریخ ۱۴۰۴/۰۸/۱۸ اعمال شده است.</li>
          </ul>
        </section>

        <section className="space-y-3 text-gray-300 leading-relaxed">
          <h2 className="text-2xl font-semibold text-blue-400">۵. پشتیبانی و تماس</h2>
          <p>
            در صورت وجود هرگونه سؤال یا ابهام درباره قوانین، از طریق کانال‌های پشتیبانی معرفی‌شده در سامانه با ما در تماس باشید.
          </p>
        </section>

        <div className="text-sm text-gray-400 border-t border-gray-700 pt-4">
          <p>ادامه استفاده شما از سامانه به معنی پذیرش کامل تمامی بندهای فوق است.</p>
        </div>
      </div>
    </div>
  )
}



