import client from './client'

export interface AuthResponse {
  success: boolean
  message?: string
  user?: {
    id: number
    username: string
    phone_number: string
    email?: string
    first_name?: string
    last_name?: string
    is_staff?: boolean
    is_superuser?: boolean
  }
  device_id?: string
  authenticated?: boolean
  expires_in?: number
  errors?: any
}

export const sendOTP = async (phoneNumber: string): Promise<AuthResponse> => {
  const response = await client.post<AuthResponse>('/auth/send-otp/', {
    phone_number: phoneNumber,
  })
  return response.data
}

export const verifyOTP = async (phoneNumber: string, otpCode: string): Promise<AuthResponse> => {
  // First, get CSRF token if not already in cookies
  try {
    await client.get('/auth/csrf-token/', { withCredentials: true })
  } catch (error) {
    // Ignore errors, CSRF token might already be set
    console.log('CSRF token fetch:', error)
  }
  
  const response = await client.post<AuthResponse>('/auth/verify-otp/', {
    phone_number: phoneNumber,
    otp_code: otpCode,
  }, {
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

export const googleLogin = async (idToken: string): Promise<AuthResponse> => {
  // First, get CSRF token if not already in cookies
  try {
    await client.get('/auth/csrf-token/', { withCredentials: true })
  } catch (error) {
    // Ignore errors, CSRF token might already be set
    console.log('CSRF token fetch:', error)
  }
  
  const response = await client.post<AuthResponse>('/auth/google/', {
    id_token: idToken,
  }, {
    withCredentials: true, // Important for session cookies
  })
  return response.data
}

export interface ProfileCompletionResponse {
  success: boolean
  is_complete: boolean
  has_valid_email: boolean
  has_valid_phone: boolean
  message?: string
}

export interface UpdateProfileResponse {
  success: boolean
  message?: string
  user?: {
    id: number
    username: string
    phone_number: string
    email?: string
    first_name?: string
    last_name?: string
  }
  errors?: {
    email?: string
    phone_number?: string
  }
}

export const checkProfileCompletion = async (): Promise<ProfileCompletionResponse> => {
  const response = await client.get<ProfileCompletionResponse>('/auth/profile/check/', {
    withCredentials: true,
  })
  return response.data
}

export const updateProfile = async (email?: string, phoneNumber?: string): Promise<UpdateProfileResponse> => {
  const response = await client.post<UpdateProfileResponse>('/auth/profile/update/', {
    email: email || '',
    phone_number: phoneNumber || '',
  }, {
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

export interface GoogleAuthStatusResponse {
  success: boolean
  google_auth_enabled: boolean
  message?: string
}

export const checkGoogleAuthStatus = async (): Promise<GoogleAuthStatusResponse> => {
  const response = await client.get<GoogleAuthStatusResponse>('/auth/google-status/', {
    withCredentials: true,
  })
  return response.data
}

