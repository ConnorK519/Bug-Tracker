from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, PasswordField, FieldList, FormField
from wtforms.validators import DataRequired, URL
from flask_ckeditor import CKEditorField


class RegisterForm(FlaskForm):
    username = StringField("Username:", validators=[DataRequired()])
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
    description = CKEditorField("Description:", validators=[DataRequired()])
    languages_used = FieldList(StringField(""), min_entries=3)
    frameworks_or_libraries = FieldList(StringField(""), min_entries=3)
    hosted_url = StringField("Hosted project url:", validators=[URL()])
    repo_url = StringField("Repo url:", validators=[URL()])
    submit_project = SubmitField("Submit")


class PostBugForm(FlaskForm):
    title = StringField("Title:", validators=[DataRequired()])
    description = CKEditorField("Description:", validators=[DataRequired()])
    steps_to_recreate = CKEditorField("Steps to recreate bug:", validators=[DataRequired()])
    error_url = StringField("Link to error (if available):")
    submit_bug = SubmitField("Submit")
