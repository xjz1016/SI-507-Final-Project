import unittest
from program import *

class Test_City_Instances(unittest.TestCase):
    def setUp(self):
        self.city_instances = build_city_instance()

    def test_total_num(self):
        self.assertEqual(len(self.city_instances), 314)

    def test_name(self):
        self.assertEqual(self.city_instances[0].name, 'New York')
        self.assertEqual(self.city_instances[313].name, 'Vacaville')
    
    def test_state(self):
        self.assertEqual(self.city_instances[0].state, 'New York')
        self.assertEqual(self.city_instances[313].state, 'California')

    def test_population(self):
        self.assertEqual(self.city_instances[0].population, 8175133)
        self.assertEqual(self.city_instances[313].population, 92428)

    def test_area(self):
        self.assertEqual(self.city_instances[0].area, 301.5)
        self.assertEqual(self.city_instances[313].area, 29.0)

    def test_latitude(self):
        self.assertEqual(self.city_instances[0].latitude[:-2], '40.6635')
        self.assertEqual(self.city_instances[313].latitude[:-2], '38.3539')

    def test_longitude(self):
        self.assertEqual(self.city_instances[0].longitude[:-2], '73.9387')
        self.assertEqual(self.city_instances[313].longitude[:-2], '121.9728')





if __name__ == '__main__':
    unittest.main()
