-- Seed data for MemoVault (safe defaults; admin not meant to login)
INSERT INTO users (id, username, password, is_admin) VALUES
  (1, 'guest', 'guest', 0),
  (2, 'admin', 'THIS_IS_NOT_A_LOGIN_PASSWORD', 1);

INSERT INTO notes (id, owner_id, content) VALUES
  (1, 1, 'Welcome to MemoVault!'),
  (2, 1, 'Your notes will appear here.'),
  (3, 1, 'This is a training skeleton.'),
  (4, 1, 'Sections 3 and 4 are intentionally omitted.'),
  (5, 1, 'Complete them to turn this into a real CTF.');

INSERT INTO flags (id, value) VALUES
  (1, 'DH{**flag**}');
