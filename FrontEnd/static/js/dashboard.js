document.addEventListener("DOMContentLoaded", function () {

    const currentPath = window.location.pathname;

    document.querySelectorAll(".sidebar a").forEach(link => {

        if (link.getAttribute("href") === currentPath) {
            link.parentElement.classList.add("active");
        }

    });

});