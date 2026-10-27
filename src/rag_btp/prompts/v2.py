"""Prompts — version 2.

Problèmes observés avec la v1 (voir docs/iterations.md) :

1. Faux négatifs au tri de pertinence (grade) : sur « Quel est le délai de levée des
   réserves du lot plâtrerie ? », le retriever renvoie le PV de réception en 1re position,
   mais le LLM le juge non pertinent → réponse « non trouvé » alors que l'information existe.
   Cause : la consigne « évalue la pertinence » est trop vague ; le modèle attend une
   correspondance quasi littérale et ne sait pas quoi faire en cas de doute.
2. Réponse : aucune consigne si le contexte ne contient pas la réponse (risque
   d'hallucination), ni sur la précision des chiffres, dates et unités.
3. Reformulation : le modèle paraphrase la question en ajoutant des mots génériques
   (« sur le chantier ») au lieu d'ajouter les termes métier utiles à la recherche.

Changements :
- grade : définition explicite d'un extrait pertinent (« contient tout ou partie de
  l'information, même formulée différemment »), règle « en cas de doute, garder »,
  numérotation rappelée, exemple de sortie JSON ;
- answer : réponse uniquement à partir du contexte, phrase imposée si l'information
  manque, chiffres et unités recopiés exactement, chaque affirmation citée ;
- rewrite : développer les sigles BTP et ajouter des synonymes métier.
"""

from langchain_core.prompts import ChatPromptTemplate

VERSION = "v2"

GRADE_PROMPT = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            "Tu es un ingénieur travaux qui trie des extraits de documents de chantier BTP.\n"
            "Pour la question posée, indique quels extraits sont PERTINENTS.\n\n"
            "Un extrait est pertinent s'il contient tout ou partie de l'information "
            "nécessaire pour répondre, même si elle est formulée avec d'autres mots "
            "(ex. « délai de levée des réserves » et « réserves à lever sous 30 jours »).\n"
            "Un extrait n'est pas pertinent s'il parle seulement du même chantier ou du même "
            "thème général sans apporter d'élément de réponse.\n"
            "En cas de doute, considère l'extrait comme pertinent.\n\n"
            "Les extraits sont numérotés [1], [2], etc. Réponds uniquement avec un objet JSON, "
            'sans texte autour, par exemple : {{"pertinents": [1, 3]}} '
            'ou {{"pertinents": []}} si aucun extrait ne convient.',
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
            "3. Recopie les chiffres, unités, dates et références exactement comme dans les "
            "extraits.\n"
            "4. Cite chaque affirmation avec le numéro de l'extrait entre crochets, ex. [2].\n"
            "5. Réponds en français, de façon concise.",
        ),
        ("human", "Extraits :\n{context}\n\nQuestion : {question}"),
    ]
)

# Synthèse de rapport — limites de la v1 : résumé libre de longueur variable, sections
# (sécurité, actions) oubliées selon les rapports, chiffres arrondis ou reformulés.
# v2 : plan imposé, « Non mentionné » plutôt qu'une invention, chiffres recopiés.
SUMMARY_PROMPT = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            "Tu synthétises des rapports de chantier BTP pour un conducteur de travaux.\n"
            "Rédige la synthèse en Markdown avec exactement ces sections :\n"
            "## Résumé (2 phrases maximum)\n"
            "## Avancement\n"
            "## Problèmes et retards\n"
            "## Sécurité\n"
            "## Actions à mener (action, responsable, échéance)\n"
            "## Chiffres clés\n"
            "Règles : utilise uniquement les informations du rapport ; écris « Non mentionné » "
            "si une section est vide ; recopie les chiffres, dates et unités exactement.",
        ),
        ("human", "Rapport :\n{report}"),
    ]
)
