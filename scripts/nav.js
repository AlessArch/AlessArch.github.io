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

// --- "Lire la suite" : ouvre l'avis complet dans une fenêtre ---
const avisModal = document.getElementById('avis-modal');
const avisModalTexte = document.getElementById('avis-modal-texte');
const avisModalNom = document.getElementById('avis-modal-nom');
const avisModalDate = document.getElementById('avis-modal-date');
const avisModalAvatar = document.getElementById('avis-modal-avatar');
let avisDeclencheur = null;

function ouvrirAvisModal(carte) {
    avisModalTexte.textContent = carte.querySelector('.avis__texte').textContent.trim();
    avisModalNom.textContent = carte.querySelector('.avis__auteur').textContent.trim();
    avisModalDate.textContent = carte.querySelector('.avis__date').textContent.trim();

    const avatar = carte.querySelector('.avis__avatar');
    avisModalAvatar.textContent = avatar.textContent;
    avisModalAvatar.style.backgroundColor = avatar.style.backgroundColor;

    avisModal.hidden = false;
}

function fermerAvisModal() {
    avisModal.hidden = true;
    if (avisDeclencheur) avisDeclencheur.focus();
}

document.querySelectorAll('.avis__texte').forEach(texte => {
    const bouton = texte.nextElementSibling;
    if (!bouton || !bouton.classList.contains('avis__lire-plus')) return;

    if (texte.scrollHeight > texte.clientHeight + 2) {
        bouton.style.display = 'block';
        bouton.addEventListener('click', () => {
            avisDeclencheur = bouton;
            ouvrirAvisModal(bouton.closest('.avis__carte'));
        });
    }
});

document.querySelectorAll('[data-avis-modal-fermer]').forEach(el => {
    el.addEventListener('click', fermerAvisModal);
});

document.addEventListener('keydown', (e) => {
    if (e.key === 'Escape' && !avisModal.hidden) fermerAvisModal();
});

// --- Défilement auto + interaction manuelle (souris/doigt) ---
const avisOverflow = document.querySelector('.avis__overflow');
const reduireMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches;

if (avisOverflow && !reduireMotion) {
    let position = avisOverflow.scrollLeft;
    let pauseJusqua = 0;
    let enSurvol = false;
    let enGlissement = false;
    let departX = 0;
    let scrollDepart = 0;
    let aBouge = false;

    function pauserTemporairement(duree = 2000) {
        pauseJusqua = Date.now() + duree;
    }

    function boucler() {
        if (!enGlissement && !enSurvol && Date.now() > pauseJusqua) {
            position += 0.5;
            const demiLargeur = avisOverflow.scrollWidth / 2;
            if (position >= demiLargeur) position -= demiLargeur;
            avisOverflow.scrollLeft = position;
        } else {
            position = avisOverflow.scrollLeft;
        }
        requestAnimationFrame(boucler);
    }

    avisOverflow.addEventListener('mouseenter', () => enSurvol = true);
    avisOverflow.addEventListener('mouseleave', () => enSurvol = false);

    avisOverflow.addEventListener('wheel', () => pauserTemporairement(), { passive: true });

    avisOverflow.addEventListener('pointerdown', (e) => {
        enGlissement = true;
        aBouge = false;
        avisOverflow.style.cursor = 'grabbing';
        departX = e.pageX;
        scrollDepart = avisOverflow.scrollLeft;
    });

    window.addEventListener('pointermove', (e) => {
        if (!enGlissement) return;
        aBouge = true;
        avisOverflow.scrollLeft = scrollDepart - (e.pageX - departX);
    });

    window.addEventListener('pointerup', () => {
        if (!enGlissement) return;
        enGlissement = false;
        avisOverflow.style.cursor = 'grab';
        if (aBouge) pauserTemporairement();
        position = avisOverflow.scrollLeft;
    });

    requestAnimationFrame(boucler);
}