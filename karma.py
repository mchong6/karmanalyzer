import requests
import requests.auth
client_auth = requests.auth.HTTPBasicAuth('EUmae3KLK1aJuQ', 'anhKNWTVLRr_2yLpmHpOQxHJzhw')
post_data = {"grant_type": "password", "username": "HorriblyGood", "password": "hackathon"}
headers = {"User-Agent": "ChangeMeClient/0.1 by YourUsername"}
response = requests.post("https://www.reddit.com/api/v1/access_token", auth=client_auth, data=post_data, headers=headers)
token = response.json()["access_token"]
print token
headers = {"Authorization": "bearer "+token, "User-Agent": "ChangeMeClient/0.1 by YourUsername"}
response = requests.get("https://oauth.reddit.com/subreddits/popular/?limit=1", headers=headers)
print response.json()
