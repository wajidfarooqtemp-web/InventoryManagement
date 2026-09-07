-- ============================================================================
-- 0004_auth_trigger.sql
-- When an admin creates a login for someone in Supabase Auth, this
-- automatically creates the matching row in public.users, defaulting to the
-- lowest-privilege role. The admin promotes them from the Admin > Users
-- screen afterward (built in Phase 9) - nobody is ever auto-promoted.
-- ============================================================================

create or replace function public.handle_new_auth_user()
returns trigger as $$
begin
  insert into public.users (id, name, email, role, active)
  values (
    new.id,
    coalesce(new.raw_user_meta_data->>'name', split_part(new.email, '@', 1)),
    new.email,
    'kitchen_staff', -- safest possible default
    true
  );
  return new;
end;
$$ language plpgsql security definer;

create trigger on_auth_user_created
  after insert on auth.users
  for each row execute function public.handle_new_auth_user();