const deleteUserAnchor = document.getElementById("deleteUserAnchor")
const deleteUserModal = document.getElementById("deleteUserModalBackground")
const cancelDeleteUser = document.getElementById("cancelDeleteUser")

if (deleteUserAnchor && deleteUserModal) {
deleteUserAnchor.addEventListener("click", (event) => {
event.preventDefault();
deleteUserModal.classList.add('active');
})
}

if (cancelDeleteUser) {
cancelDeleteUser.addEventListener("click", (event) => {
event.preventDefault();
deleteUserModal.classList.remove('active');
})
}