import requests
from bs4 import BeautifulSoup
from atproto import Client
import time
import random  
from flask import Flask
import threading

app = Flask(__name__)

@app.route('/')
def home():
    return "Bot is running!"

def run_server():
    try:
        app.run(host='0.0.0.0', port=8000)
    except OSError as e:
        print(f"Could not start server: {e}")
        exit(1)

# start web server in a separate thread

server_thread = threading.Thread(target=run_server)
server_thread.start()

# settings
X_ACCOUNT = "cinemafundaj"  # change to the x.com username you want to track
NITTER_INSTANCES = [
    f"https://nitter.net/{X_ACCOUNT}/with_replies",
    f"https://nitter.cz/{X_ACCOUNT}/with_replies",
    f"https://nitter.unixfox.eu/{X_ACCOUNT}/with_replies",
    f"https://xcancel.com/{X_ACCOUNT}/with_replies",
    f"https://nitter.space/{X_ACCOUNT}/with_replies",
    f"https://lightbrd.com/{X_ACCOUNT}/with_replies",
    f"https://nitter.privacydev.net/{X_ACCOUNT}/with_replies",
    f"https://nitter.lunar.icu/{X_ACCOUNT}/with_replies",
    f"https://nitter.moomoo.me/{X_ACCOUNT}/with_replies",
]
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
}
BSKY_HANDLE = "botcinemafundaj.bsky.social"  # your full bluesky handle
BSKY_APP_PASSWORD = "rhhu-xrcm-zegf-ry3i"  # app password you generated

# function to get latest tweet
def get_latest_tweet():
    shuffled_instances = NITTER_INSTANCES[:]
    random.shuffle(shuffled_instances)

    for instance_url_base in shuffled_instances:
        try:
            print(f"Trying Nitter instance: {instance_url_base}")
            response = requests.get(instance_url_base, headers=HEADERS, timeout=10)
            response.raise_for_status()

            soup = BeautifulSoup(response.text, 'html.parser')
            tweets = soup.find_all('div', class_='tweet-content media-body')

            if tweets:
                tweet = tweets[0]
                tweet_text = tweet.text.strip()
                print(f"Raw tweet content: {tweet_text}")

                image_element = tweet.find('a', class_='tweet-media-link')
                image_url = None

                if image_element:
                    image_url = image_element['href']
                elif tweet.find('img', class_='tweet-media-image'):
                    image_url = tweet.find('img', class_='tweet-media-image')['src']

                if image_url and not image_url.startswith("http"):
                    domain = instance_url_base.split("/")[2]
                    image_url = f"https://{domain}{image_url}"

                return tweet_text, image_url  # Return both text and image URL

            print("No tweets found on this instance.")

        except requests.exceptions.RequestException as e:
            print(f"Error connecting to {instance_url_base}: {e}")
        except Exception as e:
            print(f"An unexpected error occurred: {e}")

    print("All Nitter instances failed")
    return None
# function to verify bluesky credentials
def verify_bluesky_credentials():
    global bsky_client  # Access the global client
    try:
        bsky_client = Client()  # Initialize the client
        bsky_client.login(BSKY_HANDLE, BSKY_APP_PASSWORD)
        print("Bluesky credentials verified successfully!")
        return True
    except Exception as e:
        print("Error verifying Bluesky credentials:", str(e))
        return False
# function to post to bluesky
def post_to_bluesky(text, image_url=None):  # Add image_url parameter
    global bsky_client
    if bsky_client:
        try:
            if image_url:
                try:
                    image_response = requests.get(image_url, stream=True)
                    image_response.raise_for_status()
                    bsky_client.send_post(text, images=[{"image": image_response.raw, "alt": "Tweet Image"}])
                    print("Posted to Bluesky with image:", text, image_url)
                except requests.exceptions.RequestException as e:
                    print(f"Error downloading image: {e}")
                    bsky_client.send_post(text)  # Post without image
                    print("Posted to Bluesky WITHOUT image (download failed):", text)
                except Exception as e:
                    print(f"Error posting to Bluesky with image: {e}")
                    bsky_client.send_post(text)  # Post without image
                    print("Posted to Bluesky WITHOUT image (post with image failed):", text)
            else:
                bsky_client.send_post(text)
                print("Posted to Bluesky:", text)

        except Exception as e:
            print(f"Error posting to Bluesky: {e}")
    else:
        print("Bluesky client not initialized.")
# verify credentials before starting the main loop
if not verify_bluesky_credentials():
    print("Invalid Bluesky credentials. Please check BSKY_HANDLE and BSKY_APP_PASSWORD")
    exit(1)

# main loop
last_tweet = ""
last_image_url = ""
while True:
    tweet_data = get_latest_tweet()
    if tweet_data:
        tweet, image_url = tweet_data

        if tweet and tweet != last_tweet or image_url != last_image_url:
            post_to_bluesky(tweet, image_url)  # Pass image URL
            print("Latest tweet fetched:", tweet, image_url)
            last_tweet = tweet
            last_image_url = image_url
    time.sleep(15)    


