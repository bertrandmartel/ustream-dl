#!/usr/bin/python3
import json, requests
from bs4 import BeautifulSoup
from websocket import create_connection
import random
import urllib.request
import asyncio, logging, aiohttp
from contextlib import closing
import tempfile, shutil

#https://codereview.stackexchange.com/a/69799/120531
def randN(n):
	"""generate random integer """
	assert n <= 10
	l = list(range(10)) # compat py2 & py3
	while l[0] == 0:
		random.shuffle(l)
	return int(''.join(str(d) for d in l[:n]))

def get_channel_id(url):
	"""get channel id from the URL root page """
	with urllib.request.urlopen(url) as url:
		response = url.read()
		soup = BeautifulSoup(response, 'html.parser')
		return soup.find("meta",  attrs={'name':"ustream:channel_id"})["content"]

def authenticate(name, email, company, role, phone):
	"""authenticate to get the hash JSON object """
	payload = {
		'fields[name]' : name,
		'fields[email]' : email,
		'fields[company]' : company,
		'fields[role]' : role,
		'fields[phone]' : phone
	}
	r = requests.post('https://www.ustream.tv/ajax/viewer-registration/save/' + channel_id + '/channel/' + channel_id + '.json',
		data = payload)
	return json.loads(r.text)

def get_channel_content(auth):
	"""get channel content to get video id list"""
	payload = {
		'hash' : json.dumps(auth["hash"])
	}
	r = requests.post('https://www.ustream.tv/ajax/viewing-experience/channel/' + channel_id + '/content.json',
		data = payload)
	return json.loads(r.text)

#https://stackoverflow.com/a/31795242/2614364
@asyncio.coroutine
def download(url, session, semaphore, chunk_size=1<<15):
	"""download FLV async task"""
	with (yield from semaphore): # limit number of concurrent downloads
		logging.info('downloading %s', url["location"])
		response = yield from session.get(url["location"])
		with closing(response), open(url["dest"], 'wb') as file:
			while True: # save file
				chunk = yield from response.content.read(chunk_size)
				if not chunk:
					break
				file.write(chunk)
		logging.info('done %s', url["location"])
	return url["location"], (response.status, tuple(response.headers.items()))

def get_stream_urls(dirpath, url):
	"""connect to websocket to generate stream URL list"""
	ws = create_connection("wss://r" + str(randN(8)) + "-1-" + video_id + "-recorded-wss-live.ums.ustream.tv/1/ustream")

	data = {
		"cmd":"connect",
		"args":[
			{
				"type":"viewer",
				"appId":3,
				"appVersion":2,
				"isOffairRecorded":True,
				"referrer": url,
				"media": video_id,
				"application":"recorded",
				"hash":json.dumps(auth["hash"])
			}
		]
	}
	ws.send(json.dumps(data))
	result =  { "args": [ {} ] }
	urls = []
	count = 0
	format_selected = "flv/segmented"
	
	while ("stream" not in result["args"][0]) or (format_selected not in result["args"][0]["stream"]["streamFormats"]):
		result =  json.loads(ws.recv())
		print(result)
		if ("stream" in result["args"][0]) and (format_selected in result["args"][0]["stream"]["streamFormats"]):
			hashes = result["args"][0]["stream"]["streamFormats"][format_selected]["hashes"]
			url = "https://vod-cdn.ustream.tv/" + result["args"][0]["stream"]["streamFormats"][format_selected]["contentAccess"]["accessList"][0]["data"]["path"]
			streams = result["args"][0]["stream"]["streamFormats"][format_selected]["streams"]
			for stream in streams:
				if format_selected == "flv/segmented":
					if stream["preset"] == "original":
						hash_list = sorted(hashes.items(),key=lambda x: int(x[0]))
						for i in range(len(hash_list)):
							if (i + 1) != len(hash_list):
								for x in range(int(hash_list[i][0]), int(hash_list[i+1][0])):
									print(url + stream["segmentUrl"].replace('%',str(x),1).replace('%',hash_list[i][1],1))
									urls.append({
										"location": url + stream["segmentUrl"].replace('%',str(x),1).replace('%',hash_list[i][1],1),
										"dest": dirpath + "/" + str(count) + ".flv"
									})
									count+=1
							else:
								print(url + stream["segmentUrl"].replace('%',hash_list[i][0],1).replace('%',hash_list[i][1],1))
								urls.append({
									"location": url + stream["segmentUrl"].replace('%',hash_list[i][0],1).replace('%',hash_list[i][1],1),
									"dest": dirpath + "/" + str(count) + ".flv"
								})
								count+=1
				else:
					if stream["codec"] == "avc1.64001f":
						print(stream)
						count = 0
						hash_list = sorted(hashes.items(),key=lambda x: int(x[0]))
						for i in range(len(hash_list)):
							if (i + 1) != len(hash_list):
								for x in range(int(hash_list[i][0]), int(hash_list[i+1][0])):
									print(url + stream["segmentUrl"].replace('%',str(x),1).replace('%',hash_list[i][1],1))
									urls.append({
										"location": url + stream["segmentUrl"].replace('%',str(x),1).replace('%',hash_list[i][1],1),
										"dest": dirpath + "/" + str(count) + ".m4v"
									})
									count+=1
							else:
								print(url + stream["segmentUrl"].replace('%',hash_list[i][0],1).replace('%',hash_list[i][1],1))
								urls.append({
									"location": url + stream["segmentUrl"].replace('%',hash_list[i][0],1).replace('%',hash_list[i][1],1),
									"dest": dirpath + "/" + str(count) + ".m4v"
								})
								count+=1

	ws.close()
	return count, urls

def parallel_download(urls):
	"""parallel download of all FLV files"""
	logging.basicConfig(level=logging.INFO, format='%(asctime)s %(message)s')
	with closing(asyncio.get_event_loop()) as loop, \
		 closing(aiohttp.ClientSession()) as session:
		semaphore = asyncio.Semaphore(4)
		download_tasks = (download(url, session, semaphore) for url in urls)
		result = loop.run_until_complete(asyncio.gather(*download_tasks))

dirpath = tempfile.mkdtemp()

url = "https://www.ustream.tv/channel/curJSsZFUUu"
channel_id = get_channel_id(url)

auth = authenticate('test', 'test@test.com', 'test', 'test', '0123456789')
content = get_channel_content(auth)
video_id = content["exposedVariables"]["videosData"]["videos"][0]["id"]

print(auth);
print("channel_id : " + channel_id)
print("video_id : " + video_id)

count, urls = get_stream_urls(dirpath, url)

parallel_download(urls)

print("format FLV...")

for i in range(1, count):
	with open(dirpath + "/" + str(i) + ".flv", "rb") as in_file:
		with open(dirpath + "/out" + str(i) + ".flv", "wb") as out_file:
			out_file.write(in_file.read()[13:])

print("concat FLV...")

with open(dirpath + '/0.flv', 'ab') as out_file:
	for i in range(1, count):
		with open(dirpath + "/out" + str(i) + ".flv", "rb") as in_file:
			out_file.write(in_file.read())

shutil.copyfile(dirpath + '/0.flv', './stream.flv')
shutil.rmtree(dirpath)