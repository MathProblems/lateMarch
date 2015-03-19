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

'''


def nncompound(w,deps):
    li = [x for x in deps if (x[1]==w or x[2]==w) and x[0]=='nn']
    if li:
        li = li[0]
        words = li[2].split("-")[0]+" "+li[1].split("-")[0]
    else:
        words = w.split("-")[0]
    return words


def psetsmaker(story):
    
    entities = []
    # find potential sets: quantified entities in any way and target 
    psets = []
    bigdebts = []
    for s in story["sentences"]:
        psetstmp = []
        deps = s['indexeddependencies']
        words = s['words']
        debts = []

        # deal with "half"
        half = [x for x in deps if 'half-' in x[1]]
        for h in half:
            #look at other syntactic constructions for half
            if h[0] == 'prep_of':
                nn,nidx = h[2].split("-")
                nn = nncompound(nn,deps)
                psetstmp.append((nn,int(nidx),'half',"???"))


        nums = [(x[1],x[2]) for x in deps if x[0]=='num']
        nums.extend([(x[1],"x-") for x in deps if "how-" in x[2]])

        # add othernums to debts
        othernums = [("???",str(words.index(x)+1),x[0],"???") for x in words if x[1]["PartOfSpeech"]=="CD"]
        othernums = [x for x in othernums if str(x[2])+'-'+x[1] not in [y[1] for y in nums]]
        debts.extend(othernums)
        #print(nums,othernums,debts);exit()
        
        for x,num in nums:
            el = [x for x in deps if x[0]=="nsubj"]
            if el:
                ent = el[0][2]
                ent = nncompound(ent,deps)
            else: ent = "???"
            num,numidx = num.split("-")
            word,idx = x.split("-")
            if word == 'times':


                #find the nouns after "times"
                nexnoun = [(x[0],s['words'].index(x)) for x in s['words'][int(idx):] if x[1]["PartOfSpeech"] in ["NN","NNS"]]
                if len(nexnoun)>0:
                    nidx = nexnoun[0][1]+1
                    nn = nexnoun[0][0]+"-"+str(int(nexnoun[0][1])+1)
                    #check for nn compound
                    nn = nncompound(nn,deps)
                    nidx = [x[0] for x in s['words']].index(nn.split()[-1])+1
                    psetstmp.append((nn,nidx,str(num)+'x',ent))
                else:
                    #entity is prev
                    debts.append(("PREV",int(numidx),str(num)+'x',ent))
                # else entity for this number is the previous potential entity
            elif word == 'many':
                manydep = [x for x in deps if 'many-' in x[2]][0]
                widx = int(manydep[1].split("-")[1])
                word = nncompound(manydep[1],deps)
                psetstmp.append((word,widx,'x',ent))

            elif word == 'much':
                manydep = [x for x in deps if 'much-' in x[2]][0]
                widx = int(manydep[1].split("-")[1])
                word = nncompound(manydep[1],deps)
                if word=='did':
                    wordzero = [x[0] for x in s['words']]
                    if 'cost' in wordzero:
                        word = "cost"
                psetstmp.append((word,widx,'x',ent))

            else:
                nn = nncompound(x,deps)
                psetstmp.append((nn,int(idx),num,ent))

        passtwo = []
        for word,idx,num,ent in psetstmp:
            thesewords = word.split(" ")
            lemmas = []
            for w in thesewords:
                lemmas.append(words[[x[0] for x in words].index(w)][1]['Lemma'])
            lemmas = " ".join(lemmas)
            passtwo.append((word,idx,num,lemmas,ent))

        psets.append(passtwo)
        bigdebts.append(debts)

    #second pass, get all
    allpsets = []
    for y in psets:
        for x in y:
            if x[3] not in [x[1] for x in allpsets]: allpsets.append((x[0],x[3]))

    print(allpsets)
    for i,s in enumerate(story['sentences']):
        deps = s['indexeddependencies']
        passtwo = []
        words = s['words']
        morphs = " ".join([x[1]["Lemma"] for x in words])
        print(morphs)
        for word,lemmas in allpsets:
            if " "+lemmas+" " in morphs:
                head = lemmas.split(" ")[-1]
                idx = morphs.split().index(head)+1
                ent = ' '.join([x[0] for x in words][idx-len(lemmas.split(" ")):idx])
                pset = [x for x in psets[i] if x[1]==idx]
                if pset:
                    entities.append((i*100+idx,makeentity(pset[0],deps,s['text'],i)))
                    #entities.append(pset)
                else:
                    #entities.append((ent,idx,"???",lemmas))
                    entities.append((i*100+idx,makeentity((ent,idx,"???",lemmas,"???"),deps,s['text'],i)))
                    #make entity
        #handle debts
        debts = bigdebts[i]
        for debt in debts:
            where, idx, num, cont = debt
            #find closest entity 
            thisidx = i*100+int(idx)
            if where != "PREV":
                closeness = sorted([(abs(x[0]-thisidx),x[1]) for x in entities],key=lambda y:y[0],reverse=True)[0][1]
            else:
                closeness = sorted([(abs(x[0]-thisidx),x[1]) for x in entities if x[0]<thisidx],key=lambda y:y[0],reverse=True)[0][1]
            unit = closeness.unit
            lemma = closeness.lemma
            entities.append((thisidx,makeentity((unit,idx,num,lemma,cont),deps,s['text'],i)))





    entities.sort(key=lambda x: x[0])


    return entities

def makeentity(tup,deps,s,i):
    unit,idx,num,lemma,ent = tup
    return entity(num,unit,i,idx,ent,lemma,deps)

'''


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



if __name__ == "__main__":
    raw_counts = {x:" " for x in ["+","*"]}
    if len(sys.argv)<2:
        print("args");exit()
    if sys.argv[1]=='asmd':
        f2 = open("data/3.19.asmd.verbs",'wb')
        wps = open('add.problems').readlines()
        wps.extend([x for x in open('sub.problems').readlines()])
        addlen = len(wps)
        wps.extend([x for x in open('mult.problems').readlines()])
        wps.extend([x for x in open('div.problems').readlines()])
    elif sys.argv[1]=='as':
        f2 = open("data/3.19.as.verbs",'wb')
        wps = open('add.problems').readlines()
        addlen = len(wps)
        wps.extend([x for x in open('sub.problems').readlines()])
    elif sys.argv[1]=='md':
        f2 = open("data/3.19.md.verbs",'wb')
        wps = open('mult.problems').readlines()
        addlen = len(wps)
        wps.extend([x for x in open('div.problems').readlines()])
    pos = []
    neg = []
    texamples = {x:([],[],[]) for x in ["+","*"]}
    tverbs = {x:[] for x in ["+","*"]}
    for j in range(len(wps)):
        print(wps[j])
        problem = wps[j]
        problem = problem.lower()
        story = nlp.parse(problem)
        allnumbs = setmaker.setmaker(story)
        allnumbs = {str(v.num):v for k,v in allnumbs}
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
            if state == [] and not (c.isdigit() or c=='x'): 
                i+=1; continue

            if state == [] and (c.isdigit() or c=='x'):
                state = [(c,allnumbs[c])]
                i+=1;continue

            if c in ["+","-","/","*"]:
                op = c
                c = state[-1]
                d = cmplx[i+1]
                if d == "(":
                    j=1
                    while not d.isdigit():
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
        for op,c,d in trips:
            verbs = " ".join([c[1].verb,d[1].verb])
            verbs = [v for v in verbs.split(" ") if v!="???" and v!='']
            tverbs[op].extend(verbs)
        for k in texamples:
            texamples[k][0].extend(tmpexamples[k][0])
            texamples[k][1].extend(tmpexamples[k][1])
            texamples[k][2].append(problem)


    pickle.dump(tverbs,f2)

    #Do stuff with the training data
    #for 2.11 stuff, exit and run diff code:
    exit()
    #build_d(texamples)

