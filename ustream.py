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

def get_channel_id(sess, url):
	"""get channel id from the URL root page """
	content = sess.get(url).content
	soup = BeautifulSoup(content, 'html.parser')
	return soup.find("meta",  attrs={'name':"ustream:channel_id"})["content"]

def authenticate(sess, name, email, company, role, phone):
	"""authenticate to get the hash JSON object """
	payload = {
		'fields[name]' : name,
		'fields[email]' : email,
		'fields[company]' : company,
		'fields[role]' : role,
		'fields[phone]' : phone
	}
	r = sess.post('https://www.ustream.tv/ajax/viewer-registration/save/' + channel_id + '/channel/' + channel_id + '.json',
		data = payload)
	return json.loads(r.text)

def get_channel_content(sess, auth):
	"""get channel content to get video id list"""
	payload = {
		'hash' : json.dumps(auth["hash"])
	}
	r = sess.post('https://www.ustream.tv/ajax/viewing-experience/channel/' + channel_id + '/content.json',
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

def get_stream_urls(websocket_url, cookies, dirpath, url):
	"""connect to websocket to generate stream URL list"""
	ws = create_connection(websocket_url, header={
			"Cookies": cookies
		}
	)

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
	target_host = ""

	while ("stream" not in result["args"][0]) or (format_selected not in result["args"][0]["stream"]["streamFormats"]):
		result =  json.loads(ws.recv())
		print(result)
		if ( ("cmd" in result) and (result["cmd"] == "reject") and ("cluster" in result["args"][0])):
			print("rejected...try the next host")
			target_host = result["args"][0]["cluster"]["host"]
			break;
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
	return count, urls, target_host

def parallel_download(urls):
	"""parallel download of all FLV files"""
	logging.basicConfig(level=logging.INFO, format='%(asctime)s %(message)s')
	with closing(asyncio.get_event_loop()) as loop, \
		 closing(aiohttp.ClientSession()) as session:
		semaphore = asyncio.Semaphore(4)
		download_tasks = (download(url, session, semaphore) for url in urls)
		result = loop.run_until_complete(asyncio.gather(*download_tasks))

dirpath = tempfile.mkdtemp()

sess = requests.session()
url = "https://www.ustream.tv/channel/curJSsZFUUu"
channel_id = get_channel_id(sess, url)

auth = authenticate(sess, 'test', 'test@test.com', 'test', 'test', '0123456789')
content = get_channel_content(sess, auth)
video_id = content["exposedVariables"]["videosData"]["videos"][0]["id"]

print(auth);
print("channel_id : " + channel_id)
print("video_id : " + video_id)

cookies = sess.cookies.get_dict()
cookie_string = "; ".join([str(x)+"="+str(y) for x,y in cookies.items()])

websocket_url = "wss://r" + str(randN(8)) + "-1-" + video_id + "-recorded-wss-live.ums.ustream.tv/1/ustream"
count, urls, next_host = get_stream_urls(websocket_url, cookie_string, dirpath, url)

if (next_host is not None):
	print("connecting to " + next_host)
	count, urls, next_host = get_stream_urls("wss://" + next_host + "/1/ustream", cookie_string, dirpath, url)

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