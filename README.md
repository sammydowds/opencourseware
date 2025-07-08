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

### Mechanical Engineering Course Analysis 

After scraping, I ran some analysis on the courses.

#### Top 20 Content Heavy Courses
| ID | Title | Course Number | Total Content Chars |
|----|-------|---------------|---------------------|
| 36 | Structural Mechanics in Nuclear Power Technology | 22.314J | 1291632 |
| 30 | Design and Fabrication of Microelectromechanical Devices | 6.777J | 706794 |
| 2 | Advanced Thermodynamics | 2.43 | 663264 |
| 48 | Maneuvering and Control of Surface and Underwater Vehicles (13.49) | 2.154 | 562554 |
| 9 | Numerical Fluid Mechanics | 2.29 | 537680 |
| 25 | Signal Processing: Continuous and Discrete | 2.161 | 442605 |
| 31 | Hydrofoils and Propellers | 2.23 | 368417 |
| 5 | Introduction to Manufacturing Systems | 2.854 | 362311 |
| 37 | Modeling and Simulation of Dynamic Systems | 2.141 | 361663 |
| 38 | Design of Medical Devices and Implants | 2.782J | 357594 |
| 35 | Marine Power and Propulsion | 2.611 | 353213 |
| 27 | Dynamics and Control II | 2.004 | 347880 |
| 14 | Structural Mechanics | 2.080J | 345149 |
| 45 | Multi-Scale System Design | 2.76 | 339795 |
| 4 | Wave Propagation | 2.062J | 305452 |
| 46 | Mechanical Assembly and Its Role in Product Development | 2.875 | 304462 |
| 56 | Computational Ocean Acoustics (13.853) | 2.068 | 301072 |
| 39 | Identification, Estimation, and Learning | 2.160 | 293721 |
| 6 | Micro/Nano Engineering Laboratory | 2.674 | 254647 |
| 43 | Marine Hydrodynamics (13.021) | 2.20 | 245706 |

#### Top 20 Lecture Heavy Courses 
| ID | Title | Course Number | Total Lecture Length | Lecture Count |
|----|-------|---------------|---------------------|---------------|
| 36 | Structural Mechanics in Nuclear Power Technology | 22.314J | 896851 | 26 |
| 30 | Design and Fabrication of Microelectromechanical Devices | 6.777J | 706794 | 28 |
| 2 | Advanced Thermodynamics | 2.43 | 663264 | 27 |
| 48 | Maneuvering and Control of Surface and Underwater Vehicles (13.49) | 2.154 | 562554 | 26 |
| 9 | Numerical Fluid Mechanics | 2.29 | 537680 | 25 |
| 25 | Signal Processing: Continuous and Discrete | 2.161 | 442605 | 25 |
| 31 | Hydrofoils and Propellers | 2.23 | 365419 | 1 |
| 5 | Introduction to Manufacturing Systems | 2.854 | 362311 | 20 |
| 37 | Modeling and Simulation of Dynamic Systems | 2.141 | 350677 | 39 |
| 27 | Dynamics and Control II | 2.004 | 347880 | 34 |
| 14 | Structural Mechanics | 2.080J | 345149 | 11 |
| 35 | Marine Power and Propulsion | 2.611 | 327878 | 41 |
| 4 | Wave Propagation | 2.062J | 305452 | 7 |
| 46 | Mechanical Assembly and Its Role in Product Development | 2.875 | 304462 | 21 |
| 56 | Computational Ocean Acoustics (13.853) | 2.068 | 301072 | 26 |
| 39 | Identification, Estimation, and Learning | 2.160 | 293721 | 27 |
| 43 | Marine Hydrodynamics (13.021) | 2.20 | 245706 | 23 |
| 18 | Finite Element Analysis of Solids and Fluids II | 2.094 | 231543 | 22 |
| 16 | Nano-to-Macro Transport Processes | 2.57 | 231349 | 1 |
| 41 | Introduction to Robotics | 2.12 | 205267 | 8 |

#### Top 20 Lectures By Avg Lecture Length 
| ID | Title | Course Number | Avg Lecture Length | Lecture Count |
|----|-------|---------------|-------------------|---------------|
| 31 | Hydrofoils and Propellers | 2.23 | 365419 | 1 |
| 16 | Nano-to-Macro Transport Processes | 2.57 | 231349 | 1 |
| 4 | Wave Propagation | 2.062J | 43636 | 7 |
| 36 | Structural Mechanics in Nuclear Power Technology | 22.314J | 34494 | 26 |
| 14 | Structural Mechanics | 2.080J | 31377 | 11 |
| 41 | Introduction to Robotics | 2.12 | 25658 | 8 |
| 30 | Design and Fabrication of Microelectromechanical Devices | 6.777J | 25243 | 28 |
| 2 | Advanced Thermodynamics | 2.43 | 24565 | 27 |
| 17 | Engineering Dynamics | 2.003SC | 22860 | 2 |
| 48 | Maneuvering and Control of Surface and Underwater Vehicles (13.49) | 2.154 | 21637 | 26 |
| 9 | Numerical Fluid Mechanics | 2.29 | 21507 | 25 |
| 5 | Introduction to Manufacturing Systems | 2.854 | 18116 | 20 |
| 25 | Signal Processing: Continuous and Discrete | 2.161 | 17704 | 25 |
| 61 | Precision Machine Design | 2.75 | 14645 | 2 |
| 46 | Mechanical Assembly and Its Role in Product Development | 2.875 | 14498 | 21 |
| 45 | Multi-Scale System Design | 2.76 | 12189 | 16 |
| 56 | Computational Ocean Acoustics (13.853) | 2.068 | 11580 | 26 |
| 39 | Identification, Estimation, and Learning | 2.160 | 10879 | 27 |
| 57 | Designing Paths to Peace | 2.993 | 10869 | 1 |
| 43 | Marine Hydrodynamics (13.021) | 2.20 | 10683 | 23 |

#### Top 20 Problem Set Courses
| ID | Title | Course Number | Problem Count | Total Problem Length |
|----|-------|---------------|---------------|---------------------|
| 61 | Precision Machine Design | 2.75 | 10 | 140125 |
| 26 | Control of Manufacturing Processes (SMA 6303) | 2.830J | 8 | 112481 |
| 49 | Mechanics and Materials II | 2.002 | 6 | 103969 |
| 21 | Finite Element Analysis of Solids and Fluids I | 2.092 | 8 | 41876 |
| 42 | Design Principles for Ocean Vehicles (13.42) | 2.22 | 9 | 37617 |
| 40 | Hydrodynamics (13.012) | 2.016 | 8 | 24603 |
| 38 | Design of Medical Devices and Implants | 2.782J | 1 | 10504 |
| 31 | Hydrofoils and Propellers | 2.23 | 1 | 2998 |

**NOTE**: missing data could be due to parsing assignment issues and/or grouping them improperly. Specifically, problem sets are only saved if they have solution set with them.

