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


class Test_Restaurant_Instances(unittest.TestCase):
    def setUp(self):
        self.city_instances = build_city_instance()
        self.restaurant_instances = build_restaurant_instance(self.city_instances)

    def test_rating(self):
        self.assertIsInstance(self.restaurant_instances[0].rating, float)
        self.assertIsInstance(self.restaurant_instances[-1].rating, float)

    def test_phone(self):
        self.assertIsInstance(self.restaurant_instances[0].phone, str)
        self.assertIsInstance(self.restaurant_instances[-1].phone, str)

    def test_category(self):
        self.assertIsInstance(self.restaurant_instances[0].category, str)
        self.assertIsInstance(self.restaurant_instances[-1].category, str)

    def test_yelpId(self):
        self.assertIsInstance(self.restaurant_instances[0].yelp_id, str)
        self.assertIsInstance(self.restaurant_instances[-1].yelp_id, str)
    
    def test_url(self):
        self.assertIsInstance(self.restaurant_instances[0].url, str)
        self.assertIsInstance(self.restaurant_instances[-1].url, str)

    def test_reviewNum(self):
        self.assertIsInstance(self.restaurant_instances[0].review_num, int)
        self.assertIsInstance(self.restaurant_instances[-1].review_num, int)

    def test_name(self):
        self.assertIsInstance(self.restaurant_instances[0].name, str)
        self.assertIsInstance(self.restaurant_instances[-1].name, str)

    def test_city(self):
        self.assertIsInstance(self.restaurant_instances[0].city, str)
        self.assertIsInstance(self.restaurant_instances[-1].city, str)

    def test_state(self):
        self.assertIsInstance(self.restaurant_instances[0].state, str)
        self.assertIsInstance(self.restaurant_instances[-1].state, str)


class Test_DB_Cities(unittest.TestCase):
    def setUp(self):
        query = '''SELECT * FROM Cities WHERE Id=3 AND Name="Chicago"'''
        self.results = searchDB(query)

    def test_length(self):
        self.assertEqual(len(self.results[0]), 7)

    def test_id(self):
        self.assertEqual(self.results[0][0], 3)
    
    def test_name(self):
        self.assertEqual(self.results[0][1], 'Chicago')

    def test_state(self):
        self.assertEqual(self.results[0][2], 'Illinois')

    def test_population(self):
        self.assertEqual(self.results[0][3], 2695598)

    def test_area(self):
        self.assertEqual(self.results[0][4], 227.3)


class Test_DB_Restaurants(unittest.TestCase):
    def setUp(self):
        query = '''SELECT * FROM Restaurants WHERE Yelp_id="TkFEKhsCixPWlShULKvMdQ"'''
        self.results = searchDB(query)

    def test_length(self):
        self.assertEqual(len(self.results[0]), 11)

    def test_name(self):
        self.assertEqual(self.results[0][1], 'Bottega Louie')
    
    def test_city(self):
        self.assertEqual(self.results[0][2], 'Los Angeles')

    def test_state(self):
        self.assertEqual(self.results[0][3], 'CA')

    def test_rating(self):
        self.assertEqual(self.results[0][4], 4)

    def test_price(self):
        self.assertEqual(self.results[0][5], 2)

    def test_category(self):
        self.assertEqual(self.results[0][6], 'Italian')

    def test_phone(self):
        self.assertEqual(self.results[0][7], '(213) 802-1470')


if __name__ == '__main__':
    unittest.main()
