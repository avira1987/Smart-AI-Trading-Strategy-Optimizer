import { Link, useLocation, useNavigate } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'
import { useState, useRef, useEffect } from 'react'

export default function Navbar() {
  const location = useLocation()
  const navigate = useNavigate()
  const { isAuthenticated, user, logout } = useAuth()
  const [isAboutDropdownOpen, setIsAboutDropdownOpen] = useState(false)
  const [isMobileMenuOpen, setIsMobileMenuOpen] = useState(false)
  const dropdownRef = useRef<HTMLDivElement>(null)
  const mobileDropdownRef = useRef<HTMLDivElement>(null)

  const handleLogout = async () => {
    await logout()
    navigate('/login')
  }

  // Close dropdown when clicking outside
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      const target = event.target as Node
      const isInsideDesktop = dropdownRef.current?.contains(target)
      const isInsideMobile = mobileDropdownRef.current?.contains(target)
      
      // Close dropdown only if click is outside both desktop and mobile dropdowns
      if (!isInsideDesktop && !isInsideMobile) {
        setIsAboutDropdownOpen(false)
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
                    {isAuthenticated && (
                      <Link
                        to="/profile"
                        onClick={() => setIsAboutDropdownOpen(false)}
                        className={`block px-4 py-2 text-sm transition ${
                          location.pathname === '/profile'
                            ? 'bg-gray-700 text-white'
                            : 'text-gray-300 hover:bg-gray-700 hover:text-white'
                        }`}
                      >
                        پروفایل
                      </Link>
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
                    {isAuthenticated && (
                      <Link
                        to="/profile"
                        onClick={() => {
                          setIsAboutDropdownOpen(false)
                          setIsMobileMenuOpen(false)
                        }}
                        className={`block px-4 py-2 rounded-lg text-sm transition ${
                          location.pathname === '/profile'
                            ? 'bg-gray-700 text-white'
                            : 'text-gray-300 hover:bg-gray-700 hover:text-white'
                        }`}
                      >
                        پروفایل
                      </Link>
                    )}
                  </div>
                )}
              </div>
              {isAuthenticated && user && (
                <div className="px-4 py-3 border-t border-gray-700">
                  <div className="text-sm text-gray-400 mb-1">کاربر لاگین شده:</div>
                  <div className="text-sm font-medium text-blue-400">
                    {user.username || user.email || (user.first_name && user.last_name ? `${user.first_name} ${user.last_name}` : 'کاربر')}
                  </div>
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

