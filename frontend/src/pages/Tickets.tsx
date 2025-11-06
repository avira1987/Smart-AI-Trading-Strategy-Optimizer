import { useState, useEffect } from 'react'
import { getTickets, createTicket, addTicketMessage, closeTicket, getTicket, Ticket, TicketMessage } from '../api/tickets'
import { useToast } from '../components/ToastProvider'

const categoryLabels: Record<string, string> = {
  technical: 'مسئله فنی',
  feature: 'درخواست ویژگی',
  bug: 'گزارش باگ',
  question: 'سوال',
  other: 'سایر',
}

const priorityLabels: Record<string, string> = {
  low: 'کم',
  medium: 'متوسط',
  high: 'بالا',
  urgent: 'فوری',
}

const statusLabels: Record<string, string> = {
  open: 'باز',
  in_progress: 'در حال بررسی',
  resolved: 'حل شده',
  closed: 'بسته شده',
}

const priorityColors: Record<string, string> = {
  low: 'bg-blue-500',
  medium: 'bg-yellow-500',
  high: 'bg-orange-500',
  urgent: 'bg-red-500',
}

const statusColors: Record<string, string> = {
  open: 'bg-green-500',
  in_progress: 'bg-blue-500',
  resolved: 'bg-purple-500',
  closed: 'bg-gray-500',
}

export default function Tickets() {
  const [tickets, setTickets] = useState<Ticket[]>([])
  const [selectedTicket, setSelectedTicket] = useState<Ticket | null>(null)
  const [loading, setLoading] = useState(true)
  const [creating, setCreating] = useState(false)
  const [showCreateModal, setShowCreateModal] = useState(false)
  const [filterStatus, setFilterStatus] = useState<string>('')
  const [filterCategory, setFilterCategory] = useState<string>('')
  const [newMessage, setNewMessage] = useState('')
  const [sendingMessage, setSendingMessage] = useState(false)
  const { showToast } = useToast()

  // Form state for creating new ticket
  const [newTicket, setNewTicket] = useState({
    title: '',
    description: '',
    category: 'other' as Ticket['category'],
    priority: 'medium' as Ticket['priority'],
  })

  useEffect(() => {
    loadTickets()
  }, [filterStatus, filterCategory])

  const loadTickets = async () => {
    try {
      setLoading(true)
      const params: any = {}
      if (filterStatus) params.status = filterStatus
      if (filterCategory) params.category = filterCategory
      
      const response = await getTickets(params)
      // Handle both paginated and non-paginated responses
      let ticketsData = []
      if (response.data) {
        if (Array.isArray(response.data)) {
          ticketsData = response.data
        } else if (response.data.results && Array.isArray(response.data.results)) {
          ticketsData = response.data.results
        }
      }
      setTickets(ticketsData)
    } catch (error: any) {
      console.error('Error loading tickets:', error)
      const errorMessage = error.response?.data?.error || error.response?.data?.detail || error.message || 'خطا در بارگذاری تیکت‌ها'
      showToast(errorMessage, { type: 'error' })
      setTickets([])
    } finally {
      setLoading(false)
    }
  }

  const loadTicketDetails = async (id: number) => {
    try {
      const response = await getTicket(id)
      setSelectedTicket(response.data)
    } catch (error: any) {
      console.error('Error loading ticket details:', error)
      showToast('خطا در بارگذاری جزئیات تیکت', { type: 'error' })
    }
  }

  const handleCreateTicket = async (e: React.FormEvent) => {
    e.preventDefault()
    
    if (!newTicket.title.trim() || !newTicket.description.trim()) {
      showToast('لطفاً عنوان و توضیحات را وارد کنید', { type: 'warning' })
      return
    }

    try {
      setCreating(true)
      const response = await createTicket(newTicket)
      showToast('تیکت با موفقیت ایجاد شد', { type: 'success' })
      setShowCreateModal(false)
      setNewTicket({ title: '', description: '', category: 'other', priority: 'medium' })
      await loadTickets()
      setSelectedTicket(response.data)
    } catch (error: any) {
      console.error('Error creating ticket:', error)
      const errorMessage = error.response?.data?.error || error.response?.data?.details || error.message || 'خطا در ایجاد تیکت'
      showToast(errorMessage, { type: 'error' })
      if (error.response?.data?.details) {
        console.error('Error details:', error.response.data.details)
      }
    } finally {
      setCreating(false)
    }
  }

  const handleAddMessage = async () => {
    if (!selectedTicket || !newMessage.trim()) {
      showToast('لطفاً پیام را وارد کنید', { type: 'warning' })
      return
    }

    try {
      setSendingMessage(true)
      await addTicketMessage(selectedTicket.id, newMessage)
      showToast('پیام با موفقیت ارسال شد', { type: 'success' })
      setNewMessage('')
      await loadTicketDetails(selectedTicket.id)
      await loadTickets()
    } catch (error: any) {
      console.error('Error adding message:', error)
      showToast(error.response?.data?.error || 'خطا در ارسال پیام', { type: 'error' })
    } finally {
      setSendingMessage(false)
    }
  }

  const handleCloseTicket = async () => {
    if (!selectedTicket) return
    
    if (!confirm('آیا از بستن این تیکت اطمینان دارید؟')) return

    try {
      await closeTicket(selectedTicket.id)
      showToast('تیکت بسته شد', { type: 'success' })
      await loadTicketDetails(selectedTicket.id)
      await loadTickets()
    } catch (error: any) {
      console.error('Error closing ticket:', error)
      showToast(error.response?.data?.error || 'خطا در بستن تیکت', { type: 'error' })
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
    <div className="min-h-screen bg-gray-900 py-8" dir="rtl" style={{ direction: 'rtl' }}>
      <div className="container mx-auto px-4 max-w-7xl">
        <div className="flex justify-between items-center mb-6">
          <h1 className="text-3xl font-bold text-white">سیستم تیکت</h1>
          <button
            onClick={() => setShowCreateModal(true)}
            className="bg-blue-600 hover:bg-blue-700 text-white px-6 py-2 rounded-lg transition-colors"
          >
            تیکت جدید
          </button>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Tickets List */}
        <div className="lg:col-span-1">
          <div className="bg-gray-800 rounded-lg p-4 mb-4">
            <h2 className="text-xl font-semibold text-white mb-4">فیلترها</h2>
            
            <div className="mb-4">
              <label className="block text-sm text-gray-300 mb-2">وضعیت</label>
              <select
                value={filterStatus}
                onChange={(e) => setFilterStatus(e.target.value)}
                className="w-full bg-gray-700 text-white rounded-lg px-3 py-2"
              >
                <option value="">همه</option>
                <option value="open">باز</option>
                <option value="in_progress">در حال بررسی</option>
                <option value="resolved">حل شده</option>
                <option value="closed">بسته شده</option>
              </select>
            </div>

            <div>
              <label className="block text-sm text-gray-300 mb-2">دسته‌بندی</label>
              <select
                value={filterCategory}
                onChange={(e) => setFilterCategory(e.target.value)}
                className="w-full bg-gray-700 text-white rounded-lg px-3 py-2"
              >
                <option value="">همه</option>
                <option value="technical">مسئله فنی</option>
                <option value="feature">درخواست ویژگی</option>
                <option value="bug">گزارش باگ</option>
                <option value="question">سوال</option>
                <option value="other">سایر</option>
              </select>
            </div>
          </div>

          <div className="bg-gray-800 rounded-lg p-4">
            <h2 className="text-xl font-semibold text-white mb-4">تیکت‌ها ({tickets.length})</h2>
            
            {loading ? (
              <div className="text-center text-gray-400 py-8">در حال بارگذاری...</div>
            ) : tickets.length === 0 ? (
              <div className="text-center text-gray-400 py-8">تیکتی وجود ندارد</div>
            ) : (
              <div className="space-y-2 max-h-[600px] overflow-y-auto">
                {tickets.map((ticket) => (
                  <div
                    key={ticket.id}
                    onClick={() => {
                      setSelectedTicket(ticket)
                      loadTicketDetails(ticket.id)
                    }}
                    className={`p-3 rounded-lg cursor-pointer transition-colors ${
                      selectedTicket?.id === ticket.id
                        ? 'bg-blue-600'
                        : 'bg-gray-700 hover:bg-gray-600'
                    }`}
                  >
                    <div className="flex justify-between items-start mb-2">
                      <h3 className="text-white font-semibold text-sm">{ticket.title}</h3>
                      <span className={`px-2 py-1 rounded text-xs ${priorityColors[ticket.priority]}`}>
                        {priorityLabels[ticket.priority]}
                      </span>
                    </div>
                    <div className="flex justify-between items-center text-xs text-gray-300">
                      <span>{categoryLabels[ticket.category]}</span>
                      <span className={`px-2 py-1 rounded ${statusColors[ticket.status]}`}>
                        {statusLabels[ticket.status]}
                      </span>
                    </div>
                    <div className="text-xs text-gray-400 mt-1">
                      {formatDate(ticket.created_at)}
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>

        {/* Ticket Details */}
        <div className="lg:col-span-2">
          {selectedTicket ? (
            <div className="bg-gray-800 rounded-lg p-6">
              <div className="flex justify-between items-start mb-4">
                <div>
                  <h2 className="text-2xl font-bold text-white mb-2">{selectedTicket.title}</h2>
                  <div className="flex gap-2 mb-2">
                    <span className={`px-3 py-1 rounded text-sm ${priorityColors[selectedTicket.priority]}`}>
                      {priorityLabels[selectedTicket.priority]}
                    </span>
                    <span className={`px-3 py-1 rounded text-sm ${statusColors[selectedTicket.status]}`}>
                      {statusLabels[selectedTicket.status]}
                    </span>
                    <span className="px-3 py-1 rounded text-sm bg-gray-700 text-white">
                      {categoryLabels[selectedTicket.category]}
                    </span>
                  </div>
                  <div className="text-sm text-gray-400">
                    ایجاد شده در: {formatDate(selectedTicket.created_at)}
                  </div>
                </div>
                {selectedTicket.status !== 'closed' && (
                  <button
                    onClick={handleCloseTicket}
                    className="bg-red-600 hover:bg-red-700 text-white px-4 py-2 rounded-lg text-sm"
                  >
                    بستن تیکت
                  </button>
                )}
              </div>

              <div className="bg-gray-700 rounded-lg p-4 mb-4">
                <h3 className="text-white font-semibold mb-2">توضیحات</h3>
                <p className="text-gray-300 whitespace-pre-wrap">{selectedTicket.description}</p>
              </div>

              {selectedTicket.admin_response && (
                <div className="bg-blue-900 bg-opacity-30 rounded-lg p-4 mb-4 border border-blue-500">
                  <h3 className="text-blue-300 font-semibold mb-2">پاسخ ادمین</h3>
                  <p className="text-gray-200 whitespace-pre-wrap">{selectedTicket.admin_response}</p>
                  {selectedTicket.admin_name && (
                    <div className="text-sm text-gray-400 mt-2">
                      توسط: {selectedTicket.admin_name}
                    </div>
                  )}
                </div>
              )}

              {/* Messages */}
              <div className="mb-4">
                <h3 className="text-white font-semibold mb-3">
                  پیام‌ها ({selectedTicket.messages?.length || 0})
                </h3>
                <div className="space-y-3 max-h-64 overflow-y-auto">
                  {selectedTicket.messages && selectedTicket.messages.length > 0 ? (
                    selectedTicket.messages.map((message) => (
                      <div
                        key={message.id}
                        className={`p-3 rounded-lg ${
                          message.is_admin ? 'bg-blue-900 bg-opacity-30' : 'bg-gray-700'
                        }`}
                      >
                        <div className="flex justify-between items-start mb-1">
                          <span className="text-sm font-semibold text-white">
                            {message.is_admin ? 'ادمین' : message.user_name}
                          </span>
                          <span className="text-xs text-gray-400">
                            {formatDate(message.created_at)}
                          </span>
                        </div>
                        <p className="text-gray-300 text-sm whitespace-pre-wrap">{message.message}</p>
                      </div>
                    ))
                  ) : (
                    <div className="text-center text-gray-400 py-4">پیامی وجود ندارد</div>
                  )}
                </div>
              </div>

              {/* Add Message */}
              {selectedTicket.status !== 'closed' && (
                <div className="border-t border-gray-700 pt-4">
                  <h3 className="text-white font-semibold mb-2">ارسال پیام</h3>
                  <textarea
                    value={newMessage}
                    onChange={(e) => setNewMessage(e.target.value)}
                    placeholder="پیام خود را بنویسید..."
                    className="w-full bg-gray-700 text-white rounded-lg px-3 py-2 mb-2 min-h-[100px]"
                    rows={4}
                  />
                  <button
                    onClick={handleAddMessage}
                    disabled={sendingMessage || !newMessage.trim()}
                    className="bg-green-600 hover:bg-green-700 disabled:bg-gray-600 disabled:cursor-not-allowed text-white px-6 py-2 rounded-lg transition-colors"
                  >
                    {sendingMessage ? 'در حال ارسال...' : 'ارسال پیام'}
                  </button>
                </div>
              )}
            </div>
          ) : (
            <div className="bg-gray-800 rounded-lg p-12 text-center">
              <p className="text-gray-400">تیکتی انتخاب نشده است</p>
            </div>
          )}
        </div>
        </div>
      </div>

      {/* Create Ticket Modal */}
      {showCreateModal && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50" dir="rtl" style={{ direction: 'rtl' }}>
          <div className="bg-gray-800 rounded-lg p-6 w-full max-w-2xl mx-4">
            <h2 className="text-2xl font-bold text-white mb-4">ایجاد تیکت جدید</h2>
            <form onSubmit={handleCreateTicket}>
              <div className="mb-4">
                <label className="block text-sm text-gray-300 mb-2">عنوان</label>
                <input
                  type="text"
                  value={newTicket.title}
                  onChange={(e) => setNewTicket({ ...newTicket, title: e.target.value })}
                  className="w-full bg-gray-700 text-white rounded-lg px-3 py-2"
                  required
                />
              </div>

              <div className="mb-4">
                <label className="block text-sm text-gray-300 mb-2">توضیحات</label>
                <textarea
                  value={newTicket.description}
                  onChange={(e) => setNewTicket({ ...newTicket, description: e.target.value })}
                  className="w-full bg-gray-700 text-white rounded-lg px-3 py-2 min-h-[150px]"
                  required
                />
              </div>

              <div className="grid grid-cols-2 gap-4 mb-4">
                <div>
                  <label className="block text-sm text-gray-300 mb-2">دسته‌بندی</label>
                  <select
                    value={newTicket.category}
                    onChange={(e) => setNewTicket({ ...newTicket, category: e.target.value as Ticket['category'] })}
                    className="w-full bg-gray-700 text-white rounded-lg px-3 py-2"
                  >
                    <option value="technical">مسئله فنی</option>
                    <option value="feature">درخواست ویژگی</option>
                    <option value="bug">گزارش باگ</option>
                    <option value="question">سوال</option>
                    <option value="other">سایر</option>
                  </select>
                </div>

                <div>
                  <label className="block text-sm text-gray-300 mb-2">اولویت</label>
                  <select
                    value={newTicket.priority}
                    onChange={(e) => setNewTicket({ ...newTicket, priority: e.target.value as Ticket['priority'] })}
                    className="w-full bg-gray-700 text-white rounded-lg px-3 py-2"
                  >
                    <option value="low">کم</option>
                    <option value="medium">متوسط</option>
                    <option value="high">بالا</option>
                    <option value="urgent">فوری</option>
                  </select>
                </div>
              </div>

              <div className="flex justify-end gap-3">
                <button
                  type="button"
                  onClick={() => {
                    setShowCreateModal(false)
                    setNewTicket({ title: '', description: '', category: 'other', priority: 'medium' })
                  }}
                  className="bg-gray-600 hover:bg-gray-700 text-white px-6 py-2 rounded-lg transition-colors"
                >
                  انصراف
                </button>
                <button
                  type="submit"
                  disabled={creating}
                  className="bg-blue-600 hover:bg-blue-700 disabled:bg-gray-600 disabled:cursor-not-allowed text-white px-6 py-2 rounded-lg transition-colors"
                >
                  {creating ? 'در حال ایجاد...' : 'ایجاد تیکت'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  )
}

