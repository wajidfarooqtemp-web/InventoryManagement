-- ============================================================================
-- 0002_inventory_and_movements.sql
-- The heart of the system: the item master table, the monthly period concept,
-- and the immutable stock movement log that current_stock is always derived
-- from and kept in sync with.
-- ============================================================================

create type movement_type as enum (
  'OPENING_BALANCE', 'RECEIVE', 'USE', 'ADJUSTMENT', 'TRANSFER_IN', 'TRANSFER_OUT'
);
create type period_status as enum ('open', 'closed');

-- inventory_items: the master record for one item at one location.
-- current_stock is a CACHE column - it is only ever changed by the backend,
-- in the same transaction as a stock_movements insert. Nothing else may
-- write to it directly (enforced in application code in Phase 4, and by
-- RLS/grants as a second layer in 0005).
create table public.inventory_items (
  id uuid primary key default gen_random_uuid(),
  name text not null,
  location_id uuid not null references public.locations(id),
  category_id uuid not null references public.categories(id),
  image_path text, -- Supabase Storage path, set in Phase 10

  unit text not null, -- kg, litre, box, piece, bag, bottle, dozen, cylinder, etc.

  -- Preserves "10kg bag x 2 bags" style data without collapsing it into one number.
  package_size numeric,
  package_unit text,
  package_count numeric,

  -- The REQUIREMENT is not the same as current stock (Section 50 of the plan).
  monthly_requirement numeric,       -- single fixed value, when known
  monthly_requirement_min numeric,   -- for ranges like Milkmaid's 3-5
  monthly_requirement_max numeric,
  requirement_is_estimate boolean not null default false,

  current_stock numeric not null default 0, -- cache, see comment above

  minimum_stock numeric,
  reorder_level numeric,   -- crossing this => status LOW
  critical_level numeric,  -- crossing this => status CRITICAL

  active boolean not null default true,       -- soft delete, never hard delete
  needs_confirmation boolean not null default false, -- flagged incomplete data
  confirmation_note text,  -- WHY it needs confirmation, shown on the admin screen
  notes text,

  created_by uuid references public.users(id),
  updated_by uuid references public.users(id),
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),

  -- Stops the same item name being accidentally created twice at one location.
  constraint uq_item_name_location unique (name, location_id)
);
create trigger trg_items_updated_at
  before update on public.inventory_items
  for each row execute function set_updated_at();

-- inventory_periods: one row per calendar month, e.g. September 2026.
-- Created lazily by the backend (Phase 5) - never manually, never overwritten.
create table public.inventory_periods (
  id uuid primary key default gen_random_uuid(),
  year int not null,
  month int not null check (month between 1 and 12),
  status period_status not null default 'open',
  opened_at timestamptz not null default now(),
  closed_at timestamptz,
  constraint uq_period_year_month unique (year, month)
);

-- stock_movements: the append-only source of truth for every stock change.
-- current_stock on inventory_items must always match what these rows imply.
create table public.stock_movements (
  id uuid primary key default gen_random_uuid(),
  item_id uuid not null references public.inventory_items(id),
  period_id uuid not null references public.inventory_periods(id),
  movement_type movement_type not null,
  quantity numeric not null check (quantity >= 0), -- always positive; direction comes from movement_type
  resulting_stock numeric not null, -- current_stock immediately after this row - makes history self-checking
  reason text, -- required by application code for ADJUSTMENT
  related_transfer_id uuid references public.stock_movements(id), -- links TRANSFER_OUT <-> TRANSFER_IN
  idempotency_key text not null, -- see Phase 4: stops accidental duplicate submissions
  created_by uuid not null references public.users(id),
  created_at timestamptz not null default now(),

  constraint uq_item_idempotency unique (item_id, idempotency_key)
);
create index idx_movements_item on public.stock_movements(item_id);
create index idx_movements_period on public.stock_movements(period_id);