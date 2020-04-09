from bs4 import BeautifulSoup
import requests
import json
import time
import secret
import sqlite3
import plotly.graph_objs as go 

CACHE_FILE = 'cache.json'
CACHE_DICT = {}
DB_NAME = 'final_project.sqlite'
API_KEY = secret.API_KEY
HEADERS = { 'Authorization': 'Bearer {}'.format(API_KEY),
            'User-Agent': 'UMSI 507 Course Project - Python Scraping',
            'From': 'junzhexu@umich.edu',
            'Course-Info': 'https://si.umich.edu/programs/courses/507'}

#########################################
################ Class ##################
#########################################

class City:
    def __init__(self, id_pos=0, name=None, state=None, population=0, area=0, latitude='', longitude=''):
        self.id_pos = id_pos
        self.name = name
        self.state = state
        self.population = population
        self.area = area
        self.latitude = latitude
        self.longitude = longitude

class Restaurant:
    def __init__(self, rating=0, price=None, phone='', category='', yelp_id='', url='', 
                    review_num=0, name='', city='', state=''):
        self.rating = rating
        self.price = price
        self.phone = phone
        self.category = category
        self.yelp_id = yelp_id
        self.url = url
        self.review_num = review_num
        self.name = name
        self.city = city
        self.state = state

#########################################
########### Data Processing #############
#########################################

def load_cache(cache_file_name):
    '''Load response text cache if already generated, else initiate an empty dictionary.
    
    Parameters
    ----------
    None
    
    Returns
    -------
    cache: dictionary
        The dictionary which maps url to response text.
    '''
    try:
        cache_file = open(cache_file_name, 'r')
        cache_file_contents = cache_file.read()
        cache = json.loads(cache_file_contents)
        cache_file.close()
    except:
        cache = {}
    return cache

def save_cache(cache, cache_file_name):
    '''Save the cache
    
    Parameters
    ----------
    cache: dictionary
        The dictionary which maps url to response.
    
    Returns
    -------
    None
    '''
    cache_file = open(cache_file_name, 'w')
    contents_to_write = json.dumps(cache)
    cache_file.write(contents_to_write)
    cache_file.close()

def db_create_table_cities():
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()
    # drop_cities_sql = 'DROP TABLE IF EXISTS "Cities"'
    create_cities_sql = '''
        CREATE TABLE IF NOT EXISTS "Cities" (
            "Id" INTEGER PRIMARY KEY UNIQUE, 
            "Name" TEXT NOT NULL,
            "State" TEXT NOT NULL, 
            "Population" INTEGER NOT NULL,
            "Area" REAL NOT NULL,
            "Latitude" TEXT NOT NULL,
            "Longitude" TEXT NOT NULL
        )
    '''
    # cur.execute(drop_cities_sql)
    cur.execute(create_cities_sql)
    conn.commit()
    conn.close()

def db_create_table_restaurants():
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()
    # drop_restaurants_sql = 'DROP TABLE IF EXISTS "Restaurants"'
    create_restaurants_sql = '''
        CREATE TABLE IF NOT EXISTS "Restaurants" (
            "Id" INTEGER PRIMARY KEY AUTOINCREMENT, 
            "Name" TEXT NOT NULL,
            "City" TEXT NOT NULL,
            "State" TEXT NOT NULL,
            "Rating" INTEGER,
            "Price" INTEGER,
            "Category" TEXT,
            "Phone" TEXT,
            "Yelp_id" TEXT NOT NULL UNIQUE,
            "Url" TEXT,
            "Number of Review" INTEGER
        )
    '''
    # cur.execute(drop_restaurants_sql)
    cur.execute(create_restaurants_sql)
    conn.commit()
    conn.close()

def db_write_table_cities(city_instances):
    insert_cities_sql = '''
        INSERT OR IGNORE INTO Cities
        VALUES (?, ?, ?, ?, ?, ?, ?)
    '''
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()
    for c in city_instances:
        cur.execute(insert_cities_sql, 
                        [c.id_pos, c.name, c.state, c.population, c.area, c.latitude, c.longitude])
    
    conn.commit()
    conn.close()

def db_write_table_restaurants(restaurant_instances):
    insert_restaurants_sql = '''
        INSERT OR IGNORE INTO Restaurants
        VALUES (NULL, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    '''
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()
    for r in restaurant_instances:
        cur.execute(insert_restaurants_sql,
            [r.name, r.city, r.state, r.rating, r.price, r.category, r.phone, r.yelp_id, r.url, r.review_num]
        )
    
    conn.commit()
    conn.close()

def build_city_instance():
    city_instances = []
    site_url = 'https://en.wikipedia.org/wiki/List_of_United_States_cities_by_population'
    url_text = make_url_request_using_cache(url_or_uniqkey=site_url)
    soup = BeautifulSoup(url_text, 'html.parser')
    tr_list = soup.find('table', class_='wikitable sortable').find('tbody').find_all('tr')[1:] # total 314 cities in the list, each in a row
    for tr in tr_list: # each tr is a city row, td is the data in each column
        td_list = tr.find_all('td')
        id_pos = int(td_list[0].text.strip())
        name = str(td_list[1].find('a').text.strip())
        try:
            state = str(td_list[2].find('a').text.strip())
        except:
            state = td_list[2].text.strip()
        population = int(td_list[4].text.strip().replace(',', ''))
        area = float(td_list[6].text.strip().split('\xa0')[0].replace(',', ''))
        lati_longi = td_list[10].find('span', class_='geo-dec').text.strip().split(' ')
        latitude = str(lati_longi[0])
        longitude = str(lati_longi[1])
        instance = City(id_pos=id_pos, name=name, state=state, population=population, 
                            area=area, latitude=latitude, longitude=longitude)
        city_instances.append(instance)
    
    return city_instances

def build_restaurant_instance(city_instances):
    restaurant_instances = []
    endpoint_url = 'https://api.yelp.com/v3/businesses/search'
    for c in city_instances:
        city = c.name
        params = {'location': city, 'term': 'restaurant', 'limit': 50}
        uniqkey = construct_unique_key(endpoint_url, params)
        results = make_url_request_using_cache(url_or_uniqkey=uniqkey, params=params)
        if 'businesses' in results.keys():
            for business in results['businesses']:
                rating = business['rating']
                try:
                    price = len(business['price'].strip())
                except:
                    price = None
                phone = business['display_phone']
                try:
                    category = business['categories'][0]['title']
                except:
                    category = ''
                yelp_id = business['id']
                url = business['url']
                review_num = business['review_count']
                name = business['name']
                state = business['location']['state']
                instance = Restaurant(rating=rating, price=price, phone=phone, category=category, yelp_id=yelp_id, 
                                      url=url, review_num=review_num, name=name, city=city, state=state)
                restaurant_instances.append(instance)
    
    return restaurant_instances

def construct_unique_key(baseurl, params):
    ''' constructs a key that is guaranteed to uniquely and 
    repeatably identify an API request by its baseurl and params

    Parameters
    ----------
    baseurl: string
        The URL for the API endpoint
    params: dictionary
        A dictionary of param: param_value pairs

    Returns
    -------
    string
        the unique key as a string
    '''
    param_strings = []
    connector = '_'
    for k in params.keys():
        param_strings.append(f'{k}_{params[k]}')
    
    param_strings.sort()
    unique_key = baseurl + connector + connector.join(param_strings)
    return unique_key

def make_url_request_using_cache(url_or_uniqkey, params=None):
    '''Given a url, fetch if cache not exist, else use the cache.
    
    Parameters
    ----------
    url: string
        The URL for a specific web page
    cache_dict: dictionary
        The dictionary which maps url to response text
    params: dictionary
        A dictionary of param: param_value pairs
    
    Returns
    -------
    cache[url]: response
    '''
    if url_or_uniqkey in CACHE_DICT.keys():
        print('Using cache')
        return CACHE_DICT[url_or_uniqkey]

    print('Fetching')
    if params == None: # dictionary: url -> response.text
        # time.sleep(1)
        response = requests.get(url_or_uniqkey, headers=HEADERS)
        CACHE_DICT[url_or_uniqkey] = response.text
    else: # dictionary: uniqkey -> response.json()
        endpoint_url = 'https://api.yelp.com/v3/businesses/search'
        response = requests.get(endpoint_url, headers = HEADERS, params=params)
        CACHE_DICT[url_or_uniqkey] = response.json()
    
    save_cache(CACHE_DICT, CACHE_FILE)
    return CACHE_DICT[url_or_uniqkey]

def build_database():
    print('Building database...')
    city_instances = build_city_instance()
    db_create_table_cities()
    db_write_table_cities(city_instances)
    restaurant_instances = build_restaurant_instance(city_instances)
    db_create_table_restaurants()
    db_write_table_restaurants(restaurant_instances)
    print('Finished building database!')

def searchDB(query):
    '''Search the database and return the results given the sqlite query
    
    Parameters
    ----------
    query: string 
        a sqlite query command
    
    Returns
    -------
    result: list
        a list of tuples that contains the results
    '''
    connection = sqlite3.connect(DB_NAME)
    cursor = connection.cursor()
    result = cursor.execute(query).fetchall()
    connection.close()
    return result

#########################################
########### Data Presentation ###########
#########################################

def process_city_name(city_name):
    split = city_name.split(' ')
    res = ''
    for word in split:
        res += word.lower().capitalize() + ' '
    return res.strip()

def barPlot(xvals, yvals, title):
    ''' generate a bar plot 
    
    Parameters
    ----------
    xvals: list
        values of x-axis
    yvals: list
        values of y-axis
    
    Returns
    -------
    none
    '''
    data = go.Bar(x=xvals, y=yvals)
    basic_layout = go.Layout(title=title)
    fig = go.Figure(data=data, layout=basic_layout)
    fig.show()

def pieplot(labels, values, title):
    data = go.Pie(labels=labels, values=values)
    basic_layout = go.Layout(title=title)
    fig = go.Figure(data=data, layout=basic_layout)
    fig.show()

def barplot_city_population():
    query = '''SELECT Name, Population FROM Cities
                ORDER BY Population DESC'''
    result = searchDB(query)
    xvals = []
    yvals = []
    for row in result:
        xvals.append(str(row[0]))
        yvals.append(int(row[1]))
    title = 'Barplot for population according to city'
    barPlot(xvals, yvals, title)

def barplot_avgrating_each_category(city_name):
    city_name = process_city_name(city_name)
    query = '''SELECT Category, Rating FROM Restaurants
                WHERE City="{}"'''.format(city_name)
    results = searchDB(query)
    dict_rating = {}
    for row in results:
        category = row[0]
        rating = float(row[1])
        if category in dict_rating.keys():
            dict_rating[category].append(rating)
        else:
            temp = []
            temp.append(rating)
            dict_rating[category] = temp

    dict_avg = {}
    for key, value in dict_rating.items():
        total = 0
        for val in value:
            total += val
        avg = float(total / len(value))
        dict_avg[key] = avg

    sorted_dict = sorted(dict_avg.items(), key=lambda x:x[1], reverse=True)
    xvals = []
    yvals = []
    for i in range(len(sorted_dict)):
        xvals.append(sorted_dict[i][0])
        yvals.append(sorted_dict[i][1])
    title = 'Average Rating of Each Category in City {}'.format(city_name)
    barPlot(xvals, yvals, title)

def barplot_avgprice_each_category(city_name):
    city_name = process_city_name(city_name)
    query = '''SELECT Category, Price FROM Restaurants
                WHERE City="{}" AND Price NOTNULL'''.format(city_name)
    results = searchDB(query)
    dict_price = {}
    for row in results:
        category = row[0]
        price = float(row[1])
        if category in dict_price.keys():
            dict_price[category].append(price)
        else:
            temp = []
            temp.append(price)
            dict_price[category] = temp

    dict_avg = {}
    for key, value in dict_price.items():
        total = 0
        for val in value:
            total += val
        avg = float(total / len(value))
        dict_avg[key] = avg

    sorted_dict = sorted(dict_avg.items(), key=lambda x:x[1], reverse=True)
    xvals = []
    yvals = []
    for i in range(len(sorted_dict)):
        xvals.append(sorted_dict[i][0])
        yvals.append(sorted_dict[i][1])
    title = 'Average Price of Different Categories in City {}'.format(city_name)
    barPlot(xvals, yvals, title)

def pieplot_restaurant_categories(city_name):
    city_name = process_city_name(city_name)
    query = '''SELECT Category FROM Restaurants
                WHERE City="{}"'''.format(city_name)
    results = searchDB(query)
    dict_category = {}
    for row in results:
        cur = row[0]
        if cur in dict_category.keys():
            dict_category[cur] += 1
        else:
            dict_category[cur] = 1

    sorted_dict = sorted(dict_category.items(), key=lambda x:x[1], reverse=True)
    labels = []
    values = []
    for i in range(min(5, len(sorted_dict))):
        labels.append(sorted_dict[i][0])
        values.append(sorted_dict[i][1])
    title = 'Top 5 Most Popular Restaurant Categories in City {}'.format(city_name)
    pieplot(labels, values, title)


if __name__ == '__main__':
    CACHE_DICT = load_cache(CACHE_FILE)
    build_database()
    # barplot_city_population()
    # pieplot_restaurant_categories('ann arbor')
    # barplot_avgrating_each_category('ann arbor')
    # barplot_avgprice_each_category('Ann Arbor')