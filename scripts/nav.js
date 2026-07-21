// --- Menu hamburger ---
const hamburger = document.querySelector('.nav__hamburger');
const list = document.querySelector('.nav__list');

hamburger.addEventListener('click', () => {
    const open = list.classList.toggle('nav__list--open');
    hamburger.setAttribute('aria-expanded', open);
    hamburger.setAttribute('aria-label', open ? 'Fermer le menu' : 'Ouvrir le menu');
});

// --- Dropdown mobile ---
const dropdownItem = document.querySelector('.nav__item--dropdown');
const dropdownLink = dropdownItem.querySelector('.nav__link--dropdown');

dropdownLink.addEventListener('click', (e) => {
    if (window.getComputedStyle(hamburger).display !== 'none') {
        e.preventDefault();
        e.stopPropagation();
        dropdownItem.classList.toggle('nav__item--dropdown--open');
    }
});

// --- Année dynamique dans le footer ---
const yearEl = document.getElementById('footer-year');
if (yearEl) yearEl.textContent = new Date().getFullYear();

// --- Duplique les avis pour la boucle infinie du marquee ---
const avisTrack = document.getElementById('avis-track');
if (avisTrack) {
    const clone = avisTrack.innerHTML;
    avisTrack.insertAdjacentHTML('beforeend', clone);
    // Les cartes dupliquées ne doivent pas être lues deux fois par un lecteur d'écran
    Array.from(avisTrack.children)
        .slice(avisTrack.children.length / 2)
        .forEach(carte => carte.setAttribute('aria-hidden', 'true'));
}

// --- "Lire la suite" pour les avis tronqués ---
document.querySelectorAll('.avis__texte').forEach(texte => {
    const bouton = texte.nextElementSibling;
    if (!bouton || !bouton.classList.contains('avis__lire-plus')) return;

    if (texte.scrollHeight > texte.clientHeight + 2) {
        bouton.style.display = 'block';
        bouton.addEventListener('click', () => {
            const ouvert = texte.classList.toggle('avis__texte--etendu');
            bouton.textContent = ouvert ? 'Cacher' : 'Lire la suite';
        });
    }
});

// --- Défilement auto + interaction manuelle (souris/doigt) ---
const avisOverflow = document.querySelector('.avis__overflow');
const reduireMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches;

if (avisOverflow && !reduireMotion) {
    let enPause = false;
    let enGlissement = false;
    let departX = 0;
    let scrollDepart = 0;

    function boucler() {
        if (!enPause && !enGlissement) {
            avisOverflow.scrollLeft += 0.5;
            if (avisOverflow.scrollLeft >= avisOverflow.scrollWidth / 2) {
                avisOverflow.scrollLeft -= avisOverflow.scrollWidth / 2;
            }
        }
        requestAnimationFrame(boucler);
    }

    avisOverflow.addEventListener('mouseenter', () => enPause = true);
    avisOverflow.addEventListener('mouseleave', () => enPause = false);

    avisOverflow.addEventListener('pointerdown', (e) => {
        enGlissement = true;
        avisOverflow.style.cursor = 'grabbing';
        departX = e.pageX;
        scrollDepart = avisOverflow.scrollLeft;
    });

    window.addEventListener('pointermove', (e) => {
        if (!enGlissement) return;
        avisOverflow.scrollLeft = scrollDepart - (e.pageX - departX);
    });

    window.addEventListener('pointerup', () => {
        if (!enGlissement) return;
        enGlissement = false;
        avisOverflow.style.cursor = 'grab';
    });

    requestAnimationFrame(boucler);
}