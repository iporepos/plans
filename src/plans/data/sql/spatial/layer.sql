-- /layer.sql
-- template: {layer} is set by the class (eg, zones)
-- the layer table itself is written by geopandas (GDAL), never by plain SQL
CREATE UNIQUE INDEX IF NOT EXISTS idx_{layer}_name ON {layer}(name);
