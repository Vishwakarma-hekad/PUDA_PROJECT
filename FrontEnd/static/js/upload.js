const uploadForm = document.getElementById("uploadForm");
const fileInput = document.getElementById("dwgfile");
const dropArea = document.getElementById("dropArea");
const selectedFile = document.getElementById("selectedFile");
const progressBar = document.getElementById("progressBar");

// ----------------------------------------
// File Selection
// ----------------------------------------

fileInput.addEventListener("change", () => {

    if (fileInput.files.length === 0) {
        selectedFile.innerHTML = "";
        return;
    }

    const file = fileInput.files[0];

    selectedFile.innerHTML = `
        <i class="bi bi-file-earmark-check-fill text-success"></i>
        ${file.name}
        (${(file.size / 1024 / 1024).toFixed(2)} MB)
    `;

});

// ----------------------------------------
// Drag & Drop
// ----------------------------------------

dropArea.addEventListener("dragover", (e) => {

    e.preventDefault();
    dropArea.classList.add("dragover");

});

dropArea.addEventListener("dragleave", () => {

    dropArea.classList.remove("dragover");

});

dropArea.addEventListener("drop", (e) => {

    e.preventDefault();

    dropArea.classList.remove("dragover");

    fileInput.files = e.dataTransfer.files;

    if (fileInput.files.length > 0) {

        const file = fileInput.files[0];

        selectedFile.innerHTML = `
            <i class="bi bi-file-earmark-check-fill text-success"></i>
            ${file.name}
            (${(file.size / 1024 / 1024).toFixed(2)} MB)
        `;

    }

});

// ----------------------------------------
// Upload Form
// ----------------------------------------

uploadForm.addEventListener("submit", async function (e) {

    e.preventDefault();

    // -----------------------
    // Read Form Values
    // -----------------------

    const layout = document.querySelector("[name='layout']").value.trim();
    const subtype = document.querySelector("[name='subtype']").value.trim();
    const purposecode = document.querySelector("[name='purposecode']").value.trim();
    const authority = document.querySelector("[name='authority']").value.trim();
    const location = document.querySelector("[name='location']").value.trim();
    const sub_location = document.querySelector("[name='sub_location']").value.trim();
    const total_plotArea = document.querySelector("[name='total_plotArea']").value.trim();
    const use = document.querySelector("[name='use']").value.trim();
    const subuse = document.querySelector("[name='subuse']").value.trim();

    // -----------------------
    // Validate Required Fields
    // -----------------------}

    if (layout === "") {
        alert("Please select Layout.");
        return;
    }

    if (subtype === "") {
        alert("Please enter Subtype.");
        return;
    }

    if (purposecode === "") {
        alert("Please enter Purpose Code.");
        return;
    }

    if (authority === "") {
        alert("Please enter Authority.");
        return;
    }

    if (location === "") {
        alert("Please enter Location.");
        return;
    }

    if (sub_location === "") {
        alert("Please enter Sub Location.");
        return;
    }

    if (total_plotArea === "") {
        alert("Please enter Total Plot Area.");
        return;
    }

    if (isNaN(total_plotArea) || Number(total_plotArea) <= 0) {
        alert("Total Plot Area must be greater than zero.");
        return;
    }

    if (use === "") {
        alert("Please enter Use.");
        return;
    }

    if (subuse === "") {
        alert("Please enter Sub Use.");
        return;
    }

    // -----------------------
    // Validate File
    // -----------------------

    if (fileInput.files.length === 0) {
        alert("Please choose a DWG file.");
        return;
    }

    const file = fileInput.files[0];

    if (!file.name.toLowerCase().endsWith(".dwg")) {
        alert("Only DWG files are allowed.");
        return;
    }

    // Optional: 100 MB limit
    const maxSize = 100 * 1024 * 1024;

    if (file.size > maxSize) {
        alert("DWG file size should be less than 100 MB.");
        return;
    }

    // -----------------------
    // Prepare FormData
    // -----------------------

    const formData = new FormData(uploadForm);

    simulateProgress();

    try {

        const response = await fetch("/upload", {

            method: "POST",
            body: formData,
            credentials: "include"

        });
        console.log("Status:", response.status);

         const text = await response.text();

        console.log("Raw Response:", text);

        const data = JSON.parse(text);

        if (response.ok) {

            progressBar.style.width = "100%";
            progressBar.innerHTML = "100%";
            progressBar.classList.remove("progress-bar-animated");

            alert(data.message || "Drawing uploaded successfully.");

            window.location.href = `/processing/?ref_id=${data.ref_id}`;


        }
        else {

            resetProgress();

            alert(
                data.message ||
                data.detail ||
                data.Detail ||
                "Upload Failed."
            );

        }

    }
    catch (error) {

        console.error(error);

        resetProgress();

        alert("Unable to connect to the server.");

    }

});

// ----------------------------------------
// Progress Animation
// ----------------------------------------

let progress = 0;
let timer = null;

function simulateProgress() {

    progress = 0;

    progressBar.classList.add("progress-bar-animated");

    timer = setInterval(() => {

        if (progress < 90) {

            progress += 2;

            progressBar.style.width = progress + "%";
            progressBar.innerHTML = progress + "%";

        }

    }, 150);

}

function resetProgress() {

    clearInterval(timer);

    progress = 0;

    progressBar.style.width = "0%";
    progressBar.innerHTML = "0%";
    progressBar.classList.add("progress-bar-animated");

}