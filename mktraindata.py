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
import setmaker
import pickle

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
    print(c.__dict__)
    return c

def floatcheck(x):
    try:
        float(x)
        return True
    except:
        return False



if __name__ == "__main__":
    raw_counts = {x:" " for x in ["+","*"]}
    if len(sys.argv)<2:
        print("args");exit()
    if sys.argv[1]=='asmd':
        f2 = open("data/3.19.asmd",'wb')
        wps = open('add.problems').readlines()
        wps.extend([x for x in open('sub.problems').readlines()])
        addlen = len(wps)
        wps.extend([x for x in open('mult.problems').readlines()])
        wps.extend([x for x in open('div.problems').readlines()])
    elif sys.argv[1]=='as':
        f2 = open("data/3.19.as",'wb')
        wps = open('add.problems').readlines()
        addlen = len(wps)
        wps.extend([x for x in open('sub.problems').readlines()])
    elif sys.argv[1]=='md':
        f2 = open("data/3.19.md",'wb')
        wps = open('mult.problems').readlines()
        addlen = len(wps)
        wps.extend([x for x in open('div.problems').readlines()])
    pos = []
    neg = []
    texamples = {x:([],[],[]) for x in ["+","*"]}
    for j in range(len(wps)):
        print(wps[j])
        problem = wps[j]
        problem = problem.lower()
        story = nlp.parse(problem)
        numbs = setmaker.setmaker(story)
        allnumbs = {str(float(v.num)):v for k,v in numbs if floatcheck(v.num)}
        xes = [x[1] for x in numbs if x[1].num == 'x']
        if xes:
            allnumbs['x']=xes[0]
        print(allnumbs)



        for num,e in allnumbs.items():
            ent = e.unit
            if ent[-1]=='s':
                ent = ent[:-1]
            if ent[-1]=='e':
                ent=ent[:-1]
            print(ent)
            if "each "+ent in problem:
                e.each = True
                print("good")
            elif "each" in problem:
                print("missed")



        #print(allnumbs.keys())
        prblmnumbs = [int(x) for x in allnumbs if x.isdigit()]
        prblmnumbs = [float(v.num) for k,v in numbs if floatcheck(v.num)]

        if len(prblmnumbs)<2: continue
        if j < addlen:
            equation = str(prblmnumbs[0])+" + "+str(prblmnumbs[1])+" = x"
        else:
            equation = str(prblmnumbs[0])+" * "+str(prblmnumbs[1])+" = x"

        #parse eq:
        old_op = None
        parens = False
        trips = []
        cmplx,simple = equation.split("=")
        simple = simple.strip()
        cmplx = cmplx.split()
        i=0
        state = []
        opstack = []
        print(cmplx)

        while i<len(cmplx):
            c = cmplx[i]
            #print(i,c,state)
            #raw_input()
            if state == [] and not (floatcheck(c) or c=='x'): 
                i+=1; continue

            if state == [] and (floatcheck(c) or c=='x'):
                state = [(c,allnumbs[c])]
                i+=1;continue

            if c in ["+","-","/","*"]:
                op = c
                c = state[-1]
                d = cmplx[i+1]
                if d == "(":
                    j=1
                    while not floatcheck(d):
                        d = cmplx[i+j]
                        j+=1
                    opstack.append((op,state.index(c)))
                    trips.append(("No Operation",c,(d,allnumbs[d])))
                    state.append((d,allnumbs[d]))
                    i+=j
                else:
                    trips.append((op,c,(d,allnumbs[d])))
                    state = state[:-1]
                    state.append((c[0]+op+d,combine(c[1],allnumbs[d],op)))
                    #print(i,c,state)
                    i+=2
                    continue
            if c == ")":
                if opstack == []:
                    i+=1
                    continue
                else:
                    op,c = opstack.pop()
                    c = state[c]
                    d = state[-1]
                    # this is c,d rather than d,c above because 
                    # perhaps the operation is more based on the first sentence?
                    trips.append((op,c,d))
                    state = [x for x in state[:-1] if x!= c]
                    state.append((c[0]+op+d[0],combine(c[1],d[1],op)))
                    i+=1

        problem = problem.split(". ")[-1]
        target = allnumbs['x'].unit if 'x' in allnumbs else "???"
        tmpexamples = training(trips,problem,target)
        for k in texamples:
            texamples[k][0].extend(tmpexamples[k][0])
            texamples[k][1].extend(tmpexamples[k][1])
            texamples[k][2].append(problem)


    #Do stuff with the training data
    pickle.dump(texamples,f2)
    #for 2.11 stuff, exit and run diff code:
    exit()
    #build_d(texamples)

