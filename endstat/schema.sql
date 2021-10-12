DROP TABLE IF EXISTS users;
DROP TABLE IF EXISTS user_alerts;
DROP TABLE IF EXISTS notification_settings;
DROP TABLE IF EXISTS reset_pass;
DROP TABLE IF EXISTS websites;
DROP TABLE IF EXISTS website_log;

CREATE TABLE users (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  first_name TEXT NOT NULL,
  email TEXT UNIQUE NOT NULL,
  password TEXT NOT NULL,
  time_zone TEXT NOT NULL,
  totp TEXT
);

CREATE TABLE user_alerts (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  date_time TEXT NOT NULL,
  type TEXT NOT NULL,
  message TEXT NOT NULL,
  read BOOLEAN NOT NULL,
  user_id INTEGER NOT NULL,
  website_id INTEGER,
  FOREIGN KEY (user_id) REFERENCES users (id),
  FOREIGN KEY (website_id) REFERENCES websites (id)
);

CREATE TABLE notification_settings (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  email TEXT NOT NULL,
  discord TEXT,
  email_enabled BOOLEAN NOT NULL,
  discord_enabled BOOLEAN NOT NULL,
  user_id INTEGER NOT NULL,
  FOREIGN KEY (user_id) REFERENCES users (id)
);

CREATE TABLE reset_pass (
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
  scan_time TEXT NOT NULL,
  user_id INTEGER NOT NULL,
  FOREIGN KEY (user_id) REFERENCES users (id)
);

CREATE TABLE website_log (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  date_time TEXT NOT NULL,
  status TEXT,
  general TEXT,
  ssl TEXT,
  safety TEXT,
  ports TEXT,
  website_id INTEGER NOT NULL,
  FOREIGN KEY (website_id) REFERENCES websites (id)
);