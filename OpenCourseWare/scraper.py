import requests
import json
from bs4 import BeautifulSoup
import re
import time
from helpers import request_headers, create_request_payload, download_headers
import logging

class Scraper:
    def __init__(self):
        self.host = "https://ocw.mit.edu/"
        self.api_url = "https://open.mit.edu/api/v0/search/"
        self.urls = [] # (course_url, download_url)[]
        self.headers = request_headers
        self.download_headers = download_headers
        self.download_pages_scraped = 0
        self.logger = logging.getLogger("scraper")

    def scrape(
        self,
        department="Mechanical Engineering",
        size=100,
        delay=1,
    ):
        """
        Run the complete process: fetch courses and scrape download links

        Args:
            department (str): Department name to filter by
            size (int): Number of courses to fetch
            delay (int): Delay between scraping requests in seconds

        Returns:
            dict: Summary including timing information
        """
        start_time = time.time()
        results = self._fetch_courses_with_problem_sets(
            department=department, size=size
        )

        if not results:
            raise Exception("Fetching courses failed.")

        course_urls = self._extract_course_urls(results)
        if not course_urls:
            end_time = time.time()
            duration = end_time - start_time
            return {
                "success": False,
                "message": "No courses found",
                "course_urls": [],
                "download_data": [],
                "duration_seconds": duration,
                "duration_formatted": f"{duration:.2f}s",
            }

        self._scrape_download_links(
            course_urls=course_urls, delay=delay
        )

        end_time = time.time()
        duration = end_time - start_time
        self.logger.info("scraping complete - took %s secs", duration)

    def _fetch_courses_with_problem_sets(
        self, department="Mechanical Engineering", size=50
    ):
        """
        Fetch courses with problem sets from MIT OCW and return URLs

        Args:
            department (str): Department name to filter by
            size (int): Number of courses to fetch
            output_file (str): Optional output file path for JSON results

        Returns:
            list: List of course URLs
        """
        payload = create_request_payload()

        try:
            response = requests.post(
                self.api_url, headers=self.headers, data=json.dumps(payload)
            )

            if response.status_code == 200:
                data = response.json()
                return data
            else:
                raise Exception(f"Request failed: {response.status_code}")

        except Exception as e:
            return []

    def _extract_course_urls(self, response_data):
        """Extract course URLs from the API response"""
        urls = []

        if "hits" in response_data and "hits" in response_data["hits"]:
            hits = response_data["hits"]["hits"]
            for hit in hits:
                source = hit.get("_source", {})
                runs = source.get("runs", [])

                for run in runs:
                    slug = run.get("slug", "")
                    if slug:
                        full_url = f"{self.host}{slug}"
                        urls.append(full_url)
        self.logger.info("found %s course urls to scrape", len(urls))
        return urls

    def _scrape_download_links(self, course_urls=None, delay=1):
        """
        Scrape download links from course pages

        Args:
            course_urls (list): List of course URLs to scrape. If None, uses self.course_urls
            delay (int): Delay between requests in seconds
        Returns:
            list of urls
        """
        if not course_urls:
            return []

        download_zip_urls = []
        for i, course_url in enumerate(course_urls, 1):
            download_page = f"{course_url}/download"
            response = requests.get(
                download_page, headers=self.download_headers, timeout=10
            )

            if response.status_code == 200:
                self.download_pages_scraped += 1
                soup = BeautifulSoup(response.content, "html.parser")
                zip_download_url = self._extract_zip_download_link(soup, course_url)

                if zip_download_url:
                    download_zip_urls.append(zip_download_url)
                    self.urls.append((course_url, zip_download_url))
            else:
                raise Exception(
                    f"Bad response when looking up download page: {download_page}"
                )

            if delay > 0 and i < len(course_urls):
                time.sleep(delay)
        self.logger.info("found %s download urls", len(download_zip_urls))
        return download_zip_urls 

    def _extract_zip_download_link(self, soup, base_url):
        """
        Extract zip download link from the parsed HTML

        Args:
            soup: BeautifulSoup object
            base_url: Base URL for resolving relative links

        Returns:
            str: Full download URL or None if not found
        """
        potential_elements = soup.find_all(["a", "button"], href=True)
        for element in potential_elements:
            href = element.get("href", "")
            text = element.get_text(strip=True).lower()

            if ".zip" in href:
                if any(keyword in text for keyword in ["download", "course", "zip"]):
                    if href.startswith("http"):
                        return href
                    elif href.startswith("/"):
                        return f"https://ocw.mit.edu{href}"
                    else:
                        return f"{base_url}/{href}"

        download_elements = soup.find_all(
            text=re.compile(r"download.*course", re.IGNORECASE)
        )
        for element in download_elements:
            parent = element.parent
            if parent:
                zip_links = parent.find_all("a", href=re.compile(r"\.zip"))
                if zip_links:
                    href = zip_links[0].get("href")
                    if href.startswith("http"):
                        return href
                    elif href.startswith("/"):
                        return f"https://ocw.mit.edu{href}"
                    else:
                        return f"{base_url}/{href}"

        zip_links = soup.find_all("a", href=re.compile(r"\.zip"))
        if zip_links:
            href = zip_links[0].get("href")
            if href.startswith("http"):
                return href
            elif href.startswith("/"):
                return f"https://ocw.mit.edu{href}"
            else:
                return f"{base_url}/{href}"

        return None
