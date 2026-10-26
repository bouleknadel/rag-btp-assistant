"""Contenu du corpus de démonstration (documents BTP synthétiques).

Tous les noms d'entreprises, de personnes et de chantiers sont fictifs.
Deux chantiers sont simulés :

- ``tilleuls``    : Résidence Les Tilleuls, 42 logements collectifs R+4 (Villeurbanne),
                    en phase gros œuvre ;
- ``jean-moulin`` : extension du groupe scolaire Jean Moulin (Bron),
                    en phase de second œuvre / réception.

Convention de nommage : ``<chantier>__<type>__<nom>.<ext>``.
Le contenu est écrit en Markdown simplifié (titres ``#``/``##``, listes ``-``),
rendu en PDF ou écrit tel quel selon l'extension.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class DemoDocument:
    filename: str
    content: str


DOCUMENTS: list[DemoDocument] = [
    # ======================================================================
    # Chantier 1 : Résidence Les Tilleuls
    # ======================================================================
    DemoDocument(
        "tilleuls__geotechnique__synthese-etude-g2-avp.pdf",
        """# Synthèse de l'étude géotechnique G2 AVP
## Résidence Les Tilleuls — 42 logements, 18 rue des Tilleuls, 69100 Villeurbanne

Bureau d'études géotechniques : Géosol Rhône
Rapport n° GR-2025-0412, indice B, du 30 septembre 2025
Maître d'ouvrage : Rhône Habitat Promotion

## 1. Contexte

Le projet comprend un bâtiment de logements collectifs en R+4 sur un niveau de sous-sol
à usage de parking (42 places). L'emprise au sol est d'environ 1 150 m².
La campagne de reconnaissance a comporté 4 sondages pressiométriques descendus à 15 m,
2 sondages à la pelle mécanique et la pose d'un piézomètre.

## 2. Contexte géologique

- De 0 à 0,8 m : remblais hétérogènes limono-graveleux.
- De 0,8 à 4,5 m : argiles limoneuses brunes, plastiques, sensibles à l'eau.
- Au-delà de 4,5 m : graves sablo-limoneuses compactes (alluvions fluvio-glaciaires),
  pressions limites supérieures à 2 MPa.

## 3. Hydrogéologie

Le niveau de la nappe a été mesuré à 6,20 m de profondeur par rapport au terrain naturel
le 12 septembre 2025. Le niveau des plus hautes eaux (EH) est estimé à 5,40 m de profondeur.
Le fond de fouille du sous-sol étant arrêté à 3,80 m de profondeur, aucun cuvelage n'est requis ;
un drainage périphérique et un radier drainant sont toutefois recommandés.

## 4. Recommandations pour les fondations

- Fondations superficielles par semelles filantes et isolées ancrées dans les graves
  sablo-limoneuses, à une profondeur minimale de 3,80 m sous le terrain naturel.
- Contrainte de calcul admissible à l'ELS : 0,35 MPa ; à l'ELU : 0,50 MPa.
- Tassements estimés inférieurs à 1,5 cm ; tassements différentiels inférieurs à 1 cm.
- Les argiles limoneuses ne doivent pas servir d'assise : purge obligatoire si rencontrées
  en fond de fouille.
- Terrassements : talutage provisoire à 3H/2V au-dessus de la nappe ;
  protection des fonds de fouille par béton de propreté dès l'ouverture.

## 5. Mission suivante

Une mission G3 (étude et suivi géotechniques d'exécution) devra être confiée à l'entreprise
de terrassement, et une mission G4 (supervision) au maître d'ouvrage.
""",
    ),
    DemoDocument(
        "tilleuls__cctp__lot-02-gros-oeuvre.pdf",
        """# CCTP — Lot n° 02 : Gros œuvre
## Résidence Les Tilleuls — 42 logements collectifs

Maître d'ouvrage : Rhône Habitat Promotion
Maître d'œuvre : Atelier d'architecture Lumen
Bureau de contrôle : Contrôle Alpes Ingénierie
Titulaire du lot : BTP Rhodanien SAS

## Article 2.1 — Normes et documents de référence

Les ouvrages sont exécutés conformément aux NF DTU 21 (exécution des ouvrages en béton),
NF DTU 20.1 (maçonnerie de petits éléments), à la norme NF EN 206/CN (béton) et à
l'Eurocode 2 (NF EN 1992-1-1) pour le dimensionnement.

## Article 2.4 — Bétons

- Béton de propreté : C16/20, épaisseur minimale 5 cm.
- Fondations (semelles, longrines) : C25/30, classe d'exposition XC2.
- Voiles et poteaux intérieurs : C30/37, classe d'exposition XC1.
- Voiles de façade : C30/37, classe d'exposition XC4, XF1.
- Dalles et planchers : C25/30, classe d'exposition XC1.
- Dimension maximale des granulats (Dmax) : 20 mm.
- Ciment de type CEM III/A recommandé pour limiter l'empreinte carbone.

## Article 2.5 — Armatures

Aciers à haute adhérence B500B. Enrobage nominal : 30 mm pour les parements intérieurs,
40 mm pour les parements extérieurs, 50 mm pour les éléments au contact du sol.
Le ferraillage de chaque élément fait l'objet d'une réception contradictoire avant
bétonnage, consignée sur une fiche d'autocontrôle.

## Article 2.6 — Mise en œuvre et cure

- Le bétonnage est interdit lorsque la température ambiante est inférieure à 5 °C,
  sauf dispositions particulières validées par le maître d'œuvre (béton chaud,
  accélérateur de prise, protection thermique).
- La cure des bétons est obligatoire pendant au moins 3 jours (produit de cure ou
  protection humide).
- Délai minimal de décoffrage des voiles : 18 heures à température supérieure à 10 °C.

## Article 2.7 — Tolérances

- Planéité des dalles : 7 mm sous la règle de 2 m.
- Aplomb des voiles : 1 cm par niveau, 2 cm cumulés sur la hauteur du bâtiment.

## Article 2.8 — Contrôles et essais

Un prélèvement de 3 éprouvettes est réalisé par tranche de 50 m³ de béton coulé,
avec au minimum un prélèvement par jour de coulage et par classe de béton.
Les éprouvettes sont écrasées à 7 et 28 jours par un laboratoire agréé.
Les résultats sont transmis au maître d'œuvre et au bureau de contrôle sous 48 heures.
""",
    ),
    DemoDocument(
        "tilleuls__fiche_technique__beton-c25-30-xc2.md",
        """# Fiche technique produit — Béton prêt à l'emploi C25/30 XC2

Fournisseur : Béton Lyonnais, centrale de Vaulx-en-Velin
Référence commerciale : BL-C25-XC2-S4-D20
Chantier : Résidence Les Tilleuls (fondations, dalles)

## Caractéristiques

- Classe de résistance : C25/30 (fck = 25 MPa sur cylindre à 28 jours).
- Classe d'exposition : XC2 (également conforme XC1).
- Ciment : CEM III/A 42,5 N CE PM-ES.
- Dosage minimal en ciment : 300 kg/m³.
- Rapport eau/ciment (E/C) maximal : 0,55.
- Dmax des granulats : 20 mm.
- Consistance : S4 (affaissement au cône d'Abrams compris entre 160 et 210 mm).
- Résistance moyenne visée à 28 jours : 33 MPa.
- Teneur en chlorures : Cl 0,40.

## Conditions de mise en œuvre

- Délai maximal de mise en œuvre : 1 h 30 après fabrication (heure du bon de livraison).
- Tout ajout d'eau sur chantier est interdit.
- Température du béton à la livraison : entre 5 °C et 30 °C.
- Par temps froid (température inférieure à 5 °C) : utiliser la variante « béton chaud »
  référence BL-C25-XC2-HIV, avec accélérateur de prise.
- Vibration obligatoire à l'aiguille vibrante.

## Stockage des bons de livraison

Chaque bon de livraison est conservé par le chef de chantier et rapproché du
plan de bétonnage. Les bons sont transmis hebdomadairement au conducteur de travaux.
""",
    ),
    DemoDocument(
        "tilleuls__fiche_technique__isolant-ite-laine-de-roche.md",
        """# Fiche technique — Isolation thermique par l'extérieur (ITE) en laine de roche

Chantier : Résidence Les Tilleuls — façades
Lot : n° 06, Isolation thermique par l'extérieur / enduit
Système : ITE sous enduit mince sur isolant en laine de roche

## Isolant

- Panneaux de laine de roche double densité, épaisseur 140 mm.
- Conductivité thermique déclarée : λ = 0,036 W/(m·K).
- Résistance thermique : R = 3,85 m²·K/W.
- Masse volumique : 140 kg/m³.
- Réaction au feu : Euroclasse A1 (incombustible).
- Format des panneaux : 1 200 × 600 mm.

## Mise en œuvre

- Fixation par collage (mortier-colle en plots et boudin périphérique)
  complétée par chevillage mécanique : 6 chevilles par m² en partie courante,
  8 chevilles par m² en zones de rive.
- Rail de départ en aluminium posé à 15 cm minimum au-dessus du sol fini.
- Pose des panneaux à joints décalés, sans joint ouvert supérieur à 2 mm.
- Recoupement par bande filante coupe-feu non nécessaire (isolant A1).
- Sous-enduit armé d'une trame en fibre de verre, puis finition enduit mince taloché.

## Conditions climatiques

Mise en œuvre interdite en dessous de 5 °C ou au-dessus de 30 °C, par vent fort ou
sous la pluie. Protéger l'enduit frais du soleil direct pendant 48 heures.
""",
    ),
    DemoDocument(
        "tilleuls__fiche_technique__etancheite-toiture-terrasse.txt",
        """# Fiche technique — Étanchéité de la toiture-terrasse inaccessible

Chantier : Résidence Les Tilleuls
Lot : n° 04, Étanchéité
Entreprise : Étanchéité Rhône-Alpes (ERA)
Surface : 1 080 m² de toiture-terrasse inaccessible avec protection gravillons

## Complexe d'étanchéité

- Support : dalle béton armé, pente de 1,5 % vers les évacuations d'eaux pluviales.
- Pare-vapeur : feuille bitumineuse aluminium soudée.
- Isolant : panneaux de polyuréthane (PIR) de 120 mm, λ = 0,022 W/(m·K), R = 5,45 m²·K/W.
- Revêtement : bicouche en bitume élastomère SBS (première couche fixée mécaniquement,
  seconde couche soudée en plein).
- Protection : gravillons roulés 5/15, épaisseur 4 cm minimum.

## Points singuliers

- Relevés d'étanchéité : hauteur minimale de 15 cm au-dessus de la protection.
- Évacuations des eaux pluviales : 6 naissances EP de diamètre 100 mm
  et 2 trop-pleins.
- Joint de dilatation traité par un profilé spécifique avec soufflet.

## Contrôles

- Essai d'étanchéité par mise en eau pendant 48 heures avant pose de la protection,
  sur la totalité de la surface, avec procès-verbal signé par l'entreprise et le maître d'œuvre.
- Garantie décennale et garantie produit de 10 ans du fabricant de membranes.
""",
    ),
    DemoDocument(
        "tilleuls__compte_rendu__reunion-chantier-14.pdf",
        """# Compte-rendu de réunion de chantier n° 14
## Résidence Les Tilleuls — 42 logements

Date : mercredi 4 mars 2026, 9 h 00, bungalow de chantier
Rédacteur : Atelier d'architecture Lumen (maîtrise d'œuvre d'exécution)

## Présents

- Rhône Habitat Promotion (MOA) : M. Hugo Perrin
- Atelier Lumen (MOE) : Mme Sarah Benali
- BTP Rhodanien SAS (lot 02) : M. Julien Marchand, conducteur de travaux
- Contrôle Alpes Ingénierie (bureau de contrôle) : M. Paul Girard
- Coordination SPS : Mme Claire Dubois (Sécurité Chantiers Conseil)
- Absent excusé : Étanchéité Rhône-Alpes (lot 04)

## 1. Avancement

- La dalle haute du R+2 a été coulée le 26 février 2026 (86 m³).
- Les voiles du R+3 sont en cours de coffrage et de ferraillage (60 % réalisés).
- Le chantier accuse un retard de 6 jours ouvrés sur le planning contractuel,
  principalement dû aux intempéries (gel et neige) de la semaine 9.

## 2. Décisions

- BTP Rhodanien renforce l'équipe de coffrage de 2 compagnons à partir du 9 mars 2026.
- Un samedi travaillé est autorisé le 14 mars 2026 (accord MOA).
- Le planning de rattrapage sera présenté à la réunion n° 15.

## 3. Qualité

- Non-conformité NC-007 (fissure sur le voile V12 du R+2) : la proposition de
  réparation par injection de résine est attendue pour le 6 mars.
- Rappel : réception du ferraillage obligatoire avant chaque coulage.

## 4. Lots techniques et menuiseries

- Lot 05 Menuiseries extérieures : validation des échantillons attendue au 18 mars 2026.
- Les réservations pour les gaines de VMC du R+3 sont à valider par le lot 09.

## 5. Sécurité

- Rappel suite à la visite CSPS du 2 mars : garde-corps périphériques à maintenir en
  permanence, port du casque obligatoire sur toute l'emprise.
- Presqu'accident du 5 mars à traiter en réunion suivante.

Prochaine réunion : mercredi 11 mars 2026 à 9 h 00.
""",
    ),
    DemoDocument(
        "tilleuls__compte_rendu__reunion-chantier-15.pdf",
        """# Compte-rendu de réunion de chantier n° 15
## Résidence Les Tilleuls — 42 logements

Date : mercredi 11 mars 2026, 9 h 00, bungalow de chantier
Rédacteur : Atelier d'architecture Lumen

## Présents

- Rhône Habitat Promotion (MOA) : M. Hugo Perrin
- Atelier Lumen (MOE) : Mme Sarah Benali
- BTP Rhodanien SAS (lot 02) : M. Julien Marchand
- Étanchéité Rhône-Alpes (lot 04) : M. Karim Haddad
- Coordination SPS : Mme Claire Dubois

## 1. Avancement

- Grâce au renfort de l'équipe de coffrage, le retard est ramené de 6 à 3 jours ouvrés.
- Voiles du R+3 : coulage réalisé les 9 et 10 mars 2026.
- Démarrage du coffrage de la dalle haute du R+3 prévu le 16 mars 2026.
- Avancement global du lot gros œuvre : 52 %.

## 2. Planning de rattrapage

- Fin du gros œuvre maintenue au 30 avril 2026.
- Hors d'eau / hors d'air prévu le 15 juin 2026.
- Démarrage de l'étanchéité de la toiture-terrasse prévu le 4 mai 2026.

## 3. Qualité

- NC-007 : réparation du voile V12 par injection de résine époxy réalisée le
  9 mars 2026 par l'entreprise Répar'Béton ; avis favorable du bureau de contrôle.
  La non-conformité est soldée.
- Les résultats des essais à 7 jours sur la dalle R+2 sont conformes (24,2 MPa en moyenne).

## 4. Sécurité

- Presqu'accident du 5 mars (chute d'un serre-joint depuis le R+3) : plinthes posées
  sur toutes les plateformes de travail, zone de circulation balisée.
- Quart d'heure sécurité réalisé le 6 mars 2026 avec l'ensemble des compagnons.

## 5. Points divers

- Le maître d'ouvrage demande un reporting photo hebdomadaire de l'avancement.

Prochaine réunion : mercredi 18 mars 2026 à 9 h 00.
""",
    ),
    DemoDocument(
        "tilleuls__rapport_journalier__2026-02-26.md",
        """# Rapport journalier de chantier — 26 février 2026

Chantier : Résidence Les Tilleuls
Rédigé par : M. Thomas Leroy, chef de chantier (BTP Rhodanien SAS)

## Conditions météorologiques

- Température à 7 h 30 : 4 °C ; maximum dans la journée : 9 °C.
- Temps sec, vent faible.

## Effectifs

- BTP Rhodanien : 14 compagnons (dont 1 grutier).
- Sous-traitant ferraillage (Armatures Saône) : 3 personnes.

## Travaux réalisés

- Coulage de la dalle haute du R+2 : 86 m³ de béton C25/30 XC1, de 7 h 45 à 15 h 30.
- Compte tenu de la température matinale, utilisation de béton chaud avec
  accélérateur de prise et protection de la dalle par bâches isolantes en fin de journée.
- Réception du ferraillage de la dalle réalisée la veille (25 février) par le
  conducteur de travaux, fiche d'autocontrôle signée.
- Prélèvement de 3 séries de 3 éprouvettes (1 série par tranche d'environ 30 m³).

## Livraisons

- 11 toupies de béton (Béton Lyonnais), dernier bon de livraison à 14 h 50.

## Sécurité

- Aucun incident ni accident.
- Quart d'heure sécurité du matin sur le thème du travail en bordure de dalle.

## Observations

- Pompe à béton en panne de 10 h 10 à 10 h 40 ; reprise sans joint de reprise apparent.
""",
    ),
    DemoDocument(
        "tilleuls__rapport_hebdo__semaine-10.md",
        """# Rapport hebdomadaire d'avancement — Semaine 10 (du 2 au 6 mars 2026)

Chantier : Résidence Les Tilleuls
Rédacteur : M. Julien Marchand, conducteur de travaux (BTP Rhodanien SAS)

## Synthèse

- Avancement global du lot gros œuvre : 48 % (contre 44 % la semaine précédente).
- Retard constaté : 6 jours ouvrés sur le planning contractuel.
- Effectif moyen sur la semaine : 16 personnes.
- Journée d'intempérie : mardi 3 mars 2026 (neige, chantier arrêté).

## Travaux de la semaine

- Coffrage et ferraillage des voiles du R+3 (axes A à D).
- Décoffrage et nettoyage de la dalle R+2.
- Pose des réservations de plomberie et d'électricité dans la dalle R+3.

## Approvisionnements

- Livraison de 12 tonnes d'aciers HA B500B le 4 mars 2026.
- Livraison de banches supplémentaires le 5 mars 2026.

## Hygiène, sécurité, environnement

- Visite de la coordinatrice SPS le 2 mars 2026 : 4 observations, dont 1 levée immédiatement.
- Presqu'accident le 5 mars 2026 : chute d'un serre-joint depuis le R+3, aucun blessé.
- Tri des déchets : 2 bennes évacuées (bois et gravats inertes).

## Points d'attention

- Prévoir le renfort de l'équipe de coffrage (2 compagnons) à partir du 9 mars.
- Suivre le traitement de la non-conformité NC-007 sur le voile V12.
""",
    ),
    DemoDocument(
        "tilleuls__essais__resistance-beton-dalle-r2.pdf",
        """# Procès-verbal d'essais de compression sur éprouvettes de béton

Laboratoire : Labo Contrôle Est (laboratoire accrédité)
Rapport n° LCE-26-0318 du 27 mars 2026
Chantier : Résidence Les Tilleuls
Client : BTP Rhodanien SAS
Norme d'essai : NF EN 12390-3 (éprouvettes cylindriques 16 × 32 cm)

## Série 1 — Dalle haute R+2

Béton : C25/30 XC1, coulé le 26 février 2026
Résistance caractéristique requise : fck = 25 MPa

- Essais à 7 jours (5 mars 2026) : 24,1 MPa ; 23,6 MPa ; 24,8 MPa. Moyenne : 24,2 MPa.
- Essais à 28 jours (26 mars 2026) : 34,5 MPa ; 33,9 MPa ; 35,2 MPa. Moyenne : 34,5 MPa.

Conclusion : résistance à 28 jours conforme à la classe C25/30.

## Série 2 — Voiles R+2

Béton : C30/37 XC1, coulé le 19 février 2026
Résistance caractéristique requise : fck = 30 MPa

- Essais à 7 jours : 27,9 MPa ; 28,4 MPa ; 27,5 MPa. Moyenne : 27,9 MPa.
- Essais à 28 jours : 39,8 MPa ; 41,1 MPa ; 40,2 MPa. Moyenne : 40,4 MPa.

Conclusion : résistance à 28 jours conforme à la classe C30/37.

## Observations

Aucune anomalie de rupture constatée. Les éprouvettes ont été conservées en
bassin d'eau à 20 °C ± 2 °C jusqu'à la date d'essai.
""",
    ),
    DemoDocument(
        "tilleuls__non_conformite__nc-007-fissure-voile-v12.md",
        """# Fiche de non-conformité NC-007 — Fissure sur le voile V12

Chantier : Résidence Les Tilleuls
Émetteur : BTP Rhodanien SAS (service qualité)
Date de détection : 27 février 2026
Statut : soldée le 11 mars 2026

## Description

Fissure verticale traversante sur le voile V12, niveau R+2, file C.
Longueur : 1,20 m ; ouverture maximale mesurée : 0,3 mm.
Le voile V12 est un voile porteur intérieur en béton C30/37 XC1, épaisseur 18 cm.

## Analyse des causes

- Décoffrage réalisé 18 heures après le coulage alors que la température nocturne
  était descendue à 1 °C : le béton n'avait pas atteint une résistance suffisante.
- Retrait thermique accentué par l'absence de protection du voile après décoffrage.

## Traitement

- Proposition de réparation transmise le 6 mars 2026.
- Injection de résine époxy sous basse pression réalisée le 9 mars 2026 par
  l'entreprise spécialisée Répar'Béton.
- Avis favorable du bureau de contrôle Contrôle Alpes Ingénierie le 11 mars 2026.

## Actions correctives

- Délai minimal de décoffrage des voiles porté à 36 heures lorsque la
  température est inférieure à 8 °C.
- Protection thermique systématique des voiles après décoffrage en période froide.
- Sensibilisation des chefs d'équipe réalisée le 2 mars 2026.

## Coût

Coût de la réparation : 2 850 € HT, à la charge de BTP Rhodanien SAS.
""",
    ),
    DemoDocument(
        "tilleuls__securite__visite-csps-2026-03-02.pdf",
        """# Registre journal de coordination — Visite d'inspection CSPS

Chantier : Résidence Les Tilleuls
Coordonnatrice SPS : Mme Claire Dubois, Sécurité Chantiers Conseil
Date de la visite : lundi 2 mars 2026, de 10 h 00 à 11 h 30
Niveau de coordination : niveau 2

## Entreprises présentes

BTP Rhodanien SAS (gros œuvre), Armatures Saône (ferraillage),
Élec Confluence (électricité, réservations).

## Observations

- Observation 1 : garde-corps manquant au droit de la trémie d'escalier du R+3.
  Risque de chute de hauteur. Mise en place immédiate pendant la visite (observation levée).
- Observation 2 : deux compagnons du sous-traitant de ferraillage sans casque
  sur la zone du R+2. Rappel à l'ordre effectué ; délai : immédiat.
- Observation 3 : bouteilles de gaz (oxygène et acétylène) stockées couchées
  au pied de la grue. À stocker debout, attachées, dans une zone dédiée ventilée.
  Délai : 48 heures.
- Observation 4 : accès à la base de la grue non balisé.
  Mise en place d'un balisage et d'une signalisation. Délai : 1 semaine.

## Points positifs

- Cantonnement propre et conforme (vestiaires, réfectoire, sanitaires).
- Affichage des consignes d'urgence à jour.

## Prochaine visite

Prévue le lundi 16 mars 2026.
""",
    ),
    DemoDocument(
        "tilleuls__incident__presquaccident-chute-objet-2026-03-05.md",
        """# Rapport de presqu'accident — Chute d'objet

Chantier : Résidence Les Tilleuls
Date et heure : jeudi 5 mars 2026, 10 h 20
Rédigé par : M. Thomas Leroy, chef de chantier
Classification : presqu'accident (aucun blessé, aucun dégât matériel)

## Description des faits

Un serre-joint métallique (environ 2 kg) est tombé depuis la plateforme de travail
du R+3, côté façade nord, sur la zone de circulation piétonne située en contrebas.
Aucune personne ne se trouvait dans la zone au moment de la chute.

## Causes identifiées

- Absence de plinthe sur la plateforme de travail du R+3.
- Matériel stocké en bordure de plateforme.
- Zone de circulation non balisée sous la zone de travail en hauteur.

## Actions immédiates

- Arrêt des travaux sur la plateforme concernée pendant 1 heure.
- Pose de plinthes sur l'ensemble des plateformes de travail.
- Balisage de la zone de circulation et déviation du cheminement piéton.

## Actions préventives

- Quart d'heure sécurité le 6 mars 2026 sur le thème des chutes d'objets.
- Contrôle quotidien des plinthes par le chef d'équipe.
- Interdiction de stocker du matériel à moins de 1 m du bord des plateformes.

## Diffusion

Rapport transmis au conducteur de travaux, au service QSE de BTP Rhodanien et à la
coordinatrice SPS.
""",
    ),
    DemoDocument(
        "tilleuls__securite__ppsps-extrait.pdf",
        """# Plan particulier de sécurité et de protection de la santé (PPSPS) — Extrait

Entreprise : BTP Rhodanien SAS — Lot 02 Gros œuvre
Chantier : Résidence Les Tilleuls, 18 rue des Tilleuls, 69100 Villeurbanne
Version : indice C du 12 janvier 2026

## Organisation du chantier

- Horaires de travail : du lundi au vendredi, de 7 h 30 à 12 h 00 et de 13 h 00 à 17 h 00.
- Responsable sécurité de l'entreprise sur le chantier : M. Thomas Leroy, chef de chantier.
- Effectif prévisionnel en pointe : 22 personnes.

## Secours

- Sauveteurs secouristes du travail (SST) présents sur le chantier :
  M. Thomas Leroy et M. Antoine Morel.
- Trousse de secours et défibrillateur situés dans le bungalow de chantier.
- Numéros d'urgence : SAMU 15, pompiers 18, numéro d'urgence européen 112.
- Hôpital le plus proche : Hôpital Edouard Herriot, Lyon 3e (environ 15 minutes).

## Grue à tour

- Grue à tour de 40 m de flèche, charge en bout de flèche : 1,3 tonne.
- Arrêt obligatoire de la grue lorsque le vent dépasse 72 km/h ;
  mise en girouette en fin de poste.
- Vérification générale périodique tous les 6 mois par un organisme agréé.
- Grutier titulaire d'une autorisation de conduite et du CACES R487.

## Travaux en hauteur

- Protections collectives prioritaires : garde-corps périphériques, filets en sous-face,
  plateformes de travail avec plinthes.
- Port du harnais obligatoire lorsque la protection collective est impossible.

## Équipements de protection individuelle

Casque, chaussures de sécurité, gants et gilet haute visibilité obligatoires
sur toute l'emprise du chantier.
""",
    ),
    DemoDocument(
        "tilleuls__planning__jalons-2026.md",
        """# Planning directeur — Jalons principaux

Chantier : Résidence Les Tilleuls — 42 logements
Mise à jour : 11 mars 2026 (après réunion de chantier n° 15)

## Jalons

- Ordre de service de démarrage : 3 novembre 2025.
- Fin des terrassements et des fondations : 9 janvier 2026.
- Fin du gros œuvre : 30 avril 2026.
- Démarrage de l'étanchéité de la toiture-terrasse : 4 mai 2026.
- Hors d'eau / hors d'air : 15 juin 2026.
- Démarrage des cloisons et doublages : 22 juin 2026.
- Opérations préalables à la réception (OPR) : du 16 au 27 novembre 2026.
- Réception des travaux : 4 décembre 2026.
- Livraison aux acquéreurs : 15 décembre 2026.

## Durées

- Durée totale des travaux : 13,5 mois.
- Durée du gros œuvre : 6 mois.

## Risques identifiés sur le planning

- Intempéries hivernales sur la phase de gros œuvre (marge prévue : 10 jours).
- Délais d'approvisionnement des menuiseries extérieures (8 semaines après validation
  des échantillons).
""",
    ),
    # ======================================================================
    # Chantier 2 : extension du groupe scolaire Jean Moulin
    # ======================================================================
    DemoDocument(
        "jean-moulin__cctp__lot-05-menuiseries-exterieures.pdf",
        """# CCTP — Lot n° 05 : Menuiseries extérieures aluminium
## Extension du groupe scolaire Jean Moulin, Bron

Maître d'ouvrage : Ville de Bron (fictif pour la démonstration)
Maître d'œuvre : Studio Arcade Architectes
Titulaire du lot : Alu Concept Rhône

## Article 5.1 — Performances

- Menuiseries en aluminium à rupture de pont thermique.
- Coefficient de transmission thermique de la fenêtre : Uw ≤ 1,3 W/(m²·K).
- Vitrage isolant 4/16/4 avec lame d'argon, Ug = 1,1 W/(m²·K), facteur solaire g = 0,40.
- Classement air / eau / vent minimal : A*3 E*7B V*A2.
- Affaiblissement acoustique : Ra,tr ≥ 33 dB pour les façades sur rue.

## Article 5.2 — Sécurité des usagers

- Vitrages feuilletés de sécurité 44.2 obligatoires au rez-de-chaussée et pour toutes les
  parties vitrées situées à moins de 1 m du sol (protection des enfants).
- Limiteurs d'ouverture à 10 cm sur les ouvrants des salles de classe à l'étage.
- Poignées positionnées à 1,60 m minimum dans les salles de maternelle.

## Article 5.3 — Protections solaires

- Brise-soleil orientables (BSO) motorisés sur les façades sud et ouest,
  pilotés par une station météo (repli automatique au-delà de 50 km/h de vent).

## Article 5.4 — Teinte et finition

Thermolaquage RAL 7016 (gris anthracite), label Qualicoat classe 2.

## Article 5.5 — Réception

Contrôle de fonctionnement de 100 % des ouvrants et essai d'étanchéité à l'eau
sur 2 menuiseries choisies par le maître d'œuvre.
""",
    ),
    DemoDocument(
        "jean-moulin__fiche_technique__bardage-bois-meleze.txt",
        """# Fiche technique — Bardage bois en mélèze

Chantier : Extension du groupe scolaire Jean Moulin, Bron
Lot : n° 03, Ossature bois / bardage
Entreprise : Charpentes du Beaujolais

## Produit

- Essence : mélèze de Sibérie, sans traitement chimique (durabilité naturelle).
- Classe d'emploi : 3.1 (bois extérieur vertical, sans contact avec le sol).
- Lames à claire-voie de 21 mm d'épaisseur et 90 mm de largeur.
- Réaction au feu : D-s2,d0.
- Humidité du bois à la livraison : inférieure à 18 %.

## Mise en œuvre

- Pose verticale sur tasseaux bois, entraxe maximal de l'ossature : 60 cm.
- Lame d'air ventilée de 20 mm minimum entre le pare-pluie et le bardage.
- Pare-pluie HPV (hautement perméable à la vapeur) résistant aux UV.
- Fixation par vis inox A2, deux vis par lame et par appui.
- Grille anti-rongeurs en pied et en tête de bardage.

## Entretien

Grisaillement naturel du mélèze en 12 à 18 mois. Aucun entretien obligatoire ;
nettoyage à l'eau claire tous les 2 ans recommandé.
""",
    ),
    DemoDocument(
        "jean-moulin__compte_rendu__reunion-chantier-22.md",
        """# Compte-rendu de réunion de chantier n° 22

Chantier : Extension du groupe scolaire Jean Moulin, Bron
Date : mercredi 18 février 2026, 14 h 00
Rédacteur : Studio Arcade Architectes

## Présents

- Ville de Bron (MOA) : Mme Nadia Rousseau, service bâtiments
- Studio Arcade Architectes (MOE) : M. Lucas Fontaine
- Alu Concept Rhône (lot 05), Charpentes du Beaujolais (lot 03),
  Plâtres & Cloisons du Lyonnais (lot 08), Couleurs Lumière (lot 10 peinture)

## 1. Avancement général

- Bâtiment hors d'eau / hors d'air depuis le 15 janvier 2026.
- Cloisons et doublages : 95 % réalisés.
- Peinture : démarrage avec 1 semaine de retard (attente de séchage des enduits).
- Sols souples : démarrage prévu le 2 mars 2026.

## 2. Planning

- Opérations préalables à la réception (OPR) prévues le 23 mars 2026.
- Réception des travaux visée le 3 avril 2026, pour une mise en service
  à la rentrée des vacances de printemps (20 avril 2026).

## 3. Points techniques

- Brise-soleil orientables : la mise en service de la station météo est reportée au
  4 mars 2026 (attente du raccordement électrique).
- Le lot 08 doit reprendre les bandes de joints dans la salle 104 avant peinture.

## 4. Sécurité

- Coactivité importante : planning d'intervention par zone affiché dans le cantonnement.

Prochaine réunion : mercredi 25 février 2026 à 14 h 00.
""",
    ),
    DemoDocument(
        "jean-moulin__rapport_hebdo__semaine-11.md",
        """# Rapport hebdomadaire — Semaine 11 (du 9 au 13 mars 2026)

Chantier : Extension du groupe scolaire Jean Moulin, Bron
Rédacteur : M. Lucas Fontaine, Studio Arcade Architectes

## Synthèse

- Effectif moyen : 22 personnes, réparties sur 6 lots.
- Aucun accident, aucun presqu'accident déclaré.
- Avancement global des travaux : 91 %.

## Travaux de la semaine

- Mise en service du chauffage (pompe à chaleur air/eau) le 10 mars 2026.
- Mise en service de la ventilation double flux et premiers réglages de débits.
- Peinture : deuxième couche dans les salles 101 à 106.
- Pose des sols souples (PVC acoustique) au rez-de-chaussée.

## Incidents et aléas

- Coupure électrique générale de 3 heures le 11 mars 2026 lors du raccordement
  du tableau général basse tension (TGBT).

## Points d'attention avant les OPR

- Réglage des brise-soleil orientables à finaliser.
- Nettoyage de fin de chantier à prévoir la semaine 12.
""",
    ),
    DemoDocument(
        "jean-moulin__pv_reception__lot-08-platrerie.pdf",
        """# Procès-verbal de réception avec réserves — Lot n° 08 Plâtrerie

Chantier : Extension du groupe scolaire Jean Moulin, Bron
Date de réception : 24 mars 2026
Entreprise titulaire : Plâtres & Cloisons du Lyonnais
Maître d'ouvrage : Ville de Bron — Maître d'œuvre : Studio Arcade Architectes

## Décision

Le maître d'ouvrage prononce la réception des travaux du lot 08 avec réserves,
avec effet au 24 mars 2026. Le délai de levée des réserves est fixé à 30 jours,
soit au plus tard le 23 avril 2026.

## Liste des réserves (7 réserves)

- R1 : salle 104, fissure sur un joint de plaque au-dessus de la porte.
- R2 : salle 104, bande de joint apparente sur le mur nord.
- R3 : couloir du R+1, choc sur une cloison à proximité de l'escalier.
- R4 : sanitaires du rez-de-chaussée, trappe de visite mal ajustée.
- R5 : salle 106, défaut de planéité du plafond suspendu (flèche visible).
- R6 : bureau de la direction, angle sortant non protégé par cornière.
- R7 : local ménage, plaque hydrofuge non posée en pied de cloison.

## Signatures

Le présent procès-verbal est signé par le maître d'ouvrage, le maître d'œuvre et
l'entreprise. La garantie de parfait achèvement court à compter de la date de réception.
""",
    ),
]
