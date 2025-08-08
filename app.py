from flask import Flask, render_template, redirect, url_for, flash, jsonify
from flask_login import login_user, LoginManager, current_user, logout_user, login_required
from werkzeug.security import generate_password_hash, check_password_hash
from sqlalchemy import desc, exc
from forms import RegisterForm, LoginForm, SearchForm, PostProjectForm, PostBugForm, InviteForm, \
    BugStatusAndPriorityForm, UpdateUserForm, DeleteUserForm, DeleteProjectForm, DeleteConfirmForm
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


@app.context_processor
def add_user_choices():
    delete_user_form = None
    if current_user.is_authenticated:
        delete_user_form = DeleteUserForm()
    return dict(delete_user_form=delete_user_form)


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
    form = SearchForm()
    try:
        if form.validate_on_submit():
            search = form.search.data
            # redirects to a search endpoint so the url including the search can be shared.
            return redirect(url_for("search_projects", search=search))
        projects = db.session.execute(db.select(Project).order_by(desc(Project.date_posted))).scalars().all()
        return render_template("index.html", form=form, projects=projects)
    except Exception as e:
        flash("An error occurred!", "error")
        print(e)
        return redirect(url_for("home_page"))


# ----------------------------------------------------------------------------------------------

# User endpoints

# ----------------------------------------------------------------------------------------------


@app.route("/user/register", methods=["GET", "POST"])
def register():
    form = RegisterForm()
    try:
        if form.validate_on_submit():
            username = form.username.data
            user = db.session.execute(db.select(User).where(User.username == username)).scalar()
            password = form.password.data
            re_enter_pass = form.re_enter_pass.data
            if user:
                flash("Username in use!", "error")
                return redirect(url_for("register"))
            if password != re_enter_pass:
                flash("Passwords do not match!", "error")
                return redirect(url_for("register"))
            # salts and hashes the password.
            hashed_password = generate_password_hash(password)
            new_user = User(username=username, user_bio=form.user_bio.data, hashed_password=hashed_password)
            db.session.add(new_user)
            db.session.commit()
            login_user(new_user)
            flash("Sign up successful!", "success")
            return redirect(url_for("home_page"))
        return render_template("register.html", form=form)
    except exc.IntegrityError:
        db.session.rollback()
        flash("Invalid inputs!", "error")
        return redirect(url_for("register"))
    except Exception as e:
        print(e)
        db.session.rollback()
        flash("An error occurred!", "error")
        return redirect(url_for("register"))


@app.route("/user/update-account", methods=["GET", "POST"])
@login_required
def update_user():
    form = UpdateUserForm()
    try:
        original_name = current_user.username
        if form.validate_on_submit():
            # checks for change in the users name.
            if original_name != form.username.data:
                # checks if the new name is in use.
                existing_user = db.session.execute(db.select(User).where(User.username == form.username.data).where(
                    User.id != current_user.id)).scalar()
                if existing_user:
                    flash("Username in use!", "error")
                    return redirect(url_for("update_user"))
                current_user.username = form.username.data
            if current_user.user_bio != form.user_bio.data:
                current_user.user_bio = form.user_bio.data
            if form.password.data != form.re_enter_pass.data:
                flash("Passwords do not match!", "error")
                return redirect(url_for("update_user"))
            if form.password.data:
                hashed_password = generate_password_hash(form.password.data)
                current_user.hashed_password = hashed_password
            db.session.commit()
            flash("User info updated!", "success")
            return redirect(url_for("update_user"))
        # pre-populates the form fields.
        form.username.data = current_user.username
        form.user_bio.data = current_user.user_bio
        return render_template("update_user.html", form=form)
    except exc.IntegrityError:
        db.session.rollback()
        flash("Invalid inputs!", "error")
        return redirect(url_for("update_user"))
    except Exception as e:
        print(e)
        db.session.rollback()
        flash("An error occurred!", "error")
        return redirect(url_for("update_user"))


@app.route("/user/login", methods=["GET", "POST"])
def login():
    form = LoginForm()
    try:
        if form.validate_on_submit():
            username = form.username.data
            password = form.password.data
            user = db.session.execute(db.select(User).where(User.username == username)).scalar()
            if not user or not check_password_hash(user.hashed_password, password):
                flash("Incorrect username or password!", "error")
                return redirect(url_for("login"))
            login_user(user)
            flash("Login successful!", "success")
            return redirect(url_for("home_page"))
        return render_template("login.html", form=form)
    except Exception as e:
        print(e)
        db.session.rollback()
        flash("An error occurred!", "error")
        return redirect(url_for("login"))


@app.route("/user/reports")
@login_required
def reports_by_user_id():
    try:
        bugs = current_user.bugs_reported
        return render_template("reports.html", bugs=bugs)
    except Exception as e:
        print(e)
        db.session.rollback()
        flash("An error occurred!", "error")
        return redirect(url_for("home_page"))


@app.route("/user/projects")
@login_required
def projects_by_user_id():
    try:
        projects = current_user.projects
        return render_template("projects.html", projects=projects)
    except Exception as e:
        print(e)
        db.session.rollback()
        flash("An error occurred!", "error")
        return redirect(url_for("home_page"))


@app.route("/user/logout")
@login_required
def logout():
    try:
        logout_user()
        flash("Successfully logged out!", "success")
        return redirect(url_for("home_page"))
    except Exception as e:
        print(e)
        db.session.rollback()
        flash("An error occurred!", "error")
        return redirect(url_for("home_page"))


@app.route("/user/delete-account", methods=["POST"])
@login_required
def delete_user():
    delete_user_form = DeleteUserForm()
    try:
        if not delete_user_form.validate_on_submit():
            flash("Form submission failed. Please try again.", "error")
            return redirect(url_for("home_page"))
        password = delete_user_form.confirm_password.data
        if not check_password_hash(current_user.hashed_password, password):
            flash("Incorrect password!", "error")
            return redirect(url_for("home_page"))
        db.session.delete(current_user)
        db.session.commit()
        logout_user()
        flash("User successfully deleted!", "success")
        return redirect(url_for("home_page"))
    except Exception as e:
        print(e)
        db.session.rollback()
        flash("An error occurred!", "error")
        return redirect(url_for("home_page"))


# ----------------------------------------------------------------------------------------------

# Project endpoints

# ----------------------------------------------------------------------------------------------


@app.route("/project/<int:project_id>", methods=["GET", "POST"])
@app.route("/project/<int:project_id>/<search>", methods=["GET", "POST"])
def project_page(project_id, search=None):
    search_form = SearchForm()
    bug_form = BugStatusAndPriorityForm()
    deleteProjectForm = DeleteProjectForm()
    delete_bug_form = DeleteConfirmForm()
    user_perms = None
    try:
        if current_user.is_authenticated:
            user_perms = db.session.execute(db.select(UserRole).where(
                (UserRole.project_id == project_id) & (UserRole.user_id == current_user.id) & (
                    UserRole.has_accepted))).scalar()
        if search_form.validate_on_submit():
            search = search_form.search.data
            return redirect(url_for("project_page", project_id=project_id, search=search))
        project = db.get_or_404(Project, project_id)
        bugs = project.bugs
        if search:
            search_form.search.data = search
            search_pattern = f"%{search}%"
            bugs = db.session.execute(db.select(Bug).where(
                (Bug.project_id == project_id) &
                ((Bug.title.like(search_pattern)) |
                 (Bug.description.like(search_pattern)) |
                 (Bug.steps_to_recreate.like(search_pattern)) |
                 (Bug.error_url.like(search_pattern)) |
                 (Bug.priority_level.like(search_pattern)) |
                 (Bug.status.like(search_pattern))))).scalars().all()
        # splits the string stored in the database back into a list for display.
        languages_used = project.languages_used.split("~|,-%-,|~")
        frameworks_or_libraries = project.frameworks_or_libraries.split("~|,-%-,|~")
        return render_template("project_page.html", project=project, bugs=bugs, languages_used=languages_used,
                               frameworks_or_libraries=frameworks_or_libraries, form=search_form, user_perms=user_perms,
                               bug_form=bug_form, deleteProjectForm=deleteProjectForm, delete_bug_form=delete_bug_form)
    except Exception as e:
        print(e)
        db.session.rollback()
        flash("An error occurred!", "error")
        return redirect(url_for("home_page"))


@app.route("/project/<int:project_id>/invite-users", methods=["GET", "POST"])
@login_required
def invite_users_to_project(project_id):
    users = []
    search_form = SearchForm()
    # sets up the hidden project_id field for each user's invite form.
    invite_form = InviteForm(project_id=project_id)
    try:
        # checks the project exists
        project = db.get_or_404(Project, project_id)
        # blocks the users access if not permitted.
        if current_user.id != project.manager_id:
            flash("You do not have permission to invite users to this project!")
            return redirect(url_for("home_page"))
        # retrieves none sensitive user data where they are not currently invited or on the current project.
        baseQuery = db.select(User.id, User.username, User.user_bio).where(User.id != current_user.id)
        if search_form.validate_on_submit():
            search = f"%{search_form.search.data}%"
            users = db.session.execute(
                baseQuery.where(
                    User.username.like(search) | User.user_bio.like(search)).where(
                    ~User.roles.any(UserRole.project_id == project_id))).all()
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
            flash(f"Successfully invited {user.username} to the project!", "success")
            return redirect(url_for("invite_users_to_project", project_id=project_id))
        users = db.session.execute(
            baseQuery.where(
                ~User.roles.any(UserRole.project_id == project_id))).all()
        return render_template("users.html", users=users, search_form=search_form, invite_form=invite_form,
                               project_id=project_id)
    except exc.IntegrityError:
        db.session.rollback()
        flash("This user is already on the project.", "error")
        return redirect(url_for("invite_users_to_project", project_id=project_id))
    except Exception as e:
        print(e)
        db.session.rollback()
        flash("An error occurred!", "error")
        return redirect(url_for("invite_users_to_project", project_id=project_id))


@app.route("/project/<int:project_id>/update", methods=["GET", "POST"])
@login_required
def update_project(project_id):
    is_edit = True
    form = PostProjectForm()
    try:
        project_to_update = db.get_or_404(Project, project_id)
        original_name = project_to_update.title
        if current_user.id != project_to_update.manager_id:
            flash("You don't have permission to edit this project!", "error")
            return redirect(url_for("home_page"))
        if form.validate_on_submit():
            # checks if there is a change in the project title.
            if original_name != form.title.data:
                existing_project = db.session.execute(
                    db.select(Project).where(Project.title == form.title.data)).scalar()
                # checks if there is already a project with the new title.
                if existing_project:
                    flash("Project title in use!", "error")
                    return redirect(url_for("update_project", project_id=project_id))
                project_to_update.title = form.title.data
            if project_to_update.description != form.description.data:
                project_to_update.description = form.description.data
            if project_to_update.languages_used != "~|,-%-,|~".join(form.languages_used.data):
                project_to_update.languages_used = "~|,-%-,|~".join(form.languages_used.data)
            if project_to_update.frameworks_or_libraries != "~|,-%-,|~".join(form.frameworks_or_libraries.data):
                project_to_update.frameworks_or_libraries = "~|,-%-,|~".join(form.frameworks_or_libraries.data)
            if project_to_update.hosted_url != form.hosted_url.data:
                project_to_update.hosted_url = form.hosted_url.data
            if project_to_update.repo_url != form.repo_url.data:
                project_to_update.repo_url = form.repo_url.data
            db.session.commit()
            flash("Project successfully updated!", "success")
            return redirect(url_for("project_page", project_id=project_id))
        # splits the string stored in the database back into a list to pre-populate to form fields.
        languages_used_list = project_to_update.languages_used.split("~|,-%-,|~")
        frameworks_or_libraries_list = project_to_update.frameworks_or_libraries.split("~|,-%-,|~")
        form.title.data = project_to_update.title
        form.description.data = project_to_update.description
        # Might refactor to be dealt with in html.
        for num in range(3):
            form.languages_used[num].data = languages_used_list[num]
            form.frameworks_or_libraries[num].data = frameworks_or_libraries_list[num]
        form.hosted_url.data = project_to_update.hosted_url
        form.repo_url.data = project_to_update.repo_url
        return render_template("new_project.html", form=form, project_id=project_id, is_edit=is_edit)
    except exc.IntegrityError:
        db.session.rollback()
        flash("Invalid inputs!", "error")
        return redirect(url_for("project_page", project_id=project_id))
    except Exception as e:
        print(e)
        db.session.rollback()
        flash("An error occurred!", "error")
        return redirect(url_for("project_page", project_id=project_id))


@app.route("/project/<int:project_id>/bug/add", methods=["GET", "POST"])
@login_required
def post_bug(project_id):
    is_edit = False
    form = PostBugForm()
    try:
        if form.validate_on_submit():
            reporter_id = current_user.id
            title = form.title.data
            description = form.description.data
            steps_to_recreate = form.steps_to_recreate.data
            error_url = form.error_url.data
            DEFAULT_PRIORITY = "Not yet assigned"
            DEFAULT_STATUS = "Pending"
            new_bug = Bug(project_id=project_id, reporter_id=reporter_id, title=title, description=description,
                          steps_to_recreate=steps_to_recreate, error_url=error_url, priority_level=DEFAULT_PRIORITY,
                          status=DEFAULT_STATUS)
            db.session.add(new_bug)
            db.session.commit()
            flash("Bug posted successfully!", "success")
            return redirect(url_for("project_page", project_id=project_id))
        return render_template("new_bug.html", form=form, project_id=project_id, is_edit=is_edit)
    except exc.IntegrityError:
        db.session.rollback()
        flash("Invalid inputs!", "error")
        return render_template("new_bug.html", form=form, project_id=project_id, is_edit=is_edit)
    except Exception as e:
        print(e)
        db.session.rollback()
        flash("An error occurred!", "error")
        return render_template("new_bug.html", form=form, project_id=project_id, is_edit=is_edit)


@app.route("/project/<int:project_id>/delete", methods=["POST"])
@login_required
def delete_project_by_id(project_id):
    deleteProjectForm = DeleteProjectForm()
    try:
        project_to_delete = db.get_or_404(Project, project_id)
        # ensures only the project manager can delete the project.
        if current_user.id != project_to_delete.manager_id:
            flash("You do not have permission to delete this project!", "error")
            return redirect(url_for("project_page", project_id=project_id))
        if not deleteProjectForm.validate_on_submit():
            flash("Form submission failed. Please try again.", "error")
            return redirect(url_for("project_page", project_id=project_id))
        if deleteProjectForm.confirm_project.data != project_to_delete.title:
            flash("The project name you entered did not match. Please try again.", "error")
            return redirect(url_for("project_page", project_id=project_id))
        db.session.delete(project_to_delete)
        db.session.commit()
        flash("Project successfully deleted!", "success")
        return redirect(url_for("home_page"))
    except Exception as e:
        print(e)
        db.session.rollback()
        flash("An error occurred!", "error")
        return redirect(url_for("project_page", project_id=project_id))


@app.route("/projects/search/<search>", methods=["GET", "POST"])
def search_projects(search):
    try:
        form = SearchForm()
        # adds wildcards for sql query to get all matches.
        if form.validate_on_submit():
            search = form.search.data
            return redirect(url_for("search_projects", search=search))
        # uses the search to return relevant projects.
        form.search.data = search
        search = f"%{search}%"
        projects = db.session.execute(
            db.select(Project).where(
                Project.title.like(search) | Project.description.like(search) | Project.languages_used.like(
                    search) | Project.frameworks_or_libraries.like(search)).order_by(
                desc(Project.date_posted))).scalars().all()
        return render_template("index.html", form=form, projects=projects)
    except Exception as e:
        print(e)
        db.session.rollback()
        flash("An error occurred!", "error")
        return redirect(url_for("home_page"))


@app.route("/projects/add-new-project", methods=["GET", "POST"])
@login_required
def post_project():
    form = PostProjectForm()
    try:
        is_edit = False
        if form.validate_on_submit():
            manager_id = current_user.id
            title = form.title.data
            description = form.description.data
            languages_used = "~|,-%-,|~".join(form.languages_used.data)
            frameworks_or_libraries = "~|,-%-,|~".join(form.frameworks_or_libraries.data)
            hosted_url = form.hosted_url.data
            repo_url = form.repo_url.data
            existing_project = db.session.execute(db.select(Project).where(Project.title == title)).scalar()
            # checks if there is already a project with the provided title.
            if existing_project:
                flash("A project with this title already exists. Please choose a different title!", "error")
                return render_template("new_project.html", form=form)
            new_project = Project(manager_id=manager_id, title=title, description=description,
                                  languages_used=languages_used, frameworks_or_libraries=frameworks_or_libraries,
                                  hosted_url=hosted_url,
                                  repo_url=repo_url)
            db.session.add(new_project)
            db.session.commit()
            flash("Project successfully posted!", "success")
            return redirect(url_for("home_page"))
        return render_template("new_project.html", form=form, is_edit=is_edit)
    except exc.IntegrityError:
        db.session.rollback()
        flash("Invalid inputs!", "error")
        return render_template("new_project.html", form=form)
    except Exception as e:
        print(e)
        db.session.rollback()
        flash("An error occurred!", "error")
        return render_template("new_project.html", form=form)


# ----------------------------------------------------------------------------------------------

# Bug endpoints

# ----------------------------------------------------------------------------------------------


@app.route("/bug/<int:bug_id>/update", methods=["GET", "POST"])
@login_required
def update_bug(bug_id):
    is_edit = True
    form = PostBugForm()
    bug_to_update = db.get_or_404(Bug, bug_id)
    try:
        if current_user.id != bug_to_update.reporter_id:
            return redirect(url_for("home_page"))
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
        return render_template("new_bug.html", bug_id=bug_id, form=form, is_edit=is_edit)
    except exc.IntegrityError:
        db.session.rollback()
        flash("Invalid inputs!", "error")
        return render_template("new_bug.html", bug_id=bug_id, form=form, is_edit=is_edit)
    except Exception as e:
        print(e)
        db.session.rollback()
        flash("An error occurred!", "error")
        return render_template("new_bug.html", bug_id=bug_id, form=form, is_edit=is_edit)


@app.route("/api/bug/<int:bug_id>/update-details", methods=["POST"])
@login_required
def update_bug_details(bug_id):
    bug_form = BugStatusAndPriorityForm()
    try:
        bugToUpdate = db.get_or_404(Bug, bug_id)
        userPerms = db.session.execute(db.select(UserRole).where(
            (UserRole.user_id == current_user.id) & (UserRole.project_id == bugToUpdate.project_id))).scalar()
        if bug_form.validate_on_submit():
            newStatus = bug_form.status.data
            newPriority = bug_form.priority.data
            isStatusUpdate = newStatus != bugToUpdate.status and newStatus != "Default"
            isPriorityUpdate = newPriority != bugToUpdate.priority_level and newPriority != "Default"
            isManager = current_user.id == bugToUpdate.project.manager_id
            if not userPerms and not isManager:
                return jsonify({"msg": "You do not have permission to update this project!"}), 403
            elif userPerms:
                if isStatusUpdate and not userPerms.role.update_status:
                    return jsonify({"msg": "You do not have permission to update the status!"}), 403
                if isPriorityUpdate and not userPerms.role.update_priority:
                    return jsonify({"msg": "You do not have permission to update the priority!"}), 403
            response = {"msg": "Update Successful!"}
            if isStatusUpdate and newStatus != "Default":
                bugToUpdate.status = newStatus
                response["newStatus"] = newStatus
            if isPriorityUpdate and newPriority != "Default":
                bugToUpdate.priority_level = newPriority
                response["newPriority"] = newPriority
            db.session.commit()
            return jsonify(response), 200
        return jsonify({"msg": "Invalid inputs"}), 400
    except Exception as e:
        print(e)
        db.session.rollback()
        return jsonify({"msg": "A server error occurred!"}), 500


@app.route("/api/bug/<int:bug_id>/delete", methods=["POST"])
@login_required
def delete_bug_by_id(bug_id):
    try:
        delete_bug_form = DeleteConfirmForm()
        bug_to_delete = db.get_or_404(Bug, bug_id)
        project_id = bug_to_delete.project.id
        # gets the current users permissions for the project.
        user_perms = db.session.execute(db.select(UserRole).where(
            (UserRole.project_id == project_id) & (UserRole.user_id == current_user.id))).scalar()
        # ensures only the reporter of the bug or an authorised user can delete bugs.
        can_delete = (current_user.id == bug_to_delete.reporter_id or
                      current_user.id == bug_to_delete.project.manager_id or
                      (user_perms and user_perms.role.delete_bug))
        if not can_delete:
            return jsonify({"msg": "You do not have permission to delete this bug!"}), 403
        db.session.delete(bug_to_delete)
        db.session.commit()
        return jsonify({"msg": "Update Successful!"}), 204
    except exc.IntegrityError:
        db.session.rollback()
        return jsonify({"msg": "Failed to delete bug due to a database integrity error."}), 500
    except Exception as e:
        print(e)
        db.session.rollback()
        return jsonify({"msg": "A server error occurred!"}), 500


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
        invites = db.session.execute(db.select(UserRole).where(
            (UserRole.project_id == project_id) & (UserRole.user_id != current_user.id))).scalars().all()
        current_roles = [role for role in invites if role.has_accepted]
        pending_roles = [role for role in invites if not role.has_accepted]
        perm_to_delete = False
        is_manager = False
        if current_user.id == project.manager_id:
            perm_to_delete = True
            is_manager = True
        if user_perms:
            perm_to_delete = user_perms.role.delete_members_from_project
        return render_template("project_members.html", current_roles=current_roles, pending_roles=pending_roles,
                               perm_to_delete=perm_to_delete, is_manager=is_manager)
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
