-- SQLite
SELECT asset_id, asset_name, asset_type, primary_category, secondary_category, currency, description, issuer, credit_rating, extended_attributes, created_date, updated_date
FROM assets

DELETE from assets where asset_name like '招商银行储蓄账户';