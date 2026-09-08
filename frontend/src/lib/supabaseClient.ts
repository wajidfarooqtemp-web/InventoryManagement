import { createClient } from '@supabase/supabase-js'

// Used ONLY for authentication (login, logout, session refresh). All
// actual inventory data reads/writes go through our FastAPI backend
// (see apiClient.ts) - Supabase never sees inventory data directly
// from the browser.
const supabaseUrl = import.meta.env.VITE_SUPABASE_URL
const supabaseAnonKey = import.meta.env.VITE_SUPABASE_ANON_KEY

export const supabase = createClient(supabaseUrl, supabaseAnonKey)