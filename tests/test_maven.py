"""Tests of the reading and the change of the poms."""

import pytest

from island import maven


POM = """<?xml version="1.0" encoding="UTF-8"?>
<project xmlns="http://maven.apache.org/POM/4.0.0">
  <modelVersion>4.0.0</modelVersion>
  <groupId>org.atriasoft</groupId>
  <artifactId>gale</artifactId>
  <version>0.1.0</version>
	<!-- a comment kept as it is -->
	<dependencies>
		<dependency>
			<groupId>org.atriasoft</groupId>
			<artifactId>etk</artifactId>
			<version>0.1.0</version>
		</dependency>
		<dependency>
			<groupId>org.slf4j</groupId>
			<artifactId>slf4j-api</artifactId>
			<version>2.1.0</version>
		</dependency>
	</dependencies>
	<dependencyManagement>
		<dependencies>
			<dependency>
				<groupId>org.lwjgl</groupId>
				<artifactId>lwjgl-bom</artifactId>
				<version>3.3.6</version>
			</dependency>
		</dependencies>
	</dependencyManagement>
</project>
"""


def test_read_a_pom() -> None:
    pom = maven.parse_pom(POM)
    assert (pom.key, pom.version) == ("org.atriasoft:gale", "0.1.0")
    assert [(dependency.key, dependency.version) for dependency in pom.dependencies] == [
        ("org.atriasoft:etk", "0.1.0"),
        ("org.slf4j:slf4j-api", "2.1.0"),
    ]


def test_change_the_versions_and_nothing_else() -> None:
    new = maven.set_versions(POM, "0.2.0", {"org.atriasoft:etk": "0.3.0", "org.lwjgl:lwjgl-bom": "9.9.9"})
    assert new == POM.replace("<version>0.1.0</version>\n\t<!--", "<version>0.2.0</version>\n\t<!--").replace(
        "<artifactId>etk</artifactId>\n\t\t\t<version>0.1.0", "<artifactId>etk</artifactId>\n\t\t\t<version>0.3.0"
    )
    assert maven.set_versions(POM, None, {}) == POM


def test_the_order_of_the_dependencies() -> None:
    order = maven.dependency_order({"ewol": ["gale", "etk"], "gale": ["etk", "org.slf4j"], "etk": []})
    assert order == ["etk", "gale", "ewol"]
    with pytest.raises(ValueError, match="cycle of dependencies: a -> b -> a"):
        maven.dependency_order({"a": ["b"], "b": ["a"]})
