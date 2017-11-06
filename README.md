# Download stream from ustream.tv

Experimental python script for downloading a stream (which has ended) from ustream.tv

The goal is to automate the process to get the video file for the whole stream in FLV format

This stream is protected by a dumb authentication (enter your name, role, email, phone num)

## Usage

```python
pip3 install -r requirements.txt
python3 ustream.py
```

## Call Flow

![processing](https://user-images.githubusercontent.com/5183022/32425330-9a66b3ba-c2b2-11e7-8c9c-4e693dd7b8c2.png)

[link to this diagram](https://bertrandmartel.github.io/callflow-workshop/?diagram_input=cHl0aG9uIHNjcmlwdC0%2BdXN0cmVhbS50dihodHRwcyk6IGdldCBjaGFubmVsIGlkIGZyb20gcHJvdmlkZWQgdXJsCnVzdHJlYW0udHYoaHR0cHMpLT5weXRob24gc2NyaXB0OiBodG1sIHJlc3BvbnNlCm5vdGUgb3ZlciBweXRob24gc2NyaXB0OiBzY3JhcCBjaGFubmVsX2lkIGZyb20gbWV0YSB0YWcKcHl0aG9uIHNjcmlwdC0%2BdXN0cmVhbS50dihodHRwcyk6IGF1dGhlbnRpY2F0ZSB3aXRoIGR1bW15IGlucHV0IChuYW1lLCBlbWFpbCkKdXN0cmVhbS50dihodHRwcyktPnB5dGhvbiBzY3JpcHQ6IHNlbmQgSlNPTiBoYXNoIHJlc3BvbnNlCnB5dGhvbiBzY3JpcHQtPnVzdHJlYW0udHYoaHR0cHMpOiBjYWxsIGdldCBjaGFubmVsIGNvbnRlbnQgQVBJCnVzdHJlYW0udHYoaHR0cHMpLT5weXRob24gc2NyaXB0OiBzZW5kIGNoYW5uZWwgZGF0YSBpbmNsdWRpbmcgbGlzdCBvZiB2aWRlbyBpZApweXRob24gc2NyaXB0LT51c3RyZWFtLnR2KHdlYnNvY2tldCk6IG9wZW4gd2Vic29ja2V0IGNvbm5lY3Rpb24KcHl0aG9uIHNjcmlwdC0%2BdXN0cmVhbS50dih3ZWJzb2NrZXQpOiBzZW5kIGNvbm5lY3QgY29tbWFuZAp1c3RyZWFtLnR2KHdlYnNvY2tldCktPnB5dGhvbiBzY3JpcHQ6IHJlY2VpdmUgSlNPTiBzdHJlYW0gaW5mb3JtYXRpb24gaW5jbHVkaW5nIGxpc3Qgb2YgaGFzaGVzCm5vdGUgb3ZlciBweXRob24gc2NyaXB0OiBwYXJ...iBoYXNoIHJlc3BvbnNlCnB5dGhvbiBzY3JpcHQtPnVzdHJlYW0udHYoaHR0cHMpOiBjYWxsIGdldCBjaGFubmVsIGNvbnRlbnQgQVBJCnVzdHJlYW0udHYoaHR0cHMpLT5weXRob24gc2NyaXB0OiBzZW5kIGNoYW5uZWwgZGF0YSBpbmNsdWRpbmcgbGlzdCBvZiB2aWRlbyBpZApweXRob24gc2NyaXB0LT51c3RyZWFtLnR2KHdlYnNvY2tldCk6IG9wZW4gd2Vic29ja2V0IGNvbm5lY3Rpb24KcHl0aG9uIHNjcmlwdC0%2BdXN0cmVhbS50dih3ZWJzb2NrZXQpOiBzZW5kIGNvbm5lY3QgY29tbWFuZAp1c3RyZWFtLnR2KHdlYnNvY2tldCktPnB5dGhvbiBzY3JpcHQ6IHJlY2VpdmUgSlNPTiBzdHJlYW0gaW5mb3JtYXRpb24gaW5jbHVkaW5nIGxpc3Qgb2YgaGFzaGVzCm5vdGUgb3ZlciBweXRob24gc2NyaXB0OiBwYXJhbGxlbCBkb3dubG9hZCBhbGwgRkxWIGNodW5rCm5vdGUgb3ZlciBweXRob24gc2NyaXB0OiByZW1vdmUgRkxWIGhlYWRlcnMgZnJvbSBjaHVua1sxLW5dCm5vdGUgb3ZlciBweXRob24gc2NyaXB0OiBjb25jYXQgRkxWIGNodW5rWzEtbl0gdG8gY2h1bmswCm5vdGUgb3ZlciBweXRob24gc2NyaXB0OiBjb3B5IGNodW5rMCB0byBvdXRwdXQuZmx2&diagram_theme=simple&ace_theme=github&config_view=vertical&window_size_options=%7B%22vertical%22%3A%7B%22width%22%3A1279%7D%2C%22horizontal%22%3A%7B%22height%22%3A301%7D%7D&title=download%20stream)

## Process 

* get channel id from the page : https://www.ustream.tv/channel/curJSsZFUUu
* authenticate with dummy input (name, role, email, phone numb.) to get the `hash` field via the url : 

    `https://www.ustream.tv/ajax/viewer-registration/save/{channel_id}/channel/{channel_id}.json`

* call the get channel content API (with the auth `hash`) to get the list of video : 

    `https://www.ustream.tv/ajax/viewing-experience/channel/{channel_id}/content.json`

* open websocket connection to :

    `wss://r{8_digit_random}-1-{video_id}-recorded-wss-live.ums.ustream.tv/1/ustream` 

and send a `connect` action with the following parameter : 

```
{
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
```
Then 3 responses frames are received including one with `stream` information which gives chunk url format and list of hashes to download. This includes `mp4/segmented` & `flv/segmented`. Here we download only flv/segmented
* download all chunk (for [this video](https://www.ustream.tv/channel/curJSsZFUUu) it's 14XX .flv file of 6 sec.)
* remove FLV headers of all chunk > 0 (eg chunk1 to chunkn excluding the first chunk)
* concatenate all those chunk to the first chunk : 0.flv
* copy the flv file to the specified location

Note that this is for personal use or education purpose only. For other usage, use [the official API](http://developers.ustream.tv/channel-api/)

## Convert the flv output to mp4 

Use ffmpeg : 

```
ffmpeg -i stream.flv -codec copy stream.mp4
```

## References

* [Video File Format Specification Version 10 - Adobe](https://www.google.fr/url?sa=t&rct=j&q=&esrc=s&source=web&cd=1&ved=0ahUKEwjfts6Xk6nXAhVILewKHbbFCOUQFggoMAA&url=https%3A%2F%2Fwww.adobe.com%2Fcontent%2Fdam%2Facom%2Fen%2Fdevnet%2Fflv%2Fvideo_file_format_spec_v10.pdf&usg=AOvVaw0wwfZyn48I7P4PNPwn736E)
* [flvmeta tool](https://github.com/noirotm/flvmeta)

## License 

The MIT License (MIT) Copyright (c) 2017 Bertrand Martel