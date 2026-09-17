-- ============================================================================
-- 0010_notes.sql
-- A general noticeboard, not tied to any item. Unlike stock_movements
-- (permanently immutable), notes CAN be edited and deleted by their
-- author or an admin, since a noticeboard where you can't fix a typo or
-- clear an outdated notice would be more annoying than useful.
-- Deletions are still recorded in audit_log.
-- ============================================================================

create table public.notes (
  id uuid primary key default gen_random_uuid(),
  content text not null,
  created_by uuid not null references public.users(id),
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

create index idx_notes_created_at on public.notes(created_at desc);

create trigger trg_notes_updated_at
  before update on public.notes
  for each row execute function set_updated_at();

alter table public.notes enable row level security;

-- Everyone logged in reads and writes notes - that's the point of a
-- shared noticeboard. Edit/delete authorization (author or admin only)
-- is enforced in FastAPI, same as everywhere else in this app.
create policy notes_select on public.notes for select
  using (auth.uid() is not null);
create policy notes_insert on public.notes for insert
  with check (auth.uid() is not null);
create policy notes_update on public.notes for update
  using (auth.uid() is not null);
create policy notes_delete on public.notes for delete
  using (auth.uid() is not null);