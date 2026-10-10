document.addEventListener("DOMContentLoaded", () => {
    const currentPath = window.location.pathname;
    document.querySelectorAll(".navbar .nav-link").forEach((link) => {
        const href = link.getAttribute("href");
        if (href && currentPath.startsWith(href)) {
            link.classList.add("active");
        }
    });
});
