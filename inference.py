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
sys.path.insert(0, './treebuilder')
from StringTemplate import StringTemplate
from svmutil import *
import setmaker
from sympy.solvers.solvers import solve

adds = svm_load_model("data/3.19.as.svmclassifier")
multd = svm_load_model("data/3.19.md.svmclassifier")

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


def compute(p,op,e,target,problem):
    vec,features = ENTITY.vector((0,p),(0,e),problem,target,True)
    if op == '+':
        op_label, op_acc, op_val = svm_predict([-1], [vec], adds,'-q -b 1')
        op_val = op_val[0]
        val = op_val[0]
    elif op == '-':
        op_label, op_acc, op_val = svm_predict([-1], [vec], adds,'-q -b 1')
        op_val = op_val[0]
        val = op_val[1]
    elif op == '*':
        op_label, op_acc, op_val = svm_predict([-1], [vec], multd,'-q -b 1')
        op_val = op_val[0]
        val = op_val[0]
    elif op == '/':
        op_label, op_acc, op_val = svm_predict([-1], [vec], multd,'-q -b 1')
        op_val = op_val[0]
        val = op_val[1]
    else:
        print("BAD OP:",op)
        return -1
    
    c = setmaker.combine(p,e,op)
    return (val,c)


if __name__ == "__main__":
    VERBOSE = False
    VVERBOSE = False
    EDUMP = True
    #EDUMP = False 
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
    #asmd = svm_load_model("data/3.19.asmd.svmclassifier")
    #adds = svm_load_model("data/3.19.as.svmclassifier")
    #multd = svm_load_model("data/3.19.md.svmclassifier")
    wps = open("complex_dev.problems").readlines()
    answs = open("complex_dev.answers").readlines()
    right = 0
    guesses = 0
    ad = []
    for k in range(len(wps)):
        if VERBOSE:
            for i in range(len(wps)):
                print(i,wps[i])
            j = int(input())
        print(wps[k])
        problem = wps[k].lower()



        story = nlp.parse(problem)
        numbs = setmaker.setmaker(story,VERBOSE)
        #for x in numbs: x[1].details()
        #input(); continue
        numlist = [(str(v.num),v) for k,v in numbs if setmaker.floatcheck(v.num) or v.num == 'x']
        for i in range(len(numlist)):
            if "*" in numlist[i][0] or "/" in numlist[i][0]:
                numlist[i] = (''.join([x for x in numlist[i][0] if x not in ['*','/']]),numlist[i][1])
                numlist[i][1].num = numlist[i][0]
        objs = {k:(0,v) for k,v in numlist}
        if VERBOSE:
            print(objs,numlist,[v.num for k,v in numbs])
        #print(allnumbs)




        for num,e in objs.items():
            ent = e[1].ent
            e = e[1]
            if ent[-1]=='s':
                ent = ent[:-1]
            if ent[-1]=='e':
                ent=ent[:-1]
            if "each "+ent in problem:
                e.each = True
            elif "each" in problem:
                pass


        state = []
        #print(numlist)

        

        #for e in allnumbs.items():
        print(numlist)
        numidxlist = [x[0] for x in numlist]
        ST = StringTemplate(numidxlist)
        scores = []
        for j,eq in enumerate(ST.equations):
            thisscore = []
            #print(eq.toString())
            #determine score for this eq
            l,r = [x.strip().split(' ') for x in eq.toString().split('=')]
            if len(l)>1 and len(r)>1: 
                scores.append(0);continue
            compound = r if len(l)==1 else l
            target = l[0] if len(l)==1 else r[0]
            target = (target,objs[target])

            #find innermost parens?
            while len(compound)>1:
                if "(" in compound:
                    rpidx = (len(compound) - 1) - compound[::-1].index('(')
                    lpidx = rpidx+compound[rpidx:].index(")")
                    subeq = compound[rpidx+1:lpidx]
                    substr = ' '.join(subeq)
                    compound = compound[:rpidx]+[substr]+compound[lpidx+1:]
                else:
                    subeq = compound[0:3]
                    substr = ' '.join(subeq)
                    compound = [substr]+compound[lpidx:]
                if substr in objs:
                    pute = objs[substr]
                else:
                    p,op,e = subeq
                    #print(p,op,e)
                    p = objs[p][1]
                    e = objs[e][1]
                    op = op.strip()
                    pute = compute(p,op,e,target,problem)
                    objs[substr]=pute
                if pute == -1:
                    exit()
                score,c = pute
                thisscore.append(score)
            print(thisscore)
            
            scores.append(sum(thisscore))

            #print(compound)
        m = np.argmax(scores)
        print(scores[m],ST.equations[m].toString())

        '''
        try:
            if target.ent=='dozen':
                guess = solve('('+numlist[0].num+'/12)'+"-"+target.num,'x')[0]
                print(numlist[0].num+"/12="+target.num)
            else:
                guess = solve(numlist[0].num+"-"+target.num,'x')[0]
                print(numlist[0].num+"="+target.num)
        '''
        eqidxs = [i for i,x in enumerate(scores) if x==scores[m]]
        tright = 0
        for i in eqidxs:
            eq = ST.equations[i].toString()
            eq = eq.replace("=",'-')
            print(eq)
            try:
                guess = solve(eq,'x')[0]
            except: guess = 0
            answ = answs[k]
            if guess == answ: 
                print("CORRECT")
                tright=1

            print(guess, answ)
        guesses += len(eqidxs)
        if tright==1:
            right +=1

        break
        continue
    print(right,guesses)

    exit()
    '''



            

        

        #make max choice each time
        numlist = [v for k,v in numbs if setmaker.floatcheck(v.num) or v.num == 'x']
        if "*" in numlist[-1].num:
            numlist = numlist[1:]+[numlist[0]]
        target = numlist[-1]
        if EDUMP:
            pickle.dump(numlist,open('entities'+str(j)+'.pickle','wb'))
            exit();
        numlist = numlist[:-1]
        while len(numlist)>1:
            pairs = [((i,numlist[i]),(i+1,numlist[i+1])) for i in range(len(numlist)-1)]
            pairscoresop = []
            for k,pair in enumerate(pairs):
                px,ex = pair
                pi,p = px
                ei,e = ex
                vec,features = ENTITY.vector((0,p),(0,e),problem,target,True)

                # do all the shit
                #p.details();e.details()
                if e.num[-1] == '/':
                    #DIVIDE ONLY
                    #print("DIVIDING IN HALF")
                    e.num = ''.join([x for x in e.num if x!='/'])
                    op = "/"; op_val=1
                    pairs[k]=((pi,e),(ei,p))
                elif e.num[-1] == '*':
                    #MULT:
                    e.num = ''.join([x for x in e.num if x!='*'])
                    op = "*"; op_val=1
                elif e.num[0] == "*":
                    #MULT BUT CHANGE ENT ORDER
                    e.num = ''.join([x for x in e.num if x!='*'])
                    op = "*"; op_val=1
                    pairs[k]=((pi,e),(ei,p))
                else:
                    if p.lemma==e.lemma:
                        #HARD CONSTRAINT AGAINST MULTIPLICATION
                        #print("Hard constraint against Multiplication/Division")
                        p_label = [1]
                    else:
                        p_label, p_acc, p_val = svm_predict([-1], [vec], asmd,'-q -b 1')
                        #print("Stats for +- vs */ decision : ",p_label,p_acc,p_val)
                    if p_label[0] == 1:
                        #adds 
                        #op_label, op_acc, op_val = predict([-1], [vec], adds,'-q')
                        op_label, op_acc, op_val = svm_predict([-1], [vec], adds,'-q -b 1')
                        op_val = op_val[0]
                        if op_label[0] == 1:
                            op = "+"
                            op_val = op_val[0]
                        else: 
                            op = "-"
                            op_val = op_val[1]
                    else:
                        #op_label, op_acc, op_val = predict([-1], [vec], multd,'-q')
                        op_label, op_acc, op_val = svm_predict([-1], [vec], multd,'-q -b 1')
                        #print("Stats for subsequent decision: ",op_label,op_acc,op_val)
                        op_val = op_val[0]
                        if op_label[0] == 1:
                            op = "*"
                            op_val = op_val[0]
                        else: 
                            op = "/"
                            op_val = op_val[1]
                    #print("Operation selected : "+op)
                    #print("Stats for subsequent decision: ",op_label,op_acc,op_val)

                pairscoresop.append((op_val,op))
            m = max([(x[0],i) for i,x in enumerate(pairscoresop)])[1]
            px,ex = pairs[m]
            pi,p = px
            ei,e = ex
            p.details();e.details()
            op = pairscoresop[m][1]
            print("Operation selected: ",op)


            c = setmaker.combine(p,e,op)
            #try:
            #    num = str(eval(c.num))
            #except: num = c.num
            numlist = numlist[:pi]+[c]+numlist[pi+2:]


        try:
            if target.ent=='dozen':
                guess = solve('('+numlist[0].num+'/12)'+"-"+target.num,'x')[0]
                print(numlist[0].num+"/12="+target.num)
            else:
                guess = solve(numlist[0].num+"-"+target.num,'x')[0]
                print(numlist[0].num+"="+target.num)
        except: guess = 0
        answ = answs[j]
        print(guess, answ)
        #val = answ.split("|")[1].split("=")[1]
        val = answ
        if float(guess)==float(val):
            print("Correct!")
            right +=1 
        else: print("incorrect")
        ad.append(int(float(guess)==float(val)))
        if VERBOSE:
            input("Any key to continue...")

    print("totals: ",right,len(answs))
    print(ad)
    '''
        



