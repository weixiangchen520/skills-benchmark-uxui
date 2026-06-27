from types import SimpleNamespace

from skills_benchmark_uxui.graders.static_checks import static_check
from skills_benchmark_uxui.models.trace import Trace


def test_static_check_accepts_self_contained_html(tmp_path) -> None:
    html = "<html><body><h1>Harbor</h1>" + "<section></section>" * 10 + "</body></html>"
    (tmp_path / "index.html").write_text(html, encoding="utf-8")
    ctx = SimpleNamespace(
        trace=Trace(task_id="U01en_demo", trial=1, model_id="test"),
        workdir=str(tmp_path),
    )

    passed, score, rationale = static_check(
        {
            "artifact": "index.html",
            "assertions": ["exists", "self_contained_html"],
            "must_include": ["Harbor"],
            "min_occurrences": {"<section": 10},
        },
        ctx,
    )

    assert passed is True
    assert score == 1.0
    assert "passed" in rationale


def test_static_check_rejects_network_assets(tmp_path) -> None:
    (tmp_path / "index.html").write_text(
        '<html><body><script src="https://example.com/app.js"></script></body></html>',
        encoding="utf-8",
    )
    ctx = SimpleNamespace(
        trace=Trace(task_id="U01en_demo", trial=1, model_id="test"),
        workdir=str(tmp_path),
    )

    passed, score, rationale = static_check(
        {"artifact": "index.html", "assertions": ["exists", "self_contained_html"]},
        ctx,
    )

    assert passed is False
    assert score == 0.0
    assert "external network assets" in rationale
