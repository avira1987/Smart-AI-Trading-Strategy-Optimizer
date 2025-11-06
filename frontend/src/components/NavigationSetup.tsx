import { useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { setNavigate } from '../utils/navigation'

/**
 * Component that sets up navigation for use in axios interceptors
 * This should be rendered inside the Router
 */
export default function NavigationSetup() {
  const navigate = useNavigate()

  useEffect(() => {
    setNavigate((path: string) => {
      navigate(path)
    })
  }, [navigate])

  return null
}

