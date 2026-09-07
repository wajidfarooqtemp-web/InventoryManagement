-- ============================================================================
-- 0005_rls_policies.sql
-- Row Level Security on every table. This is DEFENSE IN DEPTH: the real
-- authorization logic lives in FastAPI (Phase 2+), but these policies mean
-- that even a direct Supabase connection (bypassing our API) can't do
-- anything a user's role shouldn't allow.
-- ============================================================================

alter table public.users enable row level security;
alter table public.locations enable row level security;
alter table public.categories enable row level security;
alter table public.inventory_items enable row level security;
alter table public.inventory_periods enable row level security;
alter table public.stock_movements enable row level security;
alter table public.audit_log enable row level security;
alter table public.purchase_list_entries enable row level security;

-- Helper function: what role does the currently-authenticated user have?
-- SECURITY DEFINER lets it read public.users regardless of the calling
-- user's own row-level permissions on that table.
create or replace function public.current_user_role()
returns user_role as $$
  select role from public.users where id = auth.uid();
$$ language sql stable security definer;

-- ---- users ----
-- Anyone logged in can see basic user info (needed to show "used by Priya").
-- Only admins can change roles / active status.
create policy users_select on public.users for select
  using (auth.uid() is not null);
create policy users_admin_write on public.users for update
  using (public.current_user_role() = 'admin');

-- ---- locations / categories ----
-- Everyone reads; only manager/admin write.
create policy locations_select on public.locations for select
  using (auth.uid() is not null);
create policy locations_write on public.locations for all
  using (public.current_user_role() in ('manager', 'admin'))
  with check (public.current_user_role() in ('manager', 'admin'));

create policy categories_select on public.categories for select
  using (auth.uid() is not null);
create policy categories_write on public.categories for all
  using (public.current_user_role() in ('manager', 'admin'))
  with check (public.current_user_role() in ('manager', 'admin'));

-- ---- inventory_items ----
-- Everyone reads (kitchen staff must see the item to record usage).
-- Only manager/admin create or edit items / thresholds.
create policy items_select on public.inventory_items for select
  using (auth.uid() is not null);
create policy items_insert on public.inventory_items for insert
  with check (public.current_user_role() in ('manager', 'admin'));
create policy items_update on public.inventory_items for update
  using (public.current_user_role() in ('manager', 'admin'));

-- ---- inventory_periods ----
-- Everyone reads; periods are only ever created by the backend job (Phase 5).
create policy periods_select on public.inventory_periods for select
  using (auth.uid() is not null);

-- ---- stock_movements ----
-- Everyone reads and inserts (recording Use/Received is core kitchen work).
-- On purpose: there is NO update or delete policy here at all. Nobody,
-- not even an admin, can modify or remove a movement through the API -
-- corrections are new rows (see architecture doc, "Corrections").
create policy movements_select on public.stock_movements for select
  using (auth.uid() is not null);
create policy movements_insert on public.stock_movements for insert
  with check (auth.uid() is not null);

-- ---- audit_log ----
-- Readable by manager/admin only. Insert-only, same reasoning as movements.
create policy audit_select on public.audit_log for select
  using (public.current_user_role() in ('manager', 'admin'));
create policy audit_insert on public.audit_log for insert
  with check (auth.uid() is not null);

-- ---- purchase_list_entries ----
create policy purchase_select on public.purchase_list_entries for select
  using (auth.uid() is not null);
create policy purchase_write on public.purchase_list_entries for all
  using (public.current_user_role() in ('manager', 'admin'))
  with check (public.current_user_role() in ('manager', 'admin'));