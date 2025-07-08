import json
import re
from typing import List, Optional, Tuple
import requests
import zipfile
from pathlib import Path
import glob
from extract_pdf import extract_pdf
import os
import shutil
from database.models import Course, ProblemSet, Lecture, Reading
import logging
from database.session import Session
import fitz


class CourseContext:
    def __init__(self, download_url: str, url: str, db_session: Optional[any] = None):
        self.id = None
        self.url = url
        self.slug = url.split('/')[-1]
        self.download_url = download_url
        self.corpus_path = Path.cwd().joinpath("corpus")
        self.corpus_static_resources = self.corpus_path.joinpath("static_resources")
        self.title = None
        self.course_number = None
        self.description = None
        self.year = None
        self.level = None
        self.term = None
        self.instructors = None
        self.topics = None
        self.learning_resource_types = None
        self.readings_filenames = []  
        self.lecture_filenames = []  
        self.problem_set_filenames = []  
        self.problem_set_batches = []   # (problem_filename, sol_filename)
        self._zip_file_name = "download.zip"
        self._zip_path = self.corpus_path / self._zip_file_name
        self.session = db_session or Session()
        self.logger = logging.getLogger("course_context")
        self.out_dir = Path.cwd().joinpath("out")
        self.out_course_dir = self.out_dir.joinpath(self.slug)
        
        # init dirs
        self.corpus_path.mkdir(exist_ok=True)
        self.out_dir.mkdir(exist_ok=True) 
        self.out_course_dir.mkdir(exist_ok=True)

    def _clear_corpus(self):
        for filename in os.listdir(self.corpus_path):
            file_path = os.path.join(self.corpus_path, filename)
            if os.path.isfile(file_path) or os.path.islink(file_path):
                os.unlink(file_path)
            elif os.path.isdir(file_path):
                shutil.rmtree(file_path)
    
    def _clear_course_out_dir(self):
        for filename in os.listdir(self.out_course_dir):
            file_path = os.path.join(self.out_course_dir, filename)
            if os.path.isfile(file_path) or os.path.islink(file_path):
                os.unlink(file_path)
            elif os.path.isdir(file_path):
                shutil.rmtree(file_path)

    def get_remote_path(self, filename: str) -> str:
        """Construct remote path to file"""

        # as of 7/7/25 resources are just extended off of the course home page
        return str(Path(self.url).joinpath(filename))

    def load(self):
        """Downloads and contextualizes the OpenCourseWare course."""
        self._clear_corpus()
        self._download()
        self.contextualize()

    def contextualize(self):
        """Populate course data from corpus"""
        self._get_course_info()
        self._get_assignments()
        self._batch_problem_sets()
        self._get_lectures()
        self._get_readings()

    def extract_all(self):
        """Extract and save course and all data associated to the database"""
        self.load()
        self.save_course()
        self.extract_problem_sets()
        self.extract_lectures()
        self.extract_readings()
        self.extract_all_as_pdf()

    def extracl_all_to_db(self):
        """Extract all data to the db"""
        self.load()
        self.save_course()
        self.extract_problem_sets()
        self.extract_lectures()
        self.extract_readings()

    def extract_all_as_pdf(self):
        """Runs all pdf extractions"""
        self.extract_lectures_pdf()
        self.extract_problem_sets_pdf()
        self.extract_readings_pdf()

    def extract_problem_sets(self):
        """Extract problem sets and saves them to the db"""
        for batch in self.problem_set_batches:
            self._process_problem_set_batch(batch)

    def _process_problem_set_batch(self, batch: tuple):
        "Construct and save problem set batch"
        hw_file, sol_file = batch
        raw_problem_text = self.read_corpus_static_resource_file(hw_file)
        raw_solution_text = self.read_corpus_static_resource_file(
            sol_file
        )
        remote_problem_path = self.get_remote_path(hw_file)
        remote_solution_path = self.get_remote_path(sol_file)

        self._save_problem_set(
            raw_problem_text=raw_problem_text,
            raw_solution_text=raw_solution_text,
            remote_problem_path=remote_problem_path,
            remote_solution_path=remote_solution_path,
        )
    
    def extract_lectures(self):
        """Extract lecture text and save to db"""
        for lecture in self.lecture_filenames:
            llm_text = self.read_corpus_static_resource_file(lecture)
            try:
                lecture = Lecture.create(
                    db=self.session,
                    course_id=self.id,
                    llm_text=llm_text,
                    remote_url=self.get_remote_path(lecture),
                    character_count=len(llm_text)
                )
                if lecture.id:
                    self.logger.info("saved lecture, %s", lecture)
            except Exception as e:
                self.logger.error("error saving lecture, %s", lecture, exc_info=e)
    
    def extract_readings(self):
        """Extract readings text and save to db"""
        for reading in self.readings_filenames:
            llm_text = self.read_corpus_static_resource_file(reading)
            try:
                reading = Reading.create(
                    db=self.session,
                    course_id=self.id,
                    llm_text=llm_text,
                    remote_url=self.get_remote_path(reading),
                    character_count=len(llm_text)
                )
                if reading.id:
                    self.logger.info("saved readings, %s", reading)
            except Exception as e:
                self.logger.error("error saving readings, %s", reading, exc_info=e)

    def extract_readings(self):
        """Extract readings text and save to db"""
        for reading in self.readings_filenames:
            llm_text = self.read_corpus_static_resource_file(reading)
            try:
                reading = Reading.create(
                    db=self.session,
                    course_id=self.id,
                    llm_text=llm_text,
                    remote_url=self.get_remote_path(reading),
                    character_count=len(llm_text)
                )
                if reading.id:
                    self.logger.info("saved reading, %s", reading)
            except Exception as e:
                self.logger.error("error saving reading, %s", reading, exc_info=e)

    def _save_problem_set(
        self,
        raw_problem_text: str,
        raw_solution_text: str,
        remote_problem_path: str,
        remote_solution_path: str,
    ):
        if not self.id:
            self.logger.error(
                "Course has not been persisted to database. Please save course before creating problem sets."
            )

        ps = None
        try:
            ps = ProblemSet.create(
                self.session,
                course_id=self.id,
                problem_text=raw_problem_text,
                solution_text=raw_solution_text,
                remote_problem_url=remote_problem_path,
                remote_solution_url=remote_solution_path,
                character_count=len(raw_problem_text + raw_solution_text)
            )
        except Exception as e:
            self.logger.error(e)

        if ps:
            self.logger.info(
                "Successfully saved problem set, %s", ps.id
            )
            self.saved_ps = ps

    def save_course(self):
        """Persist course to database."""
        if not self.id:
            course = Course.create(
                db=self.session,
                course_number=self.course_number,
                title=self.title,
                description=self.description,
                topics=self.topics,
                level=self.level,
                year=self.year,
                term=self.term,
                url=self.url,
                download_url=self.download_url,
                learning_resource_types=self.learning_resource_types,
            )

            if course.id:
                self.id = course.id
                self.logger.info("saved course, id: %s", self.id)

    def _get_course_info(self):
        info_target = self.corpus_path / "data.json"
        if os.path.exists(info_target):
            course_data = json.loads(self.read_corpus_file("data.json"))
            self.title = course_data.get("course_title")
            self.description = course_data.get("course_description")
            self.year = course_data.get("year")
            self.level = course_data.get("level")[0]
            self.topics = course_data.get("topics")
            self.course_number = course_data.get("primary_course_number")
            self.term = course_data.get("term")
            self.instructors = course_data.get("instructors")
            self.learning_resource_types = course_data.get("learning_resource_types")

            self.logger.info("course info extracted for %s", self.title)

        else:
            raise Exception(
                f"Course is lacking root level data.json - cannot process this course: {self.url}"
            )

    def _download(self):
        """Download course resources from download url (.zip format)"""
        if not self.download_url:
            raise ValueError("No download URL provided")

        try:
            self._download_zip_file()
            self._extract_zip_file()

        except Exception as e:
            raise Exception(f"Failed to download course: {e}")

    def _download_zip_file(self) -> Path:
        """Download the zip file from the URL"""
        response = requests.get(self.download_url, stream=True, timeout=30)
        response.raise_for_status()

        with open(self._zip_path, "wb") as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)

    def _extract_zip_file(self) -> Path:
        """Extract the downloaded zip file"""
        try:
            with zipfile.ZipFile(self._zip_path, "r") as zip_ref:
                zip_ref.extractall(self.corpus_path)
                self.logger.info(
                    "extracted course data for %s to local corpus",
                    self.download_url,
                )

        except zipfile.BadZipFile:
            raise Exception("Downloaded file is not a valid zip file")
        except Exception as e:
            raise Exception(f"Failed to extract zip file: {e}")

    def _get_assignments(self):
        """Get assignment file paths by filtering through data.json files"""
        assignments = []
        if not self.corpus_path or not self.corpus_path.exists():
            return []

        pattern = f"{self.corpus_path}/resources/**/data.json"
        json_files = glob.glob(pattern, recursive=True)
        if not json_files:
            raise Exception("No files found when looking up assignment data.json")

        try:
            for json_file in json_files:
                data = None
                with open(json_file, "r", encoding="utf-8") as f:
                    data = json.load(f)

                if "Assignments" in data.get("learning_resource_types", []):
                    if "file" in data and data["file"] and ".pdf" in data["file"]:
                        path = data["file"]
                        file_name = path.split("/")[-1]
                        assignments.append(file_name)

            self.problem_set_filenames = assignments
            self.logger.info(
                "found %s assignments", len(self.problem_set_filenames)
            )
        except Exception as e:
            self.logger.error("_get_assignements failed", exc_info=e)
    
    def _get_lectures(self):
        """Get lecture file paths by filtering through data.json files"""
        lectures = []
        if not self.corpus_path or not self.corpus_path.exists():
            return []

        pattern = f"{self.corpus_path}/resources/**/data.json"
        json_files = glob.glob(pattern, recursive=True)
        if not json_files:
            raise Exception("No files found when looking up assignment data.json")

        try:
            for json_file in json_files:
                data = None
                with open(json_file, "r", encoding="utf-8") as f:
                    data = json.load(f)

                if "Lecture Notes" in data.get("learning_resource_types", []):
                    if "file" in data and data["file"] and ".pdf" in data["file"]:
                        path = data["file"]
                        file_name = path.split("/")[-1]
                        lectures.append(file_name)

            self.lecture_filenames = lectures 
            self.logger.info(
                "found %s lecture notes", len(self.lecture_filenames)
            )
        except Exception as e:
            self.logger.error("_get_lectures failed", exc_info=e)
    
    def _get_readings(self):
        """Get readings file paths by filtering through data.json files"""
        readings = []
        if not self.corpus_path or not self.corpus_path.exists():
            return []

        pattern = f"{self.corpus_path}/resources/**/data.json"
        json_files = glob.glob(pattern, recursive=True)
        if not json_files:
            raise Exception("No files found when looking up reading data.json")

        try:
            for json_file in json_files:
                data = None
                with open(json_file, "r", encoding="utf-8") as f:
                    data = json.load(f)

                if "Readings" in data.get("learning_resource_types", []):
                    if "file" in data and data["file"] and ".pdf" in data["file"]:
                        path = data["file"]
                        file_name = path.split("/")[-1]
                        readings.append(file_name)

            self.readings_filenames = readings 
            self.logger.info(
                "found %s readings", len(self.readings_filenames)
            )
        except Exception as e:
            self.logger.error("_get_readings failed", exc_info=e)

    def extract_lectures_pdf(self):
        """Extract all lectures into one pdf"""
        if not self.lecture_filenames:
            self.logger.warning("no lecture filenames to process for extracting into a pdf")
            return

        filename = "combined_lectures.pdf"
        path = self.out_course_dir / filename 
        combined_doc = fitz.open()
        
        try:
            for lecture_filename in self.lecture_filenames:
                lecture_path = self.corpus_static_resources / lecture_filename
                
                if not lecture_path.exists():
                    self.logger.warning(f"Lecture file not found: {lecture_path}")
                    continue
                
                try:
                    lecture_doc = fitz.open(str(lecture_path))
                    combined_doc.insert_pdf(lecture_doc)
                    lecture_doc.close()
                    self.logger.info(f"Added lecture {lecture_filename} to combined PDF")
                    
                except Exception as e:
                    self.logger.error(f"Failed to process lecture {lecture_filename}: {e}")
                    continue
            
            combined_doc.save(str(path))
            combined_doc.close()
            
            self.logger.info(f"Combined lectures saved to: {path}")
            
        except Exception as e:
            self.logger.error(f"Failed to create combined lectures PDF: {e}")
            combined_doc.close()
            raise

    def extract_readings_pdf(self):
        """Extract all readings into one pdf"""
        if not self.readings_filenames:
            self.logger.warning("no readings filenames to process for extracting into a pdf")
            return

        filename = "combined_readings.pdf"
        path = self.out_course_dir / filename 
        combined_doc = fitz.open()
        
        try:
            for reading in self.readings_filenames:
                lecture_path = self.corpus_static_resources / reading 
                
                if not lecture_path.exists():
                    self.logger.warning(f"Reading file not found: {lecture_path}")
                    continue
                
                try:
                    lecture_doc = fitz.open(str(lecture_path))
                    combined_doc.insert_pdf(lecture_doc)
                    lecture_doc.close()
                    self.logger.info(f"Added reading {reading} to combined PDF")
                    
                except Exception as e:
                    self.logger.error(f"Failed to process reading {reading}: {e}")
                    continue
            
            combined_doc.save(str(path))
            combined_doc.close()
            
            self.logger.info(f"Combined readings saved to: {path}")
            
        except Exception as e:
            self.logger.error(f"Failed to create combined readings PDF: {e}")
            combined_doc.close()
            raise

    def extract_problem_sets_pdf(self):
        """Extract all problem sets into combined PDFs"""
        if not self.problem_set_batches:
            self.logger.warning("no problem set batches to process for extracting into PDFs")
            return

        combined_paths = []
        for i, batch in enumerate(self.problem_set_batches):
            hw_file, sol_file = batch
            
            batch_num = str(i + 1).zfill(2)
            filename = f"problem_set_{batch_num}.pdf"
            path = self.out_course_dir / filename
            combined_doc = fitz.open()
            
            try:
                # problem file
                hw_path = self.corpus_static_resources / hw_file
                if hw_path.exists():
                    try:
                        hw_doc = fitz.open(str(hw_path))
                        combined_doc.insert_pdf(hw_doc)
                        hw_doc.close()
                        self.logger.info(f"Added problem file {hw_file} to batch {batch_num}")
                    except Exception as e:
                        self.logger.error(f"Failed to process problem file {hw_file}: {e}")
                else:
                    self.logger.warning(f"Problem file not found: {hw_path}")
                
                # solution file 
                sol_path = self.corpus_static_resources / sol_file
                if sol_path.exists():
                    try:
                        sol_doc = fitz.open(str(sol_path))
                        combined_doc.insert_pdf(sol_doc)
                        sol_doc.close()
                        self.logger.info(f"Added solution file {sol_file} to batch {batch_num}")
                    except Exception as e:
                        self.logger.error(f"Failed to process solution file {sol_file}: {e}")
                else:
                    self.logger.warning(f"Solution file not found: {sol_path}")
                
                combined_doc.save(str(path))
                combined_doc.close()
                
                combined_paths.append(str(path))
                self.logger.info(f"Problem set batch {batch_num} saved to: {path}")
                
            except Exception as e:
                self.logger.error(f"Failed to create problem set batch {batch_num} PDF: {e}")
                combined_doc.close()
                continue
        
        self.logger.info(f"Created {len(combined_paths)} problem set PDFs")
        return combined_paths

    def read_corpus_static_resource_file(self, file_name: str):
        target = self.corpus_static_resources.joinpath(file_name)
        max_lines = 10000

        if not target.exists():
            raise Exception(f"file does not exist: {target}")

        file_text = ""
        if target.suffix.lower() == ".json":
            with open(target, "r", encoding="utf-8") as f:
                data = json.load(f)
                file_text = json.dumps(data, indent=2)

        elif target.suffix.lower() == ".pdf":
            text = extract_pdf(str(target))
            return text

        else:
            with open(target, "r", encoding="utf-8") as f:
                lines = f.readlines()
                if len(lines) > max_lines:
                    file_text = "".join(lines[:max_lines])
                    file_text += f"\n... (truncated at {max_lines} lines)"
                else:
                    file_text = "".join(lines)

        return file_text

    def read_corpus_file(self, path: str):
        target = self.corpus_path.joinpath(path)
        max_lines = 10000

        if not target.exists():
            raise Exception(f"file does not exist: {target}")

        file_text = ""
        if target.suffix.lower() == ".json":
            with open(target, "r", encoding="utf-8") as f:
                data = json.load(f)
                file_text = json.dumps(data, indent=2)

        elif target.suffix.lower() == ".pdf":
            text = extract_pdf(str(target))
            return text

        else:
            with open(target, "r", encoding="utf-8") as f:
                lines = f.readlines()
                if len(lines) > max_lines:
                    file_text = "".join(lines[:max_lines])
                    file_text += f"\n... (truncated at {max_lines} lines)"
                else:
                    file_text = "".join(lines)

        return file_text

    def _batch_problem_sets(self):
        if not self.problem_set_filenames:
            self.logger.info("no assignments to batch.")
            return

        hw_map = {}
        sol_map = {}

        for path in self.problem_set_filenames:
            # problem / solution sets can be both of format sol _hwXX / _hwXX_sol and hwXX / solXX
            hw_match = re.search(r"hw(\d{1,2})(?!_soln?)\.pdf$", path)
            ps_match = re.search(r"ps(\d{1,2})(?!_soln?)\.pdf$", path)
            sol_match_inline = re.search(r"hw(\d{1,2})_soln?.*\.pdf$", path)
            sol_match_separate = re.search(r"soln?(\d{1,2}).*\.pdf$", path)

            if sol_match_inline:
                num = sol_match_inline.group(1).zfill(2)
                sol_map[num] = path
            elif sol_match_separate:
                num = sol_match_separate.group(1).zfill(2)
                sol_map[num] = path
            elif hw_match:
                num = hw_match.group(1).zfill(2)
                hw_map[num] = path
            elif ps_match:
                num = ps_match.group(1).zfill(2)
                hw_map[num] = path

        all_keys = sorted(set(hw_map.keys()) | set(sol_map.keys()))
        pairs: List[Tuple[str, str]] = []
        for key in all_keys:
            hw = hw_map.get(key)
            sol = sol_map.get(key)
            if hw and sol:
                pairs.append((hw, sol))

        self.problem_set_batches = pairs
        self.logger.info(
            "found %s problem solution sets",
            len(self.problem_set_batches),
        )
