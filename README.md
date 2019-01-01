# IVLEDownloader

An automatic IVLE files downloader using a web scraping tool, `Selenium`.

This is just an experiment for me to retrieve new files uploaded in a more efficient manner.

## Getting Started

These instructions will get you a copy of the project up and running on your local machine.

### Prerequisites

Ensure that you have `Python 3` and `pip` installed.

Run the following in your command line or terminal to install `selenium`.

```
pip install selenium
```

Download chromedriver from [here](https://chromedriver.storage.googleapis.com/index.html?path=2.45/) and extract the zip file. 

Copy the path to the executable file somewhere. 

Path should look something like: `C:/Users/User/Desktop/chromedriver_win32/chromedriver.exe` if you have extracted onto your desktop.

### Installing

Configure your settings using the following:

```
python setup.py -e {the path from earlier} -r {the path to your root folder} -u {username} -p {password}
```

This will create a `config.ini` file in the project folder. 

You can edit your settings from there or simply run the command above again if any mistakes were made.

To start downloading new files, run the following:

```
python ivle_downloader.py
```

## Notes

1. Folder structure has to strictly adhere to that given on IVLE.
2. Files with extensions such as `.exe` or `.py` are treated as dangerous files by Chrome and will require you to manually download them.
