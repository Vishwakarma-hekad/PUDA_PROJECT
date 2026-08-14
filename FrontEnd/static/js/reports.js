document.addEventListener("DOMContentLoaded", function () {

    const search = document.getElementById("searchReport");

    search.addEventListener("keyup", function () {

        let value = this.value.toLowerCase();

        let rows = document.querySelectorAll("#reportTable tr");

        rows.forEach(function (row) {

            row.style.display = row.textContent.toLowerCase().includes(value)
                ? ""
                : "none";

        });

    });

});