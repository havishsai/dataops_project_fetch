CREATE TABLE IF NOT EXISTS user_logins(
  user_id varchar(128),
  device_type varchar(32),
  masked_ip varchar(256),
  masked_device_id varchar(256),
  locale varchar(32),
  app_version integer,
  create_date date
);


Alter table user_logins ALTER COLUMN app_version TYPE VARCHAR;