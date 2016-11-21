import praw
import string
import nltk.probability as prob
from nltk.corpus import stopwords

"""
NOTE: You need to manually download the nltk 'stopwords' module.
To do so, run Python and type the following:
>>> import nltk
>>> nltk.download('stopwords')
"""

# getTags()
# Input: a praw submission object from reddit
# Output: a dict - key is a word (a word from all the comments)
#                - value is the frequency of that word
# Words have been stripped of punctuation and converted to lowercase

def getTags(submission):
    submission.replace_more_comments(limit=None, threshold=0)

    all_comments = submission.comments
    flat_comments = praw.helpers.flatten_tree(all_comments)

    # Build histogram
    commentsList = []
    for i in flat_comments:
        #print i
        outputStr = i.body.encode('utf-8')
        splitStr = outputStr.lower().split()

        s = set(stopwords.words('english'))

        splitStr = filter(lambda w: not w in s, outputStr.split())
        #print splitStr
        for s in splitStr:
            k = s.translate(None, string.punctuation)
            commentsList.append(k.lower())
            
    fdist = prob.FreqDist(commentsList)
    print 'Generated the following output:'
    print fdist, '\n'

    #if you want to see a histogram, just for fun
    #fdist.plot()
    wordList = dict()

    for sample in fdist:
        wordList[sample] = fdist.freq(sample)

    return wordList
