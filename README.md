# Flickr Archive

Use this tool if you would like to:

1. Quit Flickr while preserving your images, albums, tags, favorites, comments, and views ... in a way that's easy to browse on your computer—just like Flickr!

2. Archive your Flickr account, in case Flickr becomes too expensive, or shuts down someday.

3. Browse your images much more quickly than on Flickr.

## Download your data

First, download all your data from Flickr. This is very easy. Just go to your Flickr settings (it's near the "Log Out" button in Flickr) and click on "Request my Flickr Data" in the "Your Flickr Data" section. It can take several days for your data to become available, if you have a lot of images. After it's available, download it.

## Installation

Once you've successfully downloaded your images:

1. Download this tool (`flickr-archive`) by clicking on the big green button in GitHub, or (preferable) downloading the latest release from the "releases" tab.
2. Create `images` and `json` folders inside the `flickr-archive` folder, then move all the images you downloaded from Flickr to `images`, and all the json files you downloaded to the `json` folder. They should all live "flat." Yes, this means that potentially thousands of files are in one folder. That's okay.
3. If you're on a Mac, open the Terminal application. If you're on a PC, open cmder (you can download it from https://cmder.net), or your terminal of choice.
4. cd to the `flickr-archive` folder. If you've got `flickr-archive` on your Desktop, for example, you'd type `cd ~/Desktop/flickr-archive`, and then hit return.
5. Type `which python`. If you don't have Python installed, install it (check Google for instructions). I built this on Python 2.7, but Python 3 might work too.
6. Type `which pip`. If you don't have `pip` installed, install it (check Google for instructions).
7. Type `pip install -r requirements.txt` and hit enter. This installs a Python package required to create thumbnail images.

## Usage

1. Type `python build.py` and go grab something to eat.
2. Once the script is done running, you can either explore the images in the `albums` folder, or open the `html/index.html` file in your web browser of choice.

## Troubleshooting

This is beta software, but I'm happy to troubleshoot issues that come up. Just send me the relevant log in the `logs` folder, and whatever error popped up in the console. Here are some common issues:

If you see this message:

```python
    Traceback (most recent call last):
      File "build.py", line 15, in <module>
        from PIL import Image
    ImportError: No module named PIL
```

... then you haven't installed the `python-resize-image` library. Run `pip install -r requirements.txt` from the repo root.