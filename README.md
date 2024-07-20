This project is a simple bug tracking and management application built using Flask.
It provides CRUD operations for users, projects, and bugs. 
A SQLite database is used for data storage for ease of development and testing while using jinja2 templating.

**Home Page:**

Endpoint: /

This retrieves a list of the projects in descending order by date posted and offers a search bar for searching project
titles and descriptions.

# **User Endpoints:**

---

**/users/<int:project_id>**

facilitates project management by allowing authorized users to invite new team members. The endpoint enables searching for potential members and sending invitations, while emitting a response upon successful addition to the project.

**/register**

allows new users to create accounts. Users can provide a username, password, and optional bio. The system validates the username's uniqueness and ensures password confirmation before securely storing the hashed password. Upon successful registration, the user is automatically logged in and redirected to the home page.

**/user/update-account**

allows registered users to modify their account information. Users can update their username, bio, and optionally change their password. Password updates require confirmation and secure hashing before saving. The system also prevents username conflicts by checking for existing users with the chosen name.

**/login**

covers user login. Users can provide their username and password to authenticate and gain access to the application. The system validates credentials by checking the username against stored records and comparing the entered password with a securely hashed version. Successful login creates a user session and redirects to the home page.

**/reports**

retrieves and displays all bugs the current user has reported with information on the status, priority level and basic information.

**/projects**

retrieves the currently logged in users projects with information on them.

**/logout**

logs out the current user.

**/user/delete-account**

logs out the current user then deletes their account.

---

# **Project Endpoints:**

---

**/search-projects/<str:search>**

Users can efficiently find projects by searching through project titles and descriptions. Search results are presented in descending order based on project creation date.

**/project/<int:project_id>**

The project page displays project details, including languages and frameworks used. Users can search for bugs within a project and update existing bug statuses and priorities (if authorized).

**/projects/add-new-project**

Logged-in users can create new projects by providing details like title, description, and links. The system validates project titles for uniqueness and stores comma-separated lists of languages and frameworks. Upon successful creation, users are redirected to the home page.

**/project/<int:project_id>/update**

Project managers can edit existing projects by providing updated details. The system validates project titles for uniqueness and handles changes to comma-separated lists of languages and frameworks. Upon successful update, users are redirected to the project page.

**/delete-project/<int:project_id>**

Project managers can delete their projects. The system verifies user permissions to prevent unauthorized deletion. Upon successful deletion, users are redirected to the home page.

---

# **Bug Endpoints:**

---

**/project/<int:project_id>/<str:search>**

Within a project page, this endpoint allows users to refine the displayed bug list by searching bug titles and descriptions. The search term is matched against existing bugs, and only relevant bugs are presented on the project page.

**/projects/<int:project_id>/post-bug**

Logged-in users can submit bug reports for specific projects. The endpoint allows users to describe the bug, including steps to reproduce and optional error URL. Upon successful creation, users are redirected to the project page.

**/bug/<int:bug_id>/update**

Bug reporters can edit their submitted bug reports. The endpoint allows for modifying the bug details like title, description, and steps to reproduce. Title changes also verify uniqueness to prevent duplicates. Successful updates redirect users to the relevant project page.

**/delete-bug/<int:bug_id>**

Bug reporters or authorized users can delete bug reports. The system ensures only the reporter, project manager, or users with the "delete_bug" permission can delete bugs. Upon successful deletion, users are redirected to the relevant project page.

---

# **Role Endpoints:**

---

**/user/role-invites**

Logged-in users can access information about their current project roles and any pending invitations. The endpoint retrieves all user roles associated with the current user and separates them into accepted (current roles) and unaccepted (pending invitations) categories. The rendered template displays lists of both current and pending roles.

**/project/members/<int:project_id>**

This endpoint displays a project's members and pending invitations. User permissions determine visibility and actions. Project managers can view and remove members, while other users with appropriate permissions can also remove members.

**/role/accept/<int:role_id>**

Logged-in users can accept pending project role invitations. The system verifies the user's ownership of the invitation before updating the acceptance status. Upon successful acceptance, users are redirected to the manage role invites page.

**/role/delete/<int:role_id>/<str:action>**

This endpoint allows managing project roles. Project managers and authorized users can remove members from a project. Users can also decline pending project role invitations. The system verifies user permissions before allowing actions. Successful operations redirect users to the relevant page.

---

# **Models**

---

**Users:**

    id: user identification primary key.
    username: ensures a unique username.
    hashed_password: securely stores the users password hash for future comparison.
    user_bio: a short description of the user preferably containing languages know and other relevant details.
    roles: defines a relationship between a user and their role in and project they are a part of.
    projects: defines a relationship between the user and their projects.
    bugs_reported: defines a relationship between the user and the bugs they reported.

---

**Projects:**

    id: project identification primary key.
    manager_id: stores the foreign key that ties the manager to the project.
    title: stores a unique title for the project.
    description: stores a breif explaination on what the project is.
    languages_used: stores a list of languages used to build the project.
    frameworks_or_libraries: stores info on the tools used to build the project.
    hosted_url: if the project is hosted allows the storing of a link to the hosted version.
    repo_url: stores a link to a repo containing the project.
    date_posted: stores the date posted for context and display purposes.
    project_roles: defines a relationship between the project and any user roles associated with it.
    bugs: defines a relationship between the project and any bugs assigned to it.
    manager: defines a link between the owner of the project and the project itself.

---

