DROP TABLE IF EXISTS users;
DROP TABLE IF EXISTS resetPass;
DROP TABLE IF EXISTS websites;

CREATE TABLE users (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  first_name TEXT NOT NULL,
  email TEXT UNIQUE NOT NULL,
  password TEXT NOT NULL
);

CREATE TABLE resetPass (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  reset_key TEXT UNIQUE NOT NULL,
  user_id INTEGER,
  date_time TEXT NOT NULL, 
  activated BOOLEAN NOT NULL,
  FOREIGN KEY (user_id) REFERENCES users (id)
);

CREATE TABLE websites (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  domain TEXT NOT NULL,
  protocol TEXT NOT NULL,
  certificate_check BOOLEAN,
  ports_check BOOLEAN,
  blacklists_check BOOLEAN,
  user_id INTEGER,
  FOREIGN KEY (user_id) REFERENCES users (id)
);



