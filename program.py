from bs4 import BeautifulSoup
import requests
import json
import time
import secret
import sqlite3
import plotly.graph_objs as go
import plotly
from plotly.subplots import make_subplots
from plotly.offline import plot 
from flask import Flask, render_template, Markup

CACHE_FILE = 'cache.json'
CACHE_DICT = {}
DB_NAME = 'final_project.sqlite'
API_KEY = secret.API_KEY
HEADERS = {'Authorization': 'Bearer {}'.format(API_KEY),
           'User-Agent': 'UMSI 507 Course Project - Python Scraping',
           'From': 'junzhexu@umich.edu',
           'Course-Info': 'https://si.umich.edu/programs/courses/507'
}

app = Flask(__name__)

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
            "Name" TEXT NOT NULL UNIQUE,
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
                        area=area, latitude=latitude, longitude=longitude
        )
        city_instances.append(instance)
    
    return city_instances

def build_restaurant_instance(city_instances):
    restaurant_instances = []
    endpoint_url = 'https://api.yelp.com/v3/businesses/search'
    for c in city_instances:
        city = c.name
        params = {'location': city + ',' + c.state , 'term': 'restaurants', 'limit': 50}
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

def get_avg_and_sort(results):
    # result is the list of tuples returned by database query. The tuple must be length of 2!
    dict_rating = {}
    for row in results:
        data0 = row[0]
        data1 = float(row[1])
        if data0 in dict_rating.keys():
            dict_rating[data0].append(data1)
        else:
            temp = []
            temp.append(data1)
            dict_rating[data0] = temp

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

    return xvals, yvals

def barplot_city_population():
    query = '''SELECT Name, Population, State FROM Cities
                ORDER BY Population DESC'''
    result = searchDB(query)
    xvals = []
    yvals = []
    for row in result[:50]:
        xvals.append('{}({})'.format(row[0], row[2]))
        yvals.append(int(row[1]))
    
    title = 'Top 50 Cities By Population In The US'
    return flask_plot(xvals, yvals, title, 'bar')

def flask_plot(xvals, yvals, title, fig_type):
    fig = make_subplots(rows=1, cols=1, specs=[[{"type": fig_type}]], subplot_titles=(title))
    if fig_type == 'pie':
        fig.add_trace(go.Pie(labels=xvals, values=yvals), row=1, col=1)
        fig.update_traces(hole=.4, hoverinfo="label+percent+name")
    elif fig_type == 'bar':
        fig.add_trace(go.Bar(x=xvals, y=yvals), row=1, col=1)
    
    fig.update_layout(xaxis_tickangle=-45, annotations=[dict(text=title, font_size=25, showarrow=False)])
    fig_div = plot(fig, output_type="div")
    return fig_div

def pieplot_restaurant_categories(city_name):
    city_name = process_city_name(city_name)
    query = '''SELECT Category FROM Restaurants
                WHERE City="{}"'''.format(city_name)
    results = searchDB(query)
    dict_category = {}
    for row in results:
        category = row[0]
        if category in dict_category.keys():
            dict_category[category] += 1
        else:
            dict_category[category] = 1
    
    sorted_list = sorted(dict_category.items(), key=lambda x:x[1], reverse=True)
    labels = []
    values = []
    for row in sorted_list[:3]:
        labels.append(row[0])
        values.append(row[1])
    
    others_num = 0
    for row in sorted_list[3:]:
        others_num += row[1]
    
    labels.append('Others')
    values.append(others_num)
    title = '''Popular Restaurant Types in {}'''.format(city_name)
    return flask_plot(labels, values, title, 'pie')

def barplot_avgrating_each_category(city_name):
    city_name = process_city_name(city_name)
    query = '''SELECT Category, Rating FROM Restaurants
                WHERE City="{}"'''.format(city_name)
    results = searchDB(query)
    xvals, yvals = get_avg_and_sort(results)
    title = 'Average Rating of Restaurants By Category in {}'.format(city_name)
    return flask_plot(xvals, yvals, title, 'bar')

def barplot_avgprice_each_category(city_name):
    city_name = process_city_name(city_name)
    query = '''SELECT Category, Price FROM Restaurants
                WHERE City="{}" AND Price NOTNULL'''.format(city_name)
    results = searchDB(query)
    xvals, yvals = get_avg_and_sort(results)
    title = 'Average Price of Restaurants By Category in {}'.format(city_name)
    return flask_plot(xvals, yvals, title, 'bar')
  
def barplot_avgreview_each_category(city_name):
    city_name = process_city_name(city_name)
    query = '''SELECT Category, [Number of Review] FROM Restaurants
                WHERE City="{}"'''.format(city_name)
    results = searchDB(query)
    xvals, yvals = get_avg_and_sort(results)
    title = 'Average Number of Reviews of Different Categories in {}'.format(city_name)
    return flask_plot(xvals, yvals, title, 'bar')
  
def barplot_toprated_restaurant(city_name):
    city_name = process_city_name(city_name)
    query = '''SELECT Name, Rating FROM Restaurants WHERE City="{}"
                ORDER BY Rating DESC'''.format(city_name)
    results = searchDB(query)
    xvals = []
    yvals = []
    for row in results:
        xvals.append(str(row[0]))
        yvals.append(float(row[1]))
   
    title = 'Restaurants Ranking By Rating in {}'.format(city_name)
    return flask_plot(xvals, yvals, title, 'bar')
   
def barplot_mostreviewed_restaurant(city_name):
    city_name = process_city_name(city_name)
    query = '''SELECT Name, [Number of Review] FROM Restaurants WHERE City="{}"
                ORDER BY [Number of Review] DESC'''.format(city_name)
    results = searchDB(query)
    xvals = []
    yvals = []
    for row in results:
        xvals.append(str(row[0]))
        yvals.append(float(row[1]))
    
    title = 'Restaurants Ranking By Reviews in {}'.format(city_name)
    return flask_plot(xvals, yvals, title, 'bar')
   
def barplot_topprice_restaurant(city_name):
    city_name = process_city_name(city_name)
    query = '''SELECT Name, Price FROM Restaurants WHERE City="{}"
                AND Price NOTNULL ORDER BY Price DESC'''.format(city_name)
    results = searchDB(query)
    xvals = []
    yvals = []
    for row in results:
        xvals.append(str(row[0]))
        yvals.append(int(row[1]))
   
    title = 'Restaurants Ranking By Price in {}'.format(city_name)
    return flask_plot(xvals, yvals, title, 'bar')

def barplot_avgrating_state():
    query = '''SELECT c.State, r.Rating FROM Cities as c
                JOIN Restaurants as r ON c.Name=r.City
                WHERE r.Rating NOTNULL'''
    results = searchDB(query)
    xvals, yvals = get_avg_and_sort(results)
    title = 'Average Restaurants Rating By States'
    return flask_plot(xvals, yvals, title, 'bar')
   
def barplot_avgprice_state():
    query = '''SELECT c.State, r.Price FROM Cities as c
                JOIN Restaurants as r ON c.Name=r.City
                WHERE r.Price NOTNULL'''
    results = searchDB(query)
    xvals, yvals = get_avg_and_sort(results)
    title = 'Average Restaurants Price By States'
    return flask_plot(xvals, yvals, title, 'bar')

def barplot_compare(city_list):
    result_list = []
    for i in range(len(city_list)):
        city_list[i] = process_city_name(city_list[i])
        query = '''SELECT AVG(Rating), AVG(Price)
                    FROM Restaurants WHERE City="{}" AND Price NOTNULL'''.format(city_list[i])
        result_list.append(searchDB(query))

    xvals = ['Average Rating', 'Average Price']
    fig = go.Figure()
    for i in range(len(city_list)):
        fig.add_trace(go.Bar(
            x=xvals,
            y=list(result_list[i][0]),
            name=city_list[i],
        ))
    fig.update_layout(barmode='group', xaxis_tickangle=0, title='Comparison Between Different Cities')
    fig.show()

# def multiple_plots_city(city_name):
#     city_name = process_city_name(city_name)
#     fig = make_subplots(rows=3, cols=2,
#                         specs=[[{"type": "pie"}, {"type": "bar"}],
#                               [{"type": "bar"}, {"type": "bar"}],
#                               [{"type": "bar"}, {"type": "bar"}]], 
#                         subplot_titles=('Top 5 Most Popular Restaurant Types in {}'.format(city_name), 
#                                         'Average Number of Reviews of Each Category in {}'.format(city_name), 
#                                         'Average Rating of Each Category in {}'.format(city_name), 
#                                         'Average Price of Different Categories in {}'.format(city_name), 
#                                         'Top Rated Restaurants in {}'.format(city_name),
#                                         'Restaurants Having The Most Number of Reviews in {}'.format(city_name)))
#     fig.add_trace(pieplot_restaurant_categories(city_name), row=1, col=1)
#     fig.add_trace(barplot_avgreview_each_category(city_name), row=1, col=2)
#     fig.add_trace(barplot_avgrating_each_category(city_name), row=2, col=1)
#     fig.add_trace(barplot_avgprice_each_category(city_name), row=2, col=2)
#     fig.add_trace(barplot_toprated_restaurant(city_name), row=3, col=1)
#     fig.add_trace(barplot_mostreviewed_restaurant(city_name), row=3, col=2)
#     fig.update_layout(height=1600, title_text="", xaxis_tickangle=-45)
#     fig.show()

#########################################
############# Flask Web App #############
#########################################

@app.route('/')
def home():
    city_dict = {}
    query = '''SELECT Id, Name, State, Population FROM Cities'''
    results = searchDB(query)
    for row in results:
        temp = []
        temp.append(row[1])
        temp.append(row[2])
        temp.append(row[3])
        city_dict[row[0]] = temp
    
    return render_template('home.html', city_dict=city_dict)

@app.route('/population')
def population():
    figure = barplot_city_population()
    return render_template('plot.html', figure=Markup(figure))

@app.route('/city/<city_nm>/')
def city(city_nm):
    return render_template('city.html', name=city_nm)

@app.route('/city/<city_nm>/<choice>')
def data(city_nm, choice):
    city_name = city_nm.replace('%20', ' ')
    city_name = process_city_name(city_name)

    if choice == 'barplot_avgprice_each_category':
        figure = barplot_avgprice_each_category(city_name)
    elif choice == 'barplot_avgrating_each_category':
        figure = barplot_avgrating_each_category(city_name)
    elif choice == 'barplot_avgreview_each_category':
        figure = barplot_avgreview_each_category(city_name)
    elif choice == 'barplot_toprated_restaurant':
        figure = barplot_toprated_restaurant(city_name)
    elif choice == 'barplot_topprice_restaurant':
        figure = barplot_topprice_restaurant(city_name)
    elif choice == 'barplot_mostreviewed_restaurant':
        figure = barplot_mostreviewed_restaurant(city_name)
    if choice == 'pieplot_restaurant_categories':
        figure = pieplot_restaurant_categories(city_name)
    
    return render_template('plot.html', name=city_name, figure=Markup(figure))



if __name__ == '__main__':
    CACHE_DICT = load_cache(CACHE_FILE)
    build_database()
    app.run(debug=True, use_reloader=False)

    # barplot_city_population()
    
    # barplot_avgprice_state()
    # barplot_avgrating_state()
    
    # barplot_compare(['new york', 'los angeles', 'chicago'])
   