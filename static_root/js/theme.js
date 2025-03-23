/**
 * Gestion du thème clair/sombre pour le site Rastaaslan
 */
document.addEventListener('DOMContentLoaded', function() {
    // Fonction pour définir le thème
    function setTheme(themeName) {
        // Créer un effet de flash pour la transition
        const flash = document.createElement('div');
        flash.className = 'theme-transition-flash';
        document.body.appendChild(flash);
        
        // Appliquer le thème explicitement
        document.documentElement.setAttribute('data-theme', themeName);
        document.documentElement.style.backgroundColor = 
            themeName === 'dark' ? '#1a1a2e' : '#F8F3E6';
            
        // Mettre à jour l'arrière-plan
        const bgElement = document.querySelector('.theme-background');
        if (bgElement) {
            bgElement.style.backgroundColor = themeName === 'dark' ? '#1a1a2e' : '#F8F3E6';
        }
        
        // Stockage local
        localStorage.setItem('theme', themeName);
        
        // Mettre à jour l'icône
        const themeIcon = document.getElementById('theme-icon');
        if (themeIcon) {
            if (themeName === 'dark') {
                themeIcon.classList.remove('fa-moon');
                themeIcon.classList.add('fa-sun');
            } else {
                themeIcon.classList.remove('fa-sun');
                themeIcon.classList.add('fa-moon');
            }
        }
        
        // Supprimer l'élément de flash après l'animation
        setTimeout(() => {
            document.body.removeChild(flash);
        }, 500);
        
        console.log("Thème changé à:", themeName);
    }
    
    // Initialiser le thème
    function initTheme() {
        if (localStorage.getItem('theme') === 'dark') {
            setTheme('dark');
        } else if (localStorage.getItem('theme') === 'light') {
            setTheme('light');
        } else {
            // Préférence système par défaut
            if (window.matchMedia && window.matchMedia('(prefers-color-scheme: dark)').matches) {
                setTheme('dark');
            } else {
                setTheme('light');
            }
        }
    }
    
    // Initialiser le thème au chargement
    initTheme();
    
    // Changer de thème au clic avec un effet subtil
    const themeToggle = document.getElementById('theme-toggle');
    if (themeToggle) {
        themeToggle.addEventListener('click', function(e) {
            e.preventDefault();
            
            // Désactiver le bouton pendant la transition pour éviter les clics multiples
            this.style.pointerEvents = 'none';
            
            if (localStorage.getItem('theme') === 'dark') {
                setTheme('light');
            } else {
                setTheme('dark');
            }
            
            // Réactiver le bouton après la transition
            setTimeout(() => {
                this.style.pointerEvents = 'auto';
            }, 500);
        });
    }
    
    // Observer les changements de préférence système pour le thème
    if (window.matchMedia) {
        const colorSchemeQuery = window.matchMedia('(prefers-color-scheme: dark)');
        colorSchemeQuery.addEventListener('change', (e) => {
            // Seulement mettre à jour si l'utilisateur n'a pas explicitement choisi un thème
            if (!localStorage.getItem('theme')) {
                setTheme(e.matches ? 'dark' : 'light');
            }
        });
    }
});