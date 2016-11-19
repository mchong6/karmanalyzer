import re, praw, requests, os, glob, sys
from bs4 import BeautifulSoup
import datetime
from itertools import chain
import karma as k
import urllib


MIN_SCORE = 100 # the default minimum score before it is downloaded
image_limit = 1000


imgurUrlPattern = re.compile(r'(http://i.imgur.com/(.*))(\?.*)?')
#make parent directory
parent_dir = "data"
if not os.path.exists(parent_dir):
    os.makedirs(parent_dir)


def downloadImage(targetSubreddit, imageUrl, localFileName, count, label, submission):
    #ignore non png and jpg
    if not (imageUrl.endswith(".jpg") or imageUrl.endswith(".png")):
        return count
    response = requests.get(imageUrl)
    if response.status_code == 200:
        print('Downloading %s...' % (localFileName))
        with open(parent_dir+'/'+targetSubreddit+'/'+localFileName, 'wb') as fo:
            for chunk in response.iter_content(4096):
                fo.write(chunk)
            #write to label
            label.write(str(submission.score)+ ' '+str(get_time(submission)) + '\n')
            return count+1
    return count

def get_time(submission):
    time = submission.created_utc
    #time is in UNIX convert to hours
    return datetime.datetime.fromtimestamp(time).strftime('%H')


# Connect to reddit and download the subreddit front page
r = praw.Reddit(user_agent='test app mine') # Note: Be sure to change the user-agent to something unique.



def crawl_sub(targetSubreddit):
    print "Accessing", targetSubreddit
    #create folder if doesnt exist
    if not os.path.exists(parent_dir+'/'+targetSubreddit):
        os.makedirs(parent_dir+'/'+targetSubreddit)

    #get top submissions
    submissions = r.get_subreddit(targetSubreddit).get_top_from_week(limit=image_limit)
    #get new submissions
    submissions = chain(submissions, r.get_subreddit(targetSubreddit).get_controversial_from_week(limit=image_limit))
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
    label = open(parent_dir+'/'+targetSubreddit+'/'+targetSubreddit+'.txt', 'w')
    for submission in submissions:
        # Check for all the cases where we will skip a submission:
        if "imgur.com/" not in submission.url:
            #non imgur but is an image
            if submission.url.endswith(".jpg") or submission.url.endswith(".png"):
                #f = urllib.urlopen(submission.url)
                #name of image
                localFileName = str(submission.subreddit) + str(count)
                count  = downloadImage(targetSubreddit, submission.url, localFileName, count, label, submission)

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
                print imageUrl
                if '?' in imageUrl:
                    imageFile = imageUrl[imageUrl.rfind('/') + 1:imageUrl.rfind('?')]
                else:
                    imageFile = imageUrl[imageUrl.rfind('/') + 1:]
                #name of image
                localFileName = str(submission.subreddit) + str(count)
                count  = downloadImage(targetSubreddit, 'http:' + match['href'], localFileName, count, label, submission)

        elif 'http://i.imgur.com/' in submission.url:
            # The URL is a direct link to the image.
            mo = imgurUrlPattern.search(submission.url) # using regex here instead of BeautifulSoup because we are pasing a url, not html

            imgurFilename = mo.group(2)
            if '?' in imgurFilename:
                # The regex doesn't catch a "?" at the end of the filename, so we remove it here.
                imgurFilename = imgurFilename[:imgurFilename.find('?')]

            #name of image
            localFileName = str(submission.subreddit) + str(count)
            count = downloadImage(targetSubreddit, submission.url, localFileName, count, label, submission)

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
            count = downloadImage(targetSubreddit, imageUrl, localFileName, count, label, submission)

subreddits = k.get_subreddits(25)
for sub in subreddits:
    crawl_sub(sub)
