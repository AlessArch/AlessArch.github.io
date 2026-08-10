#!/usr/bin/env python3
"""
generer_heros.py — Génère les variantes responsives des images de hero.

Pour chaque image listée dans HEROS, produit une version 640, 960, 1280 et
1920 px de large, à côté du fichier d'origine, en conservant le ratio.
Les largeurs supérieures ou égales à l'original sont ignorées : agrandir
une image n'apporte rien et alourdirait le fichier.

Nommage : images/hero.webp -> images/hero-1280w.webp

Le fichier d'origine n'est jamais modifié : il reste le candidat de plus
grande largeur dans le srcset.

Usage :
    pip3 install Pillow      (une seule fois)
    python3 generer_heros.py

À relancer uniquement si tu remplaces une image de hero.
"""

import os
from PIL import Image

# Images concernées : uniquement les heros, visibles immédiatement au
# chargement. Les photos de chantiers restent en une seule taille : elles
# sont en loading="lazy" sous la ligne de flottaison, et multiplier les
# fichiers compliquerait la procédure d'ajout d'un chantier.
HEROS = [
    "images/hero.webp",
    "images/hero-panneaux-solaires.webp",
    "images/hero-climatisation.webp",
    "images/hero-climatisation-gainable.webp",
    "images/equipe-groupe.webp",
]

LARGEURS = [640, 960, 1280, 1920]

# 78 suffit largement : ces images sont des fonds recouverts d'un voile
# sombre, avec du texte par-dessus. Aucun détail fin à préserver.
QUALITE = 78


def generer(chemin):
    if not os.path.exists(chemin):
        print(f"  ⚠️  {chemin} introuvable, ignoré")
        return

    base, ext = os.path.splitext(chemin)
    original = Image.open(chemin)
    largeur_src, hauteur_src = original.size
    poids_src = os.path.getsize(chemin) // 1024
    print(f"\n{chemin}  ({largeur_src}×{hauteur_src}, {poids_src} Ko)")

    for largeur in LARGEURS:
        if largeur >= largeur_src:
            print(f"  – {largeur}w ignoré (original plus petit)")
            continue

        hauteur = round(hauteur_src * largeur / largeur_src)
        sortie = f"{base}-{largeur}w{ext}"

        variante = original.copy()
        variante.thumbnail((largeur, hauteur), Image.LANCZOS)
        variante.save(sortie, "WEBP", quality=QUALITE, method=6)

        poids = os.path.getsize(sortie) // 1024
        gain = round((1 - poids / poids_src) * 100)
        print(f"  ✓ {sortie}  ({variante.size[0]}×{variante.size[1]}, "
              f"{poids} Ko, −{gain} %)")


def main():
    print("Génération des variantes responsives des heros…")
    for chemin in HEROS:
        generer(chemin)
    print("\nTerminé.")


if __name__ == "__main__":
    main()