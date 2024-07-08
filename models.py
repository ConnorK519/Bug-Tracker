from sqlalchemy.orm import relationship, DeclarativeBase, Mapped, mapped_column
from sqlalchemy import Integer, String, Text, ForeignKey, desc
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, timezone
from flask_login import UserMixin


class Base(DeclarativeBase):
    pass


db = SQLAlchemy(model_class=Base)


class Bug(db.Model):
    __tablename__ = "bugs"
    id: Mapped[int] = mapped_column(primary_key=True)
    project_id: Mapped[int] = mapped_column(Integer, ForeignKey("projects.id"))
    reporter_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"))
    title: Mapped[str] = mapped_column(String)
    description: Mapped[str] = mapped_column(Text, nullable=True)
    steps_to_recreate: Mapped[str] = mapped_column(Text, nullable=False)
    error_url: Mapped[str] = mapped_column(String)
    priority_level: Mapped[str] = mapped_column(String)
    status: Mapped[str] = mapped_column(String)
    date_posted: Mapped[datetime] = mapped_column(default=lambda: datetime.now(timezone.utc))
    project = relationship("Project", back_populates="bugs")
    reporter = relationship("User", back_populates="bugs_reported")


class Project(db.Model):
    __tablename__ = "projects"
    id: Mapped[int] = mapped_column(primary_key=True)
    manager_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"))
    title: Mapped[str] = mapped_column(String, unique=True)
    description: Mapped[str] = mapped_column(Text)
    languages_used: Mapped[str] = mapped_column(Text)
    frameworks_or_libraries: Mapped[str] = mapped_column(Text)
    hosted_url: Mapped[str] = mapped_column(String, nullable=True)
    repo_url: Mapped[str] = mapped_column(String, nullable=False)
    date_posted: Mapped[datetime] = mapped_column(default=lambda: datetime.now(timezone.utc))
    bugs = relationship("Bug", order_by=Bug.date_posted, back_populates="project", cascade="all,delete, delete-orphan")
    manager = relationship("User", back_populates="projects")


class User(UserMixin, db.Model):
    __tablename__ = "users"
    id: Mapped[int] = mapped_column(primary_key=True)
    username: Mapped[str] = mapped_column(String, unique=True)
    hashed_password: Mapped[str] = mapped_column(String)
    # user_bio: Mapped[str] = mapped_column(Text)
    # coding_languages: Mapped[str] = mapped_column(String)
    projects = relationship("Project", back_populates="manager", cascade="all,delete, delete-orphan")
    bugs_reported = relationship("Bug", back_populates="reporter", cascade="all,delete, delete-orphan")
