import requests
import bs4
import queue
from threading import Thread
import json
import multiprocessing
import argparse
from pathlib import Path
import os

HEADERS = {'User-Agent':  'Mozilla/5.0 (X11; Linux x86_64; rv:104.0) Gecko/20100101 Firefox/104.0'}

BASE_URL = 'https://www.101soundboards.com'

TARGETS = queue.Queue()


def check_if_none(elem, name):
    if elem != None:
        return

    print(f'[-] failed to locate {name}, exiting')
    exit(1)


def find_sounds(url):
    res = requests.get(url, headers=HEADERS)

    if res.status_code != 200:
        print(f'[-] failed to fetch home page with status code {res.status_code}, quitting')
        exit(1)

    soup = bs4.BeautifulSoup(res.text, 'html.parser')
    scripts = soup.find_all('script')
    check_if_none(scripts, 'scripts')

    target = None

    for s in scripts:
        if 'board_id' not in str(s):
            continue
        target = s
        break

    check_if_none(target, 'info script')

    target = str(target)
    trimmedTarget = str(target[target.find('board_data_inline') + 20:target.find('}]};') + 3])
    #print(trimmedTarget)
    
    sound_list = json.loads(trimmedTarget)
    #TODO: extract properties at this point
    """
        "id": 27782,
        "board_title": "LazarBeam",
        "board_description": "A LazarBeam Fortnite SoundBoard. [...]",
        "board_adsense_allow": 0,
        "board_hide_crosspromotion": 0,
        "board_rightsfree": 0,
        "board_hits": 85762,
        "board_hits_recent": 1341,
        "board_webpush_lastsent": null,
        "board_image_generation_attempts": 0,
        "board_autotagged": 1,
        "board_autotagged_failure": 0,
        "created_at": "2020-01-05T07:30:40.000000Z",
        "updated_at": "2021-02-09T19:43:16.000000Z",

        etc.
    """

    sounds = sound_list['sounds']

    res = []

    for i in sounds:
        #TODO: parse out metadata here as wanted (ignore key 'board', literal copy of the board object above)
        #TODO: we only care about the key 'sound_file_url
        #TODO: investigate keys 'download_url' and 'waveform_url'
        """
            {
            "id": 420172,
            "sound_order": null,
            "sound_transcript": "G'day G'day",
            "board_id": 27782,
            "sound_hits": 90065,
            "created_at": "2020-01-05T07:30:58.000000Z",
            "updated_at": "2021-03-08T18:47:42.000000Z",
            "sound_bitrate": 162724,
            "sound_filesize": 22456,
            "sound_duration": 1104,
            "sound_md5": "4fafa8282726ac94ad1c45245e4f98f4",
            "sound_metadata_ok": 1,
            "sound_loudness_analysis_attempted": 1,
            "sound_loudness_i": -15.58,
            "sound_loudness_tp": -2.27,
            "sound_loudness_lra": 0,
            "sound_loudness_thresh": -25.58,
            "sound_loudness_offset": 0.01,
            "sound_allow_loudness_match": false,
            "sound_tweet_lastsent": "2020-04-28 03:30:08",
            "sound_file_url": "\/storage\/board_sounds_rendered\/420172.mp3?md5=N8CtKj2oNhrUKQsLlLXuFg&expires=1617454189",
            "sound_file_protection": 4,
            "link": "\/sounds\/420172-gday-gday",
            "waveform_url": "\/storage\/sound_waveforms\/420172.png?c=4",
            "download_url": "\/sounds\/420172\/download?md5=u5McV4vj37VRWP9p04FTFg&expires=1648556389",
            "ISO8601_duration": "PT2S",
            "board": {}
            """

        res.append({
            'id': i['id'],
            'title': i['sound_transcript'],
            'url': i['sound_file_url'],
            'dumbass_iphone_prefix_duration': i['sound_file_pitch']
            })

    return res

def download_sound(url, filepath):
    res = requests.get(BASE_URL + url, headers=HEADERS)
    if res.status_code != 200:
        print('[-] failed to download sound, quitting')
        exit(-1)

    with open(filepath, 'wb') as f:
        f.write(res.content)


def handle_sound(sound, output_directory):
    print(f'[+] downloading sound \'{sound["title"]}\' with id {sound["id"]}')
    filepath = output_directory + \
                os.path.sep + \
                sound['title'] + '-' + str(sound['id']) + '.mp3'
    download_sound(sound['url'], filepath + '_' + str(sound['dumbass_iphone_prefix_duration']))
    print('dumbass prefix duration is: ' + str(float(sound['dumbass_iphone_prefix_duration']) / 10))


def worker(output_directory):
    while True:
        i = TARGETS.get()
        if i is None:
            break
        handle_sound(i, output_directory)
        TARGETS.task_done()


def main(args):
    thread_count = multiprocessing.cpu_count() * 4
    threads = []
    for i in range(thread_count):
        t = Thread(target=worker, args=[args.output_directory])
        t.start()
        threads.append(t)

    print(f'[+] successfully started {thread_count} worker threads')

    Path(args.output_directory).mkdir(exist_ok=True)
    sounds = find_sounds(args.URL)
    print(f'[+] fetched {len(sounds)} sounds')

    for i in sounds:
        TARGETS.put(i)

    TARGETS.join()

    for i in range(thread_count):
        TARGETS.put(None)
    for t in threads:
        t.join()

    print('[+] successfully downloaded all songs')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='101soundboards downloader')
    parser.add_argument('-d', '--output-directory', default='sounds')
    parser.add_argument('URL', help='soundboard url (example: "https://www.101soundboards.com/boards/27782-lazarbeam")')
    args = parser.parse_args()
    main(args)
