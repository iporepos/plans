-- /records.sql
CREATE TABLE IF NOT EXISTS records (
	id INTEGER PRIMARY KEY,
	-- insert time for tracking database build-up, in epoch seconds
	inserted INTEGER NOT NULL DEFAULT (unixepoch()),
	-- record time stamp, also in epoch seconds
	datetime INTEGER NOT NULL,
	-- stored = actual * scale + offset; NULL only with a no-value flag (flag <= 0)
	value REAL CHECK (value IS NOT NULL OR flag_value <= 0),
	flag_value INTEGER NOT NULL,
	spec_id INTEGER NOT NULL,
	-- feature key (eg, an H3 cell); features live outside the database
	feature_id INTEGER NOT NULL,
	FOREIGN KEY (flag_value) REFERENCES flags(value),
	FOREIGN KEY (spec_id) REFERENCES specs(id)
) STRICT;

-- composite index covers (spec_id) prefix and (spec_id, datetime) range queries
CREATE INDEX IF NOT EXISTS idx_records_spec_datetime ON records(spec_id, datetime);
-- standalone index for time-range queries across all specs
CREATE INDEX IF NOT EXISTS idx_records_datetime ON records(datetime);
-- composite index for one or more features of a spec over time
CREATE INDEX IF NOT EXISTS idx_records_spec_feature_id_datetime ON records(spec_id, feature_id, datetime);