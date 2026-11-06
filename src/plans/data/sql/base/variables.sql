-- /variables.sql
CREATE TABLE IF NOT EXISTS variables (
	id INTEGER PRIMARY KEY,
	code TEXT NOT NULL UNIQUE, -- eg. HYD100
	name TEXT NOT NULL UNIQUE, -- lowercase, eg. rainfall
	alias TEXT NOT NULL UNIQUE, -- plain text symbol, eg. PPT
	symbol TEXT NOT NULL, -- LaTeX symbol, eg. P
	title TEXT NOT NULL, -- eg. Rain of Liquid Water
	abstract TEXT,
	synonyms TEXT, -- list: Rain | Rainfall
	units TEXT NOT NULL, -- units of the actual value, eg. mm/(dt)
	dimension TEXT NOT NULL, -- LaTeX, eg. L^{3}/TL^{2}
	dtype TEXT NOT NULL, -- data type primitive (real, integer, etc)
	domain TEXT NOT NULL, -- math domain, eg. [0U), [0U1], [-273.15U), (U)
	discipline TEXT NOT NULL, -- top of the hierarchy, eg. Hydrology, Geospatial
	theme TEXT NOT NULL, -- within the discipline, eg. Spectral Vegetation Indices
	category TEXT NOT NULL, -- eg. flow, level, ratio, parameter, boundary
	source TEXT, -- reference, eg. McKee_1993_a.pdf
	url TEXT
) STRICT;