import { useState, useEffect } from 'react'
import { useAuth } from '../context/AuthContext'
import { useToast } from '../components/ToastProvider'
import { getAdminUsers, allocateUserCredit, deleteUser, updateUser, type AdminUser } from '../api/client'

const AUTO_REFRESH_INTERVAL_MS = 60000

export default function AdminUserManagement() {
  const { isAdmin, user: currentUser } = useAuth()
  const { showToast } = useToast()
  const [users, setUsers] = useState<AdminUser[]>([])
  const [loading, setLoading] = useState(false)
  const [allocating, setAllocating] = useState<number | null>(null)
  const [deleting, setDeleting] = useState<number | null>(null)
  const [updating, setUpdating] = useState<number | null>(null)
  const [selectedUser, setSelectedUser] = useState<AdminUser | null>(null)
  const [amount, setAmount] = useState('')
  const [description, setDescription] = useState('')
  const [showAllocateModal, setShowAllocateModal] = useState(false)
  const [showDeleteModal, setShowDeleteModal] = useState(false)
  const [showEditModal, setShowEditModal] = useState(false)
  const [editForm, setEditForm] = useState({
    email: '',
    first_name: '',
    last_name: '',
    phone_number: '',
    nickname: '',
    is_staff: false,
    is_superuser: false,
  })

  useEffect(() => {
    if (!isAdmin) {
      return
    }
    loadUsers()
    const interval = setInterval(() => {
      if (typeof document !== 'undefined' && document.hidden) {
        return
      }
      loadUsers()
    }, AUTO_REFRESH_INTERVAL_MS)
    return () => clearInterval(interval)
  }, [isAdmin])

  if (!isAdmin) {
    return (
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
        <div className="bg-gray-800 rounded-lg p-6">
          <div className="text-red-400 text-center">
            ⚠️ فقط ادمین می‌تواند به این بخش دسترسی داشته باشد
          </div>
        </div>
      </div>
    )
  }

  const loadUsers = async () => {
    try {
      setLoading(true)
      const response = await getAdminUsers()
      setUsers(response.data.users || [])
    } catch (error: any) {
      console.error('Error loading users:', error)
      showToast('خطا در بارگذاری لیست کاربران', { type: 'error' })
    } finally {
      setLoading(false)
    }
  }

  const handleAllocateCredit = async () => {
    if (!selectedUser) return
    
    const amountNum = parseFloat(amount)
    if (isNaN(amountNum) || amountNum <= 0) {
      showToast('مبلغ باید یک عدد مثبت باشد', { type: 'error' })
      return
    }

    try {
      setAllocating(selectedUser.id)
      const response = await allocateUserCredit(
        selectedUser.id,
        amountNum,
        description || undefined
      )
      if (response.data.success) {
        showToast(response.data.message, { type: 'success' })
        setShowAllocateModal(false)
        setAmount('')
        setDescription('')
        setSelectedUser(null)
        await loadUsers()
      } else {
        showToast('خطا در تخصیص اعتبار', { type: 'error' })
      }
    } catch (error: any) {
      showToast(
        error.response?.data?.error || 'خطا در تخصیص اعتبار',
        { type: 'error' }
      )
    } finally {
      setAllocating(null)
    }
  }

  const openAllocateModal = (user: AdminUser) => {
    setSelectedUser(user)
    setAmount('')
    setDescription('')
    setShowAllocateModal(true)
  }

  const openDeleteModal = (user: AdminUser) => {
    setSelectedUser(user)
    setShowDeleteModal(true)
  }

  const openEditModal = (user: AdminUser) => {
    setSelectedUser(user)
    setEditForm({
      email: user.email || '',
      first_name: '',
      last_name: '',
      phone_number: user.phone_number || '',
      nickname: '',
      is_staff: user.is_staff || false,
      is_superuser: user.is_superuser || false,
    })
    setShowEditModal(true)
  }

  const handleDeleteUser = async () => {
    if (!selectedUser) return

    try {
      setDeleting(selectedUser.id)
      const response = await deleteUser(selectedUser.id)
      if (response.data.success) {
        showToast(response.data.message, { type: 'success' })
        setShowDeleteModal(false)
        setSelectedUser(null)
        await loadUsers()
      } else {
        showToast('خطا در حذف کاربر', { type: 'error' })
      }
    } catch (error: any) {
      showToast(
        error.response?.data?.error || 'خطا در حذف کاربر',
        { type: 'error' }
      )
    } finally {
      setDeleting(null)
    }
  }

  const handleUpdateUser = async () => {
    if (!selectedUser) return

    try {
      setUpdating(selectedUser.id)
      const response = await updateUser(selectedUser.id, editForm)
      if (response.data.success) {
        showToast(response.data.message, { type: 'success' })
        setShowEditModal(false)
        setSelectedUser(null)
        await loadUsers()
      } else {
        showToast('خطا در به‌روزرسانی کاربر', { type: 'error' })
      }
    } catch (error: any) {
      showToast(
        error.response?.data?.error || 'خطا در به‌روزرسانی کاربر',
        { type: 'error' }
      )
    } finally {
      setUpdating(null)
    }
  }

  const formatDate = (dateString: string) => {
    const date = new Date(dateString)
    return new Intl.DateTimeFormat('fa-IR', {
      year: 'numeric',
      month: 'long',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
    }).format(date)
  }

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6" dir="rtl" style={{ direction: 'rtl', textAlign: 'right' }}>
      <div className="mb-6">
        <h1 className="text-3xl font-bold text-white mb-2">مدیریت کاربران</h1>
        <p className="text-gray-400">مدیریت اعتبار و موجودی کاربران</p>
      </div>

      {/* Users Table */}
      <div className="bg-gray-800 rounded-lg shadow-lg overflow-hidden">
        <div className="px-6 py-4 border-b border-gray-700 flex justify-between items-center">
          <h2 className="text-xl font-semibold text-white">لیست کاربران</h2>
          <button
            onClick={loadUsers}
            disabled={loading}
            className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50"
          >
            {loading ? 'در حال بارگذاری...' : 'بروزرسانی'}
          </button>
        </div>

        {loading && users.length === 0 ? (
          <div className="p-8 text-center text-gray-400">در حال بارگذاری...</div>
        ) : users.length === 0 ? (
          <div className="p-8 text-center text-gray-400">کاربری یافت نشد</div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full" dir="rtl">
              <thead className="bg-gray-700">
                <tr>
                  <th className="px-6 py-3 text-right text-xs font-medium text-gray-300 uppercase tracking-wider">
                    کاربر
                  </th>
                  <th className="px-6 py-3 text-right text-xs font-medium text-gray-300 uppercase tracking-wider">
                    شماره تماس
                  </th>
                  <th className="px-6 py-3 text-right text-xs font-medium text-gray-300 uppercase tracking-wider">
                    موجودی
                  </th>
                  <th className="px-6 py-3 text-right text-xs font-medium text-gray-300 uppercase tracking-wider">
                    تاریخ عضویت
                  </th>
                  <th className="px-6 py-3 text-right text-xs font-medium text-gray-300 uppercase tracking-wider">
                    وضعیت
                  </th>
                  <th className="px-6 py-3 text-right text-xs font-medium text-gray-300 uppercase tracking-wider">
                    عملیات
                  </th>
                </tr>
              </thead>
              <tbody className="bg-gray-800 divide-y divide-gray-700">
                {users.map((user) => (
                  <tr key={user.id} className="hover:bg-gray-750">
                    <td className="px-6 py-4 whitespace-nowrap">
                      <div className="text-sm font-medium text-white">{user.username}</div>
                      <div className="text-sm text-gray-400">{user.email}</div>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-300">
                      {user.phone_number || '-'}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <div className="text-sm font-semibold text-green-400">
                        {user.balance_formatted}
                      </div>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-300">
                      {formatDate(user.date_joined)}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      {user.is_superuser ? (
                        <span className="px-2 py-1 text-xs font-medium bg-red-600 text-white rounded">
                          ادمین
                        </span>
                      ) : user.is_staff ? (
                        <span className="px-2 py-1 text-xs font-medium bg-blue-600 text-white rounded">
                          کارمند
                        </span>
                      ) : (
                        <span className="px-2 py-1 text-xs font-medium bg-gray-600 text-white rounded">
                          کاربر
                        </span>
                      )}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm font-medium">
                      <div className="flex items-center gap-3">
                        <button
                          onClick={() => openEditModal(user)}
                          className="text-green-400 hover:text-green-300"
                          title="ویرایش"
                        >
                          ویرایش
                        </button>
                        <button
                          onClick={() => openAllocateModal(user)}
                          className="text-blue-400 hover:text-blue-300"
                          title="تخصیص اعتبار"
                        >
                          تخصیص اعتبار
                        </button>
                        {!user.is_staff && !user.is_superuser && (
                          <button
                            onClick={() => openDeleteModal(user)}
                            className="text-red-400 hover:text-red-300"
                            title="حذف"
                          >
                            حذف
                          </button>
                        )}
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* Allocate Credit Modal */}
      {showAllocateModal && selectedUser && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-gray-800 rounded-lg p-6 max-w-md w-full mx-4">
            <h3 className="text-xl font-bold text-white mb-4">
              تخصیص اعتبار به {selectedUser.username}
            </h3>
            
            <div className="mb-4">
              <label className="block text-sm font-medium text-gray-300 mb-2">
                موجودی فعلی
              </label>
              <div className="text-lg font-semibold text-green-400">
                {selectedUser.balance_formatted}
              </div>
            </div>

            <div className="mb-4">
              <label className="block text-sm font-medium text-gray-300 mb-2">
                مبلغ اعتبار (تومان)
              </label>
              <input
                type="number"
                value={amount}
                onChange={(e) => setAmount(e.target.value)}
                placeholder="مثال: 10000"
                className="w-full px-4 py-2 bg-gray-700 text-white rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                min="0"
                step="0.01"
              />
            </div>

            <div className="mb-4">
              <label className="block text-sm font-medium text-gray-300 mb-2">
                توضیحات (اختیاری)
              </label>
              <textarea
                value={description}
                onChange={(e) => setDescription(e.target.value)}
                placeholder="توضیحات تخصیص اعتبار..."
                rows={3}
                className="w-full px-4 py-2 bg-gray-700 text-white rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
            </div>

            <div className="flex gap-4">
              <button
                onClick={handleAllocateCredit}
                disabled={allocating === selectedUser.id || !amount}
                className="flex-1 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50"
              >
                {allocating === selectedUser.id ? 'در حال تخصیص...' : 'تخصیص اعتبار'}
              </button>
              <button
                onClick={() => {
                  setShowAllocateModal(false)
                  setSelectedUser(null)
                  setAmount('')
                  setDescription('')
                }}
                className="flex-1 px-4 py-2 bg-gray-600 text-white rounded-lg hover:bg-gray-700"
              >
                انصراف
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Delete Confirmation Modal */}
      {showDeleteModal && selectedUser && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-gray-800 rounded-lg p-6 max-w-md w-full mx-4">
            <h3 className="text-xl font-bold text-white mb-4">
              حذف کاربر {selectedUser.username}
            </h3>
            
            <div className="mb-4">
              <p className="text-gray-300">
                آیا مطمئن هستید که می‌خواهید کاربر <span className="font-semibold text-white">{selectedUser.username}</span> را حذف کنید؟
              </p>
              <p className="text-red-400 text-sm mt-2">
                ⚠️ این عمل غیرقابل بازگشت است و تمام اطلاعات کاربر حذف خواهد شد.
              </p>
            </div>

            <div className="flex gap-4">
              <button
                onClick={handleDeleteUser}
                disabled={deleting === selectedUser.id}
                className="flex-1 px-4 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700 disabled:opacity-50"
              >
                {deleting === selectedUser.id ? 'در حال حذف...' : 'حذف'}
              </button>
              <button
                onClick={() => {
                  setShowDeleteModal(false)
                  setSelectedUser(null)
                }}
                className="flex-1 px-4 py-2 bg-gray-600 text-white rounded-lg hover:bg-gray-700"
              >
                انصراف
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Edit User Modal */}
      {showEditModal && selectedUser && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 overflow-y-auto">
          <div className="bg-gray-800 rounded-lg p-6 max-w-2xl w-full mx-4 my-8">
            <h3 className="text-xl font-bold text-white mb-4">
              ویرایش اطلاعات کاربر {selectedUser.username}
            </h3>
            
            <div className="space-y-4">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-300 mb-2">
                    ایمیل
                  </label>
                  <input
                    type="email"
                    value={editForm.email}
                    onChange={(e) => setEditForm({ ...editForm, email: e.target.value })}
                    className="w-full px-4 py-2 bg-gray-700 text-white rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-300 mb-2">
                    شماره موبایل
                  </label>
                  <input
                    type="text"
                    value={editForm.phone_number}
                    onChange={(e) => setEditForm({ ...editForm, phone_number: e.target.value })}
                    placeholder="09123456789"
                    className="w-full px-4 py-2 bg-gray-700 text-white rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-300 mb-2">
                    نام
                  </label>
                  <input
                    type="text"
                    value={editForm.first_name}
                    onChange={(e) => setEditForm({ ...editForm, first_name: e.target.value })}
                    className="w-full px-4 py-2 bg-gray-700 text-white rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-300 mb-2">
                    نام خانوادگی
                  </label>
                  <input
                    type="text"
                    value={editForm.last_name}
                    onChange={(e) => setEditForm({ ...editForm, last_name: e.target.value })}
                    className="w-full px-4 py-2 bg-gray-700 text-white rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-300 mb-2">
                    نیک‌نیم
                  </label>
                  <input
                    type="text"
                    value={editForm.nickname}
                    onChange={(e) => setEditForm({ ...editForm, nickname: e.target.value })}
                    className="w-full px-4 py-2 bg-gray-700 text-white rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                  />
                </div>
              </div>

              {currentUser?.is_superuser && (
                <div className="border-t border-gray-700 pt-4 space-y-3">
                  <div className="flex items-center gap-3">
                    <input
                      type="checkbox"
                      id="is_staff"
                      checked={editForm.is_staff}
                      onChange={(e) => setEditForm({ ...editForm, is_staff: e.target.checked })}
                      className="w-4 h-4 text-blue-600 bg-gray-700 border-gray-600 rounded focus:ring-blue-500"
                    />
                    <label htmlFor="is_staff" className="text-sm font-medium text-gray-300">
                      کارمند (Staff)
                    </label>
                  </div>

                  <div className="flex items-center gap-3">
                    <input
                      type="checkbox"
                      id="is_superuser"
                      checked={editForm.is_superuser}
                      onChange={(e) => setEditForm({ ...editForm, is_superuser: e.target.checked })}
                      disabled={selectedUser.id === currentUser?.id && !editForm.is_superuser}
                      className="w-4 h-4 text-blue-600 bg-gray-700 border-gray-600 rounded focus:ring-blue-500 disabled:opacity-50"
                    />
                    <label htmlFor="is_superuser" className="text-sm font-medium text-gray-300">
                      ادمین اصلی (Superuser)
                    </label>
                  </div>
                  {selectedUser.id === currentUser?.id && !editForm.is_superuser && (
                    <p className="text-xs text-yellow-400">
                      ⚠️ نمی‌توانید دسترسی ادمین اصلی را از خودتان بگیرید
                    </p>
                  )}
                </div>
              )}
            </div>

            <div className="flex gap-4 mt-6">
              <button
                onClick={handleUpdateUser}
                disabled={updating === selectedUser.id}
                className="flex-1 px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 disabled:opacity-50"
              >
                {updating === selectedUser.id ? 'در حال به‌روزرسانی...' : 'ذخیره تغییرات'}
              </button>
              <button
                onClick={() => {
                  setShowEditModal(false)
                  setSelectedUser(null)
                }}
                className="flex-1 px-4 py-2 bg-gray-600 text-white rounded-lg hover:bg-gray-700"
              >
                انصراف
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}

