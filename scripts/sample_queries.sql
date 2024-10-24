-- Show architecturally similar buildings to Notre-Dame
WITH notre_dame_embedding AS (
    SELECT af.embedding 
    FROM geolens.architectural_features af
    JOIN geolens.locations l ON af.location_id = l.id
    WHERE l.name = 'Notre-Dame Cathedral'
    LIMIT 1
)
SELECT 
    l.name, 
    af.style,
    1 - (af.embedding <=> (SELECT embedding FROM notre_dame_embedding)) as similarity
FROM geolens.locations l
JOIN geolens.architectural_features af ON l.id = af.location_id
WHERE l.name != 'Notre-Dame Cathedral'
ORDER BY similarity DESC;

-- Basic spatial query (find locations within 1000km of Paris):
WITH paris AS (
    SELECT geometry FROM geolens.locations 
    WHERE name = 'Notre-Dame Cathedral'
)
SELECT 
    l.name,
    ST_Distance(
        l.geometry::geography,
        (SELECT geometry::geography FROM paris)
    ) / 1000 as distance_km
FROM geolens.locations l
WHERE l.name != 'Notre-Dame Cathedral'
ORDER BY distance_km;

-- Historical timeline
SELECT 
    l.name as location,
    he.event_type,
    he.event_date,
    he.description
FROM geolens.historical_events he
JOIN geolens.locations l ON he.location_id = l.id
ORDER BY he.event_date;

-- Relationship graph
SELECT 
    l1.name as from_location,
    l2.name as to_location,
    r.relationship_type,
    r.strength,
    r.evidence
FROM geolens.relationships r
JOIN geolens.locations l1 ON r.from_location_id = l1.id
JOIN geolens.locations l2 ON r.to_location_id = l2.id
ORDER BY r.strength DESC;

-- Combined spatial-semantic query (find architecturally similar buildings ordered by distance)
WITH notre_dame AS (
    SELECT geometry, id FROM geolens.locations 
    WHERE name = 'Notre-Dame Cathedral'
),
notre_dame_embedding AS (
    SELECT embedding FROM geolens.architectural_features
    WHERE location_id = (SELECT id FROM notre_dame)
)
SELECT 
    l.name,
    af.style,
    1 - (af.embedding <=> (SELECT embedding FROM notre_dame_embedding)) as style_similarity,
    ST_Distance(
        l.geometry::geography,
        (SELECT geometry::geography FROM notre_dame)
    ) / 1000 as distance_km
FROM geolens.locations l
JOIN geolens.architectural_features af ON l.id = af.location_id
WHERE l.name != 'Notre-Dame Cathedral'
ORDER BY style_similarity DESC, distance_km;