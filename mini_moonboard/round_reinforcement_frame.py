"""Combined development candidate: bolted base shoes and kicker header screws.

This candidate preserves the selected predecessor and combines two explicit
patches. Its custom steel, new timber cuts, connections and structure are not
released for fabrication or climbing.
"""
from functools import cache

from . import hold_tnut_reinforcement as tnuts
from . import kicker_header_reinforcement as kicker
from . import steel_base_reinforcement as base_revision

KEY = 'round-reinforcement-development'
LIMITS = ('Provisional custom through-bolted steel base shoes and ten extra kicker '
          'header screws; 142 owned-type T-nut envelopes without hold bolts; new rim bearing cuts; actual material, connection, panel, '
          'timber and floor resistance unqualified; NOT build-ready')


def __getattr__(name):
    return getattr(base_revision, name)


def attachment_datums():
    return kicker.attachment_datums()


def connections():
    return base_revision.connections()+kicker.added_connections()


def panel_connections():
    return kicker.panel_connections()


@cache
def parts():
    return kicker.cut_added_connections(base_revision.parts())+tnuts.parts(base_revision)
