#!/usr/bin/env python3
"""
ajouter_srcset.py — Ajoute srcset et sizes aux balises <img> des heros.

Le script repère, dans les pages HTML de la racine, les balises <img> dont
le src correspond à une image de hero, puis insère un srcset listant les
variantes générées par generer_heros.py.

Il détecte l'indentation de la ligne src= et s'y aligne : les cinq balises
concernées sont indentées différemment selon les pages.

Idempotent : une balise qui possède déjà un srcset est laissée telle quelle.
À lancer APRÈS generer_heros.py, et AVANT build.py.
"""

import os
import re
import glob

# Même liste que generer_heros.py, mêmes largeurs.
HEROS = [
    "images/hero.webp",
    "images/hero-panneaux-solaires.webp",
    "images/hero-climatisation.webp",
    "images/hero-climatisation-gainable.webp",
    "images/equipe-groupe.webp",
]
LARGEURS = [640, 960, 1280, 1920]


def candidats(chemin):
    """Liste (url, largeur) des variantes réellement présentes sur le disque,
    plus l'original avec sa largeur réelle."""
    base, ext = os.path.splitext(chemin)
    resultat = []
    for largeur in LARGEURS:
        variante = f"{base}-{largeur}w{ext}"
        if os.path.exists(variante):
            resultat.append((f"/{variante}", largeur))

    from PIL import Image
    with Image.open(chemin) as im:
        resultat.append((f"/{chemin}", im.size[0]))
    return resultat


def main():
    # Pré-calcul : src -> chaîne srcset
    srcsets = {}
    for chemin in HEROS:
        if not os.path.exists(chemin):
            print(f"  ⚠️  {chemin} introuvable")
            continue
        srcsets[f"/{chemin}"] = candidats(chemin)

    total = 0
    for fichier in sorted(glob.glob("*.html")):
        with open(fichier, encoding="utf-8") as f:
            contenu = f.read()
        original = contenu

        for src, liste in srcsets.items():
            # Cible la ligne src= de cette image, en capturant son indentation.
            motif = re.compile(
                r'^([ \t]*)src="' + re.escape(src) + r'"[ \t]*$',
                re.M,
            )
            match = motif.search(contenu)
            if not match:
                continue

            indent = match.group(1)

            # Déjà traité ? On regarde les 400 caractères autour de la balise.
            debut = max(0, match.start() - 400)
            if 'srcset=' in contenu[debut:match.end() + 400]:
                print(f"  = {fichier} : {src} (srcset déjà présent)")
                continue

            # Le srcset s'aligne sur l'indentation de src=, avec les
            # candidats décalés pour rester lisibles.
            lignes = [f'{indent}srcset="{liste[0][0]} {liste[0][1]}w,']
            for url, largeur in liste[1:-1]:
                lignes.append(f'{indent}        {url} {largeur}w,')
            url, largeur = liste[-1]
            lignes.append(f'{indent}        {url} {largeur}w"')
            # Les heros occupent toute la largeur de la fenêtre.
            lignes.append(f'{indent}sizes="100vw"')

            bloc = match.group(0) + "\n" + "\n".join(lignes)
            contenu = contenu[:match.start()] + bloc + contenu[match.end():]
            print(f"  ✓ {fichier} : {src} ({len(liste)} candidats)")
            total += 1

        if contenu != original:
            with open(fichier, "w", encoding="utf-8") as f:
                f.write(contenu)

    print(f"\n{total} balise(s) modifiée(s).")


if __name__ == "__main__":
    main()