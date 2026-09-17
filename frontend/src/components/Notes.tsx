import { useEffect, useState } from 'react'
import { apiFetch } from '../lib/apiClient'
import { useAuth } from '../contexts/AuthContext'

type Note = {
  id: string
  content: string
  created_by: string
  created_by_name: string
  created_at: string
  updated_at: string
}

export function Notes() {
  const { profile } = useAuth()
  const [notes, setNotes] = useState<Note[]>([])
  const [draft, setDraft] = useState('')
  const [editingId, setEditingId] = useState<string | null>(null)
  const [editValue, setEditValue] = useState('')
  const [submitting, setSubmitting] = useState(false)
  const [error, setError] = useState<string | null>(null)

  function load() {
    apiFetch('/api/v1/notes?limit=20').then(setNotes).catch(() => setError('Could not load notes.'))
  }
  useEffect(load, [])

  async function post() {
    if (!draft.trim() || submitting) return
    setSubmitting(true)
    try {
      await apiFetch('/api/v1/notes', { method: 'POST', body: JSON.stringify({ content: draft.trim() }) })
      setDraft('')
      setError(null)
      load()
    } catch {
      setError('Could not post that note. Please try again.')
    } finally {
      setSubmitting(false)
    }
  }

  async function saveEdit(note: Note) {
    if (!editValue.trim() || editValue.trim() === note.content) {
      setEditingId(null)
      return
    }
    try {
      await apiFetch(`/api/v1/notes/${note.id}`, { method: 'PATCH', body: JSON.stringify({ content: editValue.trim() }) })
      setEditingId(null)
      load()
    } catch {
      setError('Could not save that change.')
    }
  }

  async function remove(note: Note) {
    if (!confirm('Delete this note?')) return
    try {
      await apiFetch(`/api/v1/notes/${note.id}`, { method: 'DELETE' })
      load()
    } catch {
      setError('Could not delete that note.')
    }
  }

  // Matches the backend rule exactly - shown here only so people aren't
  // offered buttons that would fail; the backend is what enforces it.
  function canModify(note: Note) {
    return note.created_by === profile?.id || profile?.role === 'admin'
  }

  return (
    <section>
      <h2 className="font-heading text-lg mb-3">Notes</h2>

      <div className="bg-white/60 border border-cream-dark rounded-lg p-4">
        <textarea
          value={draft} onChange={(e) => setDraft(e.target.value)}
          placeholder="Share something the team should know…"
          rows={2}
          className="w-full border border-cream-dark rounded px-3 py-2 bg-white text-sm resize-none focus:outline-none focus:ring-2 focus:ring-accent"
        />
        <div className="flex justify-between items-center mt-2">
          {error && <span className="text-status-critical text-xs">{error}</span>}
          <button
            onClick={post} disabled={submitting || !draft.trim()}
            className="ml-auto bg-accent text-white rounded px-4 py-1.5 text-sm disabled:opacity-40"
          >
            {submitting ? 'Posting…' : 'Post note'}
          </button>
        </div>

        {notes.length > 0 && (
          <div className="divide-y divide-cream-dark mt-4 border-t border-cream-dark">
            {notes.map((note) => (
              <div key={note.id} className="py-3">
                {editingId === note.id ? (
                  <div>
                    <textarea
                      autoFocus value={editValue} onChange={(e) => setEditValue(e.target.value)} rows={2}
                      className="w-full border border-cream-dark rounded px-3 py-2 bg-white text-sm resize-none"
                    />
                    <div className="flex gap-3 text-sm mt-1">
                      <button onClick={() => saveEdit(note)} className="text-accent font-medium">Save</button>
                      <button onClick={() => setEditingId(null)} className="text-ink-soft">Cancel</button>
                    </div>
                  </div>
                ) : (
                  <div className="flex justify-between items-start gap-3">
                    {/* Rendered as plain text by React, never as HTML -
                        user-written content is never trusted as markup. */}
                    <p className="text-sm whitespace-pre-wrap flex-1">{note.content}</p>
                    {canModify(note) && (
                      <span className="flex gap-2 text-xs shrink-0">
                        <button onClick={() => { setEditingId(note.id); setEditValue(note.content) }} className="text-accent">Edit</button>
                        <button onClick={() => remove(note)} className="text-status-critical">Delete</button>
                      </span>
                    )}
                  </div>
                )}
                <p className="text-xs text-ink-soft mt-1">
                  {note.created_by_name} · {new Date(note.created_at).toLocaleString()}
                  {note.updated_at !== note.created_at && ' · edited'}
                </p>
              </div>
            ))}
          </div>
        )}
      </div>
    </section>
  )
}