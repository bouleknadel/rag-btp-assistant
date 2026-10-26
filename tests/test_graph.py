from typing import Any

import pytest
from langchain_core.callbacks import CallbackManagerForRetrieverRun
from langchain_core.documents import Document
from langchain_core.language_models import FakeListChatModel
from langchain_core.retrievers import BaseRetriever
from pydantic import SecretStr

from rag_btp.config import Settings
from rag_btp.graph import NOT_FOUND_MESSAGE, answer_question, build_rag_graph
from rag_btp.graph.rag_graph import extract_citations, format_context, parse_relevant_indices
from rag_btp.llm import NoLLMConfiguredError, build_chat_model, get_llm, provider_chain
from rag_btp.prompts import get_prompts

DOCS = [
    Document(
        page_content="[PPSPS — Tilleuls]\nArrêt de la grue lorsque le vent dépasse 72 km/h.",
        metadata={"source": "ppsps.pdf", "title": "PPSPS", "page": 1, "rerank_score": 0.97},
    ),
    Document(
        page_content="[CR n° 14 — Tilleuls]\nProchaine réunion le 11 mars 2026.",
        metadata={"source": "cr14.pdf", "title": "CR 14", "page": 1, "rerank_score": 0.12},
    ),
]


class FakeRetriever(BaseRetriever):
    """Retourne toujours les mêmes documents et mémorise les requêtes reçues."""

    documents: list[Document]
    queries: list[str] = []

    def _get_relevant_documents(
        self, query: str, *, run_manager: CallbackManagerForRetrieverRun, **kwargs: Any
    ) -> list[Document]:
        self.queries.append(query)
        return self.documents


def make_graph(responses: list[str], documents=DOCS, max_rewrites=1):
    retriever = FakeRetriever(documents=documents, queries=[])
    llm = FakeListChatModel(responses=responses)
    graph = build_rag_graph(retriever, llm, get_prompts(), max_query_rewrites=max_rewrites)
    return graph, retriever


# --- Utilitaires ------------------------------------------------------------------------
def test_parse_relevant_indices():
    assert parse_relevant_indices('{"pertinents": [2, 1, 2]}', 3) == [1, 2]
    assert parse_relevant_indices('Voici : {"pertinents": [1, 9]}', 3) == [1]
    assert parse_relevant_indices('{"pertinents": []}', 3) == []
    assert parse_relevant_indices("je ne sais pas", 3) is None


def test_extract_citations():
    assert extract_citations("Arrêt à 72 km/h [1]. Voir aussi [2, 3] et [4][5].") == {1, 2, 3, 4, 5}
    assert extract_citations("Aucune citation.") == set()


def test_format_context_numbers_documents_without_chunk_header():
    context = format_context(DOCS)
    assert context.startswith("[1] PPSPS — ppsps.pdf, p. 1\nArrêt de la grue")
    assert "[2] CR 14" in context
    assert "[PPSPS — Tilleuls]" not in context


# --- Chemins du graphe ---------------------------------------------------------------------
def test_relevant_documents_lead_to_answer_with_cited_sources():
    graph, retriever = make_graph(['{"pertinents": [1]}', "La grue s'arrête à 72 km/h [1]."])
    result = answer_question("Vent maximal pour la grue ?", graph=graph)

    assert result.status == "answered"
    assert "72 km/h" in result.answer
    assert [s["source"] for s in result.sources] == ["ppsps.pdf"]
    assert result.sources[0]["cited"] is True
    assert result.attempts == 1
    assert retriever.queries == ["Vent maximal pour la grue ?"]


def test_no_relevant_document_triggers_rewrite_then_answer():
    graph, retriever = make_graph(
        [
            '{"pertinents": []}',  # 1er grade : rien de pertinent
            "vitesse de vent maximale grue à tour",  # reformulation
            '{"pertinents": [1]}',  # 2e grade
            "Arrêt au-delà de 72 km/h [1].",  # réponse
        ]
    )
    result = answer_question("grue et vent ?", graph=graph)

    assert result.status == "answered"
    assert result.attempts == 2
    assert result.search_query == "vitesse de vent maximale grue à tour"
    assert retriever.queries == ["grue et vent ?", "vitesse de vent maximale grue à tour"]


def test_not_found_after_max_rewrites():
    graph, retriever = make_graph(['{"pertinents": []}', "autre requête", '{"pertinents": []}'])
    result = answer_question("Couleur des volets ?", graph=graph)

    assert result.status == "not_found"
    assert result.answer == NOT_FOUND_MESSAGE
    assert result.sources == []
    assert len(retriever.queries) == 2


def test_empty_retrieval_without_rewrite_is_not_found():
    graph, _ = make_graph([], documents=[], max_rewrites=0)
    result = answer_question("Question hors sujet", graph=graph)
    assert result.status == "not_found"


def test_unreadable_grade_keeps_all_documents():
    graph, _ = make_graph(["réponse non JSON", "Réponse [1]."])
    result = answer_question("Question", graph=graph)
    assert result.status == "answered"
    assert len(result.sources) == 2
    assert [s["cited"] for s in result.sources] == [True, False]


# --- Factory LLM ----------------------------------------------------------------------------
def _settings(**keys) -> Settings:
    values = {"groq_api_key": None, "openai_api_key": None, "google_api_key": None}
    values.update({k: SecretStr(v) for k, v in keys.items()})
    return Settings(
        _env_file=None, llm_provider="groq", llm_fallbacks=["openai", "gemini"], **values
    )


def test_provider_chain_skips_providers_without_key():
    assert provider_chain(_settings(google_api_key="g")) == ["gemini"]
    assert provider_chain(_settings(groq_api_key="x", google_api_key="g")) == ["groq", "gemini"]


def test_no_api_key_raises_clear_error():
    with pytest.raises(NoLLMConfiguredError):
        get_llm(_settings())


@pytest.mark.parametrize(
    ("provider", "key_field", "class_name"),
    [
        ("groq", "groq_api_key", "ChatGroq"),
        ("openai", "openai_api_key", "ChatOpenAI"),
        ("gemini", "google_api_key", "ChatGoogleGenerativeAI"),
    ],
)
def test_build_chat_model_for_each_provider(provider, key_field, class_name):
    model = build_chat_model(provider, _settings(**{key_field: "fake-key"}))
    assert type(model).__name__ == class_name


def test_fallback_is_used_when_primary_fails():
    class FailingModel(FakeListChatModel):
        def _call(self, *args, **kwargs):
            raise RuntimeError("quota dépassé")

    llm = FailingModel(responses=["x"]).with_fallbacks([FakeListChatModel(responses=["ok"])])
    assert llm.invoke("bonjour").content == "ok"


def test_gemini_3_uses_low_thinking_level():
    model = build_chat_model("gemini", _settings(google_api_key="fake-key"))
    assert model.thinking_level == "low"


def test_groq_gpt_oss_uses_low_reasoning_effort():
    model = build_chat_model("groq", _settings(groq_api_key="fake-key"))
    assert model.model_name == "openai/gpt-oss-120b"
    assert model.reasoning_effort == "low"


def test_each_failing_provider_is_logged(caplog, monkeypatch):
    import rag_btp.llm.factory as factory

    class FailingModel(FakeListChatModel):
        def _call(self, *args, **kwargs):
            raise RuntimeError("503 UNAVAILABLE")

    monkeypatch.setattr(factory, "build_chat_model", lambda p, s: FailingModel(responses=["x"]))
    llm = get_llm(_settings(groq_api_key="x", google_api_key="g"))
    with caplog.at_level("WARNING"), pytest.raises(RuntimeError):
        llm.invoke("bonjour")
    failures = [r.getMessage() for r in caplog.records if "Échec du LLM" in r.getMessage()]
    assert len(failures) == 2
    assert "groq/openai/gpt-oss-120b" in failures[0]
    assert "gemini/" in failures[1]
