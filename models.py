from sqlalchemy.orm import relationship, DeclarativeBase, Mapped, mapped_column
from sqlalchemy import Integer, String, Text, ForeignKey, Boolean
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
    project_roles = relationship("UserRole", back_populates="project", cascade="all,delete, delete-orphan")
    bugs = relationship("Bug", order_by=Bug.date_posted, back_populates="project", cascade="all,delete, delete-orphan")
    manager = relationship("User", back_populates="projects")


class User(UserMixin, db.Model):
    __tablename__ = "users"
    id: Mapped[int] = mapped_column(primary_key=True)
    username: Mapped[str] = mapped_column(String, unique=True)
    hashed_password: Mapped[str] = mapped_column(String)
    user_bio: Mapped[str] = mapped_column(Text)
    roles = relationship("UserRole", back_populates="user", cascade="all,delete, delete-orphan")
    projects = relationship("Project", back_populates="manager", cascade="all,delete, delete-orphan")
    bugs_reported = relationship("Bug", back_populates="reporter", cascade="all,delete, delete-orphan")


class Role(db.Model):
    __tablename__ = "roles"
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String, unique=True)
    update_status: Mapped[bool] = mapped_column(Boolean)
    update_priority: Mapped[bool] = mapped_column(Boolean)
    delete_bug: Mapped[bool] = mapped_column(Boolean)
    delete_members_from_project: Mapped[bool] = mapped_column(Boolean)


class UserRole(db.Model):
    __tablename__ = "user_roles"
    id: Mapped[int] = mapped_column(primary_key=True)
    role_id: Mapped[int] = mapped_column(Integer, ForeignKey("roles.id"))
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"))
    project_id: Mapped[int] = mapped_column(Integer, ForeignKey("projects.id"))
    role = relationship("Role", backref="role")
    project = relationship("Project", back_populates="project_roles")
    user = relationship("User", back_populates="roles")
    has_accepted: Mapped[bool] = mapped_column(Boolean, default=False)
