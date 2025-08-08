const deleteProjectAnchor = document.getElementById("deleteProjectAnchor")
const deleteProjectModal = document.getElementById("deleteProjectModalBackground")
const cancelDeleteProject = document.getElementById("cancelDeleteProject")

if (deleteProjectAnchor && deleteProjectModal) {
deleteProjectAnchor.addEventListener("click", (event) => {
event.preventDefault();
deleteProjectModal.classList.add("active")
})
}

if (cancelDeleteProject) {
cancelDeleteProject.addEventListener("click", (event) => {
event.preventDefault();
deleteProjectModal.classList.remove("active")
})
}