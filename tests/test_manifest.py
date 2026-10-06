"""Tests of the manifest module, called directly."""

from pathlib import Path

from island import manifest


MANIFEST = """<?xml version="1.0" encoding="UTF-8"?>
<manifest>
	<remote name="origin" fetch="git@island.test"/>
	<import name="extra.repos"/>
	<project name="alpha.git" path="alpha"/>
	<project name="beta.git" path="beta" tag="v0.1.0"/>
</manifest>
"""


def test_tag_manifest_sets_the_tags_and_keeps_the_imports(tmp_path: Path) -> None:
    file = tmp_path / "default.xml"
    file.write_text(MANIFEST)
    manifest.tag_manifest(str(file), [{"name": "alpha.git", "tag": "v1.0.0"}])
    content = file.read_text()
    assert '<project name="alpha.git" path="alpha" tag="v1.0.0"/>' in content
    assert '<import name="extra.repos"/>' in content


def test_tag_clear_removes_the_tags_and_keeps_the_imports(tmp_path: Path) -> None:
    file = tmp_path / "default.xml"
    file.write_text(MANIFEST)
    manifest.tag_clear(str(file))
    content = file.read_text()
    assert "tag=" not in content
    assert '<import name="extra.repos"/>' in content


def test_a_manifest_without_option_delivers_dev_on_master(tmp_path: Path) -> None:
    file = tmp_path / "default.xml"
    file.write_text('<?xml version="1.0" encoding="UTF-8"?>\n<manifest>\n\t<remote name="origin" fetch="git@island.test"/>\n</manifest>\n')
    mani = manifest.Manifest(str(file))
    assert (mani.deliver_develop, mani.deliver_master, mani.deliver_mode) == ("dev", "master", "fast_forward")
