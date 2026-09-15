-- /variables.sql
CREATE TABLE IF NOT EXISTS variables (
	id INTEGER PRIMARY KEY,
	code TEXT NOT NULL UNIQUE, -- eg. HYD001
	name TEXT NOT NULL UNIQUE, -- eg. Precipitation
	alias TEXT NOT NULL UNIQUE, -- plain text symbol PPT
	symbol TEXT NOT NULL, -- LaTeX symbol P
	title TEXT NOT NULL, -- eg. Precipitation Layer
	abstract TEXT,
	synonyms TEXT, -- list: Rain | Rainfall
	units TEXT NOT NULL, -- Units in actual value, eg mm/(dt)
	dimension TEXT NOT NULL, -- LaTeX, eg, L^{3}/TL^{2}
	dtype TEXT NOT NULL, -- data type primitive (real, integer, etc)
	domain TEXT NOT NULL, -- math domain (0U), (0U1), (-273.15U)
	theme TEXT NOT NULL, -- Hydrology
	system TEXT NOT NULL -- Options: flow, storage, parameter
) STRICT;