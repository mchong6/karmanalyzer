import praw
import matplotlib.pyplot as plt
import matplotlib.image as img
import numpy as np
import scipy as sp
import scipy.stats as st
import pickle as pkl
import csv as csv
import networkx as nx
from Queue import PriorityQueue
print "Modules Imported!"

r = praw.Reddit('sssa')
submission = r.get_submission(submission_id='5dspd1')
submission.replace_more_comments(limit=10, threshold=0)
all_comments = submission.comments
flat_comments = praw.helpers.flatten_tree(all_comments)

# commentsSize = len(r.get_submission(submission_id='1kxd1n').comments)
# for i in range(commentsSize):
#     replies = r.get_submission(submission_id='1kxd1n').comments[i]
#     print replies

output = open('output.txt', 'w+')

for i in flat_comments:
    output.write(i.body.encode('utf-8'))

print 'Write to output.txt done.\n'

class Markov_text:
    def __init__(self, open_file):   # The single parameter passed is a file handle
        self.cache = {}  # Will be dictionary mapping a key (two consecutive words) to possible next word
        self.open_file = open_file
        self.words = self.file_to_words()  # Read the words from the file into array self.words
        self.word_size = len(self.words)
        self.database()   # Fill in the dictionary
       
       
    def file_to_words(self):
        self.open_file.seek(0)
        data = self.open_file.read()
        words = data.split()
        return words
           
       
    def triples(self):
    #Generates triples from the given data string. So if our string were
    # "What a lovely day", we'd generate (What, a, lovely) and then (a, lovely, day)."""
           
        if len(self.words) < 4:
            return
         
        for i in range(len(self.words) - 3):
            yield (self.words[i], self.words[i+1], self.words[i+2], self.words[i+3])    #Like return but returns a generator to be used once
               
    def database(self):
        for w1, w2, w3, w4 in self.triples():
            key = (w1, w2, w3)
            if key in self.cache:
                self.cache[key].append(w4)
            else:
                self.cache[key] = [w4]
                         
    def generate_markov_text(self, size=100):
        seed = np.random.randint(0, self.word_size-4)
        w1, w2, w3 = self.words[seed], self.words[seed+1], self.words[seed+2]  # Initial key is (w1,w2)
        gen_words = [w1,w2,w3]
        for i in xrange(size):
            w1, w2, w3 = w2, w3, np.random.choice(self.cache[(w1, w2, w3)])
            gen_words.append(w3)
        return ' '.join(gen_words)
                
        
        
file_ = open('output.txt')
markov = Markov_text(file_)   # Creates the object markov using the file
print markov.generate_markov_text(300)   # Generate random text