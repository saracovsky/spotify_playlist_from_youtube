import json
import requests
import os

from secrets import spotify_user_id, spotify_token
import google_auth_oauthlib.flow
import googleapiclient.discovery
import googleapiclient.errors
import youtube_dl


class CreatePlaylist:

    def __init__(self):
        self.user_id = spotify_user_id
        self.spotify_token = spotify_token
        self.youtube_client = self.get_youtube_client()
        self.all_song_info = {}


    #Log Into Youtube
    def get_youtube_client(self):
        # Disable OAuthlib's HTTPS verification when running locally.
        # *DO NOT* leave this option enabled in production.
        os.environ["OAUTHLIB_INSECURE_TRANSPORT"] = "1"

        api_service_name = "youtube"
        api_version = "v3"
        client_secrets_file = "YOUR_CLIENT_SECRET_FILE.json"

        scopes = ["https://www.googleapis.com/auth/youtube.readonly"]

        flow = google_auth_oauthlib.flow.InstalledAppFlow.from_client_secrets_file(
            client_secrets_file, scopes)
        credentials = flow.run_console()
        youtube_client = googleapiclient.discovery.build(
            api_service_name, api_version, credentials=credentials)

        return youtube_client

    #Obtain liked videos
    def get_liked_videos(self):
        request = self.get_youtube_client().list(
            part="snippet,contentDetails,statistics",
            myRating="like"
        )
        response = request.execute()

        #collect each vid and get important info

        for item in response["items"]:
            video_title = item["snippet"]["title"]
            youtube_url = "https://www.youtube.com/watch?v={}".format(item["id"])

            #use youtube_dl to collect the song name and artist name
            video = youtube_dl.YoutubeDL.extract_info(youtube_url,download=False)
            song_name = video["track"]
            artist = video["artist"]

            #save important info
            self.all_song_info[video_title] = {
                "youtube_url":youtube_url,
                "song_name":song_name,
                "artist":artist,

                #add the uri, easy to get song to pu into playlist
                "spotify_uri":self.get_spotify_uri(song_name,artist)

            }
    #Create playlist on spotify
    def create_playlist(self):

        request_body = json.dumps({
            "name" : "Playlist from Youtube",
            "description":"All my liked songs on Youtube!",
            "public":False
        })

        query = "https://api.spotify.com/v1/users/{}/playlists".format(self.user_id)
        response = request.post(
            query,
            data = request_body,
            headers = {
                "Content-Type":"application/json",
                "Authorization":"Bearer{}".format(spotify_token)
            }
        )
        response_json = response.json()
        #playlist id
        return response_json["id"]


    #Search for a song
    def get_spotify_uri(self,song_name,artist):

        query = "https://api.spotify.com/v1/search?q={}&type=track%2C{}&market=US&limit=10&offset=5".format(
            song_name,
            artist
        )

        response = requests.get(
            query,
            headers = {
                "Content-Type": "application/json",
                "Authorization": "Bearer{}".format(spotify_token)
            }
        )

        response_json = response.json()
        songs = response_json["tracks"]["items"]

        #only use the first song
        uri = song[0]["uri"]

        return uri


    #Add this song into the playlist
    def add_song_to_playlist(self):
        self.get_liked_videos()

        #collect uri
        uri = []
        for song,info in self.all_song_info.items():
            uri.append(info["spotify_uri"])

        #create new playlist
        playlist_id = self.create_playlist()

        #add all songs into playlist
        request_data = json.dumps(uris)

        query =  "https://api.spotify.com/v1/playlists/{}/tracks".format(playlist_id)

        response = requests.post(
            query,
            data = request_data,
            headers={
                "Content-Type": "application/json",
                "Authorization": "Bearer{}".format(spotify_token)
            }
        )

        response_json = response.json()
        return response_json