"""Historical selection must not suppress new tests or import excluded models."""
import ast
import os
import subprocess
import sys
from pathlib import Path

import pytest

TEST_ROOT = Path(__file__).resolve().parent


def test_historical_inventory_references_existing_unique_tests():
    entries = [line.strip() for line in (TEST_ROOT / 'historical.txt').read_text().splitlines()
               if line.strip() and not line.lstrip().startswith('#')]
    assert len(entries) == len(set(entries)), 'Duplicate historical inventory entries'
    for entry in entries:
        filename, separator, function = entry.partition('::')
        assert Path(filename).name == filename and filename.startswith('test_')
        path = TEST_ROOT / filename
        assert path.is_file(), entry
        if separator:
            assert filename not in entries, f'Redundant function entry: {entry}'
            tree = ast.parse(path.read_text())
            assert function in {node.name for node in tree.body
                                if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))}, entry


@pytest.mark.parametrize('arguments, expected_code, expected, imported', [
    ([], 0, '3 passed, 2 deselected', False),
    (['--include-historical'], 0, '6 passed', True),
    (['--include-historical', '-m', 'historical'], 0, '3 passed, 3 deselected', True),
    (['tests/test_archived.py'], 5, '1 deselected', True),
    (['tests/test_archived.py', '--include-historical'], 0, '1 passed', True),
])
def test_selection_in_independent_pytest_process(tmp_path, arguments, expected_code, expected, imported):
    tests = tmp_path / 'tests'
    tests.mkdir()
    (tests / 'conftest.py').write_bytes((TEST_ROOT / 'conftest.py').read_bytes())
    (tests / 'historical.txt').write_text(
        '# Only explicitly listed tests are historical.\n'
        'test_archived.py\n'
        'test_mixed.py::test_old_case\n',
    )
    (tests / 'test_archived.py').write_text(
        'from pathlib import Path\n'
        'Path(__file__).with_name("archived-imported").touch()\n'
        'def test_old_model():\n    assert True\n',
    )
    (tests / 'test_active.py').write_text('def test_current():\n    assert True\n')
    (tests / 'test_new.py').write_text('def test_new_unlisted():\n    assert True\n')
    (tests / 'test_mixed.py').write_text(
        'import pytest\n'
        'def test_shared():\n    assert True\n'
        '@pytest.mark.parametrize("value", [1, 2])\n'
        'def test_old_case(value):\n    assert value > 0\n',
    )
    environment = dict(os.environ, PYTEST_DISABLE_PLUGIN_AUTOLOAD='1')
    environment.pop('PYTEST_ADDOPTS', None)
    result = subprocess.run(
        [sys.executable, '-m', 'pytest', '-q', *arguments], cwd=tmp_path,
        env=environment, capture_output=True, text=True, timeout=30, check=False,
    )
    assert result.returncode == expected_code, result.stdout + result.stderr
    assert expected in result.stdout, result.stdout
    assert (tests / 'archived-imported').exists() is imported
