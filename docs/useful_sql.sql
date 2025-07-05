-- SQLite
-- SQLite
SELECT asset_id, asset_name, asset_type, asset_subtype, currency, description, issuer, credit_rating, extended_attributes, created_date, updated_date
FROM assets

DELETE from assets where asset_name like '活期-人民币';
drop table assets;


select * from transactions