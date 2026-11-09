-- /catchments.sql
-- template: {layer} is set by the class (the sites layer)
-- the catchments table itself is written by geopandas (GDAL), never by plain SQL
-- GDAL tables have no foreign keys, so these rules also guard edits made in a GIS

-- at most one catchment per site
CREATE UNIQUE INDEX IF NOT EXISTS idx_catchments_name ON catchments(name);

-- a catchment needs its site
CREATE TRIGGER IF NOT EXISTS catchments_need_site_insert
BEFORE INSERT ON catchments
WHEN NOT EXISTS (SELECT 1 FROM {layer} WHERE name = NEW.name)
BEGIN
	SELECT RAISE(ABORT, 'catchment name is not a site name');
END;

CREATE TRIGGER IF NOT EXISTS catchments_need_site_update
BEFORE UPDATE OF name ON catchments
WHEN NOT EXISTS (SELECT 1 FROM {layer} WHERE name = NEW.name)
BEGIN
	SELECT RAISE(ABORT, 'catchment name is not a site name');
END;
