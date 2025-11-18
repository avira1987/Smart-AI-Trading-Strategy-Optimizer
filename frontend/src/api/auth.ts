import client, { type GoldAPIAccessInfo } from './client'

export interface AuthResponse {
  success: boolean
  message?: string
  user?: {
    id: number
    username: string
    phone_number: string
    nickname?: string
    email?: string
    first_name?: string
    last_name?: string
    is_staff?: boolean
    is_superuser?: boolean
    gold_api_access?: GoldAPIAccessInfo
  }
  device_id?: string
  authenticated?: boolean
  expires_in?: number
  errors?: any
}

export const sendOTP = async (phoneNumber: string, captchaData?: any): Promise<AuthResponse> => {
  const payload: any = {
    phone_number: phoneNumber,
  }
  
  // Add CAPTCHA data if provided
  if (captchaData) {
    Object.assign(payload, captchaData)
  }
  
  const response = await client.post<AuthResponse>('/auth/send-otp/', payload)
  return response.data
}

export const verifyOTP = async (phoneNumber: string, otpCode: string, captchaData?: any): Promise<AuthResponse> => {
  // First, get CSRF token if not already in cookies
  try {
    await client.get('/auth/csrf-token/', { withCredentials: true })
  } catch (error) {
    // Ignore errors, CSRF token might already be set
    console.log('CSRF token fetch:', error)
  }
  
  const payload: any = {
    phone_number: phoneNumber,
    otp_code: otpCode,
  }
  
  // Add CAPTCHA data if provided
  if (captchaData) {
    Object.assign(payload, captchaData)
  }
  
  const response = await client.post<AuthResponse>('/auth/verify-otp/', payload, {
    withCredentials: true, // Important for session cookies
  })
  return response.data
}

export const checkAuth = async (): Promise<AuthResponse> => {
  const response = await client.get<AuthResponse>('/auth/check/', {
    withCredentials: true,
  })
  return response.data
}

export const logout = async (): Promise<AuthResponse> => {
  const response = await client.post<AuthResponse>('/auth/logout/', {}, {
    withCredentials: true,
  })
  return response.data
}

export interface ProfileCompletionResponse {
  success: boolean
  is_complete: boolean
  has_valid_email: boolean
  has_valid_phone: boolean
  preferred_symbol?: string
  message?: string
}

export interface UpdateProfileResponse {
  success: boolean
  message?: string
  user?: {
    id: number
    username: string
    phone_number: string
    nickname?: string
    email?: string
    first_name?: string
    last_name?: string
    gold_api_access?: GoldAPIAccessInfo
  }
  errors?: {
    email?: string
    phone_number?: string
    nickname?: string
  }
}

export const checkProfileCompletion = async (): Promise<ProfileCompletionResponse> => {
  const response = await client.get<ProfileCompletionResponse>('/auth/profile/check/', {
    withCredentials: true,
  })
  return response.data
}

export const updateProfile = async (email?: string, phoneNumber?: string, preferredSymbol?: string, nickname?: string): Promise<UpdateProfileResponse> => {
  const payload: any = {}
  if (email !== undefined) payload.email = email || ''
  if (phoneNumber !== undefined) payload.phone_number = phoneNumber || ''
  if (preferredSymbol !== undefined) payload.preferred_symbol = preferredSymbol || ''
  if (nickname !== undefined) payload.nickname = nickname || ''
  
  const response = await client.post<UpdateProfileResponse>('/auth/profile/update/', payload, {
    withCredentials: true,
  })
  return response.data
}

export interface IPLocationResponse {
  success: boolean
  is_iran?: boolean
  country_code?: string
  country_name?: string
  ip?: string
  message?: string
  error?: string
}

export const checkIPLocation = async (): Promise<IPLocationResponse> => {
  const response = await client.get<IPLocationResponse>('/auth/check-ip/', {
    withCredentials: true,
  })
  return response.data
}

