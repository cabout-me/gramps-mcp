"""
Shared pytest fixtures for Gramps MCP tests.

The direct-client tests use a synthetic .gpkg file generated in memory from
a known XML fixture — no private genealogical data, no external server needed.
"""

import gzip
import io
import tarfile

import pytest

# ---------------------------------------------------------------------------
# Minimal Gramps XML fixture
# ---------------------------------------------------------------------------
# Covers all fields parsed by GrampsDirectClient:
#   - person: gender, name (first/surname/suffix/call/nick), eventref, parentin,
#             childof, noteref, citationref, mediaref, url
#   - event: type, dateval, daterange, datespan, place, description
#   - family: rel, father, mother, childref, eventref, noteref
#   - placeobj: ptitle, pname, placeref, url
#   - source: stitle, sauthor, spubinfo, sabbrev
#   - citation: dateval, page, confidence, sourceref, noteref
#   - note: text, type
#   - object (media): file (src, mime, description)
#   - repository: rname, type, url
#
# NOT YET PARSED (DTD fields, future work):
#   attribute, personref, tagref, srcattribute, coord,
#   lds_ord, familynick, group_as
#
# The Test family (Testor & Testiane von Test, Baumallee 12, Testhausen)
# serves as the canonical TDD fixture for address parsing and sibling queries.

FIXTURE_XML = """\
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE database PUBLIC "-//GRAMPS//DTD GRAMPS XML 1.7.1//EN"
"http://gramps-project.org/xml/1.7.1/grampsxml.dtd">
<database xmlns="http://gramps-project.org/xml/1.7.1/">
  <header>
    <created date="2024-01-01" version="5.2.0"/>
    <researcher/>
  </header>

  <events>
    <event id="E0001" handle="h_ev_birth_john" change="0">
      <type>Birth</type>
      <dateval val="1950-06-15"/>
      <place hlink="h_pl_berlin"/>
    </event>
    <event id="E0002" handle="h_ev_death_john" change="0">
      <type>Death</type>
      <dateval val="2020-03-01" type="about" quality="estimated"/>
      <place hlink="h_pl_hamburg"/>
    </event>
    <event id="E0003" handle="h_ev_birth_jane" change="0">
      <type>Birth</type>
      <dateval val="1952-11-30"/>
    </event>
    <event id="E0004" handle="h_ev_marriage" change="0">
      <type>Marriage</type>
      <dateval val="1975-04-20"/>
      <place hlink="h_pl_berlin"/>
    </event>
    <event id="E0005" handle="h_ev_birth_child" change="0">
      <type>Birth</type>
      <daterange start="1976-01-01" stop="1976-12-31" quality="estimated"/>
    </event>
    <event id="E0006" handle="h_ev_residence" change="0">
      <type>Residence</type>
      <datespan start="1980-01-01" stop="2000-12-31"/>
      <description>Lived in Hamburg</description>
    </event>
    <event id="E0007" handle="h_ev_textdate" change="0">
      <type>Census</type>
      <datestr val="Michaelmas 1901"/>
    </event>
    <event id="E0008" handle="h_ev_birth_testor" change="0">
      <type>Birth</type>
      <dateval val="1980-03-15"/>
    </event>
    <event id="E0009" handle="h_ev_birth_testiane" change="0">
      <type>Birth</type>
      <dateval val="1982-07-22"/>
    </event>
  </events>

  <people>
    <person id="I0001" handle="h_pe_john" change="0">
      <gender>M</gender>
      <name type="Birth Name">
        <first>John Robert</first>
        <surname>Smith</surname>
        <suffix>Jr.</suffix>
        <call>Rob</call>
        <nick>Bobby</nick>
        <title>Dr.</title>
      </name>
      <eventref hlink="h_ev_birth_john" role="Primary"/>
      <eventref hlink="h_ev_death_john" role="Primary"/>
      <parentin hlink="h_fa_smith"/>
      <noteref hlink="h_no_john"/>
      <citationref hlink="h_ci_birth"/>
      <objref hlink="h_me_photo"/>
      <url href="https://example.com/john" description="Homepage" type="Web Home"/>
    </person>
    <person id="I0002" handle="h_pe_jane" change="0">
      <gender>F</gender>
      <name type="Birth Name">
        <first>Jane</first>
        <surname>Doe</surname>
      </name>
      <eventref hlink="h_ev_birth_jane" role="Primary"/>
      <parentin hlink="h_fa_smith"/>
    </person>
    <person id="I0003" handle="h_pe_child" change="0">
      <gender>M</gender>
      <name type="Birth Name">
        <first>James</first>
        <surname>Smith</surname>
      </name>
      <eventref hlink="h_ev_birth_child" role="Primary"/>
      <childof hlink="h_fa_smith"/>
    </person>
    <person id="I0004" handle="h_pe_unknown" change="0">
      <gender>U</gender>
      <name type="Birth Name">
        <first/>
        <surname>Unknown</surname>
      </name>
    </person>
    <person id="I0005" handle="h_pe_testor" change="0">
      <gender>M</gender>
      <name type="Birth Name">
        <first>Testor</first>
        <surname>von Test</surname>
      </name>
      <eventref hlink="h_ev_birth_testor" role="Primary"/>
      <childof hlink="h_fa_test"/>
      <address>
        <street>Baumallee 12</street>
        <city>Testhausen</city>
      </address>
    </person>
    <person id="I0006" handle="h_pe_testiane" change="0">
      <gender>F</gender>
      <name type="Birth Name">
        <first>Testiane</first>
        <surname>von Test</surname>
      </name>
      <eventref hlink="h_ev_birth_testiane" role="Primary"/>
      <childof hlink="h_fa_test"/>
      <address>
        <street>Baumallee 12</street>
        <city>Testhausen</city>
      </address>
    </person>
  </people>

  <families>
    <family id="F0001" handle="h_fa_smith" change="0">
      <rel type="Married"/>
      <father hlink="h_pe_john"/>
      <mother hlink="h_pe_jane"/>
      <eventref hlink="h_ev_marriage" role="Family"/>
      <childref hlink="h_pe_child" frel="Birth" mrel="Birth"/>
      <noteref hlink="h_no_john"/>
    </family>
    <family id="F0002" handle="h_fa_test" change="0">
      <rel type="Unknown"/>
      <childref hlink="h_pe_testor" frel="Birth" mrel="Birth"/>
      <childref hlink="h_pe_testiane" frel="Birth" mrel="Birth"/>
    </family>
  </families>

  <citations>
    <citation id="C0001" handle="h_ci_birth" change="0">
      <dateval val="2024-01-15"/>
      <page>Certificate No. 12345</page>
      <confidence>2</confidence>
      <noteref hlink="h_no_john"/>
      <sourceref hlink="h_so_civil"/>
    </citation>
  </citations>

  <sources>
    <source id="S0001" handle="h_so_civil" change="0">
      <stitle>Civil Records Office</stitle>
      <sauthor>State Archive</sauthor>
      <spubinfo>Berlin, 1950</spubinfo>
      <sabbrev>CRO</sabbrev>
      <reporef hlink="h_re_archive" callno="Vol. 3" medium="Book"/>
      <objref hlink="h_me_photo"/>
    </source>
  </sources>

  <places>
    <placeobj id="P0001" handle="h_pl_berlin" change="0" type="City">
      <ptitle>Berlin, Germany</ptitle>
      <pname value="Berlin"/>
      <url href="https://en.wikipedia.org/wiki/Berlin" type="Web Home"/>
    </placeobj>
    <placeobj id="P0002" handle="h_pl_hamburg" change="0" type="City">
      <ptitle>Hamburg, Germany</ptitle>
      <pname value="Hamburg"/>
      <placeref hlink="h_pl_germany"/>
    </placeobj>
    <placeobj id="P0003" handle="h_pl_germany" change="0" type="Country">
      <ptitle>Germany</ptitle>
      <pname value="Germany"/>
    </placeobj>
  </places>

  <objects>
    <object id="O0001" handle="h_me_photo" change="0">
      <file src="/photos/family.jpg" mime="image/jpeg"
            checksum="abc123def456" description="Family photo 1975"/>
    </object>
  </objects>

  <repositories>
    <repository id="R0001" handle="h_re_archive" change="0">
      <rname>State Archive Berlin</rname>
      <type>Archive</type>
      <url href="https://archive.berlin.de" type="Web Home"/>
    </repository>
  </repositories>

  <notes>
    <note id="N0001" handle="h_no_john" change="0" type="General">
      <text>John Smith was a notable person in his community.</text>
    </note>
  </notes>
</database>
"""


def _make_gpkg(xml_content: str) -> bytes:
    """Wrap XML string as a .gpkg: tar.gz archive containing gzip-compressed .gramps."""
    compressed = gzip.compress(xml_content.encode("utf-8"))
    buf = io.BytesIO()
    with tarfile.open(fileobj=buf, mode="w:gz") as tar:
        info = tarfile.TarInfo(name="data.gramps")
        info.size = len(compressed)
        tar.addfile(info, io.BytesIO(compressed))
    return buf.getvalue()


@pytest.fixture(scope="session")
def gpkg_path(tmp_path_factory):
    """Write the synthetic fixture to a temp file and return its path."""
    path = tmp_path_factory.mktemp("fixtures") / "test_tree.gpkg"
    path.write_bytes(_make_gpkg(FIXTURE_XML))
    return str(path)


@pytest.fixture(scope="session")
def db(gpkg_path):
    """In-memory GrampsXmlDB loaded from the fixture."""
    from gramps_mcp.direct_client import _load_gpkg
    return _load_gpkg(gpkg_path)


@pytest.fixture(scope="session")
def client(gpkg_path):
    """GrampsDirectClient connected to the fixture."""
    from gramps_mcp.direct_client import GrampsDirectClient
    return GrampsDirectClient(gpkg_path)


# ---------------------------------------------------------------------------
# SQLite fixtures  (imported from conftest_sqlite.py)
# ---------------------------------------------------------------------------

import sys, os  # noqa: E401
sys.path.insert(0, os.path.dirname(__file__))
from conftest_sqlite import (  # noqa: E402
    sqlite_conn,
    sqlite_db,
    sqlite_client,
)
