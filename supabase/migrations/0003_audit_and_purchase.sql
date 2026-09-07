-- ============================================================================
-- 0003_audit_and_purchase.sql
-- Structural audit trail (non-stock changes) and the purchase workflow table.
-- ============================================================================

create type purchase_status as enum (
  'needs_purchase', 'ordered', 'partially_received', 'received'
);

-- audit_log: covers everything stock_movements doesn't - item edits, role
-- changes, deactivations, threshold changes. Append-only, same as movements.
create table public.audit_log (
  id uuid primary key default gen_random_uuid(),
  actor_id uuid references public.users(id),
  action text not null,        -- e.g. 'item_created', 'role_changed'
  entity_type text not null,   -- e.g. 'inventory_item', 'user'
  entity_id uuid not null,
  before jsonb,                -- state before the change, for traceability
  after jsonb,                 -- state after the change
  created_at timestamptz not null default now()
);
create index idx_audit_entity on public.audit_log(entity_type, entity_id);

-- purchase_list_entries: tracks the human workflow ("ordered", "received")
-- on top of the deterministic "is this item low" calculation, since ordering
-- status is a real-world action, not something derivable from stock alone.
create table public.purchase_list_entries (
  id uuid primary key default gen_random_uuid(),
  item_id uuid not null references public.inventory_items(id),
  status purchase_status not null default 'needs_purchase',
  quantity_ordered numeric,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  updated_by uuid references public.users(id)
);
create trigger trg_purchase_updated_at
  before update on public.purchase_list_entries
  for each row execute function set_updated_at();