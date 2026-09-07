-- ============================================================================
-- seed_real_inventory.sql
-- Seeds the THREE real locations, EIGHT categories, and every real inventory
-- item you supplied, with real monthly-requirement figures. Run this ONCE,
-- after all migrations. Safe to re-run: it checks for existing rows by
-- name first, so it won't create duplicates.
--
-- ASSUMPTION FLAGGED: your original list groups items under "G3 / Store"
-- without saying which item belongs to which. Everything below is seeded
-- under "Store" for now - move individual items to "G3" later from the
-- admin edit screen once you know the real split. This is a starting
-- point, not an invented fact about your actual quantities.
-- ============================================================================

insert into public.locations (name) values ('G3'), ('Store'), ('F3')
  on conflict (name) do nothing;

insert into public.categories (name) values
  ('Food'), ('Spices'), ('Dairy'), ('Cooking Oil'),
  ('Cleaning'), ('Kitchen Supplies'), ('Gas'), ('Room Supplies')
  on conflict (name) do nothing;

do $$
declare
  store_id uuid; g3_id uuid; f3_id uuid;
  cat_food uuid; cat_spices uuid; cat_dairy uuid; cat_oil uuid;
  cat_cleaning uuid; cat_kitchen uuid; cat_gas uuid; cat_room uuid;
begin
  select id into store_id from public.locations where name = 'Store';
  select id into g3_id    from public.locations where name = 'G3';
  select id into f3_id    from public.locations where name = 'F3';
  select id into cat_food     from public.categories where name = 'Food';
  select id into cat_spices   from public.categories where name = 'Spices';
  select id into cat_dairy    from public.categories where name = 'Dairy';
  select id into cat_oil      from public.categories where name = 'Cooking Oil';
  select id into cat_cleaning from public.categories where name = 'Cleaning';
  select id into cat_kitchen  from public.categories where name = 'Kitchen Supplies';
  select id into cat_gas      from public.categories where name = 'Gas';
  select id into cat_room     from public.categories where name = 'Room Supplies';

  insert into public.inventory_items
    (name, location_id, category_id, unit, package_size, package_unit, package_count,
     monthly_requirement, monthly_requirement_min, monthly_requirement_max,
     requirement_is_estimate, needs_confirmation, confirmation_note, notes)
  values
    -- 1. Pulses: 7 types, exact names not yet supplied. Real structure, placeholder names.
    ('Pulse Type 1', store_id, cat_food, 'kg', null,null,null, 2, null,null, false, true, 'Name pending confirmation - one of 7 pulse varieties used monthly', null),
    ('Pulse Type 2', store_id, cat_food, 'kg', null,null,null, 2, null,null, false, true, 'Name pending confirmation - one of 7 pulse varieties used monthly', null),
    ('Pulse Type 3', store_id, cat_food, 'kg', null,null,null, 2, null,null, false, true, 'Name pending confirmation - one of 7 pulse varieties used monthly', null),
    ('Pulse Type 4', store_id, cat_food, 'kg', null,null,null, 2, null,null, false, true, 'Name pending confirmation - one of 7 pulse varieties used monthly', null),
    ('Pulse Type 5', store_id, cat_food, 'kg', null,null,null, 2, null,null, false, true, 'Name pending confirmation - one of 7 pulse varieties used monthly', null),
    ('Pulse Type 6', store_id, cat_food, 'kg', null,null,null, 2, null,null, false, true, 'Name pending confirmation - one of 7 pulse varieties used monthly', null),
    ('Pulse Type 7', store_id, cat_food, 'kg', null,null,null, 2, null,null, false, true, 'Name pending confirmation - one of 7 pulse varieties used monthly', null),

    -- 2-5. Grouped in your original note as "2 each per month on estimate"
    ('Semolina (Sooji)', store_id, cat_food, 'kg', null,null,null, 2, null,null, true, false, null, 'Estimated - confirm actual monthly usage'),
    ('Corn Flour',        store_id, cat_food, 'kg', null,null,null, 2, null,null, true, false, null, 'Estimated - confirm actual monthly usage'),
    ('Besan',             store_id, cat_food, 'kg', null,null,null, 2, null,null, true, false, null, 'Estimated - confirm actual monthly usage'),
    ('Poha (Powa)',       store_id, cat_food, 'kg', null,null,null, 2, null,null, true, false, null, 'Estimated - confirm actual monthly usage'),

    -- 6. Amul Milk: 1 litre boxes, 5 per month
    ('Amul Milk', store_id, cat_dairy, 'box', 1, 'litre', 5, 5, null, null, false, false, null, '1 litre per box'),

    -- 7. Milkmaid: a genuine range, not an average
    ('Milkmaid', store_id, cat_dairy, 'piece', null,null,null, null, 3, 5, false, false, null, 'Range of 3-5 per month - do not treat as a fixed 4'),

    ('Coconut',            store_id, cat_food, 'piece', null,null,null, 3,   null,null, false,false,null,null),
    ('Raisins (Kismesh)',  store_id, cat_food, 'kg',    null,null,null, 0.5, null,null, false,false,null,null),
    ('Cashews',            store_id, cat_food, 'kg',    null,null,null, 0.5, null,null, false,false,null,null),
    ('Almonds',            store_id, cat_food, 'kg',    null,null,null, 0.5, null,null, false,false,null,null),
    ('Walnuts',            store_id, cat_food, 'kg',    null,null,null, 0.5, null,null, false,false,null,null),
    ('Onion',              store_id, cat_food, 'bag',   null,null,null, 2,   null,null, false,false,null,null),
    ('Potato',             store_id, cat_food, 'bag',   null,null,null, 2,   null,null, false,false,null,null),

    -- 15. Atta: package info AND total both preserved
    ('Atta (Flour)', store_id, cat_food, 'kg', 10, 'kg', 2, 20, null, null, false, false, null, '10kg bag x 2 bags = 20kg total monthly'),

    ('Garlic',     store_id, cat_food, 'kg', null,null,null, 5, null,null, false,false,null,null),
    ('Tea Sugar',  store_id, cat_food, 'kg', null,null,null, 5, null,null, false,false,null,'Distinct item from regular Sugar'),
    ('Tea Salt',   store_id, cat_food, 'kg', null,null,null, 5, null,null, false,false,null,'Distinct item from regular Salt'),

    -- 19. Sugar: 1 bag of 50kg = 50kg
    ('Sugar', store_id, cat_food, 'kg', 50, 'kg', 1, 50, null, null, false, false, null, '1 bag of 50kg = 50kg total monthly'),

    ('Small Butter', store_id, cat_dairy, 'box', null,null,null, 2, null,null, false,false,null,null),

    -- 21-22. Oils: package info AND total both preserved
    ('P Mark Oil', store_id, cat_oil, 'kg', 15, 'kg', 2, 30, null, null, false, false, null, '2 tins x 15kg = 30kg total monthly'),
    ('Dara Oil',   store_id, cat_oil, 'kg', 10, 'kg', 2, 20, null, null, false, false, null, '2 pieces x 10kg = 20kg total monthly'),

    -- 23. Salt: packaging explicitly noted as configurable, not confirmed rigid
    ('Salt', store_id, cat_food, 'kg', 1, 'kg', 30, 30, null, null, false, false, null, '1 bag made up of 30 x 1kg units = 30kg total monthly; exact packaging is configurable'),

    ('Mirchi',                        store_id, cat_spices, 'kg', null,null,null, 5,   null,null, false,false,null,null),
    ('Turmeric (Haldi)',              store_id, cat_spices, 'kg', null,null,null, 5,   null,null, false,false,null,null),
    ('Badiyan',                       store_id, cat_spices, 'kg', null,null,null, 2,   null,null, false,false,null,null),
    ('Shoonhr (Dry Ginger)',          store_id, cat_spices, 'kg', null,null,null, 2,   null,null, false,false,null,'Original note refers to a dry-ginger grinder; name preserved as supplied'),
    ('Cinnamon (Dalchini)',           store_id, cat_spices, 'kg', null,null,null, 2,   null,null, false,false,null,null),
    ('Cardamom (Nech Aele)',          store_id, cat_spices, 'kg', null,null,null, 0.5, null,null, false,false,null,null),
    ('Bede Ael',                      store_id, cat_spices, 'kg', null,null,null, 0.5, null,null, false, true, 'Exact English/common name needs confirmation', null),
    ('White Zeera',                   store_id, cat_spices, 'kg', null,null,null, 0.5, null,null, false,false,null,null),
    ('Kala Mirch (Black Pepper)',     store_id, cat_spices, 'kg', null,null,null, 1,   null,null, false,false,null,null),
    ('Roong',                         store_id, cat_spices, 'kg', null,null,null, 0.5, null,null, false, true, 'Exact product identity needs confirmation', null),
    ('Whole Badiyan (Soobut Badiyan)',store_id, cat_spices, 'kg', null,null,null, 0.5, null,null, false,false,null,null),
    ('Whole Coriander (Sobut Daniwal)',store_id, cat_spices, 'kg', null,null,null, 0.5, null,null, false,false,null,null),

    ('Gas Cylinders', store_id, cat_gas, 'cylinder', null,null,null, 4, null,null, false,false,null,null),
    ('Rice',          store_id, cat_food, 'kg',      null,null,null, 500, null,null, false,false,null,null),

    ('Tissue Paper - Small', store_id, cat_kitchen, 'dozen', null,null,null, 4, null,null, false,false,null,null),
    ('Tissue Paper - Big',   store_id, cat_kitchen, 'dozen', null,null,null, 4, null,null, false,false,null,null),
    ('Kitchen Tissue',       store_id, cat_kitchen, 'dozen', null,null,null, 2, null,null, false,false,null,null),

    ('Washing Soap (Vim)',   store_id, cat_cleaning, 'piece', null,null,null, 24, null,null, false,false,null,null),
    ('Soft Washing Brush',   store_id, cat_cleaning, 'piece', null,null,null, 24, null,null, false,false,null,null),

    -- 43. Pril: package info AND total both preserved
    ('Washing Liquid (Pril)', store_id, cat_cleaning, 'litre', 750, 'ml', 2, 1.5, null, null, false, false, null, '2 bottles x 750ml = 1.5 litres total monthly'),

    ('Finile',    store_id, cat_cleaning, 'can',    null,null,null, 1, null,null, false,false,null,'1 large can per month'),
    ('Hand Wash', store_id, cat_cleaning, 'packet', null,null,null, 2, null,null, false,false,null,null),

    -- 46-47. Sub-unit counts genuinely unknown - flagged, not guessed
    ('Coffee Pouches (Bru Rs.2)', store_id, cat_kitchen, 'box', null,null,null, 1, null,null, false, true, 'Sachets per box unknown', null),
    ('Amul Creamer',              store_id, cat_dairy,   'box', null,null,null, 1, null,null, false, true, 'Pieces per box unknown', null),

    ('Taj Mahal Tea Dip', store_id, cat_kitchen, 'box', null,null,null, 1, null,null, false,false,null,null),

    -- 49. Genuinely unclear quantity - flagged rather than guessed
    ('Small Sugar', store_id, cat_food, 'packet', null,null,null, null, null,null, false, true, 'Original note: "5 grams each" - monthly quantity/frequency unclear', null),

    -- F3: incomplete list, quantities not supplied - flagged, structure ready for more items later
    ('Bed Sheets', f3_id, cat_room, 'piece', null,null,null, null, null,null, false, true, 'Quantity not yet supplied; F3 list is incomplete', null),
    ('Pillows',    f3_id, cat_room, 'piece', null,null,null, null, null,null, false, true, 'Quantity not yet supplied; F3 list is incomplete', null),
    ('Covers',     f3_id, cat_room, 'piece', null,null,null, null, null,null, false, true, 'Quantity not yet supplied; F3 list is incomplete', null)

  on conflict (name, location_id) do nothing; -- safe to re-run without duplicating
end $$;