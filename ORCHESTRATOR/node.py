
class NodeWorker():
    def __init__(self, *args, **kwargs):
        self.nodes = kwargs.get('nodes',[])
        self.nodeId = kwargs.get('nodeId',None)
        self.ip = kwargs.get('ip','127.0.0.1')
        self.publicPort = kwargs.get('publicPort',5000)
        self.dockerPort = kwargs.get('dockerPort',5000)
        self.mode = kwargs.get('mode',"DOCKER")
        self.events = kwargs.get('events',0)
        self.algorithm = kwargs.get('algorithm',"RR")

    def getInfoNode(self):
        return 'nodeId = {} \nip = {} \npublicPort = {} \ndockerPort = {}'.format(self.nodeId,
                                            self.ip,
                                            self.publicPort,
                                            self.dockerPort)
    
    def getURL(self,mode='DOCKER',endPoint='workers'):
        if (mode=='DOCKER'):
            return 'http://{}:{}/{}'.format(self.nodeId,self.dockerPort,endPoint)
        else:
            return 'http://{}:{}/{}'.format(self.ip,self.publicPort,endPoint)
    
    def toJSON(self):
        return  {"nodeId"    : self.nodeId,
                "ip"         : self.ip,
                "publicPort" : self.publicPort,
                "dockerPort" : self.dockerPort}

    def getID(self):
        return self.nodeId
    
    def addNode(self,node):
        self.nodes.append(node)
    
    def getNodes(self):
        return self.nodes
    
    def getMode(self):
        return self.mode
    
    def getNumberEvents(self):
        return int(self.events)
    
    def setNumberEvents(self):
        self.events = self.events+1
        
    def getAlgorithm(self):
        return self.algorithm
    
    

