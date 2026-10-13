"""Run portable checks by default; retain explicit evidence-dependent checks."""
from pathlib import Path

import pytest

TEST_ROOT = Path(__file__).resolve().parent
HISTORICAL = frozenset(
    line.strip()
    for line in (TEST_ROOT / 'historical.txt').read_text().splitlines()
    if line.strip() and not line.lstrip().startswith('#')
)
RECOVERED_EVIDENCE = frozenset(
    line.strip()
    for line in (TEST_ROOT / 'recovered-evidence.txt').read_text().splitlines()
    if line.strip() and not line.lstrip().startswith('#')
)


def pytest_addoption(parser):
    parser.addoption(
        '--include-historical', action='store_true',
        help='Also collect and run archived model and evidence checks.',
    )
    parser.addoption(
        '--include-recovered-evidence', action='store_true',
        help='Also run checks requiring the documented recovered local source banks.',
    )


def pytest_configure(config):
    config.addinivalue_line(
        'markers', 'historical: archived model/evidence check (requires --include-historical)',
    )
    config.addinivalue_line(
        'markers', 'recovered_evidence: requires recovered inputs and --include-recovered-evidence',
    )


def pytest_ignore_collect(collection_path, config):
    if (not config.getoption('--include-historical')
            and collection_path.parent == TEST_ROOT and collection_path.name in HISTORICAL):
        return True
    if (not config.getoption('--include-recovered-evidence')
            and collection_path.parent == TEST_ROOT and collection_path.name in RECOVERED_EVIDENCE):
        return True
    return None


@pytest.hookimpl(tryfirst=True)
def pytest_collection_modifyitems(config, items):
    selected, deselected = [], []
    for item in items:
        filename = item.path.name if item.path.parent == TEST_ROOT else ''
        test_name = item.nodeid.split('::', 1)[-1].split('[', 1)[0]
        if filename in HISTORICAL or f'{filename}::{test_name}' in HISTORICAL:
            item.add_marker(pytest.mark.historical)
        if filename in RECOVERED_EVIDENCE or f'{filename}::{test_name}' in RECOVERED_EVIDENCE:
            item.add_marker(pytest.mark.recovered_evidence)
        if ((item.get_closest_marker('historical') and not config.getoption('--include-historical'))
                or (item.get_closest_marker('recovered_evidence')
                    and not config.getoption('--include-recovered-evidence'))):
            deselected.append(item)
        else:
            selected.append(item)
    items[:] = selected
    if deselected:
        config.hook.pytest_deselected(items=deselected)
