-- ============================================================================
-- 0007_adjustment_signed_quantity.sql
-- Every movement type except ADJUSTMENT has a fixed direction (RECEIVE is
-- always +, USE is always -), so quantity can just be stored positive.
-- ADJUSTMENT is the exception - a correction can go either way - so we
-- allow ADJUSTMENT rows to store a signed quantity, while every other
-- movement type still must be non-negative.
-- ============================================================================
alter table public.stock_movements drop constraint if exists stock_movements_quantity_check;
alter table public.stock_movements
  add constraint chk_quantity_sign check (movement_type = 'ADJUSTMENT' or quantity >= 0);