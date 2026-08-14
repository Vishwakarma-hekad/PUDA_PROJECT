document.addEventListener("DOMContentLoaded", function () {

    const searchInput = document.getElementById("searchInput");
    const statusFilter = document.getElementById("statusFilter");
    const rows = document.querySelectorAll("#applicationTable tr");

    function filterTable() {

        const search = searchInput.value.toLowerCase();
        const status = statusFilter.value.toLowerCase();

        rows.forEach(row => {

            const text = row.textContent.toLowerCase();

            const badge = row.querySelector(".badge");
            const rowStatus = badge ? badge.textContent.trim().toLowerCase() : "";

            const matchesSearch = text.includes(search);
            const matchesStatus = !status || rowStatus === status;

            row.style.display = (matchesSearch && matchesStatus) ? "" : "none";

        });

    }

    searchInput.addEventListener("keyup", filterTable);
    statusFilter.addEventListener("change", filterTable);

});