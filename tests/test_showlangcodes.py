import runpy
import sys
import types
from pathlib import Path


def test_showlangcodes_uses_bibliographic_when_terminology_missing(
    monkeypatch, capsys
):
    fake_pycountry = types.SimpleNamespace(
        languages=[
            types.SimpleNamespace(
                name='Language without terminology',
                bibliographic='lwt',
            )
        ]
    )
    script_path = Path(__file__).resolve().parents[1] / 'wiktionarytodict3.py'

    monkeypatch.setitem(sys.modules, 'pycountry', fake_pycountry)
    monkeypatch.setattr(sys, 'argv', ['wiktionarytodict3.py', '--showlangcodes'])

    runpy.run_path(script_path, run_name='__main__')

    assert capsys.readouterr().out == 'Language without terminology:lwt\n'
