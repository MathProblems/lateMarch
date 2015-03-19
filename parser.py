# This is a function for parsing a problem into the semantics. 
# TODO
# use lemmas rather than Morph function
# fix nn compound issue (assign head node)
import sys
import json
import jsonrpclib
from nltk.corpus import wordnet as wn
from nltk.corpus import wordnet_ic
from entity import entity

class StanfordNLP:
    def __init__(self, port_number=8080):
        self.server = jsonrpclib.Server("http://localhost:%d" % port_number)

    def parse(self, text):
        return json.loads(self.server.parse(text))

nlp = StanfordNLP()

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
        for word,lemmas in allpsets:
            if lemmas in morphs:
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
def morphs(w):
    try:
        w = [x for x in w if x.isalpha()]
        w = w[:-1] if w[-1]=='s' else w
        w = w[:-1] if w[-1]=='e' else w
        w = ''.join(w)
    except:
        pass
    return w

class entity:
    def __init__(self,num,unit,entity,deps=[]):
        self.num = num
        self.unit = unit
        self.entity = entity
        self.deps = deps
    def details(self):
        for x in self.__dict__:
            if type(self.__dict__[x])==type([]):
                print(x)
                for y in self.__dict__[x]:
                    print(y)
            else:
                print(x + " : " + self.__dict__[x])

def convert(num):
    replacements = {"two":2,"one":1,"a":1,"three":3,' four':4,' five':5,' six':6,' seven':7,' eight':8,' nine':9,'dozen':12}
    if num in replacements:
        return replacements[num]
    else:
        return False

def makesets(psets,story):
    #using the potential sets to determine the entities. 
    # we want this to parse to a entity/container kinda situation
    ents = []
    for i,s in enumerate(story['sentences']):
        relvsets = psets[i]
        deps = s['dependencies']
        ideps = s['indexeddependencies']

        


        nums = [x for x in ideps if x[0]=='num']
        nums.extend([x for x in ideps if "how-" in x[2]])
        for y,x,num in nums:
            num = num.split("-")[0]
            if num == 'how':
                num = 'x'
            elif not num.isdigit():
                print(num)
                num = convert(num)
                if not num:
                    print("BIG FAIL");exit()
            word,idx = x.split("-")
            if word == 'times':
                el = [x for x in deps if x[0]=="nsubj"]
                if el:
                    ent = el[0][2]
                    ent = nncompound(ent,ideps)
                else: ent = "???"
                #find the nouns after "times"

                nexnoun = [(x[0],s['words'].index(x)) for x in s['words'][int(idx):] if x[1]["PartOfSpeech"] in ["NN","NNS"]]

                if len(nexnoun)>0:
                    nexnoun = nexnoun[0][0]+"-"+str(int(nexnoun[0][1])+1)
                    #check for nn compound
                    unit = nncompound(nexnoun,deps)
                    #create entity
                else:
                    # else entity for this number is the previous potential entity
                    thissent = [x for x in relvsets if x[1]<int(idx)]
                    while not thissent:
                        try:
                            thissent = psets[i-1]
                        except:
                            thissent = [("???",0)]
                            break
                    unit = thissent[-1][0]
                ents.append(entity(str(num)+'x',"&"+unit,ent))

            elif word == 'many':
                manydep = [x for x in ideps if 'many-' in x[2]][0]
                unit = nncompound(manydep[1],deps)
                el = [x for x in deps if x[0]=="nsubj"]
                if el:
                    ent = el[0][2]
                    ent = nncompound(ent,ideps)
                else: ent = "???"
                ents.append(entity('x',unit,ent))




            elif word == 'much':
                manydep = [x for x in ideps if 'much-' in x[2]][0]
                unit = nncompound(manydep[1],deps)
                if unit=='did':
                    if 'cost' in [x[0] for x in s['words']]:
                        unit = "money"
                el = [x for x in deps if x[0]=="nsubj"]
                if el:
                    ent = el[0][2]
                    ent = nncompound(ent,ideps)
                else: ent = "???"
                ents.append(entity('x',unit,ent))


            else:
                unit = nncompound(word,deps)
                #THIS IS BAD
                el = [x for x in deps if x[0]=="nsubj"]
                if el:
                    ent = el[0][2]
                    ent = nncompound(ent,ideps)
                else: ent = "???"
                ents.append(entity(str(num),unit,ent))




    return ents
                

'''


if __name__=="__main__":
    with open(sys.argv[1]) as f:
        for p in f:
            print(p)
            story = nlp.parse(p.lower())
            ents = psetsmaker(story)
            for i,ent in ents: 
                ent.details()
                print()
            input()
