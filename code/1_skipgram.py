#!/usr/bin/env python3
#--coding:utf-8--

"""
2018-07-12: not work now
"""

#sys
import os
from collections import Counter

#3rd
import numpy as np
import tensorflow as tf

#global settings
os.environ["CUDA_DEVICE_ORDER"] = "PCI_BUS_ID"
os.environ["CUDA_VISIBLE_DEVICES"] = ""
os.environ['TF_CPP_MIN_LOG_LEVEL']='3'


class skipGram:
    """
    Simple word2vector using tokens directly,tokens may contain stop words.
    """
    minFreq = 1
    windows = 5
    dim = 200
    nsampled = 100
    batchSize = 1000
    epochs = 10
    dropProb = 1e-5
    dropCutoff = 0.95
    poorWords = None
    richWords = None
    vocabSize = None

    def __init__(self, tokens):
        self.tokens = tokens
        self.preprocessTokens()
        self.getXy()
        self.train()
    
    def preprocessTokens(self,):
        wordFreq = Counter(self.tokens)
        #total original words count
        tt = sum(wordFreq.values())
        #filtering words
        #1. too fewer
        wordFreq2 = {w:c for w,c in wordFreq.items() if c > self.minFreq}
        self.poorWords = set(wordFreq.keys()).difference(wordFreq2.keys())
        wordFreq = wordFreq2
        #2. too many such as stop words
        wordFreq2 = {w: 1 - np.sqrt(self.dropProb/c*tt) for w,c in wordFreq.items()}
        wordFreq2 = {w: c for w,c in wordFreq2.items() if c < self.dropCutoff}
        self.richWords = set(wordFreq.keys()).difference(wordFreq2.keys())
        wordFreq = wordFreq2
        #word2idx and idx2word
        self.word2idx = {w:i for i,w in enumerate(wordFreq.keys())}
        self.idx2word = {i:w for i,w in enumerate(wordFreq.keys())}
        #converting all words to number vectors
        self.indexedWords = [self.word2idx[w] for w in self.tokens if w in wordFreq]
        self.vocabSize = len(self.idx2word)
        print(self.vocabSize)
    
    def getXy(self,):
        x,y = [],[]
        for i in range(len(self.indexedWords)):
            input_w = self.indexedWords[i]
            left = max(0,i-self.windows)
            right = min(i+self.windows+1,len(self.indexedWords))
            labels = list(set(self.indexedWords[left:i]+self.indexedWords[i+1:right]))
            x.extend([input_w]*len(labels))
            y.extend(labels)
        self.x = np.array(x)
        self.y = np.expand_dims(y,-1)

    def train(self,):
        xs = tf.placeholder(tf.int32,[self.batchSize])
        ys = tf.placeholder(tf.int32,[self.batchSize,1])
        weight = tf.Variable(tf.random_normal([self.vocabSize,self.dim]))
        bias = tf.Variable(tf.random_normal([self.vocabSize]))
        E = tf.Variable(tf.random_normal([self.vocabSize,self.dim]))
        embed = tf.nn.embedding_lookup(E,xs)
        loss = tf.reduce_mean(
            tf.nn.sampled_softmax_loss(
                weights = weight,
                biases = bias,
                labels = ys,
                inputs = embed,
                num_sampled =self.nsampled,
                num_classes = self.vocabSize,
                )
        )
        train = tf.train.AdamOptimizer().minimize(loss)
        model = tf.estimator.EstimatorSpec(mode=tf.estimator.ModeKeys.TRAIN,loss=loss,train_op=train)
        estimator = tf.estimator.Estimator(model)
        estimator.train(
            tf.estimator.inputs.numpy_input_fn(
                self.x,
                self.y,
                batch_size = self.batchSize,
                num_epoches = self.epochs,
                shuffle = True
            )
        )


def test():
    ss = open("../data/test_tokens.txt").read().split("\n")
    ns = []
    for s in ss:
        ns.extend(s.split(","))
    skipGram(ns[:10000])


if __name__ == "__main__":
    test()