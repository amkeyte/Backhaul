from pathlib import Path

import pytest

pylnk3 = pytest.importorskip("pylnk3")

from backhaul.modules.shortcuts import LnkBuildError, LnkSpec, build_and_verify, verify


def test_folder_shortcut_segments_all_folder(tmp_path: Path):
    out = tmp_path / "Project Folder"
    spec = LnkSpec(
        target=r"C:\_R Clone\Project_Managers\Aaron K\__Projects\Precision Electric",
        out=str(out),
        type="folder",
        name="Precision Electric",
    )
    out_path = build_and_verify(spec)
    assert out_path.endswith(".lnk")

    ok, problems = verify(out_path, spec.target, expect_all_folder=True)
    assert ok, problems


def test_file_shortcut_last_segment_is_file(tmp_path: Path):
    out = tmp_path / "domiResponse"
    spec = LnkSpec(
        target=r"C:\_R Clone\Project_Managers\Aaron K\__Projects\Shoreline School District\domiResponse.docx",
        out=str(out),
        type="file",
        name="Domi Response",
    )
    out_path = build_and_verify(spec)

    ok, problems = verify(out_path, spec.target, expect_all_folder=False)
    assert ok, problems


def test_refuses_overwrite_without_force(tmp_path: Path):
    out = tmp_path / "dup.lnk"
    spec = LnkSpec(target=r"C:\Somewhere", out=str(out), type="folder")
    build_and_verify(spec)

    with pytest.raises(LnkBuildError):
        build_and_verify(spec)

    # force=True should succeed
    spec.force = True
    build_and_verify(spec)
