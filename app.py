from flask import Flask, render_template, redirect, url_for
from flask_login import login_user, LoginManager, current_user, logout_user, login_required
from werkzeug.security import generate_password_hash, check_password_hash
from sqlalchemy import desc
from forms import RegisterForm, LoginForm, SearchForm, PostProjectForm, PostBugForm
from datetime import datetime
from models import db, Bug, Project, User, Role, UserRole
from dotenv import load_dotenv
import os

load_dotenv(".env.dev")

app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY')
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('SQLALCHEMY_DATABASE_URI')
db.init_app(app)

login_manager = LoginManager()
login_manager.init_app(app)


@login_manager.user_loader
def load_user(user_id):
    return db.get_or_404(User, user_id)


with app.app_context():
    db.create_all()
    roles = db.session.execute(db.select(Role)).scalars().all()
    if not len(roles):
        roles = [
            Role(name="tester", update_status=False, update_priority=False, delete_bug=False,
                 delete_members_from_project=False),
            Role(name="developer", update_status=True, update_priority=False, delete_bug=False,
                 delete_members_from_project=False),
            Role(name="admin", update_status=True, update_priority=True, delete_bug=True,
                 delete_members_from_project=True)
        ]
        db.session.add_all(roles)
        db.session.commit()


@app.route("/", methods=["GET", "POST"])
def home_page():
    form = SearchForm()
    if form.validate_on_submit():
        search = f"%{form.search.data}%"
        return redirect(url_for("search_projects", search=search))
    projects = db.session.execute(db.select(Project).order_by(desc(Project.date_posted))).scalars().all()
    is_projects = False
    if len(projects):
        is_projects = True
    return render_template("index.html", form=form, projects=projects, is_projects=is_projects)


# ----------------------------------------------------------------------------------------------

# User endpoints

# ----------------------------------------------------------------------------------------------


@app.route("/users", methods=["GET", "POST"])
@login_required
def get_users():
    users = db.session.execute(db.select(User.id, User.username, User.user_bio)).scalars().all()


@app.route("/register", methods=["GET", "POST"])
def register():
    form = RegisterForm()
    if form.validate_on_submit():
        username = form.username.data
        user = db.session.execute(db.select(User).where(User.username == username)).scalar()
        password = form.password.data
        re_enter_pass = form.re_enter_pass.data
        if user:
            return redirect(url_for("register"))
        if password != re_enter_pass:
            return redirect(url_for("register"))
        hashed_password = generate_password_hash(password)
        new_user = User(username=username, user_bio=form.user_bio.data, hashed_password=hashed_password)
        db.session.add(new_user)
        db.session.commit()
        login_user(new_user)
        return redirect(url_for("home_page"))
    return render_template("register.html", form=form)


@app.route("/user/update-account", methods=["GET", "POST"])
@login_required
def update_user():
    form = RegisterForm()
    original_name = current_user.username
    if form.validate_on_submit():
        if original_name != form.username.data:
            existing_user = db.session.execute(db.select(User).where(User.username == form.username.data)).scalar()
            if existing_user:
                return redirect(url_for("update_user"))
            current_user.username = form.username.data
            current_user.user_bio = form.user_bio.data
        if form.password.data != form.re_enter_pass.data:
            return redirect(url_for("update_user"))
        if form.password.data:
            hashed_password = generate_password_hash(form.password.data)
            current_user.hashed_password = hashed_password
        db.session.commit()
        return redirect(url_for("home_page"))
    form.username.data = current_user.username
    form.user_bio.data = current_user.user_bio
    return render_template("update_user.html", form=form)


@app.route("/login", methods=["GET", "POST"])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        username = form.username.data
        password = form.password.data
        user = db.session.execute(db.select(User).where(User.username == username)).scalar()
        if user:
            if check_password_hash(user.hashed_password, password):
                login_user(user)
                return redirect(url_for("home_page"))
        return redirect(url_for("login"))
    return render_template("login.html", form=form)


@app.route("/reports")
@login_required
def reports_by_user_id():
    reports = current_user.bugs_reported
    has_reported = False
    if len(reports):
        has_reported = True
    return render_template("reports.html", reports=reports, has_reported=has_reported)


@app.route("/projects")
@login_required
def projects_by_user_id():
    projects = current_user.projects
    is_projects = False
    if len(projects):
        is_projects = True
    return render_template("projects.html", projects=projects, is_projects=is_projects)


@app.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for("home_page"))


@app.route("/user/delete-account")
@login_required
def delete_user():
    user = current_user
    db.session.delete(user)
    db.session.commit()
    logout_user()
    return redirect(url_for("home_page"))


# ----------------------------------------------------------------------------------------------

# Project endpoints

# ----------------------------------------------------------------------------------------------


@app.route("/search-projects/<search>", methods=["GET", "POST"])
def search_projects(search):
    form = SearchForm()
    projects = db.session.execute(
        db.select(Project).where(Project.title.like(search) | Project.description.like(search)).order_by(
            desc(Project.date_posted))).scalars().all()
    is_projects = False
    if len(projects):
        is_projects = True
    return render_template("index.html", form=form, projects=projects, is_projects=is_projects)


@app.route("/project/<int:project_id>", methods=["GET", "POST"])
def project_page(project_id):
    form = SearchForm()
    if form.validate_on_submit():
        search = form.search.data
        return redirect(url_for("project_page_search", project_id=project_id, search=search))
    project = db.get_or_404(Project, project_id)
    languages_used = project.languages_used.split("~|,-%-,|~")
    frameworks_or_libraries = project.frameworks_or_libraries.split("~|,-%-,|~")
    return render_template("project_page.html", project=project, languages_used=languages_used,
                           frameworks_or_libraries=frameworks_or_libraries, form=form)


@app.route("/projects/add-new-project", methods=["GET", "POST"])
@login_required
def post_project():
    form = PostProjectForm()
    if form.validate_on_submit():
        manager_id = current_user.id
        title = form.title.data
        description = form.description.data
        languages_used = "~|,-%-,|~".join(form.languages_used.data)
        frameworks_or_libraries = "~|,-%-,|~".join(form.frameworks_or_libraries.data)
        hosted_url = form.hosted_url.data
        repo_url = form.repo_url.data
        date_posted = datetime.now().date()
        existing_project = db.session.execute(db.select(Project).where(Project.title == title)).scalar()
        if existing_project:
            return render_template("new_project.html", form=form)
        new_project = Project(manager_id=manager_id, title=title, description=description,
                              languages_used=languages_used, frameworks_or_libraries=frameworks_or_libraries,
                              hosted_url=hosted_url,
                              repo_url=repo_url, date_posted=date_posted)
        db.session.add(new_project)
        db.session.commit()
        return redirect(url_for("home_page"))
    return render_template("new_project.html", form=form)


@app.route("/project/<int:project_id>/update", methods=["GET", "POST"])
@login_required
def update_project(project_id):
    form = PostProjectForm()
    project_to_update = db.get_or_404(Project, project_id)
    original_name = project_to_update.title
    if form.validate_on_submit():
        if original_name != form.title.data:
            existing_project = db.session.execute(db.select(Project).where(Project.title == form.title.data)).scalar()
            if existing_project:
                return redirect(url_for("update_project", project_id=project_id))
        project_to_update.title = form.title.data
        project_to_update.description = form.description.data
        project_to_update.languages_used = "~|,-%-,|~".join(form.languages_used.data)
        project_to_update.frameworks_or_libraries = "~|,-%-,|~".join(form.frameworks_or_libraries.data)
        project_to_update.hosted_url = form.hosted_url.data
        project_to_update.repo_url = form.repo_url.data
        db.session.commit()
        return redirect(url_for("project_page", project_id=project_id))
    form.title.data = project_to_update.title
    form.description.data = project_to_update.description
    form.hosted_url.data = project_to_update.hosted_url
    form.repo_url.data = project_to_update.repo_url
    return render_template("update_project.html", project_id=project_id, form=form)


@app.route("/delete-project/<int:project_id>")
@login_required
def delete_project_by_id(project_id):
    project_to_delete = db.get_or_404(Project, project_id)
    if current_user.id == project_to_delete.manager_id:
        db.session.delete(project_to_delete)
        db.session.commit()
        return redirect(url_for("home_page"))


# ----------------------------------------------------------------------------------------------

# Bug endpoints

# ----------------------------------------------------------------------------------------------

@app.route("/project/<int:project_id>/<search>")
def project_page_search(project_id, search):
    form = SearchForm()
    project = db.get_or_404(Project, project_id)
    bugs = [bug for bug in project.bugs if search in bug.title or search in bug.description]
    project.bugs = bugs
    return render_template("project_page.html", project=project, form=form)


@app.route("/projects/<project_id>/post-bug", methods=["GET", "POST"])
@login_required
def post_bug(project_id):
    form = PostBugForm()
    if form.validate_on_submit():
        reporter_id = current_user.id
        title = form.title.data
        description = form.description.data
        steps_to_recreate = form.steps_to_recreate.data
        error_url = form.error_url.data
        priority_level = "Not yet assigned"
        status = "pending"
        date_posted = datetime.now().date()
        new_bug = Bug(project_id=project_id, reporter_id=reporter_id, title=title, description=description,
                      steps_to_recreate=steps_to_recreate, error_url=error_url, priority_level=priority_level,
                      status=status, date_posted=date_posted)
        db.session.add(new_bug)
        db.session.commit()
        return redirect(url_for("project_page", project_id=project_id))
    return render_template("new_bug.html", form=form, project_id=project_id)


@app.route("/bug/<int:bug_id>/update", methods=["GET", "POST"])
@login_required
def update_bug(bug_id):
    form = PostBugForm()
    bug_to_update = db.get_or_404(Bug, bug_id)
    if form.validate_on_submit():
        bug_to_update.title = form.title.data
        bug_to_update.description = form.description.data
        bug_to_update.steps_to_reproduce = form.steps_to_recreate.data
        bug_to_update.error_url = form.error_url.data
        db.session.commit()
        return redirect(url_for("project_page", project_id=bug_to_update.project_id))
    form.title.data = bug_to_update.title
    form.description.data = bug_to_update.description
    form.steps_to_recreate.data = bug_to_update.steps_to_recreate
    form.error_url.data = bug_to_update.error_url
    return render_template("update_bug.html", bug_id=bug_id, form=form)


@app.route("/delete-bug/<int:bug_id>")
@login_required
def delete_bug_by_id(bug_id):
    bug_to_delete = db.get_or_404(Bug, bug_id)
    project_id = bug_to_delete.project.id
    if current_user.id == bug_to_delete.reporter_id or current_user.id == bug_to_delete.project.manager_id:
        db.session.delete(bug_to_delete)
        db.session.commit()
        return redirect(url_for("project_page", project_id=project_id))


if __name__ == '__main__':
    app.run(debug=True)
