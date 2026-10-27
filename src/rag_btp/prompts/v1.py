"""Prompts — version 1 (première version, volontairement simple).

Objectif de la v1 : faire fonctionner le graphe de bout en bout.
Ses limites seront mesurées puis corrigées dans les versions suivantes.
"""

from langchain_core.prompts import ChatPromptTemplate

VERSION = "v1"

GRADE_PROMPT = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            "Tu évalues la pertinence d'extraits de documents de chantier pour une question. "
            'Réponds uniquement en JSON : {{"pertinents": [numéros des extraits pertinents]}}.',
        ),
        ("human", "Question : {question}\n\nExtraits :\n{context}"),
    ]
)

REWRITE_PROMPT = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            "Reformule la question pour améliorer la recherche dans des documents de chantier BTP. "
            "Réponds uniquement par la question reformulée.",
        ),
        ("human", "{question}"),
    ]
)

ANSWER_PROMPT = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            "Tu es un assistant pour les équipes de chantier BTP. "
            "Réponds à la question à partir du contexte fourni. "
            "Cite les extraits utilisés avec leur numéro entre crochets, par exemple [1].",
        ),
        ("human", "Contexte :\n{context}\n\nQuestion : {question}"),
    ]
)

SUMMARY_PROMPT = ChatPromptTemplate.from_messages(
    [
        ("system", "Résume ce rapport de chantier en quelques points clés."),
        ("human", "{report}"),
    ]
)
