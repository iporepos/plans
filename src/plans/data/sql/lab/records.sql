-- /records.sql
CREATE TABLE IF NOT EXISTS records (
	id INTEGER PRIMARY KEY,
	-- insert time for tracking database build-up, in epoch seconds
	inserted INTEGER NOT NULL DEFAULT (unixepoch()),
	-- analysis time, in epoch seconds; NULL when unknown
	datetime INTEGER,
	-- stored = actual * scale + offset; NULL only with a no-value flag (flag <= 0)
	value REAL CHECK (value IS NOT NULL OR flag_value <= 0),
	flag_value INTEGER NOT NULL,
	spec_id INTEGER NOT NULL,
	-- the analysed mixture; the site is reached through its samples
	mixture_id INTEGER NOT NULL,
	FOREIGN KEY (flag_value) REFERENCES flags(value),
	FOREIGN KEY (spec_id) REFERENCES specs(id),
	FOREIGN KEY (mixture_id) REFERENCES mixtures(id)
) STRICT;

-- composite index for one or more mixtures of a spec
CREATE INDEX IF NOT EXISTS idx_records_spec_mixture ON records(spec_id, mixture_id);
-- standalone index for analysis-time queries
CREATE INDEX IF NOT EXISTS idx_records_datetime ON records(datetime);
