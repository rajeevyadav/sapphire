import unittest
import numpy as np
import tables
import os
import tempfile
import shutil
import sys

import clusters
from simulations.base import BaseSimulation


class BaseSimulationAcceptanceTest(unittest.TestCase):
    def test_simulation_results(self):
        data_path = self.create_tempfile_from_testdata()
        self.data = tables.openFile(data_path, 'a')

        self.create_test_simulation_output()
        self.validate_simulation_results()

        self.data.close()
        os.remove(data_path)

    def create_test_simulation_output(self):
        np.random.seed(1)
        self.sim = 'E_100TeV/zenith_0'
        cluster = clusters.SimpleCluster(size=50)
        simulation = BaseSimulation(cluster, self.data,
                                    os.path.join('/showers', self.sim, 'leptons'),
                                    #os.path.join('/simulations', self.sim),
                                    os.path.join('/test_output', self.sim),
                                    R=10, N=20)
        self.redirect_stdout_stderr_to_devnull()
        simulation.run()
        simulation.store_observables()
        self.restore_stdout_stderr()

    def validate_simulation_results(self):
        expected_path = os.path.join('/simulations', self.sim)
        expected = self.data.getNode(expected_path)

        actual_path = os.path.join('/test_output', self.sim)
        actual = self.data.getNode(actual_path)

        self.validate_column_data(expected.observables, actual.observables)
        self.validate_column_data(expected.coincidences, actual.coincidences)
        self.validate_cindex(expected, actual)

    def validate_column_data(self, expected, actual):
        for colname in expected.colnames:
            expected_col = expected.col(colname)
            actual_col = actual.col(colname)
            self.assertTrue((expected_col == actual_col).all())

    def validate_cindex(self, expected, actual):
        expected = expected.c_index.read()
        actual = actual.c_index.read()

        # c_index is a list of arrays, so test accordingly
        for i, j in zip(expected, actual):
            self.assertTrue((i == j).all())

    def create_tempfile_from_testdata(self):
        tmp_path = self.create_tempfile_path()
        data_path = self.get_testdata_path()
        shutil.copyfile(data_path, tmp_path)
        return tmp_path

    def create_tempfile_path(self):
        fd, path = tempfile.mkstemp('.h5')
        os.close(fd)
        return path

    def get_testdata_path(self):
        dir_path = os.path.dirname(__file__)
        return os.path.join(dir_path, 'testdata.h5')

    def redirect_stdout_stderr_to_devnull(self):
        self.__stdout = sys.stdout
        self.__stderr = sys.stderr
        sys.stdout = open(os.devnull, 'w')
        sys.stderr = open(os.devnull, 'w')

    def restore_stdout_stderr(self):
        sys.stdout.close()
        sys.stderr.close()
        sys.stdout = self.__stdout
        sys.stderr = self.__stderr
