DROP TABLE IF EXISTS user;
DROP TABLE IF EXISTS datas;

CREATE TABLE user (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  author_hash TEXT NOT NULL,
  
  datas JSON DEFAULT '{}'
);

/*created TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP*/

CREATE TABLE datas (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  author_hash TEXT NOT NULL,
  object_date TIMESTAMP NOT NULL,
  datas JSON DEFAULT '{}'
);