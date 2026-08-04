#!/usr/bin/env python3
"""
build.py — Propage partials/header.html et partials/footer.html
dans toutes les pages HTML du site SWATT.

Usage :
    python3 build.py

À lancer à chaque fois que header.html ou footer.html est modifié,
AVANT de commit/push. Les fichiers HTML à la racine sont mis à jour
sur place (le header/footer existant est remplacé par la version
à jour des partials).
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

    if not ok_header:
        print(f"  ⚠️  {nom_fichier} : aucun <header class=\"header\"> trouvé, ignoré")
    if not ok_footer:
        print(f"  ⚠️  {nom_fichier} : aucun <footer class=\"footer\"> trouvé, ignoré")

    if ok_header or ok_footer:
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
