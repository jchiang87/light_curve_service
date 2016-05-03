"""
Example unit tests for light_curve_service package
"""
import unittest
import matplotlib.pyplot as plt
from light_curve_service import LightCurveFactory

class LightCurveFactoryTestCase(unittest.TestCase):
    """
    Test code for LightCurveFactory class.
    """
    def setUp(self):
        self.lc_factory = LightCurveFactory(db='jc_desc',
                                            read_default_file='~/.my.cnf')

    def tearDown(self):
        pass

    def test_run(self):
        object_ids = self.lc_factory.getObjectIds()
        nobjs = len(object_ids)
        objectId = object_ids[max(0, nobjs/2)]
        lc = self.lc_factory.create(objectId)
        lc.plot()
        plt.savefig('lc_%i.png' % objectId)

if __name__ == '__main__':
    unittest.main()
