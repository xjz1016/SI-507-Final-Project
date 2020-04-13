# WN2020 SI 507 Final Project

## Introduction
This project aims to build a basic web application, which allows the user to get information about cities in the US and the visualized data for restaurants in different cities. Several basic programming techniques are adopted in the project, which includes accessing data efficiently with caching via scraping and web API, using SQLite for data manipulating, using Unit Test for verification and using Plotly and Flask for data visualization, etc.

## Data Sources
(1) The web from Wikipedia, which is the data source for the table "Cities" in the database. (https://en.wikipedia.org/wiki/List_of_United_States_cities_by_population). 

(2) Yelp Fusion, which is the data source for the table "Restaurants" in the database.
(https://www.yelp.com/developers/documentation/v3/business_search)

## Run the Program
### Step 1: Apply an API Key for Yelp Fusion
(1) Go to "https://www.yelp.com/developers/documentation/v3/authentication" and create your app according to the instruction. 

(2) Create a new python file "secret.py" in the same folder as "program.py". And add the code:
```
API_KEY = '<your key>'
```  
### Step 2: Install packages
```
$ pip install -r requirements.txt --user
```  

### Step 3: Run program.py  
```  
$ python program.py
```  
### Step 4: Open "http://127.0.0.1:5000/ " in a browser
