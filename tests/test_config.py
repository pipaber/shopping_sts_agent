from shopping_agent.config import find_env_file, load_env, parse_env


def test_parse_env_handles_comments_quotes_and_export():
    text = "# comentario\nA=1\nexport B = 'dos palabras'\nC=\"x=y\"\n\nsin_igual\n"
    assert parse_env(text) == {"A": "1", "B": "dos palabras", "C": "x=y"}


def test_load_env_does_not_override_existing(tmp_path, monkeypatch):
    env = tmp_path / ".env"
    env.write_text("SA_TEST_NEW=archivo\nSA_TEST_SET=archivo\n", encoding="utf-8")
    monkeypatch.delenv("SA_TEST_NEW", raising=False)
    monkeypatch.setenv("SA_TEST_SET", "entorno")

    import os

    assert load_env(env) == {"SA_TEST_NEW": "archivo"}
    assert os.environ["SA_TEST_NEW"] == "archivo"
    assert os.environ["SA_TEST_SET"] == "entorno"
    monkeypatch.delenv("SA_TEST_NEW")


def test_find_env_file_stops_at_repo_root(tmp_path):
    repo = tmp_path / "repo"
    (repo / "src" / "pkg").mkdir(parents=True)
    (repo / "pyproject.toml").write_text("", encoding="utf-8")
    (tmp_path / ".env").write_text("FUERA=1", encoding="utf-8")  # fuera del repo: no se usa
    assert find_env_file(repo / "src" / "pkg") is None
    (repo / ".env").write_text("DENTRO=1", encoding="utf-8")
    assert find_env_file(repo / "src" / "pkg") == repo / ".env"
