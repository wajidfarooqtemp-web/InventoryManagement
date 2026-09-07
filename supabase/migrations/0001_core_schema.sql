-- ============================================================================
-- 0001_core_schema.sql
-- Sets up: extensions, the reusable "updated_at" trigger, and the three
-- foundational tables (users, locations, categories) that everything else
-- references.
-- ============================================================================

-- gen_random_uuid() needs this extension
create extension if not exists "pgcrypto";

-- Every user has exactly one of these three roles. Adding a new role later
-- means a migration (ALTER TYPE), so keep this list intentional.
create type user_role as enum ('kitchen_staff', 'manager', 'admin');

-- Reusable function: any table with an "updated_at" column can attach this
-- as a trigger so we never have to remember to set it manually in app code.
create or replace function set_updated_at()
returns trigger as $$
begin
  new.updated_at = now();
  return new;
end;
$$ language plpgsql;

-- users mirrors auth.users (Supabase's built-in auth table) but adds the
-- app-specific fields we actually need: role and active/inactive.
-- The id is the SAME id as auth.users.id, not a separate identity.
create table public.users (
  id uuid primary key references auth.users(id) on delete cascade,
  name text not null,
  email text not null unique,
  role user_role not null default 'kitchen_staff',
  active boolean not null default true, -- admin can disable access instantly
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);
create trigger trg_users_updated_at
  before update on public.users
  for each row execute function set_updated_at();

-- locations: G3, Store, F3 (seeded in the seed file, not here — this file
-- only defines structure).
create table public.locations (
  id uuid primary key default gen_random_uuid(),
  name text not null unique,
  active boolean not null default true,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);
create trigger trg_locations_updated_at
  before update on public.locations
  for each row execute function set_updated_at();

-- categories: Food, Spices, Dairy, Cooking Oil, Cleaning, Kitchen Supplies,
-- Gas, Room Supplies.
create table public.categories (
  id uuid primary key default gen_random_uuid(),
  name text not null unique,
  active boolean not null default true,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);
create trigger trg_categories_updated_at
  before update on public.categories
  for each row execute function set_updated_at();