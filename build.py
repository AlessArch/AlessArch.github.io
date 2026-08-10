#!/usr/bin/env python3
"""
build.py — Propage partials/header.html et partials/footer.html
dans toutes les pages HTML du site SWATT, injecte/maintient le
script anti-flash du mode sombre et le preload des polices dans
le <head>, et versionne les assets CSS/JS pour le cache navigateur.

Usage :
    python3 build.py

À lancer à chaque fois que header.html, footer.html, main.css,
un script JS ou le script anti-flash est modifié, AVANT de
commit/push. Les fichiers HTML à la racine sont mis à jour sur place.
"""

import re
import glob
import os
import hashlib

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

# --- Preload des polices ---
# Les @font-face sont déclarées dans main.css : sans preload, le navigateur
# ne découvre les woff2 qu'après avoir téléchargé ET parsé la feuille de
# style (3 requêtes en série). Le preload lance le téléchargement en
# parallèle du CSS.
# ATTENTION : l'attribut crossorigin est obligatoire même en same-origin.
# Les polices sont toujours récupérées en mode CORS anonyme ; sans lui, le
# navigateur télécharge le fichier deux fois.
MARQUEUR_DEBUT_PRELOAD = "<!-- SWATT: preload polices -->"
MARQUEUR_FIN_PRELOAD = "<!-- /SWATT: preload polices -->"

PRELOAD_POLICES = f"""{MARQUEUR_DEBUT_PRELOAD}
    <link rel="preload" href="/assets/fonts/inter-v20-latin-regular.woff2" as="font" type="font/woff2" crossorigin>
    <link rel="preload" href="/assets/fonts/inter-v20-latin-700.woff2" as="font" type="font/woff2" crossorigin>
    {MARQUEUR_FIN_PRELOAD}"""

# Point d'ancrage du preload : juste avant la feuille de style.
# On matche sans le guillemet fermant pour que l'ancre reste valide
# même une fois l'URL versionnée (main.css?v=xxxxxxxx).
ANCRE_CSS = '<link rel="stylesheet" href="/styles/main.css'

# --- Versionnement des assets (cache-busting) ---
# Empreinte du CONTENU, pas la date de modification : Git ne conserve pas
# les mtime, donc chaque déploiement Hostinger casserait le cache pour rien.
MOTIF_ASSET = re.compile(
    r'(href|src)="(/styles/[^"?]+\.css|/scripts/[^"?]+\.js)(?:\?v=[^"]*)?"'
)

_cache_empreintes = {}


def empreinte(chemin_url):
    """Hash court du contenu d'un fichier local, à partir de son URL absolue."""
    if chemin_url in _cache_empreintes:
        return _cache_empreintes[chemin_url]
    chemin_disque = os.path.join(RACINE, chemin_url.lstrip("/"))
    try:
        with open(chemin_disque, "rb") as f:
            h = hashlib.md5(f.read()).hexdigest()[:8]
    except FileNotFoundError:
        print(f"  ⚠️  Asset introuvable, non versionné : {chemin_url}")
        h = None
    _cache_empreintes[chemin_url] = h
    return h


def versionner_assets(contenu):
    """Ajoute ou met à jour ?v=<hash> sur les CSS et JS locaux."""
    def remplacer(match):
        attribut, chemin_url = match.group(1), match.group(2)
        h = empreinte(chemin_url)
        if h is None:
            return f'{attribut}="{chemin_url}"'
        return f'{attribut}="{chemin_url}?v={h}"'

    contenu_maj, nb = MOTIF_ASSET.subn(remplacer, contenu)
    return contenu_maj, nb > 0


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


def injecter_bloc_head(contenu, marqueur_debut, marqueur_fin, bloc, ancre, avant=False):
    """Insère un bloc dans le <head> s'il est absent, ou le remplace en
    place s'il est déjà présent (idempotent).
    `avant=True` insère avant l'ancre, sinon juste après."""
    if marqueur_debut in contenu:
        return remplacer_bloc(contenu, marqueur_debut, marqueur_fin, bloc)

    pos = contenu.find(ancre)
    if pos == -1:
        return contenu, False

    if avant:
        return contenu[:pos] + bloc + "\n    " + contenu[pos:], True
    pos_insertion = pos + len(ancre)
    return contenu[:pos_insertion] + "\n    " + bloc + contenu[pos_insertion:], True


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
    contenu, ok_theme = injecter_bloc_head(
        contenu, MARQUEUR_DEBUT_THEME, MARQUEUR_FIN_THEME,
        SCRIPT_THEME, '<meta charset="UTF-8">'
    )
    contenu, ok_preload = injecter_bloc_head(
        contenu, MARQUEUR_DEBUT_PRELOAD, MARQUEUR_FIN_PRELOAD,
        PRELOAD_POLICES, ANCRE_CSS, avant=True
    )
    contenu, ok_version = versionner_assets(contenu)

    if not ok_header:
        print(f"  ⚠️  {nom_fichier} : aucun <header class=\"header\"> trouvé, ignoré")
    if not ok_footer:
        print(f"  ⚠️  {nom_fichier} : aucun <footer class=\"footer\"> trouvé, ignoré")
    if not ok_theme:
        print(f"  ⚠️  {nom_fichier} : <meta charset=\"UTF-8\"> introuvable, script thème non injecté")
    if not ok_preload:
        print(f"  ⚠️  {nom_fichier} : lien vers main.css introuvable, preload non injecté")

    if ok_header or ok_footer or ok_theme or ok_preload or ok_version:
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