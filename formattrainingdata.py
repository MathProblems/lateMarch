import sys, os, pickle

d = pickle.load(open('data/bigtexamples.pickle','rb'))
named = {'+':'plus','-':'minus','/':'divide','*':'multiply','=':'equal'}
f = open("data/md.data",'w')

for k,x in enumerate(['*','/']):
    '''
    if k < 2:
        k=0
    else:
        k=1
    '''
    for v in d[x][0]:
        f.write(str(k)+" ")
        for i,j in enumerate(v):
            f.write(str(i+1)+":"+str(j)+" ")
        f.write("\n")

f.close()
