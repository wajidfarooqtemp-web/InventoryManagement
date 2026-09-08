import { supabase } from './supabaseClient'

const API_URL = import.meta.env.VITE_API_URL

// One shared fetch wrapper: attaches the current session token to every
// request and turns a non-2xx response into a thrown Error with the
// backend's own message, so every page can just try/catch instead of
// re-implementing this each time.
export async function apiFetch(path: string, options: RequestInit = {}) {
  const { data } = await supabase.auth.getSession()
  const token = data.session?.access_token

  const response = await fetch(`${API_URL}${path}`, {
    ...options,
    headers: {
      'Content-Type': 'application/json',
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
      ...options.headers,
    },
  })

  if (!response.ok) {
    const body = await response.json().catch(() => ({}))
    throw new Error(body.detail || `Request failed (${response.status})`)
  }
  return response.json()
}