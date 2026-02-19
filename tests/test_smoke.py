from codedoctor.runner import scan_repo


def test_scan_repo_smoke(tmp_path) -> None:
    repo = tmp_path
    report = scan_repo(repo_path=repo, apply_fixes=False, skip_tests=True)
    assert report.results
