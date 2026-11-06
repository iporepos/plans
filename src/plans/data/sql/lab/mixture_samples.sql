-- /mixture_samples.sql
-- link table: a mixture holds one or more samples, a sample may enter several mixtures
CREATE TABLE IF NOT EXISTS mixture_samples (
	mixture_id INTEGER NOT NULL,
	sample_id INTEGER NOT NULL,
	PRIMARY KEY (mixture_id, sample_id),
	FOREIGN KEY (mixture_id) REFERENCES mixtures(id),
	FOREIGN KEY (sample_id) REFERENCES samples(id)
) STRICT;

-- the primary key covers lookups by mixture; this one covers lookups by sample
CREATE INDEX IF NOT EXISTS idx_mixture_samples_sample ON mixture_samples(sample_id);
