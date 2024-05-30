import os
import sys
import time
import json
import queue
import threading
from tqdm import tqdm
from lib.is_audio import is_audio_file
from lib.file_manager import File_manager
from lib.select_folder import select_folder
from lib.get_folder_size import get_folder_size
from lib.playlist_manager import Playlist_manager
from lib.cue_from_discogs import  cue_from_releaseid
from Podcast import updatePlayer as updatePodcast
from lib.log import log, print_change_log, files_with_issues, need_attention, reset_log

file_path = os.path.abspath(__file__)
script_folder = os.path.dirname(file_path)
config_path = os.path.join(script_folder, 'config.json')
with open(config_path, 'r') as j:
  config = json.load(j)

sorted_dir = select_folder()
working_dir = config['source']
ignore_folders = config['lrc_ignore_folders'] # folders whos files we will be ignored when attempting tog et lyrics
remove_lrc_wd = False # default value.  user will be propted if needed
use_sync_file = False # default value.  user will be propted if needed
import_cues = False
import_lyrics = False
json_data = {}
lib_data = {}
changes = { # log of file changes 
  "lrc_created":0,
  "new_folders": 0,
  "files_writen": 0,
  "playlist_created": 0,
  "files_deleted": 0,
  "folders_deleted": 0,
  "folders_contained": 0,
  "images_renamed": 0,
  "files_renamed": 0
}

sync_file = os.path.join(sorted_dir, 'sync.json')
file_manager = File_manager(changes)
pl_manager = Playlist_manager(changes)



def is_ignored(source_file):
  return any(os.path.join(working_dir, folder) in source_file for folder in ignore_folders)



def add_to_lib(artist, album, location, file, title, track, disc):
  """
  add audio file to data dict.

  Parameters:
  - artist (str): album artist
  - album (str): album title
  - location  (str): file path
  - file (str): audio filename
  - title (str): track title
  - track (num): track number
  - disc (num): disc number
  
  Returns:
  None
  """
  if artist not in lib_data:
    lib_data[artist] = []

  # Find the album in the artist's list of albums
  album_exists = False
  for alb in lib_data[artist]:
    if alb['title'] == album:
      alb['tracks'].append({
        'file': file,
        'path': location,
        'artist': artist, 
        'title': title, 
        'track': track, 
        'disc': disc
      })
      album_exists = True
      break

  # If the album does not exist, create a new entry
  if not album_exists:
      lib_data[artist].append({
        'title': album, 
        'artist':artist,
        'tracks': [
          {
            'file': file,
            'path': location,
            'artist': artist, 
            'title': title, 
            'track': track, 
            'disc': disc
          }
        ]
      })



def move_file(root, file, ext):
  """
  Process audio file in the specified root directory.

  Parameters:
  - root (str): The root directory path.
  - file (str): The name of the audio file.
  - ext  (str): the file extension
  
  Returns:
  None
  """
  global lib_data
  source_file = os.path.join(root, file)
  jpg = os.path.join(root, 'cover.jpg')
  alt_jpg = os.path.join(root, '..', 'cover.jpg')
  lrc_filename = f'{os.path.splitext(file)[0]}.lrc'
  lrc = os.path.join(root, lrc_filename)
  releaseID = os.path.join(root, 'releaseid.txt')

  # create cue from discogs data 
  # will be saved to source location and not destination 
  # will copy it to destination later in this function
  if os.path.exists(releaseID) and import_cues:
    cue_from_releaseid(releaseID, source_file, changes)

  # get info needed to sort the file
  if ext == '.flac':
    info = pl_manager.get_flac_info(source_file, file)
  else:
    info = pl_manager.get_mp3_info(source_file, file, jpg)

  # return if no info was found
  if not info:
    return

  # early return if no cover.jpg is found
  # placed here so that get_mp3_info() has a chance to attempt extract
  if not os.path.exists(jpg) and not os.path.exists(alt_jpg):
    need_attention.append(f'file: {source_file}\nissue: art\n')
    return

  artist_folder = info['artist']
  album_folder = file_manager.formatFilename(info['album'])
  lrc_artist = info['lrc_artist']
  song_title = info['title']

  # build data dictonary of artists and albums
  add_to_lib(artist_folder, album_folder, root.replace(config['source'], ''), file, song_title, info['track'], info['disc'])

  # early return if artist or album isn't listed in sync file
  if use_sync_file:

    # artist is not in sync file
    if artist_folder not in json_data:

      # artist folder path
      artf = os.path.join(sorted_dir, artist_folder)

      # if folder is there but not in sync file
      if os.path.exists(artf):
        file_manager.count_folder_content(artf)
        file_manager.remove_folder(artf)
      return
    
    # album is not in sync file
    if album_folder not in json_data[artist_folder]:

      # album folder path
      albf = os.path.join(sorted_dir, artist_folder, album_folder)

      # if folder is there but not in sync file
      if os.path.exists(albf):
        file_manager.count_folder_content(albf)
        file_manager.remove_folder(albf)
      return

  if import_lyrics and not is_ignored(source_file):
    file_manager.save_lrc_file(lrc, lrc_artist, song_title)

  # setup destination location string and create folders
  dest = os.path.join(sorted_dir, artist_folder, album_folder)
  if not os.path.exists(dest):
    try:
      os.makedirs(dest)
      changes['new_folders'] += 1
    except FileExistsError:
      pass

  img_path = os.path.join(dest, 'cover.jpg')
  if os.path.exists(jpg):
    file_manager.copy_file(jpg, dest, img_path)
  elif os.path.exists(alt_jpg): 
    file_manager.copy_file(alt_jpg, dest, img_path)         

  if os.path.exists(lrc) and import_lyrics:
    file_manager.copy_file(lrc, dest, os.path.join(dest, lrc_filename))

  if import_cues:
    if ext == '.flac':
      pl_manager.import_m3u_files(root, dest)
    else:
      pl_manager.import_cue_files(root, dest)

  try:
    file_manager.copy_file(source_file, dest, os.path.join(dest, file))
  except Exception as e:
    log('copy failed..')
    need_attention.append(f"file:{source_file}\ndest:{dest}\nerror:{str(e)}\n\n")
    return

def get_audio_files():
  audio_files = []
  for root, dirs, files in os.walk(working_dir):
    for file in files:
      if is_audio_file(file) and not file.startswith('._'):
        file = file_manager.fix_filename(root, file)
        audio_files.append({'root': root, 'file': file, 'ext': os.path.splitext(file)[-1].lower()})
  return audio_files

def process_audio_files(window):
  """
  Process all audio files in the working directory.

  Parameters:
  - window (object): pywebview window object.

  Returns:
  None
  """
  audio_files = get_audio_files()
  length = len(audio_files)
  for ndx, file in enumerate(tqdm(audio_files, desc ='Copying files', unit='file')):
    move_file(file['root'], file['file'], file['ext'])
    if window:
      window.evaluate_js(f'document.querySelector("sync-ui").updateBar("#files-bar", {ndx}, {length});')

def notify(s, window):
  try:
    if window:
      window.evaluate_js(f'document.querySelector("sync-ui").syncUpdate({json.dumps(s)});')
      return
    print(s['text'])
  except Exception as e:
    print(e)

def get_lib_size(queue):
  queue.put(get_folder_size(config['source']))

def run_sync(window):
  """
  Main function to organize and process audio files.

  Parameters:
  None

  Returns:
  None
  """
  global sorted_dir
  global use_sync_file
  global import_cues
  global import_lyrics
  global json_data
  global sync_file
  global lib_data

  lib_data = {}

  sync_file = os.path.join(sorted_dir, 'sync.json')
  playlist_folder = os.path.join(sorted_dir, 'playlist_data')

  if os.path.exists(sync_file):
    use_sync_file = True
    try:
      json_data = json.load(open(sync_file))
    except Exception as e:
      print(f'Error importing {sync_file}: {e}')
      sys.exit()

  with open(config_path, 'r') as j:
    config = json.load(j)

  import_cues = config['import_cues']
  import_lyrics = config['import_lyrics']
  remove_lrc_wd = config['remove_lrc_wd']
  podcast = config['podcast']

  reset_log()

  # calculate filesize of music lib on a second thread
  fs_queue = queue.Queue()
  thread = threading.Thread(target=get_lib_size, args=(fs_queue,))
  thread.start()

  # begin transfer timer
  notify({
    "text": 'Beginning Sync.. This can take a while.',
    "summary" : False,
    "toast" : True
  }, window)
  start_time = time.time()

  # create destination
  notify({
    "text": 'Creating folders.',
    "summary" : False,
    "toast" : False
  }, window)
  if not os.path.exists(sorted_dir):
    os.makedirs(sorted_dir)
    changes['new_folders'] += 1

  #rename images to cover.jpg
  notify({
    "text": 'Checking image names and sizes.',
    "summary" : False,
    "toast" : False
  }, window)
  file_manager.rename_images(working_dir)

  # remove all cue file in destination location 
  if import_cues:
    notify({
      "text": f'Removing .cue files from {sorted_dir}',
      "summary" : False,
      "toast" : False
    }, window)
    file_manager.remove_cue_files(sorted_dir)

  # attempt to find lyrics for each song
  if import_lyrics:
    notify({
      "text": f'Removing .lrc files from {sorted_dir}',
      "summary" : False,
      "toast" : False
    }, window)
    file_manager.remove_lrc(sorted_dir)
    if remove_lrc_wd:
      notify({
        "text": f'Removing .lrc files from {working_dir}',
        "summary" : False,
        "toast" : False
      }, window)
      file_manager.remove_lrc(working_dir)

  # copy files
  notify({
    "text": 'Starting audio file transfers.',
    "summary" : False,
    "toast" : False
  }, window)
  process_audio_files(window)

  # sort tracks by disc then track number
  for artist in lib_data:
    lib_data[artist].sort(key=lambda x: x["title"])
    for album in lib_data[artist]:
      album['tracks'].sort(key=lambda x: (x['disc'], x['track']))

  # write data file of all artists and albums
  sorted_data = dict(sorted(lib_data.items()))
  sorted_data['lib_size'] = fs_queue.get()

  lib_path = os.path.join(script_folder, 'lib_data.json')

  with open(lib_path, 'w') as data_file:
    data_file.write(json.dumps(sorted_data, indent=2))

  # copy / delete podcasts and add those changes to the total changes
  if podcast:
    stats = updatePodcast(sorted_dir, window, bypass=True, logger=log)
    changes['new_folders'] += stats['new_podcasts']
    changes['files_writen'] += stats['files_writen']
    changes['files_deleted'] += stats['files_deleted']
    changes['folders_deleted'] += stats['folders_deleted']
    changes['folders_contained'] += stats['folders_contained']
  
  # create .cue / .m3u8 file for each album that doesn't already have one
  if import_cues:
    pl_manager.create_cue_files(sorted_dir, window)
  
    # create folder for new_files playlist  
    if not os.path.exists(playlist_folder):
      os.makedirs(playlist_folder)
      changes['new_folders'] += 1

    # create playlist containing all new files
    pl_manager.new_files_playlist(sorted_dir)

  # output file containing trouble files
  notify({
    "text": 'Generating trouble file.',
    "summary" : False,
    "toast" : False
  }, window)
  files_with_issues()

  # sync summary
  change_log = print_change_log(changes, time.time() - start_time)
  notify({
    "text": change_log,
    "summary" : True,
    "toast" : False
  }, window)
  log(change_log)

def build_lib(root, file, ext):
  global lib_data
  source_file = os.path.join(root, file)
  jpg = os.path.join(root, 'cover.jpg')
  if ext == '.flac':
    info = pl_manager.get_flac_info(source_file, file)
  else:
    info = pl_manager.get_mp3_info(source_file, file, jpg)
  if not info:
    return
  if not os.path.exists(jpg):
    return
  add_to_lib(info['artist'], info['album'], root.replace(config['source'], ''), file, info['title'], info['track'], info['disc'])

def create_lib_json(window):
  global lib_data
  lib_data = {}
  fs_queue = queue.Queue()
  thread = threading.Thread(target=get_lib_size, args=(fs_queue,))
  thread.start()
  audio_files = get_audio_files()
  length = len(audio_files)
  for ndx, file in enumerate(audio_files):
    build_lib(file['root'], file['file'], file['ext'])
    if window:
      window.evaluate_js(f'document.querySelector("music-library").updateBar({ndx}, {length});')   
  
  # sort tracks by disc then track number
  for artist in lib_data:
    lib_data[artist].sort(key=lambda x: x["title"])
    for album in lib_data[artist]:
      album['tracks'].sort(key=lambda x: (x['disc'], x['track']))
  
  sorted_data = dict(sorted(lib_data.items()))
  sorted_data['lib_size'] = fs_queue.get()

  lib_path = os.path.join(script_folder, 'lib_data.json')

  with open(lib_path, 'w') as data_file:
    data_file.write(json.dumps(sorted_data, indent=2))

if __name__ == "__main__":
  run_sync(False)
