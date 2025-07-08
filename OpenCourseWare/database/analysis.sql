-- rank courses by lecture length
SELECT 
    c.id,
    c.title,
    c.course_number,
    SUM(l.character_count) as total_lecture_length,
    COUNT(l.id) as lecture_count
FROM course c
LEFT JOIN lecture l ON c.id = l.course_id
GROUP BY c.id, c.title, c.course_number
ORDER BY total_lecture_length DESC NULLS LAST
LIMIT 20;

-- rank courses by avg lecture length 
SELECT 
    c.id,
    c.title,
    c.course_number,
    ROUND(AVG(l.character_count)) as avg_lecture_length,
    COUNT(l.id) as lecture_count
FROM course c
LEFT JOIN lecture l ON c.id = l.course_id
GROUP BY c.id, c.title, c.course_number
HAVING COUNT(l.id) > 0  -- Only include courses with lectures
ORDER BY avg_lecture_length DESC
LIMIT 20;

-- rank courses by problem set length
SELECT 
    c.id,
    c.title,
    c.course_number,
    COUNT(p.id) as problem_count,
    SUM(p.character_count) as total_problem_length 
FROM course c
LEFT JOIN problem_set p ON c.id = p.course_id
GROUP BY c.id, c.title, c.course_number
HAVING COUNT(p.id) > 0  -- Only include courses with lectures
ORDER BY total_problem_length DESC
LIMIT 20;

-- rank courses by avg problem set length
SELECT 
    c.id,
    c.title,
    c.course_number,
    COUNT(p.id) as problem_count,
    ROUND(AVG(p.character_count)) as avg_problem_length 
FROM course c
LEFT JOIN problem_set p ON c.id = p.course_id
GROUP BY c.id, c.title, c.course_number
HAVING COUNT(p.id) > 0
ORDER BY avg_problem_length DESC
LIMIT 20;

-- rank best course by characters 
SELECT 
    c.id,
    c.title,
    c.course_number,
    (COALESCE(ps_stats.total_ps_chars, 0) + 
     COALESCE(r_stats.total_reading_chars, 0) + 
     COALESCE(l_stats.total_lecture_chars, 0)) as total_content_chars
FROM course c
LEFT JOIN (
    SELECT course_id, SUM(character_count) as total_ps_chars, COUNT(*) as ps_count
    FROM problem_set 
    GROUP BY course_id
) ps_stats ON c.id = ps_stats.course_id
LEFT JOIN (
    SELECT course_id, SUM(character_count) as total_reading_chars, COUNT(*) as reading_count
    FROM reading 
    GROUP BY course_id
) r_stats ON c.id = r_stats.course_id
LEFT JOIN (
    SELECT course_id, SUM(character_count) as total_lecture_chars, COUNT(*) as lecture_count
    FROM lecture 
    GROUP BY course_id
) l_stats ON c.id = l_stats.course_id
ORDER BY total_content_chars DESC
LIMIT 20;
