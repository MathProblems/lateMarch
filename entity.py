from nltk.corpus import wordnet as wn
from nltk.corpus import wordnet_ic
import pickle
brown_ic = wordnet_ic.ic('ic-brown.dat')
asverbs = pickle.load(open('data/3.24.verbs.as','rb'))
mdverbs = pickle.load(open('data/3.24.verbs.md','rb'))
asverbs += mdverbs


class entity:
    # an entity corresponds to a quantified pl or mass noun
    # TODO distinguish pl and mass nouns from others somehow
    def __init__(self,num='',ent='',sidx='',widx='',container='',lemma='',deps=None,s=None):
        self.sidx=sidx
        self.widx=widx
        self.num = num
        self.unit = ""
        self.ent = ent
        self.adj = ""
        self.verb = ""
        self.role = ""
        self.ow = ""
        self.orels = ""
        self.loc = ""
        self.container = container
        self.lemma = lemma
        self.sent = ""
        self.text = ""
        self.each = False
        self.times = False
        if deps != None:
            self.parsedeps(deps)
        if s != None:
            self.text = s["text"]
            #self.getContainer(s)


    def setUnit(self,unit):
        self.unit = unit

    def getContainer(self,s):
        self.container = ' '.join([w[0] for w in s["words"] if w[1]["PartOfSpeech"] in ["PRP","NNP"]])
        #print(self.container)

    def parsedeps(self,deps):
        noun = self.ent.split(" ")[-1]+"-"+str(self.widx)
        ndeps = [x for x in deps if x[1] == noun]
        protod = [(x[0],x[2].split("-")[0]) for x in ndeps]
        ndeps = [x for x in deps if x[2] == noun]
        protod.extend([(x[0],x[1].split("-")[0]) for x in ndeps])
        deps = {k:v for k,v in protod}

        preps = [x for x in deps if "prep_" in x]
        locations = [deps[x] for x in preps if x.split("_")[1] in ["in","at","on"]]
        # need to check if prep_on is a noun or a verb
        self.loc = " ".join(locations)

        if "nsubj" in deps:
            self.verb = self.verb+" "+deps["nsubj"]
            self.role = "s"

        if "nsubjpass" in deps:
            self.verb = self.verb+" "+deps["nsubjpass"]
            self.role = "s"

        if "dobj" in deps:
            self.verb = self.verb+" "+deps["dobj"]
            self.role = "do"

        #TODO add idobj

        if "amod" in deps:
            self.adj += " "+deps["amod"]

        for x in deps:
            if x not in ["amod","dobj","nsubjpass","nsubj","prep_in","prep_at","prep_on","nn"]:
                #all other relations
                self.orels += " "+x
                self.ow += " "+deps[x]


    def details(self):
        print()
        print("ENTITY DESCRIPTION")
        print("Entity : "+self.ent)
        print('Number : '+str(self.num))
        print('Unit : '+self.unit)
        for x in self.__dict__:
            if x in ['ent','unit','num']: continue
            if type(self.__dict__[x])==type([]):
                print(x)
                for y in self.__dict__[x]:
                    print(y)
            else:
                print(x + " : " + str(self.__dict__[x]))
        print("------------------")




def vector(a,b,problem,target,v=False):
    #this function take the trips and creates positive and negative training instances from them

    a = a[1]
    b = b[1]

    s = a.sent.lower().strip()+" "

    #build vector from two quantities:
    vec = []
    
    #local
    features = []
    srtd = sorted(a.__dict__.keys());
    for k in srtd:
        #print(k)
        if k in ["sent","ow","orels",'text','each','num']:continue
        if type(a.__dict__[k])!=type('aaa'):continue
        if type(b.__dict__[k])!=type('aaa'):continue
        features.append(k)
        ak = [x for x in a.__dict__[k].strip().split(" ") if x is not "" and x is not "???"]
        bk = [x for x in b.__dict__[k].strip().split(" ") if x is not "" and x is not "???"]
        if len([x for x in ak if x in bk ])>0:
            dist = 0
        else:
            dist = 1
            for aw in ak:
                asyns = wn.synsets(aw)
                for asyn in asyns:
                    for bw in bk:
                        bsyns = wn.synsets(bw)
                        for bsyn in bsyns:
                            if asyn._pos != bsyn._pos: continue
                            try:
                                sim = 1/(1+bsyn.res_similarity(asyn,brown_ic))
                            except:
                                continue
                            if sim < dist:
                                dist = sim
        vec.append(dist)

    
    #match location to entity
    features.append('a location b ent')
    a.loc = ' '.join([x for x in a.loc.split(" ") if x!="???"])
    b.loc = ' '.join([x for x in b.loc.split(" ") if x!="???"])

    a.ent = ' '.join([x for x in a.ent.split(" ") if x!="???"])
    b.ent = ' '.join([x for x in b.ent.split(" ") if x!="???"])

    a.container = ' '.join([x for x in a.container.split(" ") if x!="???"])
    b.container = ' '.join([x for x in b.container.split(" ") if x!="???"])
    if len(set(a.__dict__["loc"].split(" ")).intersection(set(b.__dict__["ent"].split(" "))))>0:
        vec.append(1)
    else: vec.append(0)
    features.append('b location a ent')
    if len(set(b.__dict__["loc"].split(" ")).intersection(set(a.__dict__["ent"].split(" "))))>0:
        vec.append(1)
    else: vec.append(0)

    features.append('a location b cont')
    if len(set(a.__dict__["loc"].split(" ")).intersection(set(b.__dict__["container"].split(" "))))>0:
        vec.append(1)
    else: vec.append(0)
    features.append('b location a cont')
    if len(set(b.__dict__["loc"].split(" ")).intersection(set(a.__dict__["container"].split(" "))))>0:
        vec.append(1)
    else: vec.append(0)

    features.append('a cont b ent')
    if len(set(a.__dict__["container"].split(" ")).intersection(set(b.__dict__["ent"].split(" "))))>0:
        vec.append(1)
    else: vec.append(0)
    features.append('b cont a ent')
    if len(set(b.__dict__["container"].split()).intersection(set(a.__dict__["ent"].split())))>0:
        vec.append(1)
    else: vec.append(0)

    #Verb features
    for i in range(4):
        features.append('b verb + - * /')
        vdist = 1 
        if b.verb != "" and b.verb != "???":
            if b.verb in asverbs[i]:
                vdist = 0
            else:
                for asyn in asverbs[i]:
                    try:
                        sim = 1/(1+bsyn.res_similarity(asyn,brown_ic))
                    except:
                        sim = 1
                    if sim < vdist:
                        vdis = sim
        vec.append(vdist)
    



    features.append('a each')
    if a.each:
        vec.append(1)
    else:
        vec.append(0)
    features.append('b each')
    if b.each: vec.append(1)
    else: vec.append(0)

    features.extend(["a.times",'b.times','a or b .times'])
    if a.times: vec.append(1)
    else: vec.append(0)
    if b.times: vec.append(1)
    else: vec.append(0)
    if a.times or b.times: vec.append(1)
    else: vec.append(0)

    features.append('a target match')
    if a.ent==target: vec.append(1)
    else: vec.append(0)
    features.append('b target match')
    if b.ent==target: vec.append(1)
    else: vec.append(0)

    
    asent = a.__dict__['text'].lower().split()
    bsent = b.__dict__['text'].lower().split()
    features.extend(["a each",'b each',"a times",'b times',"a total",'b total',"a together",'b together',"a more", 'b more' ,"a less",'b less',"a add",'b add',"a divide",'b divide',"a split",'b split',"a equal",'b equal',"a equally",'b equally'])
    for li in ["each","times","total","together","more","less","add","divide","split","equal","equally"]:
        if li in asent:
            vec.append(1)
        else:
            vec.append(0)
        if li in bsent: vec.append(1)
        else: vec.append(0)
    #global
    problem = problem.lower()
    features.append("in all")
    if "in all" in problem: vec.append(1)
    else: vec.append(0)
    features.append("end with")
    if "end with" in problem: vec.append(1)
    else: vec.append(0)
    problem = problem.split()
    features.extend(["each","times","total","together","more","less","add","divide","split","left","equal","equally","now",'left','start'])
    for li in ["each","times","total","together","more","less","add","divide","split","left","equal","equally","now",'left','start']:
        if li in problem:
            vec.append(1)
        else:
            vec.append(0)

    if v:
        return (vec,features)
    else: return vec


