from entity import entity
from xfinder import xfinder

def combine(a,b,op):
    #takes two entities and returns a combo of them.
    c = entity()
    for k in a.__dict__:
        if k == "num":
            c.num = "("+str(a.__dict__[k])+op+str(b.__dict__[k])+")"
        else:
            c.__dict__[k]= b.__dict__[k]
    #print(c.__dict__)
    return c

def floatcheck(x):
    if "/" in x or "*" in x:
        return True
    else:
        try:
            float(x)
            return True
        except:
            return False


def nncompound(w,deps):
    li = [x for x in deps if (x[1]==w or x[2]==w) and x[0]=='nn']
    if li:
        li = li[0]
        words = li[2].split("-")[0]+" "+li[1].split("-")[0]
    else:
        words = w.split("-")[0]
    return words

def makeentity(tup,deps,s,i,words=None):
    ent,idx,num,lemma,cont= tup
    e = entity(num,ent,i,idx,cont,lemma,deps)
    ws = [x[0] for x in words]
    e.verb = e.verb.strip()
    if e.verb in ws:
        i = ws.index(e.verb)
        if "VB" not in words[i][1]["PartOfSpeech"]:
            e.verb = ''
    else: e.verb = ''


    if e.verb=='':
        verbs = [x[0] for x in words if "VB" in x[1]["PartOfSpeech"] and x[1]["Lemma"] not in ['do','be']]
        #print("VERBS : ",verbs);input()
        e.verb = ' '.join(verbs)
        
    return e



def setmaker(story):
    
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
                psetstmp.append((nn,int(nidx),"2/","???"))


        nums = [(x[1],x[2]) for x in deps if x[0]=='num' or x[0]=='number']
        #many = [(x[1],"x-") for x in deps if "many-" in x[2] if "times-" not in x[1]]
        #much = [(x[1],"x-") for x in deps if "much-" in x[2] if "times-" not in x[1]]
        #if len(many+much)==0:
        nums.extend([(x[1],"x-") for x in deps if "how-" in x[2]])
        #else:

        #   nums.extend(many+much)

        # add othernums to debts
        othernums = [("???",str(words.index(x)+1),x[0],"???") for x in words if x[1]["PartOfSpeech"]=="CD"]
        othernums = [x for x in othernums if str(x[2])+'-'+x[1] not in [y[1] for y in nums]]
        debts.extend(othernums)
        #print(nums,othernums,debts);exit()
        
        for x,num in nums:
            #print(x,num)
            el = [x for x in deps if x[0]=="nsubj"]
            if el:
                cont = el[0][2]
                cont = nncompound(cont,deps)
            else: cont = "???"
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
                    psetstmp.append((nn,nidx,str(num)+"*",cont))
                else:
                    #entity is prev
                    #print(numidx)
                    debts.append(("PREV",int(numidx),str(num)+'*',cont))
                # else entity for this number is the previous potential entity
            elif word == 'many':
                manydep = [x for x in deps if 'many-' in x[2]][0]
                if manydep[0]=='amod':
                    widx = int(manydep[1].split("-")[1])
                    word = nncompound(manydep[1],deps)
                    psetstmp.append((word,widx,'x',cont))
                elif manydep[0]=='dep':
                    verb = manydep[1]
                    word = [x[2] for x in deps if x[1]==verb and 'subj' in x[0]]
                    if word:
                        word = word[0]
                        widx = int(word.split("-")[1])
                        word = nncompound(word,deps)
                        psetstmp.append((word,widx,'x',cont))
                    else:
                        debts.append(("PREV",manydep[1].split("-")[1],'x',cont))

                else:
                    debts.append(("PREV",manydep[1].split("-")[1],'x',cont))


            elif word == 'much':
                #print("MUCH!")
                manydep = [x for x in deps if 'much-' in x[2]][0]
                widx = int(manydep[1].split("-")[1])
                word = nncompound(manydep[1],deps)
                '''
                if word=='did':
                    wordzero = [x[0] for x in s['words']]
                    if 'cost' in wordzero or 'spend' in wordzero:
                        word = "$"
                        widx = "???"
                if word=='spend':
                    word = "$"
                    widx = "???"
                '''
                psetstmp.append((word,widx,'x',cont))

            else:
                nn = nncompound(x,deps)
                psetstmp.append((nn,int(idx),num,cont))

        passtwo = []
        for word,idx,num,cont in psetstmp:
            thesewords = word.split(" ")
            lemmas = []
            for w in thesewords:
                lemmas.append(words[[x[0] for x in words].index(w)][1]['Lemma'])
            lemmas = " ".join(lemmas)
            passtwo.append((word,idx,num,lemmas,cont))

        psets.append(passtwo)
        bigdebts.append(debts)

    #second pass, get all
    allpsets = []
    for y in psets:
        for x in y:
            if x[3] not in [x[1] for x in allpsets]: allpsets.append((x[0],x[3]))
    
    #print("PSETS:",allpsets)
    for i,s in enumerate(story['sentences']):
        deps = s['indexeddependencies']
        passtwo = []
        words = s['words']
        for word,lemmas in allpsets:
            morphs = " "+" ".join([x[1]["Lemma"] for x in words])+" "
            offset = 0
            #print(lemmas)
            #print(psets[i])
            while " "+lemmas+" " in morphs:
                head = lemmas.split(" ")[-1]
                idx = morphs.split().index(head)+1
                trueidx = offset+idx
                ent = ' '.join([x[0] for x in words][idx-len(lemmas.split(" ")):idx])
                pset = [x for x in psets[i] if x[1]==trueidx]
                #print(trueidx)
                if pset:
                    entities.append([i*100+trueidx,makeentity(pset[0],deps,s['text'],i,words)])
                    #entities.append(pset)
                else:
                    #entities.append((ent,idx,"???",lemmas))
                    entities.append([i*100+trueidx,makeentity((ent,idx,"???",lemmas,"???"),deps,s['text'],i,words)])
                    #make entity
                morphs = " "+' '.join(morphs.split()[idx:])+" "
                offset = trueidx
        #handle debts
        debts = bigdebts[i]
        for debt in debts:
            where, idx, num, cont = debt
            #find closest entity 
            thisidx = i*100+int(idx)
            if where != "PREV":
                closeness = sorted([(abs(x[0]-thisidx),x[1]) for x in entities],key=lambda y:y[0],reverse=True)
                if closeness:
                    closeness=closeness[0][1]
                else:
                    closeness=makeentity(("???",idx,num,"???","???"),deps,s,i,words)

            else:
                closeness = sorted([(abs(x[0]-thisidx),x[1]) for x in entities if x[0]<thisidx],key=lambda y:y[0],reverse=True)[0][1]
            ent = closeness.ent
            lemma = closeness.lemma
            entities.append([thisidx,makeentity((ent,idx,num,lemma,cont),deps,s['text'],i,words)])
    
    '''
    timeses = [j for j,x in enumerate(entities) if "_TIMES" in x[1].num]
    for j in timeses:
        num = float(entities[j][1].num.split("_")[0])
        entities[j][1].times = True
        entities[j][0]=num
    '''

    #find x
    exes = [(i,x) for i,x in enumerate(entities) if x[1].num=='x']
    if len(exes)==1:
        i,x = exes[0]
        idx,ent,target = xfinder(story['sentences'][-1],x,allpsets)
        if ent is not None:
            word,lemma = ent
            entities[i][1].ent = word
            entities[i][1].lemma = lemma
        
        if target is not None:
            #print("TARGET:" + target)
            entnames = [y[1].lemma for y in entities]
            if target in entnames:
                oidx = entities[entnames.index(target)][0]
                entities[i][0]=oidx+1
                #print(oidx)
                entities[i][1].num = "x*"

        else:
            if idx==-1:
                entities[i][0] = 10000000
            elif idx==0:
                entities[i][0] = -1
                #multiply by the thing

        words = [x[0] for x in story['sentences'][-1]['words']]
        if 'spend' in words:
            x[1].ent = '$'
            x[1].lemma = "$"
            x[1].verb = 'spend'
        elif 'cost' in words:
            x[1].ent='$'
            x[1].lemma = "$"
            x[1].verb='cost'



        




    entities.sort(key=lambda x: x[0])

    #Verbfix


    return entities


