-- /samples.sql
-- field samples (eg, a water bottle or a soil core) taken at a site
CREATE TABLE IF NOT EXISTS samples (
	id INTEGER PRIMARY KEY,
	name TEXT NOT NULL UNIQUE, -- eg. the bottle label
	alias TEXT,
	abstract TEXT,
	-- sampling time, in epoch seconds
	datetime INTEGER NOT NULL,
	site_id INTEGER NOT NULL,
	FOREIGN KEY (site_id) REFERENCES sites(id)
) STRICT;

-- samples of one or more sites over time
CREATE INDEX IF NOT EXISTS idx_samples_site_datetime ON samples(site_id, datetime);
