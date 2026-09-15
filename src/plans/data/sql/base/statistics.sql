-- /statistics.sql
CREATE TABLE IF NOT EXISTS statistics (
	id INTEGER PRIMARY KEY,
	name TEXT NOT NULL UNIQUE, -- eg. Mean
	alias TEXT NOT NULL UNIQUE, -- plain text symbol, eg. avg
	title TEXT NOT NULL, -- eg. Arithmetic Mean
	abstract TEXT NOT NULL,
	symbol TEXT NOT NULL, -- LaTeX symbol, eg \bar{x}
	formula TEXT NOT NULL -- LaTeX formula, eg \frac{1}{n}\sum_{i=1}^{n}x_i
) STRICT;