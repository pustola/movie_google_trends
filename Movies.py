import requests
import re
import pandas as pd
from bs4 import BeautifulSoup
from IPython.display import clear_output

'''
LEGEND:
r_ = request
s_ = soup
'''

# Function scraps synopsis and original title
def scrap_synopsis(title_id):
    # 1. Create working link to a movie. Combingin constant imdb url with title ID : '/title/ID/'
    movie_url = 'https://www.imdb.com'+title_id
    # 2. Link that leads to synopsis
    plot_url = 'plotsummary?ref_=tt_stry_pl#synopsis'
    # 3. Create working synopsis link and get request model
    r_synopsis = requests.get(movie_url + plot_url).text
    # 4. Use soup to parse synopsis html object
    s_synopsis = BeautifulSoup(r_synopsis, 'html.parser')
    # 5. Extract synopsis text
    synopsis = s_synopsis.find('ul', id='plot-synopsis-content').li.text

    # Scrapping original title. If basic title = original it creates error. Get basic title.
    try:
        r_title = requests.get(movie_url).text
        s_title = BeautifulSoup(r_title, 'html.parser')
        original_title = s_title.find_all('div', class_='originalTitle')[0].text
        original_title = re.sub(' \(original title\)', '', original_title)
    except:
        original_title = s_title.find_all('div', class_='title_wrapper')
        original_title = re.search(r'[^\xa0]*',original_title[0].h1.text).group()

    return synopsis, original_title

title_ids = []
titles = []
years = []
ratings = []
votes = []

for page_counter in range(0,251,50): # Looping over next pages in top 250
    # 1. Get request model of top 250 imdb movies and convert it to str with .txt
    r_top250 = requests.get(f'https://www.imdb.com/search/title/?groups=top_250&view=simple&sort=year,desc&start={page_counter}').text
    # 2. Use soup to parse html object
    s_top250 = BeautifulSoup(r_top250, 'html.parser')

    # Scrapping title ID
    for div in s_top250.find_all('div', class_='col-title'):
        for link in div.find_all('a'):
            title_ids.append(link.get('href'))
            titles.append(link.text)

    # Scrapping year
    for span in s_top250.find_all('span', class_='lister-item-year text-muted unbold'):
        year_str = span.text
        year = re.search('\d\d\d\d',year_str).group()
        years.append(int(year))

    # Scrapping rating and votes
    for div in s_top250.find_all('div', class_='col-imdb-rating'):
        for strong in div.find_all('strong'):
            s = re.split(' ', strong.get('title'))
            ratings.append(s[0])
            votes.append(int(s[3].replace(',',''))) # Converting comma separated string to int ('115,334' = 115334)

# Creating DataFrame from previous elements
movies = pd.DataFrame({'ID':title_ids, 'Title':titles, 'Year':years, 'Rating':ratings, 'Votes':votes})

# Scrapping plots and original titles into a list
plots = []
original_titles = []
for i,t in enumerate(movies[movies['Year'] >= 2004]['ID']):
    print(len(movies[movies['Year'] >= 2004]['ID'])-i) # Printing counter and clearing output in the end
    plot, title = scrap_synopsis(t)
    plots.append(plot)
    original_titles.append(title)
    clear_output()

# Adding two columns
movies.insert(2, 'Original Title', pd.Series(original_titles))
movies['Plot'] = pd.Series(plots)

# Getting movies released after 2004 since Google trends dates back to 2004
movies2004 = movies[movies['Year'] >= 2004]
# Setting None value where there was no synopsis available on IMDB
movies2004['Plot'] = movies2004['Plot'].apply(lambda x: None if 'looks like we don\'t have' in x else x)

# Saving both dataframes to csv
movies2004.to_csv('movies2004.csv')
movies.to_csv('movies.csv')
