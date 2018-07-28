import time

class Meminfo():
    def __init__(self, zclient,**kwargs):
        self.MemTotal = []
        self.meminfo = {}
        self.time = 0
        self.zclient = zclient

    def update(self):
        self.time = int(time.time() * 1000)
        data = self.zclient.get_procinfo('/proc/meminfo')
        if data == None:
            return
        data = data.split('\n')
        for line in data:
            if line:
                line=line.replace(' ','')
                line=line.split(':')
                iskB = 0
                if 'kB' in line[1]:
                    iskB = 1
                if iskB == 1:
                    self.meminfo[line[0]] = int(line[1].replace('kB','')) * 1024
                else:
                    self.meminfo[line[0]] = int(line[1])

    def getdata(self,name,num=0):
        if len(self.meminfo) > 0 :
            if name == 'total':
                return self.meminfo['MemTotal']
            elif name == 'free':
                return self.meminfo['MemFree']
            elif name == 'cache':
                return self.meminfo['Cached']
            elif name == 'buffer':
                return self.meminfo['Buffers']
            elif name == 'used':
                return self.meminfo['MemTotal'] - self.meminfo['Buffers'] - self.meminfo['Cached'] - self.meminfo['MemFree']
            elif name == 'mem':
                return [self.meminfo['MemTotal'],self.meminfo['MemFree'],self.meminfo['Cached'],self.meminfo['Buffers'],
                self.meminfo['MemTotal'] - self.meminfo['Buffers'] - self.meminfo['Cached'] - self.meminfo['MemFree']]
        return 0
