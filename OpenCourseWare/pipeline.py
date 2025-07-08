import asyncio
from typing import Dict, Any
from datetime import datetime
import logging
from course_context import CourseContext
from scraper import Scraper

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("pipeline")


class OpenCourseWarePipeline:
    def __init__(self):
        self.scraper = Scraper()
        self.processed_courses = []
        self.failed_courses = []
        self.pipeline_stats = {
            "start_time": None,
            "end_time": None,
            "total_courses": 0,
            "successful": 0,
            "failed": 0,
        }

    def run(self) -> Dict[str, Any]:
        """Run the complete course processing pipeline"""
        return asyncio.run(self._async_run_pipeline())

    async def _async_run_pipeline(self) -> Dict[str, Any]:
        """Async implementation of the pipeline"""
        self.pipeline_stats["start_time"] = datetime.now().isoformat()

        try:
            self.scraper.scrape()
            if not self.scraper.urls:
                raise Exception("No scraper URLs found")

            self.pipeline_stats["total_courses"] = len(self.scraper.urls)
            for payload in self.scraper.urls:
                try:
                    url, download_url = payload
                    course = CourseContext(
                        url=url, download_url=download_url
                    )
                    course.extracl_all_to_db()

                    self.pipeline_stats["successful"] += 1
                except Exception as e:
                    self.failed_courses.append(payload[0])
                    self.pipeline_stats["failed"] += 1
                    logger.error(e)
                    continue

        except Exception as e:
            raise

        finally:
            self.pipeline_stats["end_time"] = datetime.now().isoformat()

        return self.pipeline_stats
