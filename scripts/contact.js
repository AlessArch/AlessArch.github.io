const formContact = document.getElementById('form-contact');

if (formContact) {
    formContact.addEventListener('submit', async (e) => {
        e.preventDefault();

        const bouton = formContact.querySelector('.form__submit');
        const texteInitial = bouton.textContent;
        bouton.disabled = true;
        bouton.textContent = 'Envoi en cours...';

        try {
            const reponse = await fetch(formContact.action, {
                method: 'POST',
                body: new FormData(formContact),
                headers: { 'Accept': 'application/json' }
            });

            if (reponse.ok) {
                window.location.href = '/merci.html';
            } else {
                throw new Error('Erreur d\'envoi');
            }
        } catch (erreur) {
            bouton.disabled = false;
            bouton.textContent = texteInitial;
            alert('Une erreur est survenue. Merci de réessayer, ou appelez-nous directement au 06 50 54 71 58.');
        }
    });
}