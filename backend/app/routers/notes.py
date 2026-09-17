"""
A shared noticeboard, not tied to any inventory item. Anyone logged in
can post and read; only the note's own author (or an admin) can edit or
delete it - enforced here in FastAPI rather than in RLS, consistent with
how every other permission in this app works.
"""
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, Query
from app.database import get_pool
from app.security import get_current_user, CurrentUser
from app.schemas import NoteOut, NoteCreate, NoteUpdate
from app.audit import record_audit

router = APIRouter(prefix="/api/v1/notes", tags=["notes"])

_SELECT = """
    select n.id, n.content, n.created_by, u.name as created_by_name,
           n.created_at, n.updated_at
    from public.notes n
    join public.users u on u.id = n.created_by
"""


async def _load_or_404(conn, note_id: UUID):
    row = await conn.fetchrow(f"{_SELECT} where n.id = $1", note_id)
    if row is None:
        raise HTTPException(status_code=404, detail="Note not found.")
    return row


def _require_author_or_admin(note, user: CurrentUser):
    if str(note["created_by"]) != user.id and user.role != "admin":
        raise HTTPException(status_code=403, detail="You can only change your own notes.")


@router.get("", response_model=list[NoteOut])
async def list_notes(
    limit: int = Query(default=50, le=200),
    offset: int = 0,
    user: CurrentUser = Depends(get_current_user),
):
    pool = get_pool()
    rows = await pool.fetch(f"{_SELECT} order by n.created_at desc limit $1 offset $2", limit, offset)
    return [dict(r) for r in rows]


@router.post("", response_model=NoteOut, status_code=201)
async def create_note(body: NoteCreate, user: CurrentUser = Depends(get_current_user)):
    pool = get_pool()
    async with pool.acquire() as conn, conn.transaction():
        row = await conn.fetchrow(
            "insert into public.notes (content, created_by) values ($1, $2) returning id",
            body.content, user.id,
        )
        created = await _load_or_404(conn, row["id"])
    return dict(created)


@router.patch("/{note_id}", response_model=NoteOut)
async def update_note(note_id: UUID, body: NoteUpdate, user: CurrentUser = Depends(get_current_user)):
    pool = get_pool()
    async with pool.acquire() as conn, conn.transaction():
        before = await _load_or_404(conn, note_id)
        _require_author_or_admin(before, user)

        await conn.execute("update public.notes set content = $2 where id = $1", note_id, body.content)
        after = await _load_or_404(conn, note_id)
    return dict(after)


@router.delete("/{note_id}", status_code=204)
async def delete_note(note_id: UUID, user: CurrentUser = Depends(get_current_user)):
    pool = get_pool()
    async with pool.acquire() as conn, conn.transaction():
        before = await _load_or_404(conn, note_id)
        _require_author_or_admin(before, user)

        await conn.execute("delete from public.notes where id = $1", note_id)
        # The note itself is gone, but the fact it existed and who removed
        # it stays permanently recorded.
        await record_audit(conn, user.id, "note_deleted", "note", str(note_id), dict(before), None)