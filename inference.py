# This is a function for parsing a problem into the semantics. 
# TODO
# use lemmas rather than Morph function
# fix nn compound issue (assign head node)
import sys
import json
import jsonrpclib
from nltk.corpus import wordnet as wn
from nltk.corpus import wordnet_ic
import entity as ENTITY
from entity import entity
import pickle
import numpy as np
sys.path.insert(0, '/Users/rikka/liblinear-1.94/python')
from liblinearutil import *
import setmaker

class StanfordNLP:
    def __init__(self, port_number=8080):
        self.server = jsonrpclib.Server("http://localhost:%d" % port_number)

    def parse(self, text):
        return json.loads(self.server.parse(text))

nlp = StanfordNLP()


def training(trips,problem,target):
    #this function take the trips and creates positive and negative training instances from them
    
    texamples = {x:([],[]) for x in ["+","*"]}
    for op,a,b in trips:
        vec = ENTITY.vector(a,b,problem,target)
        for k in texamples:
            if op == k:
                texamples[k][0].append(vec)
            else:
                texamples[k][1].append(vec)

    return texamples



def combine(a,b,op):
    #takes two entities and returns a combo of them.
    c = entity()
    for k in a.__dict__:
        if k == "num":
            c.num = str(a.__dict__[k])+" "+op+" "+str(b.__dict__[k])
        else:
            if k!='each':
                c.__dict__[k]= str(a.__dict__[k])+" "+str(b.__dict__[k])
    #print(c.__dict__)
    return c

def floatcheck(x):
    try:
        float(x)
        return True
    except:
        return False



if __name__ == "__main__":
    VERBOSE = False
    if len(sys.argv) > 1:
        if sys.argv[1] == '-v':
            VERBOSE = True
    asmd = load_model("data/3.19.asmd.classifier")
    adds = load_model("data/3.19.as.classifier")
    multd = load_model("data/3.19.md.classifier")
    wps = open("complex_dev.problems").readlines()
    answs = open("complex_dev.answers").readlines()
    right = 0
    ad = []
    for j in range(len(wps)):
        if VERBOSE:
            for i in range(len(wps)):
                print(i,wps[i])
            j = int(input())
        print(wps[j])
        problem = wps[j].lower()



        story = nlp.parse(problem)
        numbs = setmaker.setmaker(story)
        allnumbs = {str(v.num):v for k,v in numbs}
        numlist = [(str(v.num),v) for k,v in numbs if floatcheck(v.num) or v.num == 'x']
        if VERBOSE:
            print(allnumbs,numlist,[v.num for k,v in numbs])
        #print(allnumbs)



        for num,e in allnumbs.items():
            ent = e.unit
            if ent[-1]=='s':
                ent = ent[:-1]
            if ent[-1]=='e':
                ent=ent[:-1]
            if "each "+ent in problem:
                e.each = True
            elif "each" in problem:
                pass


        state = []
        print(numlist)
        #for e in allnumbs.items():
        for e in numlist:
            if e[0]=='x':continue
            if state == []:
                state.append(e)
                continue
            possibilites = []
            p = state[-1]
            #turn into jawns and run through the classifiers. 
            target = allnumbs['x'].unit if 'x' in allnumbs else "???"
            vec,features = ENTITY.vector(p,e,problem,target,True)
            if VERBOSE:
                for i in range(len(vec)):
                    print(features[i],vec[i])
                input()
            p_label, p_acc, p_val = predict([-1], [vec], asmd,'-q')
            p[1].details();e[1].details()
            if p_label[0] == 1:
                #adds 
                op_label, op_acc, op_val = predict([-1], [vec], adds,'-q')
                if op_label[0] == 1:
                    op = " + "
                else: op = " - "
            else:
                op_label, op_acc, op_val = predict([-1], [vec], multd,'-q')
                if op_label[0] == 1:
                    op = " * "
                else: op = " / "
            print("Operation selected : "+op)
            print("Stats for +- vs */ decision : ",p_label,p_acc,p_val)
            print("Stats for subsequent decision: ",op_label,op_acc,op_val)
            c = combine(p[1],e[1],op)
            try:
                num = eval(c.num)
            except: num = -1
            state.append(e)
            state.append((num,c))
        if len(state)>0:
            guess = state[-1][0]
        else: guess = 0
        answ = answs[j]
        #val = answ.split("|")[1].split("=")[1]
        val = answ
        if float(guess)==float(val):
            print("Correct!")
            right +=1 
        else: print("incorrect")
        ad.append(int(float(guess)==float(val)))
        print(guess, answ)
        if VERBOSE:
            input("Any key to continue...")
    
    print("totals: ",right,len(answs))
    print(ad)
    
        



