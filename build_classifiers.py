from __future__ import print_function
import sys
import pickle
import numpy as np
#sys.path.insert(0, '/Users/rikka/liblinear-1.94/python')
#from liblinearutil import *
sys.path.insert(0, '/Users/rikka/libsvm-3.18/python')
from svmutil import *
import pdb

def build_d(d, fn, c=1):     

    i = 1
    pos = d[0]
    neg = d[1]
    pl = len(pos)
    nl = len(neg)
    labels = [1 for b in range(pl)] + [-1 for b in range(nl)]
    bsqs =  pos + neg 
    #print(bsqs)
    #print(pl,nl)
    pl = float(1/pl)
    nl = float(1/nl)
    print(pl,nl)

    '''
    #LIB LINEAR
    prob = problem(labels, bsqs)
    param = parameter('-q -s 2 -B 1 -c '+str(c)+' -w-1 '+str(nl)+' -w1 '+str(pl))
    m = train(prob, param)
    p_label, p_acc, p_val = predict(labels,bsqs, m)
    ACC, MSE, SCC = evaluations(labels, p_label,)
    '''


    prob = svm_problem(labels, bsqs)
    param = svm_parameter('-q -b 1 -t 2 -c '+str(c)+' -w-1 '+str(1/nl)+' -w1 '+str(1/pl))

    m = svm_train(prob, param)

    filename = fn + ".svmclassifier"
    svm_save_model(filename, m)
    #save_model(filename, m)

if __name__=="__main__":
    fn = sys.argv[1]
    d= pickle.load(open(fn,"rb"))
    #NOT GENERIC CODE:
    ex = d["+"]
    build_d((ex[0],ex[1]),fn)


