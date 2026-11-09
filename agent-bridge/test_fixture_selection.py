from pathlib import Path
import tempfile
import unittest
from continuous import standalone_test


class FixtureSelectionTests(unittest.TestCase):
    def accepts(self,source):
        with tempfile.TemporaryDirectory() as tmp:
            path=Path(tmp)/'test_unit.py';path.write_text(source,encoding='utf-8')
            return standalone_test(path)

    def test_missing_client_and_db_are_not_sent_to_standalone_pytest(self):
        self.assertFalse(self.accepts('def test_auth(client, monkeypatch): pass'))
        self.assertFalse(self.accepts('def test_data(db_session): pass'))

    def test_builtin_fixtures_and_direct_parametrization_work(self):
        self.assertTrue(self.accepts('import pytest\n@pytest.mark.parametrize("value, expected", [(1,1)])\ndef test_value(value, expected, monkeypatch): pass'))

    def test_local_fixtures_resolve_dependencies_but_not_missing_project_fixtures(self):
        self.assertTrue(self.accepts('import pytest\n@pytest.fixture\ndef data(tmp_path): return tmp_path\ndef test_data(data): pass'))
        self.assertFalse(self.accepts('import pytest\n@pytest.fixture\ndef data(db_session): return db_session\ndef test_data(data): pass'))

    def test_hidden_and_indirect_fixture_dependencies_are_rejected(self):
        self.assertFalse(self.accepts('import pytest\n@pytest.mark.usefixtures("client")\ndef test_data(): pass'))
        self.assertFalse(self.accepts('import pytest\n@pytest.mark.parametrize("client", [1], indirect=["client"])\ndef test_data(client): pass'))
        self.assertFalse(self.accepts('import pytest\n@pytest.fixture(autouse=True)\ndef data(db_session): pass\ndef test_data(): pass'))


if __name__=='__main__':unittest.main()
