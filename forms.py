from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, PasswordField, FieldList, TextAreaField, SelectField, IntegerField, HiddenField
from wtforms.validators import DataRequired, URL


class RegisterForm(FlaskForm):
    username = StringField("Username:", validators=[DataRequired()])
    user_bio = TextAreaField("User Bio (Coding experience, languages you know, etc):", validators=[])
    password = PasswordField("Password:", validators=[DataRequired()])
    re_enter_pass = PasswordField("Re-Enter Password:", validators=[DataRequired()])
    submit_user = SubmitField("Submit")


class LoginForm(FlaskForm):
    username = StringField("Username:", validators=[DataRequired()])
    password = PasswordField("Password:", validators=[DataRequired()])
    submit_login = SubmitField("Login")


class SearchForm(FlaskForm):
    search = StringField("Search", validators=[DataRequired()])
    submit_search = SubmitField("Search")


class PostProjectForm(FlaskForm):
    title = StringField("Title:", validators=[DataRequired()])
    description = TextAreaField("Description:", validators=[DataRequired()])
    languages_used = FieldList(StringField(""), min_entries=3)
    frameworks_or_libraries = FieldList(StringField(""), min_entries=3)
    hosted_url = StringField("Hosted project url:", validators=[URL()])
    repo_url = StringField("Repo url:", validators=[URL()])
    submit_project = SubmitField("Submit")


class PostBugForm(FlaskForm):
    title = StringField("Title:", validators=[DataRequired()])
    description = TextAreaField("Description:", validators=[DataRequired()])
    steps_to_recreate = TextAreaField("Steps to recreate bug:", validators=[DataRequired()])
    error_url = StringField("Link to error (if available):")
    submit_bug = SubmitField("Submit")


class InviteForm(FlaskForm):
    role = SelectField("Role", choices=[(1, "Tester"), (2, "Developer"), (3, "Admin")])
    user_id = IntegerField()
    project_id = HiddenField()
    submit_invite = SubmitField("Invite")


class BugStatusAndPriorityForm(FlaskForm):
    priority = SelectField("Priority", choices=[("Not yet assigned", "Not yet assigned"), ("Very low", "Very low"), ("Low", "Low"), ("Mid", "Mid"), ("High", "High"), ("Very high", "Very high")])
    status = SelectField("Status", choices=[("Pending", "Pending"), ("In Progress", "In Progress"), ("Testing", "Testing"), ("Fixed", "Fixed")])
    bug_id = IntegerField()
    submit_update = SubmitField("Update")
