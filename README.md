# VirtualGraffiti
OpenCV + Python magic for Laser Pointer Graffiti fun!

Kind of like this:
https://www.instructables.com/id/LASER-GRAFFITI-1/  
But for much, much more modest setups :-)

In short, you can use any red laser pointer to paint graffiti on your screen. It even has on screen buttons that work!

![Demo video](gif/Demo.gif)

## Requirements:

You must have a screen and a reasonably decent camera *pointing at that screen*.

I found the simplest way to do this is by using my phone as a camera, and installing an IP webcam app.
I personally use [this app for Android](https://play.google.com/store/apps/details?id=com.pas.webcam), but I do not endorse it or take any responsibility over what it does.

Apart from that you will need a working windows setup with Python3 and opencv installed.

## Usage:

Running with an external camera feed (such as an IP camera) is as simple as 

```
python Graffiti.py --video_url="http://{URL_OF_VIDEO_FEED}/video"
```

Where URL_OF_VIDEO_FEED is the url to the video feed (for example, for the IP webcam app I use it typically http://10.0.0.2:8080/video).

If using a camera device connected to the same computer running the code, you can use

```
python Graffiti.py --cemera_id=0
```

## Saving masterpieces

Simply shine the laser pointer on the save icon. Images will be saved in the SavedImages/ dir.