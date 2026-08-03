from pathlib import Path

import pytest

from backhaul.foundation import frontmatter, identity


def test_frontmatter_roundtrip(tmp_path: Path):
    p = tmp_path / "doc.md"
    p.write_text("---\ntitle: Hello\nnumber: 3\n---\nSome body text.\n", encoding="utf-8")

    doc = frontmatter.parse(p)
    assert doc.frontmatter == {"title": "Hello", "number": 3}
    assert doc.body.strip() == "Some body text."

    doc.frontmatter["status"] = "open"
    frontmatter.write(doc)

    reparsed = frontmatter.parse(p)
    assert reparsed.frontmatter["status"] == "open"
    assert reparsed.frontmatter["title"] == "Hello"


def test_frontmatter_rejects_missing_block(tmp_path: Path):
    p = tmp_path / "bad.md"
    p.write_text("no frontmatter here\n", encoding="utf-8")
    with pytest.raises(frontmatter.FrontmatterError):
        frontmatter.parse(p)


def test_identity_next_number():
    assert identity.next_number("UW", []) == 1
    assert identity.next_number("UW", [1, 2, 3]) == 4
    assert identity.next_number("UW", [1, 5, 2]) == 6


def test_numbered_identity_str():
    ident = identity.NumberedIdentity(uid="UW", number=2)
    assert str(ident) == "UW_002"


def test_path_identity_str():
    ident = identity.PathIdentity(category="knowledge-base/clients", slug="uw-tacoma")
    assert str(ident) == "knowledge-base/clients/uw-tacoma"
