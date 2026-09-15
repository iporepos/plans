-- /sources.sql
CREATE TABLE IF NOT EXISTS sources (
	id INTEGER PRIMARY KEY,
	name TEXT NOT NULL UNIQUE, -- Eg, CHIRPS Version 3
	alias TEXT NOT NULL, -- CHIRPSV3
	title TEXT NOT NULL,
	abstract TEXT,
	citation TEXT,
	url TEXT -- link to source
) STRICT;