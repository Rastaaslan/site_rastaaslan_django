/**
 * Gestion du défilement horizontal pour les listes de miniatures
 */
document.addEventListener('DOMContentLoaded', function() {
    initializeScrolls();
    
    // Initialiser le défilement sur tous les conteneurs
    function initializeScrolls() {
        // Cibler tous les wrappers de défilement
        document.querySelectorAll('.thumbnails-scroll-wrapper').forEach(function(scrollWrapper) {
            // Obtenir les éléments parents pertinents
            const scrollContainer = scrollWrapper.closest('.horizontal-scroll-container');
            if (!scrollContainer) return;
            
            const leftArrow = scrollContainer.querySelector('.scroll-left');
            const rightArrow = scrollContainer.querySelector('.scroll-right');
            
            if (!leftArrow || !rightArrow) return;
            
            // Largeur de défilement
            const scrollAmount = 300;
            
            // Fonction pour faire défiler vers la gauche
            leftArrow.addEventListener('click', function() {
                scrollWrapper.scrollBy({
                    left: -scrollAmount,
                    behavior: 'smooth'
                });
            });
            
            // Fonction pour faire défiler vers la droite
            rightArrow.addEventListener('click', function() {
                scrollWrapper.scrollBy({
                    left: scrollAmount,
                    behavior: 'smooth'
                });
            });
            
            // Fonction pour mettre à jour l'opacité des flèches
            function updateArrows() {
                const maxScrollLeft = scrollWrapper.scrollWidth - scrollWrapper.clientWidth;
                leftArrow.style.opacity = scrollWrapper.scrollLeft > 0 ? '1' : '0.3';
                rightArrow.style.opacity = scrollWrapper.scrollLeft < maxScrollLeft ? '1' : '0.3';
            }
            
            // Mise à jour initiale des flèches
            updateArrows();
            
            // Mettre à jour en cas de défilement
            scrollWrapper.addEventListener('scroll', updateArrows);
            
            // Défilement avec la molette
            scrollWrapper.addEventListener('wheel', function(e) {
                e.preventDefault();
                scrollWrapper.scrollBy({
                    left: e.deltaY < 0 ? -100 : 100,
                    behavior: 'smooth'
                });
                updateArrows();
            });
            
            // Défilement tactile
            let isDown = false;
            let startX;
            let scrollLeft;
            
            scrollWrapper.addEventListener('mousedown', (e) => {
                isDown = true;
                scrollWrapper.classList.add('active');
                startX = e.pageX - scrollWrapper.offsetLeft;
                scrollLeft = scrollWrapper.scrollLeft;
            });
            
            scrollWrapper.addEventListener('mouseleave', () => {
                isDown = false;
                scrollWrapper.classList.remove('active');
            });
            
            scrollWrapper.addEventListener('mouseup', () => {
                isDown = false;
                scrollWrapper.classList.remove('active');
            });
            
            scrollWrapper.addEventListener('mousemove', (e) => {
                if(!isDown) return;
                e.preventDefault();
                const x = e.pageX - scrollWrapper.offsetLeft;
                const walk = (x - startX) * 2;
                scrollWrapper.scrollLeft = scrollLeft - walk;
                updateArrows();
            });
        });
    }
    
    // Lier aux changements d'onglets
    const tabLinks = document.querySelectorAll('a[data-toggle="tab"]');
    tabLinks.forEach(tabLink => {
        tabLink.addEventListener('shown.bs.tab', function() {
            initializeScrolls();
        });
    });
});