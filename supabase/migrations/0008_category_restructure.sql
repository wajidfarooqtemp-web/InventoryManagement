-- ============================================================================
-- 0008_category_restructure.sql
-- Requested by leadership: collapse the food sub-categories into one, and
-- shift focus toward furnishings/furniture/decor/heritage - which better
-- reflects what this business actually deals in.
--
-- Items are REASSIGNED, never deleted. Old categories are deactivated,
-- not dropped, so nothing in existing audit_log history becomes confusing.
-- ============================================================================
do $$
declare
  food_kitchen_id uuid;
  furnishings_id uuid;
begin
  insert into public.categories (name) values ('Food & Kitchen')
    on conflict (name) do nothing;
  select id into food_kitchen_id from public.categories where name = 'Food & Kitchen';

  update public.inventory_items set category_id = food_kitchen_id
  where category_id in (select id from public.categories where name in ('Food', 'Spices', 'Dairy', 'Cooking Oil'));

  update public.categories set active = false
  where name in ('Food', 'Spices', 'Dairy', 'Cooking Oil');

  insert into public.categories (name) values
    ('Furniture'), ('Furnishings'), ('Decor'), ('Heritage Items')
    on conflict (name) do nothing;
  select id into furnishings_id from public.categories where name = 'Furnishings';

  -- F3's bed sheets/pillows/covers fit "Furnishings" better than the old
  -- generic "Room Supplies" bucket.
  update public.inventory_items set category_id = furnishings_id
  where category_id in (select id from public.categories where name = 'Room Supplies');

  update public.categories set active = false where name = 'Room Supplies';
end $$;