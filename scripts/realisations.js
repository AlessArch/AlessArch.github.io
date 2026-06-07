// --- Filtres chantiers ---
const filtres = document.querySelectorAll('.filtre');
const chantiers = document.querySelectorAll('.chantier');

filtres.forEach(btn => {
    btn.addEventListener('click', () => {
        // Mettre à jour le bouton actif
        filtres.forEach(f => f.classList.remove('filtre--actif'));
        btn.classList.add('filtre--actif');

        const categorie = btn.dataset.filtre;

        chantiers.forEach(chantier => {
            if (categorie === 'tous' || chantier.dataset.categorie === categorie) {
                chantier.style.display = '';
            } else {
                chantier.style.display = 'none';
            }
        });
    });
});
