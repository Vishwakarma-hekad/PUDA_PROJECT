document.addEventListener("DOMContentLoaded", function () {

    const darkMode = document.getElementById("darkMode");

    if (darkMode) {

        darkMode.addEventListener("change", function () {

            document.body.classList.toggle("dark-mode");

            console.log("Dark Mode:", this.checked);

        });

    }

});