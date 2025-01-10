from plexapi.server import PlexServer
import feedparser
import requests

import argparse
import logging
import time
import os
import re

def sanitize_filename(title):
    return re.sub(r'[<>:"/\\|?*]', '_', title)

def sportscult_rss():
    d = feedparser.parse(rss_feed)
    items = d.entries

    history_file = os.path.join(directory, "history.txt")

    with open(history_file, "r") as file:
        history = [line.strip() for line in file]

    for item in items:
        if ("toronto" in item.title.lower() and "rs" in item.title.lower()):
            torrent_title = sanitize_filename(item.title).split(" [SEEDERS")[0]

            if torrent_title not in history:
                with open(history_file, "a") as file:
                    file.write(torrent_title + "\n")

                torrent_link = item.link
                filename = os.path.join(directory, f"{torrent_title}.torrent")

                try:
                    logging.info(f"Downloading: {torrent_title}")
                    response = requests.get(torrent_link)
                    response.raise_for_status()

                    with open(filename, "wb") as file:
                        file.write(response.content)

                    logging.info(f"Saved: {filename} to qBittorent monitored folder.")
                except Exception as e:
                    logging.error(f"Failed to download {torrent_title}: {e}")
            else:
                 logging.info(f"Torrent: {torrent_title} already grabbed. Skipping...")

def plex_rename():
    plex = PlexServer(plex_url, plex_token)

    #TODO: pass this in as an arg
    show_name = "NHL: Recorded Games" 
    season_name = "Season 2025" 

    show = plex.library.section('TV Shows').get(show_name)
    season = next((s for s in show.seasons() if s.title == season_name), None)
    episodes = season.episodes()
    for episode in episodes:
        episode_title = episode.title
        episode_filename = str(episode.media[0].parts[0].file)
        
        if "Episode" in episode_title:
            new_title = (
                episode_filename
                .split("/NHL ")[1]
                .split(" 720p60")[0]
                .split(" 1080p60")[0]
                .replace(" RS ", " ")
            )
            logging.info(f"Renaming Plex episode title: {episode_title} to: {new_title}")
            episode.edit(**{'title.value': new_title, 'title.locked': 1})

sleep_time = 300

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

parser = argparse.ArgumentParser(description="A script to process a Sportscult RSS feed and save torrent files to a directory.")

parser.add_argument('-r', '--rss-feed', required=True, help='URL of the RSS feed')
parser.add_argument('-d', '--directory', required=True, help='Path to the directory where files will be saved')
parser.add_argument('-u', '--plex-url', required=True, help='Plex URL')
parser.add_argument('-t', '--plex-token', required=True, help='Plex token')

args = parser.parse_args()

rss_feed = args.rss_feed
directory = args.directory
plex_url = args.plex_url
plex_token = args.plex_token

sportscult_rss()
logging.info(f"Waiting {sleep_time} seconds before running plex rename function.")

time.sleep(sleep_time)
plex_rename() 