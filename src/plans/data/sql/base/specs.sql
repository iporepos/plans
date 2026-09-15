CREATE TABLE IF NOT EXISTS specs (
	id INTEGER PRIMARY KEY,
	-- basic info
	name TEXT NOT NULL, -- name of the dataset
	abstract TEXT NOT NULL, -- summary of the dataset
	method TEXT NOT NULL, -- method of generation

	-- time and space extents of each data value
	timestep TEXT NOT NULL,
	extent TEXT NOT NULL,

	-- linear transform parameters of the stored values
	-- stored = (actual * scale) + offset
	-- this is useful when `records` strict INTEGER values
	scale REAL NOT NULL DEFAULT 1, -- scale factor
	offset REAL NOT NULL DEFAULT 0, -- offset value

	-- validation times
	start INTEGER NOT NULL, -- start of valid time range
	end INTEGER, -- end of valid time range

	-- foreign keys
	-- variable
	variable_name TEXT NOT NULL,
	-- statistic applied over the timestep (eg, mean)
	statistic_name TEXT NOT NULL,
	-- source name for the dataset (eg, CHIRPSV3)
	source_name TEXT NOT NULL,

	FOREIGN KEY (variable_name) REFERENCES variables(name),
	FOREIGN KEY (statistic_name) REFERENCES statistics(name),
	FOREIGN KEY (source_name) REFERENCES sources(name)
) STRICT;