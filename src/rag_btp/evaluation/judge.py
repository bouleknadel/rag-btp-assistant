"""Juge LLM (« LLM-as-a-judge ») : compare la réponse de l'assistant à la référence."""

from __future__ import annotations

import json
import re

from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import Runnable
from pydantic import BaseModel

JUDGE_PROMPT = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            "Tu évalues un assistant qui répond à des questions sur des documents de chantier "
            "BTP. Compare la RÉPONSE de l'assistant à la RÉPONSE DE RÉFÉRENCE.\n\n"
            "- pertinent : la réponse traite bien la question posée (pas une autre question, "
            "pas un refus injustifié).\n"
            "- correct : les éléments essentiels de la référence sont présents (chiffres, "
            "dates, unités, noms) et rien ne la contredit. Une réponse plus détaillée que la "
            "référence reste correcte si les ajouts ne contredisent pas la référence. Une "
            "formulation différente est acceptée.\n\n"
            "Sois exigeant sur les valeurs numériques. Réponds uniquement avec un objet JSON, "
            "sans texte autour :\n"
            '{{"pertinent": true, "correct": true, "raison": "justification en 1 phrase"}}',
        ),
        (
            "human",
            "QUESTION : {question}\n\nRÉPONSE DE RÉFÉRENCE : {reference}\n\n"
            "RÉPONSE DE L'ASSISTANT : {answer}",
        ),
    ]
)


class JudgeVerdict(BaseModel):
    pertinent: bool
    correct: bool
    raison: str = ""

    @property
    def success(self) -> bool:
        return self.pertinent and self.correct


def parse_verdict(text: str) -> JudgeVerdict | None:
    match = re.search(r"\{.*\}", text, flags=re.DOTALL)
    if not match:
        return None
    try:
        return JudgeVerdict.model_validate(json.loads(match.group(0)))
    except (json.JSONDecodeError, ValueError):
        return None


def judge_answer(llm: Runnable, question: str, reference: str, answer: str) -> JudgeVerdict:
    """Fait évaluer une réponse par le juge. Lève ``ValueError`` si son verdict est illisible."""
    chain = JUDGE_PROMPT | llm | StrOutputParser()
    raw = chain.invoke(
        {"question": question, "reference": reference, "answer": answer},
        config={"run_name": "rag_btp_judge", "tags": ["evaluation", "judge"]},
    )
    verdict = parse_verdict(raw)
    if verdict is None:
        raise ValueError(f"Verdict du juge illisible : {raw[:200]!r}")
    return verdict
