DROP TABLE IF EXISTS users;
DROP TABLE IF EXISTS user_alerts;
DROP TABLE IF EXISTS resetPass;
DROP TABLE IF EXISTS websites;
DROP TABLE IF EXISTS website_log;

CREATE TABLE users (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  first_name TEXT NOT NULL,
  email TEXT UNIQUE NOT NULL,
  password TEXT NOT NULL
);

CREATE TABLE user_alerts (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  date_time TEXT NOT NULL,
  type TEXT NOT NULL,
  alert TEXT NOT NULL,
  user_id INTEGER NOT NULL,
  FOREIGN KEY (user_id) REFERENCES users (id)
);

CREATE TABLE resetPass (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  reset_key TEXT UNIQUE NOT NULL,
  date_time TEXT NOT NULL, 
  activated BOOLEAN NOT NULL,
  user_id INTEGER NOT NULL,
  FOREIGN KEY (user_id) REFERENCES users (id)
);

CREATE TABLE websites (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  domain TEXT NOT NULL,
  protocol TEXT NOT NULL,
  cert_check BOOLEAN NOT NULL,
  ports_check BOOLEAN NOT NULL,
  blacklists_check BOOLEAN NOT NULL,
  user_id INTEGER NOT NULL,
  FOREIGN KEY (user_id) REFERENCES users (id)
);

CREATE TABLE website_log (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  date_time TEXT NOT NULL,
  status TEXT NOT NULL,
  cert_errors TEXT NOT NULL,
  open_ports TEXT NOT NULL,
  blacklists TEXT NOT NULL,
  website_id INTEGER NOT NULL,
  FOREIGN KEY (website_id) REFERENCES websites (id)
);