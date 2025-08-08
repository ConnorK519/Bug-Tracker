const bugDeleteAnchors = document.querySelectorAll(".deleteBugAnchor")
const confirmModal = document.getElementById("deleteBugConfirmationModal")
const confirmForm = document.querySelector(".bug_delete_form")
const cancelDeleteButton = document.getElementById("cancelDeleteBug")

let deleteUrl = null;
let bugIdToDelete = null;

bugDeleteAnchors.forEach(anchor => {
anchor.addEventListener("click", (event) => {
event.preventDefault()
deleteUrl = event.currentTarget.dataset.deleteUrl;
bugIdToDelete = event.currentTarget.dataset.bugId;
confirmModal.classList.add('active')
})
})

cancelDeleteButton.addEventListener("click", (event) => {
event.preventDefault()
confirmModal.classList.remove('active')
})

confirmForm.addEventListener("submit", (event) => {
event.preventDefault()
const formData = new FormData(confirmForm)
fetch(deleteUrl, {method: "POST", body: formData}).then((response) => {
if (response.status == 204) {
let bugCard = document.getElementById(`bugCard-${ bugIdToDelete }`)
bugCard.classList.add("hidden")
confirmModal.classList.remove('active')
}
})
})


//bugDeleteForms.forEach(form => {
//form.addEventListener("submit", (event) => {
//event.preventDefault()
//const formData = new FormData(form)
//const url = form.action
//const bugId = formData.get("id");
//fetch(url, {method: "POST", body: formData}).then((response) => {
//if (response.status == 204) {
//let bugCard = document.getElementById(`bugCard-${ bugId }`)
//bugCard.classList.add("hidden")
//}
//})
//})})