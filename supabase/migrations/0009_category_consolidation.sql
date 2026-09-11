-- ============================================================================
-- 0009_category_consolidation.sql
-- Reduces the active category set to exactly 4, per leadership direction:
-- Food & Kitchen, Furniture & Furnishings, Decor, Heritage Items.
-- Items are reassigned, old categories deactivated (not deleted) so
-- existing audit_log history stays legible.
-- ============================================================================
do $$
declare
  food_kitchen_id uuid;
  furniture_furnishings_id uuid;
  old_furniture_id uuid;
  old_furnishings_id uuid;
begin
  select id into food_kitchen_id from public.categories where name = 'Food & Kitchen';

  -- Fold the remaining operational categories into Food & Kitchen too,
  -- so the total lands at exactly 4 rather than leaving orphans.
  update public.inventory_items set category_id = food_kitchen_id
  where category_id in (select id from public.categories where name in ('Kitchen Supplies', 'Cleaning', 'Gas'));

  update public.categories set active = false where name in ('Kitchen Supplies', 'Cleaning', 'Gas');

  -- Merge Furniture + Furnishings into one category.
  insert into public.categories (name) values ('Furniture & Furnishings')
    on conflict (name) do nothing;
  select id into furniture_furnishings_id from public.categories where name = 'Furniture & Furnishings';
  select id into old_furniture_id from public.categories where name = 'Furniture';
  select id into old_furnishings_id from public.categories where name = 'Furnishings';

  update public.inventory_items set category_id = furniture_furnishings_id
  where category_id in (old_furniture_id, old_furnishings_id);

  update public.categories set active = false where id in (old_furniture_id, old_furnishings_id);
end $$;