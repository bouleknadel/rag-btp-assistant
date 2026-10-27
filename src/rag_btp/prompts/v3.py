"""Prompts — version 3 (version active par défaut).

Limites restantes de la v2 :

1. Tri de pertinence : une liste de numéros sans justification reste fragile ; le
   modèle décide « en bloc » et peut écarter un extrait utile noyé parmi d'autres.
2. Contradictions entre documents : le corpus contient des informations qui évoluent
   dans le temps (ex. retard de 6 jours au CR n° 14, ramené à 3 jours au CR n° 15).
   La v2 peut citer l'ancienne valeur sans préciser de quelle date elle provient.
3. Format des réponses : longueur et structure variables, difficiles à lire sur
   chantier et à comparer lors de l'évaluation.

Changements :
- grade : évaluation extrait par extrait avec une courte justification avant la
  décision (raisonnement explicite → meilleur rappel), sortie JSON structurée ;
- answer : réponse directe en première phrase, détails éventuels en liste,
  priorité au document le plus récent en cas de contradiction (en le signalant),
  chantier précisé lorsque la question est ambiguë.
"""

from langchain_core.prompts import ChatPromptTemplate

VERSION = "v3"

GRADE_PROMPT = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            "Tu es un ingénieur travaux qui trie des extraits de documents de chantier BTP.\n"
            "Évalue CHAQUE extrait séparément pour la question posée :\n"
            "- pertinent = true si l'extrait contient tout ou partie de l'information "
            "nécessaire pour répondre, même formulée autrement ;\n"
            "- pertinent = false s'il parle seulement du même chantier ou du même thème "
            "sans élément de réponse ;\n"
            "- en cas de doute, pertinent = true.\n\n"
            "Donne d'abord une raison courte (moins de 15 mots), puis la décision.\n"
            "Réponds uniquement avec un objet JSON, sans texte autour, au format :\n"
            '{{"evaluations": [{{"extrait": 1, "raison": "...", "pertinent": true}}, '
            '{{"extrait": 2, "raison": "...", "pertinent": false}}]}}',
        ),
        ("human", "Question : {question}\n\nExtraits :\n{context}"),
    ]
)

REWRITE_PROMPT = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            "Tu réécris une question pour un moteur de recherche dans des documents de "
            "chantier BTP (comptes-rendus, PV, CCTP, PPSPS, fiches techniques, rapports).\n"
            "- Développe les sigles (CSPS, PPSPS, OPR, PV, CCTP, GO, ITE…) et garde le sigle.\n"
            "- Ajoute 2 ou 3 synonymes ou termes métier utiles.\n"
            "- Conserve les éléments précis (niveaux R+2, lots, dates, noms).\n"
            "- N'invente aucune information.\n"
            "Réponds uniquement par la requête réécrite, en une ligne.",
        ),
        ("human", "{question}"),
    ]
)

ANSWER_PROMPT = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            "Tu es un assistant pour les équipes de chantier BTP (conducteurs de travaux, "
            "chefs de chantier, maîtrise d'œuvre).\n"
            "Règles :\n"
            "1. Réponds uniquement à partir des extraits fournis, jamais de connaissances "
            "générales.\n"
            "2. Si les extraits ne contiennent pas la réponse, réponds exactement : "
            "« Je n'ai pas trouvé cette information dans les documents de chantier "
            "disponibles. »\n"
            "3. Commence par une phrase qui répond directement à la question. Ajoute "
            "ensuite, si utile, au plus 4 puces de détails.\n"
            "4. Recopie les chiffres, unités, dates et références exactement comme dans les "
            "extraits.\n"
            "5. Cite chaque affirmation avec le numéro de l'extrait entre crochets, ex. [2].\n"
            "6. Si des extraits se contredisent (valeur mise à jour), donne la valeur du "
            "document le plus récent et signale l'évolution avec les dates.\n"
            "7. Si la question ne précise pas le chantier et que les extraits concernent "
            "plusieurs chantiers, précise le chantier dans la réponse.\n"
            "8. Réponds en français, sans introduction ni formule de politesse.",
        ),
        ("human", "Extraits :\n{context}\n\nQuestion : {question}"),
    ]
)

# Synthèse de rapport — limite de la v2 : le Markdown est lisible mais difficile à
# exploiter automatiquement (API, notifications n8n, tableau de bord).
# v3 : sortie JSON validée par un schéma Pydantic côté API.
SUMMARY_PROMPT = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            "Tu synthétises des rapports de chantier BTP pour un conducteur de travaux.\n"
            "Règles : utilise uniquement les informations du rapport, n'invente rien ; "
            "recopie les chiffres, dates et unités exactement ; liste vide [] ou null si "
            "l'information est absente.\n"
            "Réponds uniquement avec un objet JSON, sans texte autour, au format :\n"
            '{{"resume": "2 phrases maximum", '
            '"avancement": "état d\'avancement ou null", '
            '"points_cles": ["..."], '
            '"problemes": ["retards, non-conformités, aléas"], '
            '"securite": ["incidents, observations, mesures"], '
            '"actions": [{{"action": "...", "responsable": "... ou null", '
            '"echeance": "... ou null"}}], '
            '"chiffres_cles": ["..."]}}',
        ),
        ("human", "Rapport :\n{report}"),
    ]
)
