-- /records.sql
CREATE TABLE IF NOT EXISTS records (
	id INTEGER PRIMARY KEY,
	-- insert time for tracking database build-up, in epoch seconds
	inserted INTEGER NOT NULL DEFAULT (unixepoch()),
	-- record time stamp, also in epoch seconds
	datetime INTEGER NOT NULL,
	value REAL NOT NULL,
	flag_value INTEGER NOT NULL,
	spec_id INTEGER NOT NULL,

	FOREIGN KEY (flag_value) REFERENCES flags(value),
	FOREIGN KEY (spec_id) REFERENCES specs(id)
) STRICT;

-- composite index covers (spec_id) prefix and (spec_id, datetime) range queries
CREATE INDEX IF NOT EXISTS idx_records_spec_datetime ON records(spec_id, datetime);
-- standalone index for time-range queries across all specs
CREATE INDEX IF NOT EXISTS idx_records_datetime ON records(datetime);