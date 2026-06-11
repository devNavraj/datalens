from datalens.skills import TAXONOMY, extract_skills, skill_category


def test_extracts_basic_skills_case_insensitively() -> None:
    text = "Experience with PYTHON, Airflow and dbt; AWS preferred."
    assert {"python", "airflow", "dbt", "aws"} <= extract_skills(text)


def test_symbol_skills_match() -> None:
    assert "c++" in extract_skills("Legacy C++ modules")
    assert "c#" in extract_skills("Backend in C# and .NET")
    assert ".net" in extract_skills("Backend in C# and .NET")
    assert "ci/cd" in extract_skills("strong CI/CD culture")


def test_word_boundaries_prevent_substring_false_positives() -> None:
    assert "java" not in extract_skills("JavaScript developer")
    assert "javascript" not in extract_skills("We use JSON heavily")  # "js" inside json
    assert "excel" not in extract_skills("Excellent communication skills")
    assert "machine learning" not in extract_skills("html templates")  # "ml" inside html
    assert "r" not in extract_skills("Senior developer role")


def test_go_requires_disambiguating_context() -> None:
    assert "go" in extract_skills("Golang microservices")
    assert "go" in extract_skills("Go developer wanted")
    assert "go" not in extract_skills("We let nothing go to waste, go team!")


def test_aliases_map_to_canonical_name() -> None:
    assert "nodejs" in extract_skills("Node.js services")
    assert "scikit-learn" in extract_skills("models in sklearn")
    assert "kubernetes" in extract_skills("deployed on k8s")
    assert "genai" in extract_skills("building LLM applications")


def test_empty_and_skill_free_text() -> None:
    assert extract_skills("") == set()
    assert extract_skills("We sell flowers in Sydney.") == set()


def test_every_taxonomy_entry_has_category_and_matches_itself() -> None:
    for skill in TAXONOMY:
        assert skill_category(skill)  # no KeyError, non-empty


def test_skill_category_unknown_skill_raises_value_error() -> None:
    import pytest

    with pytest.raises(ValueError, match="not in TAXONOMY"):
        skill_category("underwater-basket-weaving")
