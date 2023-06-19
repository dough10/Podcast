import sys
from Podcast import Podcast, listCronjobs
from config import *
from art import *

try:
  urls = listCronjobs()
  tprint("Podcast.py", font="italic")
  print('Choose a URL to unsubscribe from')
  print('0.) Quit')
  for ndx, url in enumerate(urls):
    print(f'{ndx + 1}.) {url}')
  try:
    unsubURL = int(input(f'Enter Choice: (0-{len(urls)}) '))
  except ValueError:
    print('Invalid input. Number required')
    sys.exit()
  if unsubURL == 0:
    sys.exit()
  elif unsubURL > 0 and unsubURL <= len(urls):
    Podcast(urls[unsubURL - 1]).unsubscribe()
  else:
    print('Invalid input')
    sys.exit()
except KeyboardInterrupt:
  pass

