from skills_benchmark_uxui.render import render_html_snapshot


def test_render_html_snapshot_static_fallback_counts_html(tmp_path) -> None:
    (tmp_path / "index.html").write_text(
        """
<!doctype html>
<html>
  <head><title>Harbor deck</title></head>
  <body>
    <section><h1>Problem</h1><p>Tidal forecasting is hard.</p></section>
    <section><h2>Solution</h2><p>Harbor API helps operators.</p></section>
    <a href="#demo">Demo</a>
    <button>Next</button>
    <svg aria-label="chart"></svg>
  </body>
</html>
""".lstrip(),
        encoding="utf-8",
    )

    snapshot = render_html_snapshot(workdir=tmp_path, artifact="index.html", use_playwright=False)

    assert snapshot.used_playwright is False
    assert snapshot.error is None
    assert snapshot.title == "Harbor deck"
    assert snapshot.section_count == 2
    assert snapshot.heading_count == 2
    assert snapshot.button_count == 1
    assert snapshot.image_count == 1
    assert snapshot.link_count == 1
    assert "Harbor API" in snapshot.body_text


def test_render_html_snapshot_reports_missing_artifact(tmp_path) -> None:
    snapshot = render_html_snapshot(workdir=tmp_path, artifact="missing.html", use_playwright=False)

    assert snapshot.section_count == 0
    assert snapshot.error is not None
    assert "artifact missing" in snapshot.error
