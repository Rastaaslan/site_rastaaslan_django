/**
 * Script pour améliorer le comportement de la navbar
 * À ajouter dans un nouveau fichier static/js/navbar.js
 */
document.addEventListener('DOMContentLoaded', function() {
    // Fermer le menu mobile lorsqu'un lien est cliqué
    const navLinks = document.querySelectorAll('.navbar-nav .nav-link');
    const navbarCollapse = document.getElementById('navbarContent');
    const navbarToggler = document.querySelector('.navbar-toggler');
    
    navLinks.forEach(function(link) {
        link.addEventListener('click', function() {
            // Vérifier si le menu est actuellement ouvert et si nous sommes en mode mobile
            if (window.innerWidth < 992 && navbarCollapse.classList.contains('show')) {
                // Simuler un clic sur le bouton hamburger pour fermer le menu
                navbarToggler.click();
            }
        });
    });
    
    // Ajouter la classe active au lien correspondant à la page courante
    const currentPath = window.location.pathname;
    
    navLinks.forEach(function(link) {
        const linkPath = link.getAttribute('href');
        
        // Si le lien correspond à la page courante ou à une section de la page
        if (currentPath === linkPath || 
            (currentPath.includes('/forum/') && linkPath.includes('/forum/')) ||
            (currentPath.includes('/vods/') && linkPath.includes('/vods/')) ||
            (currentPath.includes('/clips/') && linkPath.includes('/clips/'))) {
            
            // Ajouter la classe active
            link.classList.add('active');
            
            // Si le lien est dans un dropdown, activer aussi le parent
            const dropdownItem = link.closest('.dropdown-item');
            if (dropdownItem) {
                const dropdownToggle = dropdownItem.closest('.dropdown').querySelector('.dropdown-toggle');
                if (dropdownToggle) {
                    dropdownToggle.classList.add('active');
                }
            }
        }
    });
});