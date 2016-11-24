# karmanalyzer

This project scraps popular subreddits for images and their respective karmas/post times and aims to predict the karma of an image given where and what time it was posted.

Also as it scrapes the subreddits, it uses VGG19 to classify all the images, giving a respresentations of what images are most popular in each subreddit.

reddit_scrapy.py: scrapes the top 25 subreddits and save the images/karma to your directory

classify.lua: Prints out the most popular classes of the images in each subreddit. Here we found out that the top subreddits are mostly filled with "websites, internet" and "book covers" which suggests that memes make up a huge portion of these popular subreddits A notable exception is /r/aww, which consists mostly of "tabby cat" and "golden retriever"

provider.lua: Compress and create labels for the images scraped.

CNN.lua: Uses all the data and trained a CNN to estimate karma based on an image, the subreddit it was posted to, and the time of posting.

markov.lua: Given a reddit thread, create a TL;DR using Markov Chain (think Subreddit Simulator) and use sentiment analysis to determine the sentiment of the thread.
