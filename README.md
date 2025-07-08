# OpenCourseWare Scraping 

## Summary

This project contains tools to scrape course data from https://ocw.mit.edu/. This could be used to get the raw text from various course lectures, readings, and problem sets with solutions.

_Note: this is not a production pipeline._

Key features: 
- Groups problem sets with solutions
- Reads files and converts to LLM friendly markdown
- Stores character count and topics for future filtering (quality, discovery, etc)
- Stores metadata for each course

## Scraping an individual course

### Setup DB 

```bash
cd OpenCourseWare/database && docker compose up
```

.env should look like this
```
DATABASE_URL=postgresql://postgres:password@localhost:5432/courses
```

create the tables
```python
from database.model import Base
from database.session import engine

Base.metadata.create_all(engine)
```

You are now ready to scrape!

### Scraping a single course

For this you will need a download url and the course home URL.

Example urls: 
- Download url: https://ocw.mit.edu/courses/2-61-internal-combustion-engines-spring-2017/2.61-spring-2017.zip
- Course home url: https://ocw.mit.edu/courses/2-61-internal-combustion-engines-spring-2017/

getting started

```bash
cd OpenCourseWare && uv run python
```

create a `CourseContext` instance & extract
```python
from course_context import CourseContext

course = CourseContext(download_url='https://ocw.mit.edu/courses/2-61-internal-combustion-engines-spring-2017/2.61-spring-2017.zip', url='https://ocw.mit.edu/courses/2-61-internal-combustion-engines-spring-2017/')

# save data to DB
course.extract_all_to_db()
```

Running the above will do the following: 
1. Download the course files into a `corpus` folder in the current working directory
2. Saves the course data to the DB 
3. Contextualize the course files (parse assignment, lecture, and reading file names)
4. Saves problems sets to the DB
5. Saves lectures to the DB
6. Saves readings to the DB 

Note: raw text from the files is saved in markdown via `pymupdf4llm`

### Create combined problem set, reading, and lecture PDFs

I built in the ability to also export PDF's which are combinations of all lectures, problem sets, and readings. You can save data to the database _and_ to local PDFs by running the following:

```python
...

# save to database and combine PDFs
course.extract_all()
```

This will save combined PDF's for the course in `/out/<course slug>/`.


## Scraping multiple courses: running the pipeline

Right now, I have a pre-baked search query in `helpers.py` that is used in my scraper to pull Mechanical Engineering courses that have: lecture notes, readings, and problem sets with solutions. This results in about ~ 66 courses surfacing.

To run a pipeline that searches courses, scrapes their download links, and extracts each course:

```python
from pipeline import OpenCourseWarePipeline

pipeline = OpenCourseWarePipeline()

# scrape courses, download them, extract data to the DB and into combined PDFs
pipeline.run()
```

### Learnings

I initially wired this up with an LLM at the extraction layer - utilizing it to create a title and summary of each problem set. I found this to be an issue for multiple reasons:
1. Inconsistent and lackluster summaries
2. Additional latency
3. Complexity of putting a non-deterministic process into a data pipeline

TL;DR: Do not utilize LLM's until you have the deterministic process saving data to the DB. Then after, process that data with an LLM. Don't over-engineer the pipeline! 
