from entity import entity
from xfinder import xfinder

def nncompound(w,deps):
    li = [x for x in deps if (x[1]==w or x[2]==w) and x[0]=='nn']
    if li:
        li = li[0]
        words = li[2].split("-")[0]+" "+li[1].split("-")[0]
    else:
        words = w.split("-")[0]
    return words

def makeentity(tup,deps,s,i):
    unit,idx,num,lemma,ent = tup
    return entity(num,unit,i,idx,ent,lemma,deps)

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
                psetstmp.append((nn,int(nidx),"2","???"))


        nums = [(x[1],x[2]) for x in deps if x[0]=='num']
        many = [(x[1],"x-") for x in deps if "many-" in x[2] if "times-" not in x[1]]
        much = [(x[1],"x-") for x in deps if "much-" in x[2] if "times-" not in x[1]]
        if len(many+much)==0:
            nums.extend([(x[1],"x-") for x in deps if "how-" in x[2]])
        else:

            nums.extend(many+much)

        # add othernums to debts
        othernums = [("???",str(words.index(x)+1),x[0],"???") for x in words if x[1]["PartOfSpeech"]=="CD"]
        othernums = [x for x in othernums if str(x[2])+'-'+x[1] not in [y[1] for y in nums]]
        debts.extend(othernums)
        #print(nums,othernums,debts);exit()
        
        for x,num in nums:
            print(x,num)
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
                    psetstmp.append((nn,nidx,str(num)+"_TIMES",ent))
                else:
                    #entity is prev
                    print(numidx)
                    debts.append(("PREV",int(numidx),str(num)+'_TIMES',ent))
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
    
    print("PSETS:",allpsets)
    for i,s in enumerate(story['sentences']):
        deps = s['indexeddependencies']
        passtwo = []
        words = s['words']
        for word,lemmas in allpsets:
            morphs = " "+" ".join([x[1]["Lemma"] for x in words])+" "
            offset = 0
            print(lemmas)
            print(psets[i])
            while " "+lemmas+" " in morphs:
                head = lemmas.split(" ")[-1]
                idx = morphs.split().index(head)+1
                trueidx = offset+idx
                ent = ' '.join([x[0] for x in words][idx-len(lemmas.split(" ")):idx])
                pset = [x for x in psets[i] if x[1]==trueidx]
                print(trueidx)
                if pset:
                    entities.append([i*100+trueidx,makeentity(pset[0],deps,s['text'],i)])
                    #entities.append(pset)
                else:
                    #entities.append((ent,idx,"???",lemmas))
                    entities.append([i*100+trueidx,makeentity((ent,idx,"???",lemmas,"???"),deps,s['text'],i)])
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
                    closeness=makeentity(("???",idx,num,"???","???"),deps,s,i)

            else:
                closeness = sorted([(abs(x[0]-thisidx),x[1]) for x in entities if x[0]<thisidx],key=lambda y:y[0],reverse=True)[0][1]
            unit = closeness.unit
            lemma = closeness.lemma
            entities.append([thisidx,makeentity((unit,idx,num,lemma,cont),deps,s['text'],i)])
        
    timeses = [j for j,x in enumerate(entities) if "_TIMES" in x[1].num]
    for j in timeses:
        num = float(entities[j][1].num.split("_")[0])
        entities[j][1].times = True
        entities[j][0]=num

    #find x
    exes = [(i,x) for i,x in enumerate(entities) if x[1].num=='x']
    if len(exes)==1:
        i,x = exes[0]
        idx = xfinder(story['sentences'][-1])
        if idx==-1:
            entities[i][0] = 10000000
        if idx==0:
            entities[i][0] = -1

        




    entities.sort(key=lambda x: x[0])


    return entities


