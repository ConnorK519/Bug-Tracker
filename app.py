from flask import Flask, render_template, redirect, url_for
from flask_login import login_user, LoginManager, current_user, logout_user, login_required
from werkzeug.security import generate_password_hash, check_password_hash
from sqlalchemy import desc, exc
from forms import RegisterForm, LoginForm, SearchForm, PostProjectForm, PostBugForm, InviteForm, BugStatusAndPriorityForm
from datetime import datetime
from models import db, Bug, Project, User, Role, UserRole
from dotenv import load_dotenv
import os

load_dotenv(".env.dev")

app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY')
app.config['SQLALCHEMY_DATABASE_URI'] = (f"{os.environ.get('SQLALCHEMY_DATABASE_URI')}?pool_pre_ping=true"
                                         f"&pool_recycle=300")
db.init_app(app)

login_manager = LoginManager()
login_manager.init_app(app)


@login_manager.user_loader
def load_user(user_id):
    return db.get_or_404(User, user_id)


with app.app_context():
    db.create_all()
    # inserts basic test users and default roles
    test_roles = db.session.execute(db.select(Role)).scalars().all()
    test_users = db.session.execute(db.select(User)).scalars().all()
    if not len(test_roles):
        test_roles = [
            Role(name="tester", update_status=False, update_priority=False, delete_bug=False,
                 delete_members_from_project=False),
            Role(name="developer", update_status=True, update_priority=False, delete_bug=False,
                 delete_members_from_project=False),
            Role(name="admin", update_status=True, update_priority=True, delete_bug=True,
                 delete_members_from_project=True)
        ]
        db.session.add_all(test_roles)
    if not len(test_users):
        test_users = [
            User(username="test-user-1", hashed_password=generate_password_hash("123"), user_bio="C++, Java"),
            User(username="test-user-2", hashed_password=generate_password_hash("123"),
                 user_bio="JavaScript, Rust"),
            User(username="test-user-3", hashed_password=generate_password_hash("123"),
                 user_bio="C#, Python"),
            User(username="test-user-4", hashed_password=generate_password_hash("123"),
                 user_bio="C#, Python"),
            User(username="test-user-5", hashed_password=generate_password_hash("123"),
                 user_bio="C#, Python")
        ]
        db.session.add_all(test_users)
    db.session.commit()


@app.route("/", methods=["GET", "POST"])
def home_page():
    try:
        form = SearchForm()
        if form.validate_on_submit():
            # adds wildcards for sql query to get all matches.
            search = f"%{form.search.data}%"
            # redirects to a search endpoint so the url including the search can be shared.
            return redirect(url_for("search_projects", search=search))
        projects = db.session.execute(db.select(Project).order_by(desc(Project.date_posted))).scalars().all()
        is_projects = False
        if len(projects):
            is_projects = True
        return render_template("index.html", form=form, projects=projects, is_projects=is_projects)
    except exc.IntegrityError:
        db.session.rollback()


# ----------------------------------------------------------------------------------------------

# User endpoints

# ----------------------------------------------------------------------------------------------


@app.route("/users/<int:project_id>", methods=["GET", "POST"])
@login_required
def invite_users_to_project(project_id):
    try:
        # checks the project exists
        project = db.get_or_404(Project, project_id)
        # blocks the users access if not permitted.
        if current_user.id != project.manager_id:
            return redirect(url_for("home_page"))
        # retrieves none sensitive user data where they are not currently invited or on the current project.
        users = db.session.execute(
            db.select(User.id, User.username, User.user_bio).where(User.id != current_user.id).where(
                ~User.roles.any(UserRole.project_id == project_id))).all()
        search_form = SearchForm()
        # sets up the hidden project_id field for each user's invite form.
        invite_form = InviteForm(project_id=project_id)
        if search_form.validate_on_submit():
            search = f"%{search_form.search.data}%"
            users = db.session.execute(
                db.select(User.id, User.username, User.user_bio).where(User.id != current_user.id).where(
                    User.username.like(search) | User.user_bio.like(search)).where(
                    ~User.roles.any(project_id == project_id))).all()
            return render_template("users.html", users=users, search_form=search_form, invite_form=invite_form,
                                   project_id=project_id)
        if invite_form.validate_on_submit():
            user_id = invite_form.user_id.data
            role_id = invite_form.role.data
            # checks the user still exists.
            user = db.get_or_404(User, user_id)
            invite = UserRole(user_id=user_id, role_id=role_id, project_id=project_id)
            db.session.add(invite)
            db.session.commit()
            return redirect(url_for("invite_users_to_project", project_id=project_id))
        return render_template("users.html", users=users, search_form=search_form, invite_form=invite_form,
                               project_id=project_id)
    except exc.IntegrityError:
        db.session.rollback()


@app.route("/register", methods=["GET", "POST"])
def register():
    try:
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
            # salts and hashes the password.
            hashed_password = generate_password_hash(password)
            new_user = User(username=username, user_bio=form.user_bio.data, hashed_password=hashed_password)
            db.session.add(new_user)
            db.session.commit()
            login_user(new_user)
            return redirect(url_for("home_page"))
        return render_template("register.html", form=form)
    except exc.IntegrityError:
        db.session.rollback()


@app.route("/user/update-account", methods=["GET", "POST"])
@login_required
def update_user():
    try:
        form = RegisterForm()
        original_name = current_user.username
        if form.validate_on_submit():
            # checks for change in the users name.
            if original_name != form.username.data:
                # checks if the new name is in use.
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
        # pre-populates the form fields.
        form.username.data = current_user.username
        form.user_bio.data = current_user.user_bio
        return render_template("update_user.html", form=form)
    except exc.IntegrityError:
        db.session.rollback()


@app.route("/login", methods=["GET", "POST"])
def login():
    try:
        form = LoginForm()
        if form.validate_on_submit():
            username = form.username.data
            password = form.password.data
            user = db.session.execute(db.select(User).where(User.username == username)).scalar()
            if user:
                # checks the provided pass against the stored hash.
                if check_password_hash(user.hashed_password, password):
                    login_user(user)
                    return redirect(url_for("home_page"))
            return redirect(url_for("login"))
        return render_template("login.html", form=form)
    except exc.IntegrityError:
        db.session.rollback()


@app.route("/reports")
@login_required
def reports_by_user_id():
    try:
        bugs = current_user.bugs_reported
        has_reported = False
        if len(bugs):
            has_reported = True
        return render_template("reports.html", bugs=bugs, has_reported=has_reported)
    except exc.IntegrityError:
        db.session.rollback()


@app.route("/projects")
@login_required
def projects_by_user_id():
    try:
        projects = current_user.projects
        is_projects = False
        if len(projects):
            is_projects = True
        return render_template("projects.html", projects=projects, is_projects=is_projects)
    except exc.IntegrityError:
        db.session.rollback()


@app.route("/logout")
@login_required
def logout():
    try:
        logout_user()
        return redirect(url_for("home_page"))
    except exc.IntegrityError:
        db.session.rollback()


@app.route("/user/delete-account")
@login_required
def delete_user():
    try:
        user = current_user
        # ensures the user is the owner of the account to delete.
        if current_user.id != user.id:
            return redirect(url_for("home_page"))
        db.session.delete(user)
        db.session.commit()
        logout_user()
        return redirect(url_for("home_page"))
    except exc.IntegrityError:
        db.session.rollback()


# ----------------------------------------------------------------------------------------------

# Project endpoints

# ----------------------------------------------------------------------------------------------


@app.route("/search-projects/<search>", methods=["GET", "POST"])
def search_projects(search):
    try:
        form = SearchForm()
        # uses the search to return relevant projects.
        projects = db.session.execute(
            db.select(Project).where(Project.title.like(search) | Project.description.like(search)).order_by(
                desc(Project.date_posted))).scalars().all()
        is_projects = False
        if len(projects):
            is_projects = True
        return render_template("index.html", form=form, projects=projects, is_projects=is_projects)
    except exc.IntegrityError:
        db.session.rollback()


@app.route("/project/<int:project_id>", methods=["GET", "POST"])
def project_page(project_id):
    try:
        form = SearchForm()
        bug_form = BugStatusAndPriorityForm()
        user_perms = None
        if current_user.is_authenticated:
            user_perms = db.session.execute(db.select(UserRole).where(
                (UserRole.project_id == project_id) & (UserRole.user_id == current_user.id) & (
                    UserRole.has_accepted))).scalar()
        if form.validate_on_submit():
            search = form.search.data
            return redirect(url_for("project_page_search", project_id=project_id, search=search))
        if bug_form.validate_on_submit():
            bug_id = bug_form.bug_id.data
            bug_to_update = db.get_or_404(Bug, bug_id)
            status = bug_form.status.data
            priority = bug_form.priority.data
            bug_to_update.status = status
            bug_to_update.priority_level = priority
            db.session.commit()
            return redirect(url_for("project_page", project_id=project_id))
        project = db.get_or_404(Project, project_id)
        # splits the string stored in the database back into a list for display.
        languages_used = project.languages_used.split("~|,-%-,|~")
        frameworks_or_libraries = project.frameworks_or_libraries.split("~|,-%-,|~")
        return render_template("project_page.html", project=project, languages_used=languages_used,
                               frameworks_or_libraries=frameworks_or_libraries, form=form, user_perms=user_perms, bug_form=bug_form)
    except exc.IntegrityError:
        db.session.rollback()


@app.route("/projects/add-new-project", methods=["GET", "POST"])
@login_required
def post_project():
    try:
        form = PostProjectForm()
        is_edit = False
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
            # checks if there is already a project with the provided title.
            if existing_project:
                return render_template("new_project.html", form=form)
            new_project = Project(manager_id=manager_id, title=title, description=description,
                                  languages_used=languages_used, frameworks_or_libraries=frameworks_or_libraries,
                                  hosted_url=hosted_url,
                                  repo_url=repo_url, date_posted=date_posted)
            db.session.add(new_project)
            db.session.commit()
            return redirect(url_for("home_page"))
        return render_template("new_project.html", form=form, is_edit=is_edit)
    except exc.IntegrityError:
        db.session.rollback()


@app.route("/project/<int:project_id>/update", methods=["GET", "POST"])
@login_required
def update_project(project_id):
    try:
        form = PostProjectForm()
        project_to_update = db.get_or_404(Project, project_id)
        original_name = project_to_update.title
        is_edit = True
        if current_user.id != project_to_update.manager_id:
            return redirect(url_for("home_page"))
        if form.validate_on_submit():
            # checks if there is a change in the project title.
            if original_name != form.title.data:
                existing_project = db.session.execute(
                    db.select(Project).where(Project.title == form.title.data)).scalar()
                # checks if there is already a project with the new title.
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
        # splits the string stored in the database back into a list to pre-populate to form fields.
        languages_used_list = project_to_update.languages_used.split("~|,-%-,|~")
        frameworks_or_libraries_list = project_to_update.frameworks_or_libraries.split("~|,-%-,|~")
        form.title.data = project_to_update.title
        form.description.data = project_to_update.description
        for num in range(3):
            form.languages_used[num].data = languages_used_list[num]
            form.frameworks_or_libraries[num].data = frameworks_or_libraries_list[num]
        form.hosted_url.data = project_to_update.hosted_url
        form.repo_url.data = project_to_update.repo_url
        return render_template("new_project.html", form=form, project_id=project_id, is_edit=is_edit)
    except exc.IntegrityError:
        db.session.rollback()


@app.route("/delete-project/<int:project_id>")
@login_required
def delete_project_by_id(project_id):
    try:
        project_to_delete = db.get_or_404(Project, project_id)
        # ensures only the project manager can delete the project.
        if current_user.id == project_to_delete.manager_id:
            db.session.delete(project_to_delete)
            db.session.commit()
            return redirect(url_for("home_page"))
    except exc.IntegrityError:
        db.session.rollback()


# ----------------------------------------------------------------------------------------------

# Bug endpoints

# ----------------------------------------------------------------------------------------------

@app.route("/project/<int:project_id>/<search>")
def project_page_search(project_id, search):
    try:
        form = SearchForm()
        bug_form = BugStatusAndPriorityForm()
        project = db.get_or_404(Project, project_id)
        user_perms = None
        if current_user.is_authenticated:
            user_perms = db.session.execute(db.select(UserRole).where(
                (UserRole.project_id == project_id) & (UserRole.user_id == current_user.id) & (
                    UserRole.has_accepted))).scalar()
        # filters the list of bugs by the search term.
        bugs = [bug for bug in project.bugs if search in bug.title or search in bug.description]
        project.bugs = bugs
        return render_template("project_page.html", project=project, form=form, user_perms=user_perms, bug_form=bug_form)
    except exc.IntegrityError:
        db.session.rollback()


@app.route("/projects/<int:project_id>/post-bug", methods=["GET", "POST"])
@login_required
def post_bug(project_id):
    try:
        form = PostBugForm()
        is_edit = False
        if form.validate_on_submit():
            reporter_id = current_user.id
            title = form.title.data
            description = form.description.data
            steps_to_recreate = form.steps_to_recreate.data
            error_url = form.error_url.data
            priority_level = "Not yet assigned"
            status = "Pending"
            date_posted = datetime.now().date()
            new_bug = Bug(project_id=project_id, reporter_id=reporter_id, title=title, description=description,
                          steps_to_recreate=steps_to_recreate, error_url=error_url, priority_level=priority_level,
                          status=status, date_posted=date_posted)
            db.session.add(new_bug)
            db.session.commit()
            return redirect(url_for("project_page", project_id=project_id))
        return render_template("new_bug.html", form=form, project_id=project_id, is_edit=is_edit)
    except exc.IntegrityError:
        db.session.rollback()


@app.route("/bug/<int:bug_id>/update", methods=["GET", "POST"])
@login_required
def update_bug(bug_id):
    try:
        form = PostBugForm()
        bug_to_update = db.get_or_404(Bug, bug_id)
        original_name = bug_to_update.title
        is_edit = True
        if current_user.id != bug_to_update.reporter_id:
            return redirect(url_for("home_page"))
        if form.validate_on_submit():
            # checks for change in the project title.
            if original_name != form.title.data:
                existing_project = db.session.execute(db.select(Bug).where(Bug.title == form.title.data)).scalar()
                # checks the new name is available.
                if existing_project:
                    return render_template("new_bug.html", bug_id=bug_id, form=form, is_edit=is_edit)
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
        return render_template("new_bug.html", bug_id=bug_id, form=form, is_edit=is_edit)
    except exc.IntegrityError:
        db.session.rollback()


@app.route("/delete-bug/<int:bug_id>")
@login_required
def delete_bug_by_id(bug_id):
    try:
        bug_to_delete = db.get_or_404(Bug, bug_id)
        project_id = bug_to_delete.project.id
        # gets the current users permissions for the project.
        user_perms = db.session.execute(db.select(UserRole).where(
            (UserRole.project_id == project_id) & (UserRole.user_id == current_user.id))).scalar()
        # ensures only the reporter of the bug or an authorised user can delete bugs.
        if current_user.id == bug_to_delete.reporter_id or current_user.id == bug_to_delete.project.manager_id or user_perms.role.delete_bug:
            db.session.delete(bug_to_delete)
            db.session.commit()
            return redirect(url_for("project_page", project_id=project_id))
    except exc.IntegrityError:
        db.session.rollback()


# ----------------------------------------------------------------------------------------------

# Role endpoints

# ----------------------------------------------------------------------------------------------


@app.route("/user/role-invites")
@login_required
def get_user_invites():
    try:
        # gets all current and pending roles for a user.
        invites = db.session.execute(db.select(UserRole).where(UserRole.user_id == current_user.id)).scalars().all()
        current_roles = [role for role in invites if role.has_accepted]
        pending_roles = [role for role in invites if not role.has_accepted]
        return render_template("invites.html", current_roles=current_roles, pending_roles=pending_roles)
    except exc.IntegrityError:
        db.session.rollback()


@app.route("/project/members/<int:project_id>")
@login_required
def get_project_members(project_id):
    try:
        # gets all current and pending roles for a project.
        user_perms = db.session.execute(db.select(UserRole).where(
            (UserRole.project_id == project_id) & (UserRole.user_id == current_user.id) & (
                UserRole.has_accepted))).scalar()
        project = db.get_or_404(Project, project_id)
        invites = db.session.execute(db.select(UserRole).where((UserRole.project_id == project_id) & (UserRole.user_id != current_user.id))).scalars().all()
        current_roles = [role for role in invites if role.has_accepted]
        pending_roles = [role for role in invites if not role.has_accepted]
        perm_to_delete = False
        is_manager = False
        if current_user.id == project.manager_id:
            perm_to_delete = True
            is_manager = True
        if user_perms:
            perm_to_delete = user_perms.role.delete_members_from_project
        return render_template("project-members.html", current_roles=current_roles, pending_roles=pending_roles, perm_to_delete=perm_to_delete, is_manager=is_manager)
    except exc.IntegrityError:
        db.session.rollback()


@app.route("/role/accept/<int:role_id>")
@login_required
def accept_role(role_id):
    try:
        user_role_to_update = db.get_or_404(UserRole, role_id)
        if current_user.id != user_role_to_update.user_id:
            return redirect(url_for("get_user_invites"))
        user_role_to_update.has_accepted = True
        db.session.commit()
        return redirect(url_for("get_user_invites"))
    except exc.IntegrityError:
        db.session.rollback()


@app.route("/role/delete/<int:role_id>/<action>")
@login_required
def delete_user_role(role_id, action):
    try:
        user_role_to_delete = db.get_or_404(UserRole, role_id)
        project_id = user_role_to_delete.project_id
        project = user_role_to_delete.project
        if action == "remove":
            user_perms = db.session.execute(db.select(UserRole).where(
                (UserRole.project_id == project_id) & (UserRole.user_id == current_user.id) & (
                    UserRole.has_accepted))).scalar()
            manager = current_user.id == project.manager_id
            if not manager and not user_perms:
                return redirect(url_for("home_page"))
            if not manager and not user_perms.role.delete_members_from_project:
                return redirect(url_for("home_page"))
            db.session.delete(user_role_to_delete)
            db.session.commit()
            return redirect(url_for("get_project_members", project_id=project_id))
        db.session.delete(user_role_to_delete)
        db.session.commit()
        return redirect(url_for("get_user_invites"))
    except exc.IntegrityError:
        db.session.rollback()


if __name__ == '__main__':
    app.run(debug=True)
