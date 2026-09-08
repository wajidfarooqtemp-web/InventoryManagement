import { useState, FormEvent } from 'react'
import { useNavigate } from 'react-router-dom'
import { useAuth } from '../contexts/AuthContext'
import { ChinarMark } from '../components/ChinarMark'

export function Login() {
  const { signIn } = useAuth()
  const navigate = useNavigate()
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState<string | null>(null)
  const [submitting, setSubmitting] = useState(false)

  async function handleSubmit(e: FormEvent) {
    e.preventDefault()
    setError(null)
    setSubmitting(true)
    try {
      await signIn(email, password)
      navigate('/')
    } catch {
      // Deliberately generic - never surface raw backend/Supabase error text (Section 38).
      setError('Could not sign in. Check your email and password and try again.')
    } finally {
      setSubmitting(false)
    }
  }

  return (
    <div className="min-h-screen bg-cream flex items-center justify-center px-4">
      <div className="w-full max-w-sm">
        <div className="flex flex-col items-center mb-8">
          <ChinarMark className="w-10 h-10 text-accent mb-2" />
          <h1 className="font-heading text-2xl text-ink">Inventory</h1>
        </div>

        <form onSubmit={handleSubmit} className="bg-white/60 border border-cream-dark rounded-lg p-6 space-y-4">
          <div>
            <label className="block text-sm text-ink-soft mb-1">Email</label>
            <input
              type="email" required value={email}
              onChange={(e) => setEmail(e.target.value)}
              className="w-full border border-cream-dark rounded px-3 py-2 bg-white focus:outline-none focus:ring-2 focus:ring-accent"
            />
          </div>
          <div>
            <label className="block text-sm text-ink-soft mb-1">Password</label>
            <input
              type="password" required value={password}
              onChange={(e) => setPassword(e.target.value)}
              className="w-full border border-cream-dark rounded px-3 py-2 bg-white focus:outline-none focus:ring-2 focus:ring-accent"
            />
          </div>
          {error && <p className="text-sm text-status-critical">{error}</p>}
          <button
            type="submit" disabled={submitting}
            className="w-full bg-accent text-white rounded py-2 font-medium disabled:opacity-50"
          >
            {submitting ? 'Signing in…' : 'Sign in'}
          </button>
        </form>
      </div>
    </div>
  )
}