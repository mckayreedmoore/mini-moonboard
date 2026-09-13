"""Run current/shared checks by default; retain historical checks as an opt-in."""
from pathlib import Path

import pytest

TEST_ROOT = Path(__file__).resolve().parent
HISTORICAL = frozenset(
    line.strip()
    for line in (TEST_ROOT / 'historical.txt').read_text().splitlines()
    if line.strip() and not line.lstrip().startswith('#')
)


def pytest_addoption(parser):
    parser.addoption(
        '--include-historical', action='store_true',
        help='Also collect and run archived model and evidence checks.',
    )


def pytest_configure(config):
    config.addinivalue_line(
        'markers', 'historical: archived model/evidence check (requires --include-historical)',
    )


def pytest_ignore_collect(collection_path, config):
    if (not config.getoption('--include-historical')
            and collection_path.parent == TEST_ROOT and collection_path.name in HISTORICAL):
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
        if item.get_closest_marker('historical') and not config.getoption('--include-historical'):
            deselected.append(item)
        else:
            selected.append(item)
    items[:] = selected
    if deselected:
        config.hook.pytest_deselected(items=deselected)
