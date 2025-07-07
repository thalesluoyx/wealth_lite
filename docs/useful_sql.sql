-- SQLite
-- SQLite
SELECT asset_id, asset_name, asset_type, asset_subtype, currency, description, issuer, credit_rating, extended_attributes, created_date, updated_date
FROM assets

DELETE from assets where asset_name like '活期-人民币';
drop table assets;


select * from transactions


select * from transactions join fixed_income_transactions 
on transactions.transaction_id = fixed_income_transactions.transaction_id where transaction_id = 'b07a5e2b-bce4-4b95-92e9-65d7957fed6e';