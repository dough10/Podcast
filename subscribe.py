import os
from filename import formatFilename
from Podcast import Podcast

url = input('URL for the XML feed = ')
file = formatFilename(input('name the .log file = '))
os.system(f"(crontab -l 2>/dev/null; echo \"0 0 * * * /usr/local/bin/python3 /Users/dough10/Podcast/Podcast.py {url} > /Users/dough10/Downloads/{file}.log 2>&1\") | crontab -")
print('Starting download. This may take a minuite.')
Podcast(url).downloadNewest()