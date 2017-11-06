# Download stream from ustream.tv

[![CircleCI](https://img.shields.io/circleci/project/bertrandmartel/ustream-dl.svg?maxAge=2592000?style=plastic)](https://circleci.com/gh/bertrandmartel/ustream-dl) 
[![License](http://img.shields.io/:license-mit-blue.svg)](LICENSE.md)

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

[link to this diagram](https://bertrandmartel.github.io/callflow-workshop/?CYSwhg5gTmC2D6IB2AHArgFwLwoJ4YAsB7JAUgCYAGAZwGMoQUMBaUgZgFE1qMoBTOADoMANwAUBDBhTUAlOwCCFShD4ZltAmCRI+AG2UhgygGZQisZSnMijfY1TRQDlBd14DYw8ZOlzWnHiEJMp0DEyKypKwBlT81Cgk1HykrkhEGClURCJ8UFb4xGRUYYzqbEol9GAoGlo6+ogOlGYWyrBqYMoYkKkKQUWh9GUBXDz8QqISUjLyFcpgmAR8SBggtGCZygDuIITKwGiwsLiGqJjKYkhwWQDCynywYCB68q7uE15TvrOjAyFVcLlSo0FbNABSAGUAPIAOSiYGoBGU8USSGSfX+xRowyYow+nm80z8cxBGz0sRUajq2l0lNoJEyq2UCgACgBJPoEyY+Gb+dgcLFDIGREpgmkNSnATZdKjIWh6NCgJAQZR6EA8ZREEzKWzAPhEQzGVxCwEjAXcr7ibZ8ABG1CItAA1mpSVqUCsdnaHc7qVQGQ1aGsQibCgCcUD8eNCVMbfbHS6MG6xUhmgHdEGNBYnqmudGeWI4z7E7I-mHsaUIvM4nxaHwQLllFC4aEPHAziYiFAnsHsfLFcrVVR1ZrsjqqFokXxqH10ltsrl8lRTRGyqLKCgwDAKfoDkRtkg9EQwM0wBTlAAxAAyADU6mgkE7ZxkspQcnkCsEK7jgSjHu-L1vKIBH1KAZyoVpLH9AgHyfABWAAhABGZgyDggARZ95zfRdP0GM0qzJEgNnUKhrzvaDYNIRCULQzCqAwQ1KMfSgsNfd8lw3cthTXatKAZPB7xY7omLfTB0AwQQTD0EQADJQEgGAEEIR4+CwagQFgFA9D4WSwDreAVI6LAID2GDbVkgMTBACB4FsPhtiwRc1nJWTdlTfd4A0gAvPh4CIJgQCSLBSAAdgQihyGc9Yz0iyJwsi3ZgH2chyEUJCqFY0L6PuVLiAYbzGVi1L4oivL6wgSQ4oqcg4KyzDstktYMB0rB0P3Q9j2afMoJaF52OxS1vCAA)

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