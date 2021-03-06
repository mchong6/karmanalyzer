import requests
import requests.auth
import pprint
	
def get_subreddits(number):
    client_auth = requests.auth.HTTPBasicAuth('EUmae3KLK1aJuQ', 'anhKNWTVLRr_2yLpmHpOQxHJzhw')
    post_data = {"grant_type": "password", "username": "HorriblyGood", "password": "hackathon"}
    headers = {"User-Agent": "ChangeMeClient/0.1 by YourUsername"}
    response = requests.post("https://www.reddit.com/api/v1/access_token", auth=client_auth, data=post_data, headers=headers)
    token = response.json()["access_token"]
    headers = {"Authorization": "bearer "+token, "User-Agent": "ChangeMeClient/0.1 by YourUsername"}
    response = requests.get("https://oauth.reddit.com/subreddits/popular", headers=headers)
    #pprint.pprint(response.json()['data']['children'][0]['data']['display_name'])

    subreddits = []
    for i in range(number):
        subreddits.append(response.json()['data']['children'][i]['data']['display_name'])
    return [str(x) for x in subreddits]
