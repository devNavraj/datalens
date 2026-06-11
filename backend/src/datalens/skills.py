"""Deterministic skill extraction from job-ad text.

Taxonomy-based regex matching — intentionally not an LLM: results must be
reproducible, free, and fast across hundreds of thousands of descriptions.
Canonical skill -> (category, alias patterns). Aliases are matched
case-insensitively with boundaries that tolerate symbols like "+" and "#".
"""

import re
from dataclasses import dataclass


@dataclass(frozen=True)
class SkillDef:
    category: str
    aliases: tuple[str, ...]  # regex fragments, lowercase


TAXONOMY: dict[str, SkillDef] = {
    # Languages
    "python": SkillDef("language", ("python",)),
    "java": SkillDef("language", ("java",)),
    "javascript": SkillDef("language", ("javascript", "js")),
    "typescript": SkillDef("language", ("typescript", "ts")),
    # bare "go" is a common English word; require golang or a role/-lang context
    "go": SkillDef("language", ("golang", r"go(?=[ -](?:lang\b|developer|engineer|programming))")),
    "rust": SkillDef("language", ("rust",)),
    "c++": SkillDef("language", (r"c\+\+",)),
    "c#": SkillDef("language", ("c#",)),
    "scala": SkillDef("language", ("scala",)),
    "r": SkillDef("language", (r"r programming", r"\br\b(?= (?:language|programming|studio))")),
    "sql": SkillDef("language", ("sql",)),
    "bash": SkillDef("language", ("bash", "shell scripting")),
    # Frontend / frameworks
    "react": SkillDef("framework", ("react", "react\\.js", "reactjs")),
    "nextjs": SkillDef("framework", (r"next\.js", "nextjs")),
    "angular": SkillDef("framework", ("angular",)),
    "vue": SkillDef("framework", (r"vue(?:\.js)?",)),
    "nodejs": SkillDef("framework", (r"node\.js", "nodejs", "node js")),
    "django": SkillDef("framework", ("django",)),
    "fastapi": SkillDef("framework", ("fastapi", "fast api")),
    "flask": SkillDef("framework", ("flask",)),
    "spring": SkillDef("framework", ("spring boot", "spring framework", "spring")),
    ".net": SkillDef("framework", (r"\.net", "dotnet")),
    # Cloud
    "aws": SkillDef("cloud", ("aws", "amazon web services")),
    "azure": SkillDef("cloud", ("azure",)),
    "gcp": SkillDef("cloud", ("gcp", "google cloud")),
    # Data engineering
    "airflow": SkillDef("data", ("airflow",)),
    "dbt": SkillDef("data", ("dbt",)),
    "spark": SkillDef("data", ("spark", "pyspark")),
    "kafka": SkillDef("data", ("kafka",)),
    "hadoop": SkillDef("data", ("hadoop",)),
    "snowflake": SkillDef("data", ("snowflake",)),
    "databricks": SkillDef("data", ("databricks",)),
    "redshift": SkillDef("data", ("redshift",)),
    "bigquery": SkillDef("data", ("bigquery", "big query")),
    "etl": SkillDef("data", ("etl", "elt")),
    "data warehouse": SkillDef(
        "data", ("data warehouse", "data warehousing", "data lakehouse", "data lake")
    ),
    # Databases
    "postgresql": SkillDef("database", ("postgres", "postgresql")),
    "mysql": SkillDef("database", ("mysql",)),
    "sql server": SkillDef("database", ("sql server", "mssql")),
    "mongodb": SkillDef("database", ("mongodb", "mongo")),
    "redis": SkillDef("database", ("redis",)),
    "elasticsearch": SkillDef("database", ("elasticsearch", "elastic search")),
    # ML / AI
    "machine learning": SkillDef("ml_ai", ("machine learning", r"\bml\b")),
    "deep learning": SkillDef("ml_ai", ("deep learning", "neural network")),
    "nlp": SkillDef("ml_ai", ("nlp", "natural language processing")),
    "computer vision": SkillDef("ml_ai", ("computer vision",)),
    "pytorch": SkillDef("ml_ai", ("pytorch", "torch")),
    "tensorflow": SkillDef("ml_ai", ("tensorflow",)),
    "scikit-learn": SkillDef("ml_ai", (r"scikit[ -]learn", "sklearn")),
    "pandas": SkillDef("ml_ai", ("pandas",)),
    "numpy": SkillDef("ml_ai", ("numpy",)),
    "genai": SkillDef("ml_ai", ("genai", "generative ai", r"\bllms?\b", "large language model")),
    "rag": SkillDef("ml_ai", (r"\brag\b", "retrieval[ -]augmented")),
    "langchain": SkillDef("ml_ai", ("langchain",)),
    "mlops": SkillDef("ml_ai", ("mlops", "ml ops")),
    # DevOps / tooling
    "docker": SkillDef("devops", ("docker",)),
    "kubernetes": SkillDef("devops", ("kubernetes", "k8s")),
    "terraform": SkillDef("devops", ("terraform",)),
    "ci/cd": SkillDef("devops", (r"ci/cd", "cicd", "continuous integration")),
    "github actions": SkillDef("devops", ("github actions",)),
    "jenkins": SkillDef("devops", ("jenkins",)),
    "git": SkillDef("devops", (r"\bgit\b",)),
    "linux": SkillDef("devops", ("linux",)),
    # Analytics / BI
    "power bi": SkillDef("analytics", ("power bi", "powerbi")),
    "tableau": SkillDef("analytics", ("tableau",)),
    "looker": SkillDef("analytics", ("looker",)),
    "excel": SkillDef("analytics", ("excel",)),
    # Ways of working
    "agile": SkillDef("practice", ("agile", "scrum")),
}

# Boundary chars: word chars plus the symbols that appear inside skill tokens,
# so "c++" doesn't match inside "c++17" boundaries wrongly, "js" not inside "json".
_BOUNDARY_LEFT = r"(?<![\w+#./-])"
_BOUNDARY_RIGHT = r"(?![\w+#])"


def _compile(aliases: tuple[str, ...]) -> re.Pattern[str]:
    body = "|".join(f"(?:{alias})" for alias in aliases)
    return re.compile(f"{_BOUNDARY_LEFT}(?:{body}){_BOUNDARY_RIGHT}", re.IGNORECASE)


_PATTERNS: dict[str, re.Pattern[str]] = {
    skill: _compile(spec.aliases) for skill, spec in TAXONOMY.items()
}


def extract_skills(text: str) -> set[str]:
    """Return canonical skill names found in free text."""
    if not text:
        return set()
    return {skill for skill, pattern in _PATTERNS.items() if pattern.search(text)}


def skill_category(skill: str) -> str:
    spec = TAXONOMY.get(skill)
    if spec is None:
        raise ValueError(f"unknown skill {skill!r}; not in TAXONOMY")
    return spec.category
