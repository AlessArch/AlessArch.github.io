#!/usr/bin/env python3
"""
build.py — Propage partials/header.html et partials/footer.html
dans toutes les pages HTML du site SWATT, et injecte/maintient le
script anti-flash du mode sombre dans le <head> de chaque page.

Usage :
    python3 build.py

À lancer à chaque fois que header.html, footer.html ou le script
anti-flash (SCRIPT_THEME ci-dessous) est modifié, AVANT de commit/push.
Les fichiers HTML à la racine sont mis à jour sur place.
"""

import re
import glob
import os

RACINE = os.path.dirname(os.path.abspath(__file__))
PARTIALS = os.path.join(RACINE, "partials")

with open(os.path.join(PARTIALS, "header.html"), encoding="utf-8") as f:
    HEADER_SRC = f.read().rstrip("\n")

with open(os.path.join(PARTIALS, "footer.html"), encoding="utf-8") as f:
    FOOTER_SRC = f.read().rstrip("\n")

# --- Script anti-flash (FOUC) du mode sombre ---
# Doit être inline et exécuté avant le premier rendu, donc injecté directement
# dans le <head> de chaque page (build.py ne peut pas le charger depuis un
# fichier externe comme header/footer, sinon on recrée le flash qu'on évite).
# Lit la préférence manuelle enregistrée (localStorage) et l'applique tout de
# suite ; si rien n'est enregistré, le CSS prend le relais via
# prefers-color-scheme (voir main.css, section 36).
MARQUEUR_DEBUT_THEME = "<!-- SWATT: anti-flash mode sombre -->"
MARQUEUR_FIN_THEME = "<!-- /SWATT: anti-flash mode sombre -->"

SCRIPT_THEME = f"""{MARQUEUR_DEBUT_THEME}
    <script>
    (function () {{
        var theme = localStorage.getItem('swatt-theme');
        if (theme === 'dark' || theme === 'light') {{
            document.documentElement.setAttribute('data-theme', theme);
        }}
    }})();
    </script>
    {MARQUEUR_FIN_THEME}"""


def header_pour_page(nom_fichier):
    """Retourne le HTML du header avec aria-current="page" ajouté
    sur le(s) lien(s) qui pointent vers la page courante — sauf le
    lien bascule du menu déroulant "Nos prestations", qui ne se
    marque jamais lui-même."""
    cible = f'/{nom_fichier}'

    def ajouter_aria_current(match):
        balise_a = match.group(0)
        if 'nav__link--dropdown' in balise_a or 'nav__logo' in balise_a:
            return balise_a  # le lien bascule et le logo ne se marquent jamais
        if 'aria-current' in balise_a:
            return balise_a  # déjà présent, on ne double pas
        return balise_a[:-1] + ' aria-current="page">' if balise_a.endswith('>') else balise_a

    pattern = re.compile(
        r'<a href="' + re.escape(cible) + r'"[^>]*>'
    )
    return pattern.sub(ajouter_aria_current, HEADER_SRC)


def remplacer_bloc(contenu, balise_ouvrante, balise_fermante, remplacement):
    debut = contenu.find(balise_ouvrante)
    if debut == -1:
        return contenu, False
    fin = contenu.find(balise_fermante, debut)
    if fin == -1:
        return contenu, False
    fin += len(balise_fermante)
    return contenu[:debut] + remplacement + contenu[fin:], True


def injecter_script_theme(contenu):
    """Insère SCRIPT_THEME juste après <meta charset="UTF-8"> s'il est absent,
    ou le remplace en place s'il est déjà présent (idempotent, comme pour le
    header/footer)."""
    if MARQUEUR_DEBUT_THEME in contenu:
        contenu_maj, ok = remplacer_bloc(
            contenu, MARQUEUR_DEBUT_THEME, MARQUEUR_FIN_THEME, SCRIPT_THEME
        )
        return contenu_maj, ok

    ancre = '<meta charset="UTF-8">'
    pos = contenu.find(ancre)
    if pos == -1:
        return contenu, False
    pos_insertion = pos + len(ancre)
    contenu_maj = (
        contenu[:pos_insertion] + "\n    " + SCRIPT_THEME + contenu[pos_insertion:]
    )
    return contenu_maj, True


def traiter_fichier(chemin):
    nom_fichier = os.path.basename(chemin)
    with open(chemin, encoding="utf-8") as f:
        contenu = f.read()

    header_final = header_pour_page(nom_fichier)

    contenu, ok_header = remplacer_bloc(
        contenu, '<header class="header">', '</header>', header_final
    )
    contenu, ok_footer = remplacer_bloc(
        contenu, '<footer class="footer">', '</footer>', FOOTER_SRC
    )
    contenu, ok_theme = injecter_script_theme(contenu)

    if not ok_header:
        print(f"  ⚠️  {nom_fichier} : aucun <header class=\"header\"> trouvé, ignoré")
    if not ok_footer:
        print(f"  ⚠️  {nom_fichier} : aucun <footer class=\"footer\"> trouvé, ignoré")
    if not ok_theme:
        print(f"  ⚠️  {nom_fichier} : <meta charset=\"UTF-8\"> introuvable, script thème non injecté")

    if ok_header or ok_footer or ok_theme:
        with open(chemin, "w", encoding="utf-8") as f:
            f.write(contenu)
        print(f"  ✓ {nom_fichier}")


def main():
    fichiers = sorted(glob.glob(os.path.join(RACINE, "*.html")))
    print(f"Génération du header/footer sur {len(fichiers)} page(s)...")
    for chemin in fichiers:
        traiter_fichier(chemin)
    print("Terminé.")


if __name__ == "__main__":
    main()
