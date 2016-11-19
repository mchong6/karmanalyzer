import re, praw, requests, os, glob, sys
from bs4 import BeautifulSoup
import datetime

MIN_SCORE = 100 # the default minimum score before it is downloaded


imgurUrlPattern = re.compile(r'(http://i.imgur.com/(.*))(\?.*)?')
targetSubreddit = 'all'
if not os.path.exists(targetSubreddit):
    os.makedirs(targetSubreddit)


def downloadImage(imageUrl, localFileName):
    #ignore gifs
    if ".gif" in imageUrl:
        return
    response = requests.get(imageUrl)
    if response.status_code == 200:
        global count
        count += 1
        print('Downloading %s...' % (localFileName))
        with open(targetSubreddit+'/'+localFileName, 'wb') as fo:
            for chunk in response.iter_content(4096):
                fo.write(chunk)
def get_time(submission):
    time = submission.created_utc
    #time is in UNIX
    return time

# Connect to reddit and download the subreddit front page
r = praw.Reddit(user_agent='test app mine') # Note: Be sure to change the user-agent to something unique.
submissions = r.get_subreddit(targetSubreddit).get_top_from_all(limit=100)
# Or use one of these functions:
#                                       .get_top_from_year(limit=25)
#                                       .get_top_from_month(limit=25)
#                                       .get_top_from_week(limit=25)
#                                       .get_top_from_day(limit=25)
#                                       .get_top_from_hour(limit=25)
#                                       .get_top_from_all(limit=25)

# Process all the submissions from the front page
#print vars(next(submissions))
stats = []
count = 1
for submission in submissions:
    # Check for all the cases where we will skip a submission:
    if "imgur.com/" not in submission.url:
        continue # skip non-imgur submissions
    if submission.score < MIN_SCORE:
        continue # skip submissions that haven't even reached 100 (thought this should be rare if we're collecting the "hot" submission)
    if len(glob.glob('reddit_%s_%s_*' % (targetSubreddit, submission.id))) > 0:
        continue # we've already downloaded files for this reddit submission


    if 'http://imgur.com/a/' in submission.url:
        # This is an album submission.
        albumId = submission.url[len('http://imgur.com/a/'):]
        htmlSource = requests.get(submission.url).text

        soup = BeautifulSoup(htmlSource, "html.parser")
        matches = soup.select('.album-view-image-link a')
        for match in matches:
            imageUrl = match['href']
            if '?' in imageUrl:
                imageFile = imageUrl[imageUrl.rfind('/') + 1:imageUrl.rfind('?')]
            else:
                imageFile = imageUrl[imageUrl.rfind('/') + 1:]
            #name of image
            localFileName = str(submission.subreddit) + str(count)
            downloadImage('http:' + match['href'], localFileName)

    elif 'http://i.imgur.com/' in submission.url:
        # The URL is a direct link to the image.
        mo = imgurUrlPattern.search(submission.url) # using regex here instead of BeautifulSoup because we are pasing a url, not html

        imgurFilename = mo.group(2)
        if '?' in imgurFilename:
            # The regex doesn't catch a "?" at the end of the filename, so we remove it here.
            imgurFilename = imgurFilename[:imgurFilename.find('?')]

        #name of image
        localFileName = str(submission.subreddit) + str(count)
        downloadImage(submission.url, localFileName)

    elif 'http://imgur.com/' in submission.url:
        # This is an Imgur page with a single image.
        htmlSource = requests.get(submission.url).text # download the image's page
        soup = BeautifulSoup(htmlSource, "html.parser")
        if len(soup.select('.image a')) == 0:
            continue
        imageUrl = soup.select('.image a')[0]['href']
        if imageUrl.startswith('//'):
            # if no schema is supplied in the url, prepend 'http:' to it
            imageUrl = 'http:' + imageUrl
        imageId = imageUrl[imageUrl.rfind('/') + 1:imageUrl.rfind('.')]

        if '?' in imageUrl:
            imageFile = imageUrl[imageUrl.rfind('/') + 1:imageUrl.rfind('?')]
        else:
            imageFile = imageUrl[imageUrl.rfind('/') + 1:]

        #name of image
        localFileName = str(submission.subreddit) + str(count)
        downloadImage(imageUrl, localFileName)
    else:
        continue
    stats.append([str(submission.subreddit), submission.score, submission.over_18, get_time(submission)])
