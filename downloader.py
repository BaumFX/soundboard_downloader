import requests
import hashlib
import bs4
import queue
from threading import Thread
import multiprocessing

def check_if_none(elem, name):
    if elem != None:
        return
    
    print(f'[-] failed to locate {name}, exiting')
    exit(-1)

def find_sounds(username):
    res = requests.get(f'https://www.soundboard.com/sb/{username}')

    if res.status_code != 200:
        print('[-] failed to fetch home page, quitting')
        exit(-1)

    soup = bs4.BeautifulSoup(res.text, 'html.parser')

    playlist = soup.find('ul', { 'id': 'playlist' })
    check_if_none(playlist, 'playlist')

    sounds = playlist.findChildren('div' , recursive=False)
    check_if_none(sounds, 'sounds')

    res = []

    for i in sounds:
        #TODO: properly remove elements that are not sounds
        if '<ins class' in str(i) or 'adsbygoogle' in str(i):
            continue

        sound_id = i.attrs.get('data-track-id', None)
        check_if_none(sound_id, 'sound id')
        
        sound_idx = i.attrs.get('index', None)
        check_if_none(sound_idx, 'sound index')

        sound_title = i.find('a', { 'id': f'track_{sound_idx}' })
        check_if_none(sound_title, 'sound title')

        sound_title = sound_title.attrs.get('title', None)
        check_if_none(sound_title, 'sound title')

        res.append({
            'index': sound_idx,
            'id': sound_id,
            'title': sound_title
        })

    return res

def get_download_link(sound_id):
    res = requests.get(f'https://www.soundboard.com/sb/sound/{sound_id}')

    if res.status_code != 200:
        print('[-] failed to fetch sound download page, quitting')
        exit(-1)

    soup = bs4.BeautifulSoup(res.text, 'html.parser')

    btn = soup.find('button', { 'id': 'btnDownload' })
    check_if_none(btn, 'download button')

    download_link = btn.attrs.get('onclick', None)
    check_if_none(download_link, 'download link')

    return download_link[download_link.find('\'') + 1:-2]

def download_sound(url, path, filename):
    res = requests.get(url)
    if res.status_code != 200:
        print('[-] failed to download sound, quitting')
        exit(-1)

    with open(path + '\\' + filename, 'wb') as f:
        f.write(res.content)

targets = queue.Queue()

def handle_sound(sound):
    print(f'[+] downloading sound \'{sound["title"]}\' with id {sound["id"]}')
    link = get_download_link(sound['id'])
    check_if_none(link, 'download link')

    filename = hashlib.sha256(str(sound["title"] + sound["id"]).encode()).hexdigest()

    download_sound(link, path, filename + '.mp3')

def worker():
    while True:
        i = targets.get()
        if i is None:
            break
        handle_sound(i)
        targets.task_done()

#TODO: prompt user for thread count here?
thread_count = multiprocessing.cpu_count() * 4

threads = []
for i in range(thread_count):
    t = Thread(target=worker)
    t.start()
    threads.append(t)

print(f'[+] successfully started {thread_count} worker threads')

username = input('[+] please enter the soundboard url [example: \'http://www.soundboard.com/sb/username\']: ') #solrosin

#TODO: prompt user to input a folder here, currently just downloads to [cwd]/sounds
path = 'sounds'

sounds = find_sounds(username)
print(f'[+] fetched {len(sounds)} sounds')

for i in sounds:
    targets.put(i)

targets.join()

for i in range(thread_count):
    targets.put(None)
for t in threads:
    t.join()

print('[+] successfully downloaded all songs')
