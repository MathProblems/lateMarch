import sys
import json
import jsonrpclib
import pprint
import pickle

class StanfordNLP:
    def __init__(self, port_number=8080):
        self.server = jsonrpclib.Server("http://localhost:%d" % port_number)

    def parse(self, text):
        return json.loads(self.server.parse(text))

nlp = StanfordNLP()

s = "Sandy went to the mall to buy clothes. She spent $13.99 on shorts, $12.14 on a shirt, and $7.43 on a jacket. How much money did Sandy spend on clothes?"
s = "Albert has two snakes. The garden snake is 10 inches long. The boaconstrictor is 7 times longer than the garden snake. How many inches is the boaconstrictor?"
#s = "There were 2 red orchids and 4 white orchids in the vase . Jessica cut some red orchids from her flower garden . There are now 18 red orchids in the vase . How many red orchids did she cut ?"

p = nlp.parse(sys.argv[1])
pprint.pprint(p)
exit()

parseD = []
with open("3.16.siena.problems.txt") as f:
    for line in f:
        line = line.split(".")[-1]
        p = nlp.parse(line)
        pprint.pprint(p["sentences"][0]["indexeddependencies"])
        continue
        parseD.append((line,p))
        if "/" in line:
            pprint.pprint(p)
#pickle.dump(parseD,open('3.16.siena.pickle','wb'))

