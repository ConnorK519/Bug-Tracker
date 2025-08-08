from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, PasswordField, FieldList, TextAreaField, SelectField, IntegerField, \
    HiddenField
from wtforms.validators import DataRequired, URL, EqualTo, InputRequired, Length, Optional


class RegisterForm(FlaskForm):
    username = StringField("Username:", validators=[DataRequired(), Length(min=3, max=15)])
    user_bio = TextAreaField("User Bio (Coding experience, languages you know, etc):", validators=[])
    password = PasswordField("Password:", validators=[InputRequired(),
                                                      Length(min=5, max=20, message="Password Must Be within character "
                                                                                    "bounds (5-20)!")])
    re_enter_pass = PasswordField("Re-Enter Password:",
                                  validators=[InputRequired(), EqualTo('password', message='Passwords '
                                                                                           'must '
                                                                                           'match')])
    submit_user = SubmitField("Submit")


class DeleteConfirmForm(FlaskForm):
    confirm_delete = SubmitField('Delete')


class DeleteUserForm(FlaskForm):
    confirm_password = PasswordField("Enter Your Password to Confirm:", validators=[DataRequired()])
    submit = SubmitField('Delete User')


class DeleteProjectForm(FlaskForm):
    confirm_project = StringField("Enter Project Name to Confirm:", validators=[DataRequired()])
    submit = SubmitField('Delete Project')


class UpdateUserForm(FlaskForm):
    username = StringField("Username:", validators=[DataRequired(), Length(min=3, max=15)])
    user_bio = TextAreaField("User Bio (Coding experience, languages you know, etc):", validators=[])
    password = PasswordField("Password:", validators=[])
    re_enter_pass = PasswordField("Re-Enter Password:",
                                  validators=[EqualTo('password', message='Passwords '
                                                                          'must '
                                                                          'match')])
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
    priority = SelectField("Priority",
                           choices=[("Default", "Select Priority"), ("Very low", "Very low"), ("Low", "Low"),
                                    ("Mid", "Mid"), ("High", "High"), ("Very high", "Very high")],
                           validators=[Optional()], default="Default")
    status = SelectField("Status",
                         choices=[("Default", "Select Status"), ("In Progress", "In Progress"), ("Testing", "Testing"),
                                  ("Fixed", "Fixed")], validators=[Optional()], default="Default")
    bug_id = IntegerField()
    submit_update = SubmitField("Update")
