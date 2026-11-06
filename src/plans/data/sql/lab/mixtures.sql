-- /mixtures.sql
-- lab mixtures of one or more samples; the unit that gets analysed
CREATE TABLE IF NOT EXISTS mixtures (
	id INTEGER PRIMARY KEY,
	name TEXT NOT NULL UNIQUE,
	abstract TEXT
) STRICT;
