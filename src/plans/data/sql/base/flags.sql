-- /flags.sql
CREATE TABLE IF NOT EXISTS flags (
	id INTEGER PRIMARY KEY,
	name TEXT NOT NULL, -- Eg, Regular, Null, Not Analysed
	abstract TEXT NOT NULL,
	alias TEXT NOT NULL, -- eg, N.A.
	value INTEGER NOT NULL UNIQUE
) STRICT;