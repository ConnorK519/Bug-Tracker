const bugUpdateForms = document.querySelectorAll(".bugDetails")

bugUpdateForms.forEach(form => {
form.addEventListener("submit", (event) => {
event.preventDefault()
const formData = new FormData(form)
const url = form.action
const bugId = formData.get("bug_id");
fetch(url, {method: "POST", body: formData}).then((response) => {
if (response.status == 200) {
return response.json()
}
}).then((result) => {
if (result.newStatus) {
let statusElement = document.getElementById(`bugStatusValue-${bugId}`)
statusElement.innerHTML = result.newStatus
}
if (result.newPriority) {
let priorityElement = document.getElementById(`bugPriorityValue-${bugId}`)
priorityElement.innerHTML = result.newPriority
}
})
})
})