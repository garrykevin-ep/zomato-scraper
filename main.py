import os
from multiprocessing.pool import ThreadPool

import lxml
import requests
from bs4 import BeautifulSoup


def fetch_url(entry):
	path, uri = entry
	if not os.path.exists(path):
		r = requests.get(uri, stream=True)
		if r.status_code == 200:
			with open(path, 'wb') as f:
				for chunk in r:
					f.write(chunk)
	return path

class ZomatoScraper():

	headers = {'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.13; rv:62.0) Gecko/20100101 Firefox/62.0'}
	
	more_pic_api = 'https://www.zomato.com/php/load_more_res_pics.php'

	post_headers = {
	'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.13; rv:62.0) Gecko/20100101 Firefox/62.0',
	'X-Requested-With': 'XMLHttpRequest',}

	more_pic_data = {
	'action' : 'fetch_photos',
	'category' : 'all',
	'index'  : 5, # no change with this parameter
	# 'offset' : 0,  #exclusive start range
	# 'limit'  : limit, # image_count from offset
	# 'res_id' : data_id
	}


	def __init__(self, resturant_url, image_count = 100, start_index = 0):
		self.resturant_url = resturant_url
		self.more_pic_data['limit'] = image_count 
		self.more_pic_data['offset'] = start_index
		

	def get_data_id(self):
		photo_page = requests.get(self.resturant_url,headers=self.headers,timeout=10)
		soup = BeautifulSoup(photo_page.content,'lxml')
		thumbs_container = soup.find('div',{'id': 'thumbsContainer'})
		self.more_pic_data['res_id'] =  thumbs_container.attrs['data-res_id']
		return self.more_pic_data['res_id']

	def get_image_urls(self):
		more_images_html = requests.post(self.more_pic_api,data=self.more_pic_data,headers=self.post_headers,timeout = 10)
		api_data = more_images_html.json()['html']
		soup = BeautifulSoup(api_data,'lxml')
		image_tags = soup.findAll('img')
		
		self.photo_urls = []
		for image_tag in image_tags:
			full_url = image_tag.attrs['data-original']
			url, query = full_url.split('?')
			self.photo_urls.append(url+'?'+query.replace('200','800'))
		return self.photo_urls
	
	def download_images(self, download_path):
		counter = 1
		for url in self.photo_urls:
			response = requests.get(url)
			with open(download_path + str(counter) + '.jpg', 'wb') as f:
				print('Downloading -- ' + str(counter) )
				print (download_path + str(counter) + '.jpg')
				f.write(response.content)
				counter += 1

def easy_download(image_count = 10, resturant_url = 'https://www.zomato.com/chennai/mezze-ra-puram/photos'):
	'''
		dowloads the images to /images folder
	'''
	scrap = ZomatoScraper(resturant_url=resturant_url,image_count = image_count, start_index = 0)
	# unique id to get all images
	scrap.get_data_id()
	# send a post to api
	scrap.get_image_urls()
	path = os.path.dirname (os.path.realpath('__file__') )
	path += '/images/'
	urls = []
	counter = 1
	for url in scrap.photo_urls:
		urls.append( (path + str(counter) + '.jpg',url) )
		counter += 1
	results = ThreadPool(8).imap_unordered(fetch_url, urls)
	for path in results:
		print (path)
	# scrap.download_images(download_path = path)
	
def main():
	import time
	start = time.time()
	easy_download()
	end = time.time()
	print (end-start)

        
main()
