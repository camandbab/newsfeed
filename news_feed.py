import gspread
import os
import pandas as pd
import pickle
import json
import requests
import schedule
import time
from bs4 import BeautifulSoup
from oauth2client.service_account import ServiceAccountCredentials
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.svm import LinearSVC

pd.set_option('display.max_colwidth', 250)

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
		
		ws = gc.open('NewsFeed2')
		sh = ws.sheet1
		zd = list(zip(sh.col_values(2), sh.col_values(3), sh.col_values(4)))
		zf = pd.DataFrame(zd, columns=['title', 'urls', 'html'])
		zf.replace('', pd.np.nan, inplace=True)
		zf.dropna(inplace=True)
		
		def get_text(x):
			soup = BeautifulSoup(x, 'lxml')
			text = soup.get_text()
			return text
		
		zf.loc[:, 'text'] = zf['html'].map(get_text)
		tv = vect.transform(zf['text'])
		res = model.predict(tv)
		
		rf = pd.DataFrame(res, columns=['wanted'])
		res = pd.merge(rf, zf, left_index=True, right_index=True)
		
		news_str = ''
		for t, u in zip(rez[rez['wanted'] == 'y']['title'], rez[rez['wanted']=='y']['urls']):
			news_str = news_str + t + '\n' + u + '\n'
		
		payload = {"value1": news_str}
		keyfile = open('iftttkey.txt', 'r')
		iftttkey = keyfile.read()
		
		r = requests.post('https://maker.ifttt.com/trigger/babeks_newsfeed_event/with/key/' + iftttkey, data=payload)
		
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