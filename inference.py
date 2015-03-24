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
#sys.path.insert(0, '/Users/rikka/liblinear-1.94/python')
#from liblinearutil import *
sys.path.insert(0, '/Users/rikka/libsvm-3.18/python')
from svmutil import *
import setmaker
from sympy.solvers.solvers import solve

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
            c.num = str(a.__dict__[k])+op+str(b.__dict__[k])
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
    VVERBOSE = False
    if len(sys.argv) > 1:
        if sys.argv[1] == '-v':
            VERBOSE = True
        if sys.argv[1] == '-vv':
            VVERBOSE = True

    '''
    #liblinear
    asmd = load_model("data/3.19.asmd.classifier")
    adds = load_model("data/3.19.as.classifier")
    multd = load_model("data/3.19.md.classifier")
    '''
    #libsvm
    asmd = svm_load_model("data/3.19.asmd.svmclassifier")
    adds = svm_load_model("data/3.19.as.svmclassifier")
    multd = svm_load_model("data/3.19.md.svmclassifier")
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
        #for x in numbs: x[1].details()
        #input(); continue
        allnumbs = {str(v.num):v for k,v in numbs}
        numlist = [(str(v.num),v) for k,v in numbs if floatcheck(v.num) or v.num == 'x']
        if VERBOSE:
            print(allnumbs,numlist,[v.num for k,v in numbs])
        #print(allnumbs)

        #this is a rudimentary X finding method



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
        for i,e in enumerate(numlist):
            #if e[0]=='x':continue
            if i == len(numlist)-1:
                if 'x' in state[-1][0]:
                    state.append((solve(state[-1][0]+"-"+e[1].num,'x'),None))
                else:
                    state.append((solve(state[-1][0]+"-"+e[1].num,'x'),None))
                break
                
            if state == []:
                state.append(e)
                continue
            possibilites = []
            p = state[-1]
            #turn into jawns and run through the classifiers. 
            target = allnumbs['x'].unit if 'x' in allnumbs else "???"
            vec,features = ENTITY.vector(p,e,problem,target,True)
            if VVERBOSE:
                for i in range(len(vec)):
                    print(features[i],vec[i])
                input()
            #p_label, p_acc, p_val = predict([-1], [vec], asmd,'-q')
            if p[1].unit==e[1].unit:
                #HARD CONSTRAINT AGAINST MULTIPLICATION
                p_label = [1]
            else:
                p_label, p_acc, p_val = svm_predict([-1], [vec], asmd,'-q')
            p[1].details();e[1].details()
            if p_label[0] == 1:
                #adds 
                #op_label, op_acc, op_val = predict([-1], [vec], adds,'-q')
                op_label, op_acc, op_val = svm_predict([-1], [vec], adds,'-q')
                if op_label[0] == 1:
                    op = "+"
                else: op = "-"
            else:
                #op_label, op_acc, op_val = predict([-1], [vec], multd,'-q')
                op_label, op_acc, op_val = svm_predict([-1], [vec], multd,'-q')
                if op_label[0] == 1:
                    op = "*"
                else: op = "/"
            print("Operation selected : "+op)
            print("Stats for +- vs */ decision : ",p_label,p_acc,p_val)
            print("Stats for subsequent decision: ",op_label,op_acc,op_val)
            c = combine(p[1],e[1],op)
            try:
                num = str(eval(c.num))
            except: num = c.num
            state.append(e)
            state.append((num,c))
        if len(state)>0:
            g = state[-1][0]
            if type(g)==type([]):
                if g != []:
                    guess = state[-1][0][0]
                else: guess = 0
                
            else: guess = g
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
    
        



