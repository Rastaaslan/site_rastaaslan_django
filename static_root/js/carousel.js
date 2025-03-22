/**
 * Gestion des carrousels pour le site Rastaaslan
 */
document.addEventListener('DOMContentLoaded', function() {
    const carousels = document.querySelectorAll('.carousel');
    if (carousels.length === 0) {
        console.log("Aucun carrousel trouvé sur cette page");
        return;
    }
    
    console.log(`Initialisation de ${carousels.length} carrousels...`);
    
    carousels.forEach(carousel => {
        const carouselId = carousel.id || 'carousel-sans-id';
        console.log(`Initialisation du carrousel: ${carouselId}`);
        
        // Initialisation Bootstrap
        $(carousel).carousel({
            interval: 5000
        });
        
        // Vérifier si c'est un carrousel centré
        if (carousel.classList.contains('center-card-carousel')) {
            console.log(`Carrousel centré détecté: ${carouselId}`);
            initCenteredCarousel(carousel);
        }
    });
    
    // Initialisation des carrousels centrés
    function initCenteredCarousel(carousel) {
        function positionCenteredItems() {
            const items = carousel.querySelectorAll('.carousel-item');
            const active = carousel.querySelector('.carousel-item.active');
            
            if (!active || items.length <= 1) {
                console.log(`Carrousel ${carousel.id}: pas d'élément actif ou un seul élément`);
                return;
            }
            
            const activeIndex = Array.from(items).indexOf(active);
            const total = items.length;
            
            // Réinitialiser les classes
            items.forEach(item => {
                item.classList.remove('left', 'right');
            });
            
            // Définir la position des éléments adjacents
            const leftIndex = (activeIndex - 1 + total) % total;
            items[leftIndex].classList.add('left');
            
            const rightIndex = (activeIndex + 1) % total;
            items[rightIndex].classList.add('right');
            
            console.log(`Carrousel ${carousel.id} positionné - actif: ${activeIndex}, gauche: ${leftIndex}, droite: ${rightIndex}`);
        }
        
        // Appliquer immédiatement et lors des transitions
        setTimeout(positionCenteredItems, 100);
        carousel.addEventListener('slid.bs.carousel', positionCenteredItems);
        
        // Vérifier à nouveau après un délai pour s'assurer que tout est bien initialisé
        setTimeout(positionCenteredItems, 500);
    }
});