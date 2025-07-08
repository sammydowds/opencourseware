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
| Title | Course Number | Year | Total Content Chars |
|-------|---------------|------|---------------------|
| [Structural Mechanics in Nuclear Power Technology](https://ocw.mit.edu/courses/22-314j-structural-mechanics-in-nuclear-power-technology-fall-2006) | 22.314J | 2006 | 1291632 |
| [Design and Fabrication of Microelectromechanical Devices](https://ocw.mit.edu/courses/6-777j-design-and-fabrication-of-microelectromechanical-devices-spring-2007) | 6.777J | 2007 | 706794 |
| [Advanced Thermodynamics](https://ocw.mit.edu/courses/2-43-advanced-thermodynamics-spring-2024) | 2.43 | 2024 | 663264 |
| [Maneuvering and Control of Surface and Underwater Vehicles (13.49)](https://ocw.mit.edu/courses/2-154-maneuvering-and-control-of-surface-and-underwater-vehicles-13-49-fall-2004) | 2.154 | 2004 | 562554 |
| [Numerical Fluid Mechanics](https://ocw.mit.edu/courses/2-29-numerical-fluid-mechanics-spring-2015) | 2.29 | 2015 | 537680 |
| [Signal Processing: Continuous and Discrete](https://ocw.mit.edu/courses/2-161-signal-processing-continuous-and-discrete-fall-2008) | 2.161 | 2008 | 442605 |
| [Hydrofoils and Propellers](https://ocw.mit.edu/courses/2-23-hydrofoils-and-propellers-spring-2007) | 2.23 | 2007 | 368417 |
| [Introduction to Manufacturing Systems](https://ocw.mit.edu/courses/2-854-introduction-to-manufacturing-systems-fall-2016) | 2.854 | 2016 | 362311 |
| [Modeling and Simulation of Dynamic Systems](https://ocw.mit.edu/courses/2-141-modeling-and-simulation-of-dynamic-systems-fall-2006) | 2.141 | 2006 | 361663 |
| [Design of Medical Devices and Implants](https://ocw.mit.edu/courses/2-782j-design-of-medical-devices-and-implants-spring-2006) | 2.782J | 2006 | 357594 |
| [Marine Power and Propulsion](https://ocw.mit.edu/courses/2-611-marine-power-and-propulsion-fall-2006) | 2.611 | 2006 | 353213 |
| [Dynamics and Control II](https://ocw.mit.edu/courses/2-004-dynamics-and-control-ii-spring-2008) | 2.004 | 2008 | 347880 |
| [Structural Mechanics](https://ocw.mit.edu/courses/2-080j-structural-mechanics-fall-2013) | 2.080J | 2013 | 345149 |
| [Multi-Scale System Design](https://ocw.mit.edu/courses/2-76-multi-scale-system-design-fall-2004) | 2.76 | 2004 | 339795 |
| [Wave Propagation](https://ocw.mit.edu/courses/2-062j-wave-propagation-spring-2017) | 2.062J | 2017 | 305452 |
| [Mechanical Assembly and Its Role in Product Development](https://ocw.mit.edu/courses/2-875-mechanical-assembly-and-its-role-in-product-development-fall-2004) | 2.875 | 2004 | 304462 |
| [Computational Ocean Acoustics (13.853)](https://ocw.mit.edu/courses/2-068-computational-ocean-acoustics-13-853-spring-2003) | 2.068 | 2003 | 301072 |
| [Identification, Estimation, and Learning](https://ocw.mit.edu/courses/2-160-identification-estimation-and-learning-spring-2006) | 2.160 | 2006 | 293721 |
| [Micro/Nano Engineering Laboratory](https://ocw.mit.edu/courses/2-674-micro-nano-engineering-laboratory-spring-2016) | 2.674 | 2016 | 254647 |
| [Marine Hydrodynamics (13.021)](https://ocw.mit.edu/courses/2-20-marine-hydrodynamics-13-021-spring-2005) | 2.20 | 2005 | 245706 |

#### Top 20 Lecture Heavy Courses 
| Title | Course Number | Year | Total Lecture Length | Lecture Count |
|-------|---------------|------|---------------------|---------------|
| [Structural Mechanics in Nuclear Power Technology](https://ocw.mit.edu/courses/22-314j-structural-mechanics-in-nuclear-power-technology-fall-2006) | 22.314J | 2006 | 896851 | 26 |
| [Design and Fabrication of Microelectromechanical Devices](https://ocw.mit.edu/courses/6-777j-design-and-fabrication-of-microelectromechanical-devices-spring-2007) | 6.777J | 2007 | 706794 | 28 |
| [Advanced Thermodynamics](https://ocw.mit.edu/courses/2-43-advanced-thermodynamics-spring-2024) | 2.43 | 2024 | 663264 | 27 |
| [Maneuvering and Control of Surface and Underwater Vehicles (13.49)](https://ocw.mit.edu/courses/2-154-maneuvering-and-control-of-surface-and-underwater-vehicles-13-49-fall-2004) | 2.154 | 2004 | 562554 | 26 |
| [Numerical Fluid Mechanics](https://ocw.mit.edu/courses/2-29-numerical-fluid-mechanics-spring-2015) | 2.29 | 2015 | 537680 | 25 |
| [Signal Processing: Continuous and Discrete](https://ocw.mit.edu/courses/2-161-signal-processing-continuous-and-discrete-fall-2008) | 2.161 | 2008 | 442605 | 25 |
| [Hydrofoils and Propellers](https://ocw.mit.edu/courses/2-23-hydrofoils-and-propellers-spring-2007) | 2.23 | 2007 | 365419 | 1 |
| [Introduction to Manufacturing Systems](https://ocw.mit.edu/courses/2-854-introduction-to-manufacturing-systems-fall-2016) | 2.854 | 2016 | 362311 | 20 |
| [Modeling and Simulation of Dynamic Systems](https://ocw.mit.edu/courses/2-141-modeling-and-simulation-of-dynamic-systems-fall-2006) | 2.141 | 2006 | 350677 | 39 |
| [Dynamics and Control II](https://ocw.mit.edu/courses/2-004-dynamics-and-control-ii-spring-2008) | 2.004 | 2008 | 347880 | 34 |
| [Structural Mechanics](https://ocw.mit.edu/courses/2-080j-structural-mechanics-fall-2013) | 2.080J | 2013 | 345149 | 11 |
| [Marine Power and Propulsion](https://ocw.mit.edu/courses/2-611-marine-power-and-propulsion-fall-2006) | 2.611 | 2006 | 327878 | 41 |
| [Wave Propagation](https://ocw.mit.edu/courses/2-062j-wave-propagation-spring-2017) | 2.062J | 2017 | 305452 | 7 |
| [Mechanical Assembly and Its Role in Product Development](https://ocw.mit.edu/courses/2-875-mechanical-assembly-and-its-role-in-product-development-fall-2004) | 2.875 | 2004 | 304462 | 21 |
| [Computational Ocean Acoustics (13.853)](https://ocw.mit.edu/courses/2-068-computational-ocean-acoustics-13-853-spring-2003) | 2.068 | 2003 | 301072 | 26 |
| [Identification, Estimation, and Learning](https://ocw.mit.edu/courses/2-160-identification-estimation-and-learning-spring-2006) | 2.160 | 2006 | 293721 | 27 |
| [Marine Hydrodynamics (13.021)](https://ocw.mit.edu/courses/2-20-marine-hydrodynamics-13-021-spring-2005) | 2.20 | 2005 | 245706 | 23 |
| [Finite Element Analysis of Solids and Fluids II](https://ocw.mit.edu/courses/2-094-finite-element-analysis-of-solids-and-fluids-ii-spring-2011) | 2.094 | 2011 | 231543 | 22 |
| [Nano-to-Macro Transport Processes](https://ocw.mit.edu/courses/2-57-nano-to-macro-transport-processes-spring-2012) | 2.57 | 2012 | 231349 | 1 |
| [Introduction to Robotics](https://ocw.mit.edu/courses/2-12-introduction-to-robotics-fall-2005) | 2.12 | 2005 | 205267 | 8 |

#### Top 20 Lectures By Avg Lecture Length 
| Title | Course Number | Year | Avg Lecture Length | Lecture Count |
|-------|---------------|------|-------------------|---------------|
| [Hydrofoils and Propellers](https://ocw.mit.edu/courses/2-23-hydrofoils-and-propellers-spring-2007) | 2.23 | 2007 | 365419 | 1 |
| [Nano-to-Macro Transport Processes](https://ocw.mit.edu/courses/2-57-nano-to-macro-transport-processes-spring-2012) | 2.57 | 2012 | 231349 | 1 |
| [Wave Propagation](https://ocw.mit.edu/courses/2-062j-wave-propagation-spring-2017) | 2.062J | 2017 | 43636 | 7 |
| [Structural Mechanics in Nuclear Power Technology](https://ocw.mit.edu/courses/22-314j-structural-mechanics-in-nuclear-power-technology-fall-2006) | 22.314J | 2006 | 34494 | 26 |
| [Structural Mechanics](https://ocw.mit.edu/courses/2-080j-structural-mechanics-fall-2013) | 2.080J | 2013 | 31377 | 11 |
| [Introduction to Robotics](https://ocw.mit.edu/courses/2-12-introduction-to-robotics-fall-2005) | 2.12 | 2005 | 25658 | 8 |
| [Design and Fabrication of Microelectromechanical Devices](https://ocw.mit.edu/courses/6-777j-design-and-fabrication-of-microelectromechanical-devices-spring-2007) | 6.777J | 2007 | 25243 | 28 |
| [Advanced Thermodynamics](https://ocw.mit.edu/courses/2-43-advanced-thermodynamics-spring-2024) | 2.43 | 2024 | 24565 | 27 |
| [Engineering Dynamics](https://ocw.mit.edu/courses/2-003sc-engineering-dynamics-fall-2011) | 2.003SC | 2011 | 22860 | 2 |
| [Maneuvering and Control of Surface and Underwater Vehicles (13.49)](https://ocw.mit.edu/courses/2-154-maneuvering-and-control-of-surface-and-underwater-vehicles-13-49-fall-2004) | 2.154 | 2004 | 21637 | 26 |
| [Numerical Fluid Mechanics](https://ocw.mit.edu/courses/2-29-numerical-fluid-mechanics-spring-2015) | 2.29 | 2015 | 21507 | 25 |
| [Introduction to Manufacturing Systems](https://ocw.mit.edu/courses/2-854-introduction-to-manufacturing-systems-fall-2016) | 2.854 | 2016 | 18116 | 20 |
| [Signal Processing: Continuous and Discrete](https://ocw.mit.edu/courses/2-161-signal-processing-continuous-and-discrete-fall-2008) | 2.161 | 2008 | 17704 | 25 |
| [Precision Machine Design](https://ocw.mit.edu/courses/2-75-precision-machine-design-fall-2001) | 2.75 | 2001 | 14645 | 2 |
| [Mechanical Assembly and Its Role in Product Development](https://ocw.mit.edu/courses/2-875-mechanical-assembly-and-its-role-in-product-development-fall-2004) | 2.875 | 2004 | 14498 | 21 |
| [Multi-Scale System Design](https://ocw.mit.edu/courses/2-76-multi-scale-system-design-fall-2004) | 2.76 | 2004 | 12189 | 16 |
| [Computational Ocean Acoustics (13.853)](https://ocw.mit.edu/courses/2-068-computational-ocean-acoustics-13-853-spring-2003) | 2.068 | 2003 | 11580 | 26 |
| [Identification, Estimation, and Learning](https://ocw.mit.edu/courses/2-160-identification-estimation-and-learning-spring-2006) | 2.160 | 2006 | 10879 | 27 |
| [Designing Paths to Peace](https://ocw.mit.edu/courses/2-993-designing-paths-to-peace-fall-2002) | 2.993 | 2002 | 10869 | 1 |
| [Marine Hydrodynamics (13.021)](https://ocw.mit.edu/courses/2-20-marine-hydrodynamics-13-021-spring-2005) | 2.20 | 2005 | 10683 | 23 |

#### Top 20 Problem Set Courses
| Title | Course Number | Year | Problem Count | Total Problem Length |
|-------|---------------|------|---------------|---------------------|
| [Precision Machine Design](https://ocw.mit.edu/courses/2-75-precision-machine-design-fall-2001) | 2.75 | 2001 | 10 | 140125 |
| [Control of Manufacturing Processes (SMA 6303)](https://ocw.mit.edu/courses/2-830j-control-of-manufacturing-processes-sma-6303-spring-2008) | 2.830J | 2008 | 8 | 112481 |
| [Mechanics and Materials II](https://ocw.mit.edu/courses/2-002-mechanics-and-materials-ii-spring-2004) | 2.002 | 2004 | 6 | 103969 |
| [Finite Element Analysis of Solids and Fluids I](https://ocw.mit.edu/courses/2-092-finite-element-analysis-of-solids-and-fluids-i-fall-2009) | 2.092 | 2009 | 8 | 41876 |
| [Design Principles for Ocean Vehicles (13.42)](https://ocw.mit.edu/courses/2-22-design-principles-for-ocean-vehicles-13-42-spring-2005) | 2.22 | 2005 | 9 | 37617 |
| [Hydrodynamics (13.012)](https://ocw.mit.edu/courses/2-016-hydrodynamics-13-012-fall-2005) | 2.016 | 2005 | 8 | 24603 |
| [Design of Medical Devices and Implants](https://ocw.mit.edu/courses/2-782j-design-of-medical-devices-and-implants-spring-2006) | 2.782J | 2006 | 1 | 10504 |
| [Hydrofoils and Propellers](https://ocw.mit.edu/courses/2-23-hydrofoils-and-propellers-spring-2007) | 2.23 | 2007 | 1 | 2998 |

**NOTE**: missing data could be due to parsing assignment issues and/or grouping them improperly. Specifically, problem sets are only saved if they have solution set with them.

