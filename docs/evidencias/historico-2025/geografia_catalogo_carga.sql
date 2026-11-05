-- [1] tras dos cargas del catálogo real
SELECT count(*) AS paises, count(DISTINCT country_id) AS codigos FROM public.country;

