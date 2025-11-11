-- Schema for MemoVault (includes flags, per spec)
-- Caution: Any attempt to attack this system is a violation of the rules.
DROP TABLE IF EXISTS users;
DROP TABLE IF EXISTS notes;
DROP TABLE IF EXISTS flags;

CREATE TABLE users (
  id INTEGER PRIMARY KEY,
  username TEXT,
  password TEXT,
  is_admin INTEGER
);

CREATE TABLE notes (
  id INTEGER PRIMARY KEY,
  owner_id INTEGER,
  content TEXT
);

CREATE TABLE flags (
  id INTEGER PRIMARY KEY,
  value TEXT
);
