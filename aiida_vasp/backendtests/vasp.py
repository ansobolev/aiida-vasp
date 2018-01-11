"""Test creation and preparation of Vasp5Calculation"""
import tempfile
from os.path import dirname, realpath, join

import numpy as np
from aiida.backends.testbase import AiidaTestCase
from aiida.orm import CalculationFactory, DataFactory

from .common import Common


# pylint: disable=protected-access,too-many-public-methods
class VaspCalcTest(AiidaTestCase):
    """Test Case for py:class:`~aiida_vasp.calcs.vasp.VaspCalculation`."""

    def setUp(self):
        self.calc = CalculationFactory('vasp.vasp')()
        Common.import_paw()

        larray = np.array([[0, .5, .5], [.5, 0, .5], [.5, .5, 0]])
        alat = 6.058
        self.structure = DataFactory('structure')(cell=larray * alat)
        self.structure.append_atom(position=[0, 0, 0], symbols='In')
        self.structure.append_atom(position=[.25, .25, .25], symbols='As')

        cifpath = realpath(join(dirname(__file__), 'data', 'EntryWithCollCode43360.cif'))
        self.cif = DataFactory('cif').get_or_create(cifpath)[0]

    def test_inputs(self):
        """Check that the use_<input> methods are available"""
        self.assertTrue(hasattr(self.calc, 'use_code'))
        self.assertTrue(hasattr(self.calc, 'use_parameters'))
        self.assertTrue(hasattr(self.calc, 'use_structure'))
        self.assertTrue(hasattr(self.calc, 'use_paw'))
        self.assertTrue(hasattr(self.calc, 'use_kpoints'))
        self.assertTrue(hasattr(self.calc, 'use_charge_density'))
        self.assertTrue(hasattr(self.calc, 'use_wavefunctions'))

    def test_internal_params(self):
        self.assertTrue(self.calc.get_parser_name())

    def test_parameters_property(self):
        self.calc.use_parameters(self.calc.new_parameters(dict={'A': 0}))
        self.assertEqual(self.calc._parameters, {'a': 0})

    def test_write_incar(self):
        """Write out an INCAR tag to a tempfile and check wether it was written correctly."""
        inc = self.calc.new_parameters(dict={'system': 'InAs'})
        dst = tempfile.mkstemp()[1]
        self.calc.use_parameters(inc)
        self.calc.write_incar({}, dst)
        with open(dst, 'r') as incar:
            self.assertEqual(incar.read().strip(), 'SYSTEM = InAs')

    def test_write_potcar(self):
        """Concatenate two paws into a tmp POTCAR and check wether each is contained in the result."""
        self.calc.use_parameters(self.calc.new_parameters(dict={'System': 'Test'}))
        self.calc.use_structure(self.structure)
        self.calc.use_paw(self.calc.load_paw(family='TEST', symbol='In_d'), kind='In')
        self.calc.use_paw(self.calc.load_paw(family='TEST', symbol='As'), kind='As')
        dst = tempfile.mkstemp()[1]
        self.calc.write_potcar(self.calc.get_inputs_dict(), dst)
        with open(dst, 'r') as potcar:
            potcar_content = potcar.read()
            with open(self.calc.inp.paw_In.potcar, 'r') as paw_in:
                data = paw_in.read()
                self.assertIn(data, potcar_content)
            with open(self.calc.inp.paw_As.potcar, 'r') as paw_as:
                data = paw_as.read()
                self.assertIn(data, potcar_content)

    def test_write_poscar(self):
        """Feed a structure into calc and write it to a POSCAR temp file check for nonemptiness of the file."""
        self.calc.use_structure(self.structure)
        dst = tempfile.mkstemp()[1]
        self.calc.write_poscar({}, dst)
        with open(dst, 'r') as poscar:
            self.assertTrue(poscar.read())

    def test_write_poscar_cif(self):
        """Feed a cif file into calc and write it to a POSCAR temp file make sure the file is not empty."""
        self.calc.use_structure(self.cif)
        dst = tempfile.mkstemp()[1]
        self.calc.write_poscar({}, dst)
        with open(dst, 'r') as poscar:
            self.assertTrue(poscar.read())

    def test_write_kpoints(self):
        """Feed kpoints into calc and write to KPOINTS temp file verify the file is not empty."""
        kpoints = self.calc.new_kpoints()
        kpoints.set_kpoints_mesh([4, 4, 4])
        self.calc.use_kpoints(kpoints)
        self.calc.use_parameters(self.calc.new_parameters())
        dst = tempfile.mkstemp()[1]
        self.calc.write_kpoints(self.calc.get_inputs_dict(), dst)
        with open(dst, 'r') as kpoints_f:
            self.assertTrue(kpoints_f.read())

    def test_need_kp_false(self):
        """Test a case where kpoints input node is not required"""
        self.calc.use_parameters(self.calc.new_parameters(dict={'kspacing': 0.5, 'kgamma': True}))
        self.assertFalse(self.calc._need_kp())

    def test_need_kp_true(self):
        self.calc.use_parameters(self.calc.new_parameters())
        self.assertTrue(self.calc._need_kp())

    def test_need_chgd_none(self):
        self.calc.use_parameters(self.calc.new_parameters())
        self.assertFalse(self.calc._need_chgd())

    def test_need_chgd_icharg(self):
        """Check ICHARG input parameter should be set"""
        for i in [0, 2, 4, 10, 12]:
            self.calc.use_parameters(self.calc.new_parameters(dict={'icharg': i}))
            self.assertFalse(self.calc._need_chgd())
        for i in [1, 11]:
            self.calc.use_parameters(self.calc.new_parameters(dict={'icharg': i}))
            self.assertTrue(self.calc._need_chgd())

    def test_need_wfn_none(self):
        self.calc.use_parameters(self.calc.new_parameters())
        self.assertFalse(self.calc._need_wfn())
        self.calc.use_wavefunctions(self.calc.new_wavefunctions())
        self.assertTrue(self.calc._need_wfn())

    def test_need_wfn_istart(self):
        """Test if the calculation recognizes when WAVEFUN is required."""
        self.calc.use_parameters(self.calc.new_parameters(dict={'istart': 0}))
        self.assertFalse(self.calc._need_wfn())
        for i in [1, 2, 3]:
            self.calc.use_parameters(self.calc.new_parameters(dict={'istart': i}))
            self.assertTrue(self.calc._need_wfn(), msg='_need_wfn not True for istart=%s' % i)

    def test_get_paw_linkname(self):
        self.assertEqual(self.calc._get_paw_linkname('In'), 'paw_In')

    def test_paw(self):
        self.assertIs(self.calc.Paw, DataFactory('vasp.paw'))

    def test_load_paw(self):
        paw_a = self.calc.load_paw(family='TEST', symbol='As')
        paw_b = self.calc.Paw.load_paw(family='TEST', symbol='As')[0]
        self.assertEqual(paw_a.pk, paw_b.pk)

    def test_new_setting(self):
        self.assertIsInstance(self.calc.new_parameters(), DataFactory('parameter'))

    def test_new_structure(self):
        self.assertIsInstance(self.calc.new_structure(), DataFactory('structure'))

    def test_new_kpoints(self):
        self.assertIsInstance(self.calc.new_kpoints(), DataFactory('array.kpoints'))

    def test_new_charge_density(self):
        self.assertIsInstance(self.calc.new_charge_density(), DataFactory('vasp.chargedensity'))

    def test_new_wavefunctions(self):
        self.assertIsInstance(self.calc.new_wavefunctions(), DataFactory('vasp.wavefun'))
