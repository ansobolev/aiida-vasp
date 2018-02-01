"""Test the Incar io interface"""
# pylint: disable=unused-import,redefined-outer-name,unused-argument,unused-wildcard-import,wildcard-import

import pytest

from aiida_vasp.utils.fixtures import *
from aiida_vasp.utils.fixtures.testdata import data_path, read_file
from aiida_vasp.utils.aiida_utils import get_data_class
from aiida_vasp.io.potcar import PotcarIo, MultiPotcarIo


def verify_potcario(potcario):
    assert potcario.node
    assert potcario.file_node
    assert potcario.pymatgen
    assert potcario.content


def test_potcar_from_path(aiida_env):
    """Create a PotcarIo instance from a file path."""
    potcar_path_as = data_path('potcar', 'As', 'POTCAR')
    from_ctor = PotcarIo(path=potcar_path_as)
    from_from = PotcarIo.from_(potcar_path_as)
    verify_potcario(from_from)
    assert from_ctor == from_from


def test_potcar_from_file_node(potcar_family):
    """Create a PotcarIo instance from a PotcarFileData node."""
    potcar_file_in = get_data_class('vasp.potcar_file').find(element='In')
    from_ctor = PotcarIo(potcar_file_node=potcar_file_in)
    verify_potcario(from_ctor)
    from_from = PotcarIo.from_(potcar_file_in)
    assert from_ctor == from_from


def test_potcar_from_node(potcar_family):
    """Create a PotcarIo instance from a PotcarData node."""
    potcar_ga = get_data_class('vasp.potcar').find(element='Ga')
    from_ctor = PotcarIo(potcar_node=potcar_ga)
    verify_potcario(from_ctor)
    from_from = PotcarIo.from_(potcar_ga)
    assert from_ctor == from_from


def test_potcar_from_contents(potcar_family):
    """Create a PotcarIo from contents of a POTCAR file."""
    contents_as = read_file('potcar', 'As', 'POTCAR')
    from_ctor = PotcarIo(contents=contents_as)
    verify_potcario(from_ctor)
    assert from_ctor.node.uuid == get_data_class('vasp.potcar').find(element='As').uuid
    from_from = PotcarIo.from_(contents_as)
    assert from_ctor == from_from


def test_file_contents_equivalence(aiida_env):
    potcar_path_as = ['potcar', 'As', 'POTCAR']
    from_file = PotcarIo(path=data_path(*potcar_path_as))
    from_contents = PotcarIo(contents=read_file(*potcar_path_as))
    assert from_file.md5 == from_contents.md5


def test_multi_round_trip(potcar_family, tmpdir):
    """Write multiple POTCAR potentials to a file and recover the nodes stored in the db."""
    potcar_cls = get_data_class('vasp.potcar')
    multi = MultiPotcarIo(
        potcar_cls.get_potcars_dict(elements=['As', 'Ga', 'In'], family_name=potcar_family, mapping={
            'In': 'In_d',
            'As': 'As',
            'Ga': 'Ga'
        }).values())
    tempfile = tmpdir.join('POTCAR')
    multi.write(tempfile)
    recovered = multi.read(tempfile)
    uuids_start = set([potcar.node.uuid for potcar in multi.potcars])
    uuids_recov = set([potcar.node.uuid for potcar in recovered.potcars])
    assert uuids_start == uuids_recov
