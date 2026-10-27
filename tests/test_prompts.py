import pytest
from langchain_core.language_models import FakeListChatModel

from rag_btp.graph import answer_question
from rag_btp.graph.rag_graph import parse_relevant_indices
from rag_btp.prompts import LATEST_VERSION, VERSIONS, get_prompts
from test_graph import DOCS, make_graph


@pytest.mark.parametrize("version", list(VERSIONS))
def test_each_version_has_expected_variables(version):
    prompts = get_prompts(version)
    assert prompts.version == version
    assert set(prompts.grade.input_variables) == {"question", "context"}
    assert set(prompts.rewrite.input_variables) == {"question"}
    assert set(prompts.answer.input_variables) == {"question", "context"}
    assert set(prompts.summary.input_variables) == {"report"}


@pytest.mark.parametrize("version", list(VERSIONS))
def test_prompts_render_without_error(version):
    prompts = get_prompts(version)
    messages = prompts.answer.format_messages(question="Vent maximal ?", context="[1] PPSPS")
    assert "Vent maximal ?" in messages[-1].content
    # Les accolades JSON des exemples doivent être échappées (pas de variable fantôme).
    prompts.grade.format_messages(question="q", context="c")
    prompts.summary.format_messages(report="Rapport du jour")


def test_latest_version_is_default():
    assert LATEST_VERSION == "v3"
    assert get_prompts("v3").version == "v3"


def test_unknown_version_raises():
    with pytest.raises(ValueError):
        get_prompts("v99")


def test_later_versions_enforce_not_found_and_citations():
    for version in ("v2", "v3"):
        system = get_prompts(version).answer.messages[0].prompt.template
        assert "Je n'ai pas trouvé cette information" in system
        assert "[2]" in system


def test_parse_v3_evaluations_format():
    text = """{"evaluations": [
        {"extrait": 1, "raison": "donne le délai de 30 jours", "pertinent": true},
        {"extrait": 2, "raison": "autre chantier", "pertinent": false},
        {"extrait": 3, "raison": "liste des réserves", "pertinent": "true"}
    ]}"""
    assert parse_relevant_indices(text, 3) == [1, 3]


def test_graph_works_with_v3_grade_format():
    graph, _ = make_graph(
        [
            '{"evaluations": [{"extrait": 1, "raison": "72 km/h", "pertinent": true}, '
            '{"extrait": 2, "raison": "hors sujet", "pertinent": false}]}',
            "Arrêt de la grue au-delà de 72 km/h [1].",
        ]
    )
    result = answer_question("Vent maximal ?", graph=graph)
    assert result.status == "answered"
    assert [d["kept"] for d in result.retrieved] == [True, False]
    assert result.grade_raw.startswith('{"evaluations"')


def test_summary_prompt_v3_requests_json_fields():
    system = get_prompts("v3").summary.messages[0].prompt.template
    for field in ("resume", "problemes", "securite", "actions", "chiffres_cles"):
        assert f'"{field}"' in system


def test_fake_llm_sanity():
    # Garde-fou : le faux LLM des tests renvoie les réponses dans l'ordre.
    llm = FakeListChatModel(responses=["a", "b"])
    assert [llm.invoke("x").content, llm.invoke("x").content] == ["a", "b"]
    assert DOCS
