import { Link, useLocation, useNavigate } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'
import { useState, useRef, useEffect } from 'react'
import { useFeatureFlags } from '../context/FeatureFlagsContext'
import { useProfileCompletion } from '../context/ProfileCompletionContext'

export default function Navbar() {
  const location = useLocation()
  const navigate = useNavigate()
  const { isAuthenticated, user, logout, isAdmin } = useAuth()
  const { liveTradingEnabled } = useFeatureFlags()
  const { shouldRemind, snooze } = useProfileCompletion()
  const [isAboutDropdownOpen, setIsAboutDropdownOpen] = useState(false)
  const [isAdminDropdownOpen, setIsAdminDropdownOpen] = useState(false)
  const [isMobileMenuOpen, setIsMobileMenuOpen] = useState(false)
  const dropdownRef = useRef<HTMLDivElement>(null)
  const adminDropdownRef = useRef<HTMLDivElement>(null)
  const mobileDropdownRef = useRef<HTMLDivElement>(null)

  const primaryPhoneNumber =
    user?.phone_number && user.phone_number.trim().length > 0 ? user.phone_number.trim() : null
  const fullName =
    user?.first_name && user?.last_name ? `${user.first_name} ${user.last_name}`.trim() : null
  const displayName =
    (user?.nickname && user.nickname.trim()) ||
    (user?.username && user.username.trim()) ||
    (fullName && fullName.trim()) ||
    (user?.email && user.email.trim()) ||
    'کاربر'
  const handleLogout = async () => {
    await logout()
    navigate('/login')
  }

  // Close dropdown when clicking outside
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      const target = event.target as Node
      const isInsideDesktop = dropdownRef.current?.contains(target)
      const isInsideAdmin = adminDropdownRef.current?.contains(target)
      const isInsideMobile = mobileDropdownRef.current?.contains(target)
      
      // Close dropdown only if click is outside both desktop and mobile dropdowns
      if (!isInsideDesktop && !isInsideMobile) {
        setIsAboutDropdownOpen(false)
      }
      if (!isInsideAdmin && !isInsideMobile) {
        setIsAdminDropdownOpen(false)
      }
    }

    document.addEventListener('mousedown', handleClickOutside)
    return () => {
      document.removeEventListener('mousedown', handleClickOutside)
    }
  }, [])

  // Check if current path is in the about submenu
  const isAboutSubmenuActive = location.pathname === '/tickets' || 
                                location.pathname === '/tutorial' || 
                                location.pathname === '/profile' || 
                                location.pathname === '/about'
  
  // Check if current path is in the admin submenu
  const isAdminSubmenuActive = location.pathname.startsWith('/admin')
  
  return (
    <nav className="bg-gray-800 border-b border-gray-700 direction-rtl" style={{ direction: 'rtl', textAlign: 'right' }}>
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex items-center justify-between h-16">
          <div className="flex items-center flex-1 min-w-0">
            <Link to="/" className="text-sm sm:text-base md:text-lg lg:text-xl font-bold text-blue-400 truncate">
              <span className="hidden sm:inline">سامانه مدیریت هوشمند معاملات فارکس</span>
              <span className="sm:hidden">سامانه معاملات</span>
            </Link>
          </div>
          <div className="hidden md:flex items-center gap-4">
            <Link
              to="/"
              className={`px-4 py-2 rounded-lg text-sm font-medium transition ${
                location.pathname === '/'
                  ? 'bg-gray-700 text-white'
                  : 'text-gray-300 hover:bg-gray-700 hover:text-white'
              }`}
            >
              داشبورد
            </Link>
            <Link
              to="/testing"
              className={`px-4 py-2 rounded-lg text-sm font-medium transition ${
                location.pathname === '/testing'
                  ? 'bg-gray-700 text-white'
                  : 'text-gray-300 hover:bg-gray-700 hover:text-white'
              }`}
            >
              تست استراتژی
            </Link>
            <Link
              to="/results"
              className={`px-4 py-2 rounded-lg text-sm font-medium transition ${
                location.pathname === '/results'
                  ? 'bg-gray-700 text-white'
                  : 'text-gray-300 hover:bg-gray-700 hover:text-white'
              }`}
            >
              نتایج
            </Link>
            {liveTradingEnabled && (
              <Link
                to="/trading"
                className={`px-4 py-2 rounded-lg text-sm font-medium transition ${
                  location.pathname === '/trading'
                    ? 'bg-gray-700 text-white'
                    : 'text-gray-300 hover:bg-gray-700 hover:text-white'
                }`}
              >
                معاملات زنده
              </Link>
            )}
            <Link
              to="/marketplace"
              className={`px-4 py-2 rounded-lg text-sm font-medium transition ${
                location.pathname === '/marketplace'
                  ? 'bg-gray-700 text-white'
                  : 'text-gray-300 hover:bg-gray-700 hover:text-white'
              }`}
            >
              مارکت‌پلیس استراتژی‌ها
            </Link>
            {isAuthenticated && shouldRemind && (
              <div className="flex items-center gap-2 px-3 py-2 rounded-lg border border-orange-500/60 bg-orange-500/10">
                <span className="text-xs text-orange-200 whitespace-nowrap">پروفایل خود را تکمیل کنید</span>
                <Link
                  to="/profile"
                  className="px-2 py-1 text-xs font-semibold rounded-md bg-orange-500 text-gray-900 hover:bg-orange-400 transition"
                >
                  تکمیل
                </Link>
                <button
                  type="button"
                  onClick={() => snooze()}
                  className="text-xs text-orange-300 hover:text-orange-200 transition"
                >
                  بعدا
                </button>
              </div>
            )}
            {/* Admin Panel Dropdown */}
            {isAuthenticated && isAdmin && (
              <div className="relative" ref={adminDropdownRef}>
                <button
                  onClick={() => setIsAdminDropdownOpen(!isAdminDropdownOpen)}
                  className={`px-4 py-2 rounded-lg text-sm font-medium transition flex items-center gap-1 ${
                    isAdminSubmenuActive
                      ? 'bg-gray-700 text-white'
                      : 'text-gray-300 hover:bg-gray-700 hover:text-white'
                  }`}
                >
                  پنل ادمین
                  <svg
                    className={`w-4 h-4 transition-transform ${isAdminDropdownOpen ? 'rotate-180' : ''}`}
                    fill="none"
                    stroke="currentColor"
                    viewBox="0 0 24 24"
                  >
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
                  </svg>
                </button>
                
                {isAdminDropdownOpen && (
                  <div className="absolute right-0 mt-2 w-56 bg-gray-800 rounded-lg shadow-lg border border-gray-700 z-50">
                    <div className="py-1">
                      <Link
                        to="/admin/users"
                        onClick={() => setIsAdminDropdownOpen(false)}
                        className={`block px-4 py-2 text-sm transition ${
                          location.pathname === '/admin/users'
                            ? 'bg-gray-700 text-white'
                            : 'text-gray-300 hover:bg-gray-700 hover:text-white'
                        }`}
                      >
                        مدیریت کاربران
                      </Link>
                      <Link
                        to="/admin/security"
                        onClick={() => setIsAdminDropdownOpen(false)}
                        className={`block px-4 py-2 text-sm transition ${
                          location.pathname === '/admin/security'
                            ? 'bg-gray-700 text-white'
                            : 'text-gray-300 hover:bg-gray-700 hover:text-white'
                        }`}
                      >
                        مدیریت امنیت
                      </Link>
                      <Link
                        to="/admin/settings"
                        onClick={() => setIsAdminDropdownOpen(false)}
                        className={`block px-4 py-2 text-sm transition ${
                          location.pathname === '/admin/settings'
                            ? 'bg-gray-700 text-white'
                            : 'text-gray-300 hover:bg-gray-700 hover:text-white'
                        }`}
                      >
                        تنظیمات سیستم
                      </Link>
                    </div>
                  </div>
                )}
              </div>
            )}

            {/* About System Dropdown */}
            <div className="relative" ref={dropdownRef}>
              <button
                onClick={() => setIsAboutDropdownOpen(!isAboutDropdownOpen)}
                className={`px-4 py-2 rounded-lg text-sm font-medium transition flex items-center gap-1 ${
                  isAboutSubmenuActive
                    ? 'bg-gray-700 text-white'
                    : 'text-gray-300 hover:bg-gray-700 hover:text-white'
                }`}
              >
                درباره سیستم
                <svg
                  className={`w-4 h-4 transition-transform ${isAboutDropdownOpen ? 'rotate-180' : ''}`}
                  fill="none"
                  stroke="currentColor"
                  viewBox="0 0 24 24"
                >
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
                </svg>
              </button>
              
              {isAboutDropdownOpen && (
                <div className="absolute right-0 mt-2 w-48 bg-gray-800 rounded-lg shadow-lg border border-gray-700 z-50">
                  <div className="py-1">
                    {isAuthenticated && (
                      <div className="px-4 py-3 border-b border-gray-700">
                        <div className="text-xs text-gray-400 mb-1">کاربر :</div>
                        <div className="text-sm font-medium text-blue-400">{displayName}</div>
                        {primaryPhoneNumber && (
                          <div className="mt-1 text-xs text-gray-300" dir="ltr">
                            {primaryPhoneNumber}
                          </div>
                        )}
                        <Link
                          to="/profile"
                          onClick={() => setIsAboutDropdownOpen(false)}
                          className="mt-3 inline-flex w-full justify-center rounded-md bg-blue-500 px-3 py-2 text-xs font-semibold text-gray-900 hover:bg-blue-400 transition"
                        >
                          پروفایل
                        </Link>
                      </div>
                    )}
                    <Link
                      to="/about"
                      onClick={() => setIsAboutDropdownOpen(false)}
                      className={`block px-4 py-2 text-sm transition ${
                        location.pathname === '/about'
                          ? 'bg-gray-700 text-white'
                          : 'text-gray-300 hover:bg-gray-700 hover:text-white'
                      }`}
                    >
                      درباره سیستم
                    </Link>
                    {isAuthenticated && (
                      <Link
                        to="/tickets"
                        onClick={() => setIsAboutDropdownOpen(false)}
                        className={`block px-4 py-2 text-sm transition ${
                          location.pathname === '/tickets'
                            ? 'bg-gray-700 text-white'
                            : 'text-gray-300 hover:bg-gray-700 hover:text-white'
                        }`}
                      >
                        تیکت‌ها
                      </Link>
                    )}
                    <Link
                      to="/tutorial"
                      onClick={() => setIsAboutDropdownOpen(false)}
                      className={`block px-4 py-2 text-sm transition ${
                        location.pathname === '/tutorial'
                          ? 'bg-gray-700 text-white'
                          : 'text-gray-300 hover:bg-gray-700 hover:text-white'
                      }`}
                    >
                      آموزش
                    </Link>
                    <Link
                      to="/guides/free-gold-api"
                      onClick={() => setIsAboutDropdownOpen(false)}
                      className={`block px-4 py-2 text-sm transition ${
                        location.pathname === '/guides/free-gold-api'
                          ? 'bg-gray-700 text-white'
                          : 'text-gray-300 hover:bg-gray-700 hover:text-white'
                      }`}
                    >
                      راهنمای دریافت API طلا
                    </Link>
                    {isAuthenticated && (
                      <div className="px-4 py-2 text-xs text-gray-400">
                        <div className="font-medium text-gray-300">برای مدیریت بیشتر به پروفایل مراجعه کنید.</div>
                      </div>
                    )}
                  </div>
                </div>
              )}
            </div>

            {isAuthenticated ? (
              <div className="flex items-center gap-4">
                <button
                  onClick={handleLogout}
                  className="px-4 py-2 rounded-lg text-sm font-medium text-gray-300 hover:bg-gray-700 hover:text-white transition"
                >
                  خروج
                </button>
              </div>
            ) : (
              <Link
                to="/login"
                className="px-4 py-2 rounded-lg text-sm font-medium text-blue-400 hover:bg-gray-700 hover:text-blue-300 transition"
              >
                ورود
              </Link>
            )}
          </div>
          
          {/* Mobile menu button */}
          <div className="md:hidden flex items-center">
            <button
              onClick={() => setIsMobileMenuOpen(!isMobileMenuOpen)}
              className="text-gray-300 hover:text-white focus:outline-none focus:text-white"
              aria-label="منو"
            >
              <svg className="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                {isMobileMenuOpen ? (
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                ) : (
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 6h16M4 12h16M4 18h16" />
                )}
              </svg>
            </button>
          </div>
        </div>
        
        {/* Mobile menu */}
        {isMobileMenuOpen && (
          <div className="md:hidden py-4 border-t border-gray-700">
            <div className="flex flex-col gap-2">
              {isAuthenticated && shouldRemind && (
                <div className="mx-4 px-4 py-3 rounded-lg border border-orange-500/60 bg-orange-500/10 text-orange-200">
                  <div className="flex items-center justify-between gap-3">
                    <span className="text-sm font-medium">پروفایل خود را تکمیل کنید</span>
                    <Link
                      to="/profile"
                      onClick={() => {
                        setIsMobileMenuOpen(false)
                      }}
                      className="px-3 py-1 rounded-md bg-orange-500 text-gray-900 text-xs font-semibold hover:bg-orange-400 transition"
                    >
                      تکمیل
                    </Link>
                  </div>
                  <button
                    type="button"
                    onClick={() => {
                      snooze()
                      setIsMobileMenuOpen(false)
                    }}
                    className="mt-2 text-xs text-orange-300 hover:text-orange-200 transition"
                  >
                    بعدا یادآوری کن
                  </button>
                </div>
              )}
              <Link
                to="/"
                onClick={() => setIsMobileMenuOpen(false)}
                className={`px-4 py-2 rounded-lg text-sm font-medium transition ${
                  location.pathname === '/'
                    ? 'bg-gray-700 text-white'
                    : 'text-gray-300 hover:bg-gray-700 hover:text-white'
                }`}
              >
                داشبورد
              </Link>
              <Link
                to="/testing"
                onClick={() => setIsMobileMenuOpen(false)}
                className={`px-4 py-2 rounded-lg text-sm font-medium transition ${
                  location.pathname === '/testing'
                    ? 'bg-gray-700 text-white'
                    : 'text-gray-300 hover:bg-gray-700 hover:text-white'
                }`}
              >
                تست استراتژی
              </Link>
              <Link
                to="/results"
                onClick={() => setIsMobileMenuOpen(false)}
                className={`px-4 py-2 rounded-lg text-sm font-medium transition ${
                  location.pathname === '/results'
                    ? 'bg-gray-700 text-white'
                    : 'text-gray-300 hover:bg-gray-700 hover:text-white'
                }`}
              >
                نتایج
              </Link>
              {liveTradingEnabled && (
                <Link
                  to="/trading"
                  onClick={() => setIsMobileMenuOpen(false)}
                  className={`px-4 py-2 rounded-lg text-sm font-medium transition ${
                    location.pathname === '/trading'
                      ? 'bg-gray-700 text-white'
                      : 'text-gray-300 hover:bg-gray-700 hover:text-white'
                  }`}
                >
                  معاملات زنده
                </Link>
              )}
              <Link
                to="/marketplace"
                onClick={() => setIsMobileMenuOpen(false)}
                className={`px-4 py-2 rounded-lg text-sm font-medium transition ${
                  location.pathname === '/marketplace'
                    ? 'bg-gray-700 text-white'
                    : 'text-gray-300 hover:bg-gray-700 hover:text-white'
                }`}
              >
                مارکت‌پلیس استراتژی‌ها
              </Link>
              {/* Admin Panel in Mobile Menu */}
              {isAuthenticated && isAdmin && (
                <div className="px-4 py-2">
                  <div className="text-xs text-gray-400 mb-2 px-4">پنل ادمین</div>
                  <Link
                    to="/admin/users"
                    onClick={() => setIsMobileMenuOpen(false)}
                    className={`block px-4 py-2 rounded-lg text-sm transition ${
                      location.pathname === '/admin/users'
                        ? 'bg-gray-700 text-white'
                        : 'text-gray-300 hover:bg-gray-700 hover:text-white'
                    }`}
                  >
                    مدیریت کاربران
                  </Link>
                  <Link
                    to="/admin/security"
                    onClick={() => setIsMobileMenuOpen(false)}
                    className={`block px-4 py-2 rounded-lg text-sm transition ${
                      location.pathname === '/admin/security'
                        ? 'bg-gray-700 text-white'
                        : 'text-gray-300 hover:bg-gray-700 hover:text-white'
                    }`}
                  >
                    مدیریت امنیت
                  </Link>
                  <Link
                    to="/admin/settings"
                    onClick={() => setIsMobileMenuOpen(false)}
                    className={`block px-4 py-2 rounded-lg text-sm transition ${
                      location.pathname === '/admin/settings'
                        ? 'bg-gray-700 text-white'
                        : 'text-gray-300 hover:bg-gray-700 hover:text-white'
                    }`}
                  >
                    تنظیمات سیستم
                  </Link>
                </div>
              )}
              <div className="px-4 py-2" ref={mobileDropdownRef}>
                <button
                  onClick={() => setIsAboutDropdownOpen(!isAboutDropdownOpen)}
                  className={`w-full px-4 py-2 rounded-lg text-sm font-medium transition flex items-center justify-between ${
                    isAboutSubmenuActive
                      ? 'bg-gray-700 text-white'
                      : 'text-gray-300 hover:bg-gray-700 hover:text-white'
                  }`}
                >
                  درباره سیستم
                  <svg
                    className={`w-4 h-4 transition-transform ${isAboutDropdownOpen ? 'rotate-180' : ''}`}
                    fill="none"
                    stroke="currentColor"
                    viewBox="0 0 24 24"
                  >
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
                  </svg>
                </button>
                {isAboutDropdownOpen && (
                  <div className="mt-2 pr-4 space-y-1">
                    {isAuthenticated && (
                      <div className="px-4 py-3 bg-gray-800 rounded-lg border border-gray-700 space-y-2">
                        <div>
                          <div className="text-xs text-gray-400">کاربر :</div>
                          <div className="text-sm font-medium text-blue-400">{displayName}</div>
                          {primaryPhoneNumber && (
                            <div className="mt-1 text-xs text-gray-300" dir="ltr">
                              {primaryPhoneNumber}
                            </div>
                          )}
                        </div>
                        <Link
                          to="/profile"
                          onClick={() => {
                            setIsAboutDropdownOpen(false)
                            setIsMobileMenuOpen(false)
                          }}
                          className="inline-flex w-full justify-center rounded-md bg-blue-500 px-3 py-2 text-xs font-semibold text-gray-900 hover:bg-blue-400 transition"
                        >
                          پروفایل
                        </Link>
                      </div>
                    )}
                    <Link
                      to="/about"
                      onClick={() => {
                        setIsAboutDropdownOpen(false)
                        setIsMobileMenuOpen(false)
                      }}
                      className={`block px-4 py-2 rounded-lg text-sm transition ${
                        location.pathname === '/about'
                          ? 'bg-gray-700 text-white'
                          : 'text-gray-300 hover:bg-gray-700 hover:text-white'
                      }`}
                    >
                      درباره سیستم
                    </Link>
                    {isAuthenticated && (
                      <Link
                        to="/tickets"
                        onClick={() => {
                          setIsAboutDropdownOpen(false)
                          setIsMobileMenuOpen(false)
                        }}
                        className={`block px-4 py-2 rounded-lg text-sm transition ${
                          location.pathname === '/tickets'
                            ? 'bg-gray-700 text-white'
                            : 'text-gray-300 hover:bg-gray-700 hover:text-white'
                        }`}
                      >
                        تیکت‌ها
                      </Link>
                    )}
                    <Link
                      to="/tutorial"
                      onClick={() => {
                        setIsAboutDropdownOpen(false)
                        setIsMobileMenuOpen(false)
                      }}
                      className={`block px-4 py-2 rounded-lg text-sm transition ${
                        location.pathname === '/tutorial'
                          ? 'bg-gray-700 text-white'
                          : 'text-gray-300 hover:bg-gray-700 hover:text-white'
                      }`}
                    >
                      آموزش
                    </Link>
                    <Link
                      to="/guides/free-gold-api"
                      onClick={() => {
                        setIsAboutDropdownOpen(false)
                        setIsMobileMenuOpen(false)
                      }}
                      className={`block px-4 py-2 rounded-lg text-sm transition ${
                        location.pathname === '/guides/free-gold-api'
                          ? 'bg-gray-700 text-white'
                          : 'text-gray-300 hover:bg-gray-700 hover:text-white'
                      }`}
                    >
                      راهنمای دریافت API طلا
                    </Link>
                    {isAuthenticated && (
                      <div className="px-4 py-1 text-xs text-gray-400">
                        برای ویرایش اطلاعات بیشتر به بخش پروفایل بروید.
                      </div>
                    )}
                  </div>
                )}
              </div>
              {isAuthenticated && user && (
                <div className="px-4 py-3 border-t border-gray-700">
                  <div className="text-sm text-gray-400 mb-1">کاربر لاگین شده:</div>
                  <div className="text-sm font-medium text-blue-400">{displayName}</div>
                </div>
              )}
              {isAuthenticated ? (
                <button
                  onClick={() => {
                    handleLogout()
                    setIsMobileMenuOpen(false)
                  }}
                  className="px-4 py-2 rounded-lg text-sm font-medium text-gray-300 hover:bg-gray-700 hover:text-white transition text-right"
                >
                  خروج
                </button>
              ) : (
                <Link
                  to="/login"
                  onClick={() => setIsMobileMenuOpen(false)}
                  className="px-4 py-2 rounded-lg text-sm font-medium text-blue-400 hover:bg-gray-700 hover:text-blue-300 transition text-right"
                >
                  ورود
                </Link>
              )}
            </div>
          </div>
        )}
      </div>
    </nav>
  )
}

