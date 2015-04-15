#this code finds x in the jawn somehow 

from entity import entity

def xfinder(s,xent,psets):
    
    deps = s['indexeddependencies']
    idx = -1
    words = [x[0] for x in s['words']]
    ent = (xent[1].ent,xent[1].lemma)
    lemmas = " "+" ".join([x[1]["Lemma"] for x in s['words']])+" "
    if 'start with' in ' '.join(words):
        idx = 0
    elif 'begin with' in ' '.join(words):
        idx = 0

    newent=False
    entidx = [x for x in s['words'] if x[0]==ent[0]]
    if entidx:
        if entidx[0][1]["PartOfSpeech"] not in ["NN","NNS","$"]:
            newent=True

    if newent:
        for word,lemma in psets:
            if word=='cost':continue
            #print(lemmas,lemma)
            if " "+lemma+" " in lemmas:
                head = word.split(" ")[-1]
                headidx = [x for x in s['words'] if x[0]==head]
                if headidx:
                    if headidx[0][1]["PartOfSpeech"] not in ["NN","NNS"]:
                        continue
                ent = (word,lemma)
    

    target = None
    #print(ent)
    if 'each' in words:

        each = [x[1] for x in deps if 'each-' in x[2]]
        if each:
            target = s['words'][int(each[0].split("-")[1])-1][1]['Lemma']
            #print(target)
            if target == 'cost':
                #print("NEW TARGET :",ent)
                target = ent[1]
                ent = ("$","$")
            #print(ent)

            #find this entity elsewhere and times it by money


    return (idx,ent,target)
    
