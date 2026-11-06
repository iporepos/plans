-- /records.sql
-- template: {layer} and {key} are set by the class (eg, zones and zone_id)
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
	-- key to the geometry layer of this database
	{key} INTEGER NOT NULL,
	FOREIGN KEY (flag_value) REFERENCES flags(value),
	FOREIGN KEY (spec_id) REFERENCES specs(id),
	FOREIGN KEY ({key}) REFERENCES {layer}(id)
) STRICT;

-- composite index covers (spec_id) prefix and (spec_id, datetime) range queries
CREATE INDEX IF NOT EXISTS idx_records_spec_datetime ON records(spec_id, datetime);
-- standalone index for time-range queries across all specs
CREATE INDEX IF NOT EXISTS idx_records_datetime ON records(datetime);
-- composite index for one or more features of a spec over time
CREATE INDEX IF NOT EXISTS idx_records_spec_{key}_datetime ON records(spec_id, {key}, datetime);
