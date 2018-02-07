import gspread
import os
import pandas as pd
import pickle
import json
import requests
import schedule
import time
import logging
from bs4 import BeautifulSoup
from oauth2client.service_account import ServiceAccountCredentials
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.svm import LinearSVC

pd.set_option('display.max_colwidth', 250)


logging.basicConfig(filename='newsfeed.log',level=logging.DEBUG)
logging.debug('This message should go to the log file')
logging.info('second log message')
logging.warning('third log message')
logging.warning('print to console')  # will print a message to the console
logging.info('if this prints then youre doing it wrong')  # will not print anything


def get_directory():
	return os.getcwd()

def news_grab():
	try:
		currentfolder = get_directory()
		vectfile = currentfolder + 'news_vect_pickle.p'
		modelfile = currentfolder + 'news_model_pickle.p'
		vect = pickle.load(open(vectfile, 'rb'))
		model = pickle.load(open(modelfile, 'rb'))
		
		scope = ['https://spreadsheets.google.com/IFTTT']
		credentials = ServiceAccountCredentials.from_json_keyfile_name(r'Feeds-178b2b03a664.json', scope)
		gc = gspread.authorize(credentials)
		logging.warning('grabbed things from google docs')
		ws = gc.open('NewsFeed2')
		sh = ws.sheet1
		zd = list(zip(sh.col_values(2), sh.col_values(3), sh.col_values(4)))
		zf = pd.DataFrame(zd, columns=['title', 'urls', 'html'])
		zf.replace('', pd.np.nan, inplace=True)
		zf.dropna(inplace=True)
		logging.warning(zf.head)
		def get_text(x):
			soup = BeautifulSoup(x, 'lxml')
			text = soup.get_text()
			return text
		
		zf.loc[:, 'text'] = zf['html'].map(get_text)
		tv = vect.transform(zf['text'])
		logging.warning('made a vect transform')
		res = model.predict(tv)
		
		rf = pd.DataFrame(res, columns=['wanted'])
		res = pd.merge(rf, zf, left_index=True, right_index=True)
		
		news_str = ''
		for t, u in zip(rez[rez['wanted'] == 'y']['title'], rez[rez['wanted']=='y']['urls']):
			news_str = news_str + t + '\n' + u + '\n'
		logging.warning('setting up the articles to print about')
		payload = {"value1": news_str}
		keyfile = open('iftttkey.txt', 'r')
		iftttkey = keyfile.read()
		
		r = requests.post('https://maker.ifttt.com/trigger/babeks_newsfeed_event/with/key/' + iftttkey, data=payload)
		logging.warning('called ifttt')
		#clean up newsfeed worksheet
		lenv = len(sh.col_values(1))
		cell_list = sh.range('A1:F' + str(lenv))
		for cell in cell_list:
			cell.value = ""
		sh.update_cells(cell_list)
		
		print(r.text)
	except:
		print('Failed')

schedule.every(60).minutes.do(news_grab)

while 1:
	schedule.run_pending()
	time.sleep(1)

print("great success!")