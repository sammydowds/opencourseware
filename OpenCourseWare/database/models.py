from sqlalchemy import Column, Integer, String, Text, DateTime, JSON, ForeignKey
from sqlalchemy.orm import DeclarativeBase, Session, relationship
from datetime import datetime


class Base(DeclarativeBase):
    pass


class Course(Base):
    __tablename__ = "course"

    id = Column(Integer, primary_key=True)
    title = Column(Text, nullable=False)
    url = Column(Text, nullable=False)
    download_url = Column(Text, nullable=False)
    description = Column(Text, nullable=False)
    topics = Column(JSON)
    level = Column(JSON)
    learning_resource_types = Column(JSON)
    year = Column(String(10), nullable=False)
    term = Column(String(10), nullable=False)
    course_number = Column(Text, nullable=False, unique=True)
    problem_sets = relationship(
        "ProblemSet", back_populates="course", cascade="all, delete-orphan"
    )
    lectures = relationship(
        "Lecture", back_populates="course", cascade="all, delete-orphan"
    )
    readings = relationship(
        "Reading", back_populates="course", cascade="all, delete-orphan"
    )

    @classmethod
    def create(
        cls,
        db: Session,
        title: str,
        description: str,
        level: str,
        term: str,
        topics: any,
        learning_resource_types: any,
        year: str,
        url: str,
        download_url: str,
        course_number: str,
    ) -> "ProblemSet":
        """
        Create a new ProblemSet and save to database
        """

        course = cls(
            title=title,
            description=description,
            level=level,
            topics=topics,
            learning_resource_types=learning_resource_types,
            year=year,
            term=term,
            url=url,
            download_url=download_url,
            course_number=course_number,
        )

        db.add(course)
        db.commit()
        db.refresh(course)
        return course


class ProblemSet(Base):
    __tablename__ = "problem_set"

    id = Column(Integer, primary_key=True)
    problem_text = Column(Text, nullable=False)
    solution_text = Column(Text, nullable=False)
    remote_problem_url = Column(Text, nullable=False)
    remote_solution_url = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    course_id = Column(Integer, ForeignKey("course.id"), nullable=False)
    course = relationship("Course", back_populates="problem_sets")
    character_count = Column(Integer, nullable=False)

    def __repr__(self):
        return f"<ProblemSet(id={self.id}, title='{self.title}')>"

    @classmethod
    def create(
        cls,
        db: Session,
        course_id: str,
        problem_text: str,
        solution_text: str,
        remote_problem_url: str,
        remote_solution_url: str,
        character_count: int
    ) -> "ProblemSet":
        """
        Create a new ProblemSet and save to database
        """
        problem_set = cls(
            course_id=course_id,
            problem_text=problem_text,
            solution_text=solution_text,
            remote_problem_url=remote_problem_url,
            remote_solution_url=remote_solution_url,
            character_count=character_count
        )

        db.add(problem_set)
        db.commit()
        db.refresh(problem_set)
        return problem_set

class Lecture(Base):
    __tablename__ = "lecture"

    id = Column(Integer, primary_key=True)
    llm_text = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    remote_url = Column(Text, nullable=False)
    course_id = Column(Integer, ForeignKey("course.id"), nullable=False)
    course = relationship("Course", back_populates="lectures")
    character_count = Column(Integer, nullable=False)

    def __repr__(self):
        return f"<Lecture(id={self.id}, course_id='{self.course_id}')>"

    @classmethod
    def create(
        cls,
        db: Session,
        course_id: str,
        llm_text: str,
        remote_url: str,
        character_count: int,
    ) -> "Lecture":
        """
        Create a new Lecture and save to database
        """
        lecture = cls(
            course_id=course_id,
            llm_text=llm_text,
            remote_url=remote_url,
            character_count=character_count
        )

        db.add(lecture)
        db.commit()
        db.refresh(lecture)
        return lecture 

class Reading(Base):
    __tablename__ = "reading"

    id = Column(Integer, primary_key=True)
    llm_text = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    remote_url = Column(Text, nullable=False)
    course_id = Column(Integer, ForeignKey("course.id"), nullable=False)
    course = relationship("Course", back_populates="readings")
    character_count = Column(Integer, nullable=False)

    def __repr__(self):
        return f"<Reading(id={self.id}, course_id='{self.course_id}')>"

    @classmethod
    def create(
        cls,
        db: Session,
        course_id: str,
        llm_text: str,
        remote_url: str,
        character_count: int,
    ) -> "Reading":
        """
        Create a new Reading and save to database
        """
        reading = cls(
            course_id=course_id,
            llm_text=llm_text,
            remote_url=remote_url,
            character_count=character_count,
        )

        db.add(reading)
        db.commit()
        db.refresh(reading)
        return reading 
