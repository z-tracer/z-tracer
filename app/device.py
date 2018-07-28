import json
import socket
import time
import threading
from app.zclient.zclient import Zclient
#from app.record.record import Loadavg, Process, Processes, Stat, Softirqs, Interrupts, Meminfo, Uptime
from app.record.cpu import Loadavg, Stat, Softirqs, Interrupts, Uptime
from app.record.task import Process, Processes
from app.record.mem import Meminfo

class RecordDate():
    def __init__(self, **kwargs):
        self.data = []
        self.len = 120
        self.cnt = 0
        if kwargs:
            self.len = kwargs['len']

    def add(self, val):
        if self.cnt >= self.len:
            self.data.pop(0)
        else:
            self.cnt+=1
        self.data.append(val)
        
    def dump(self):
        for val in self.data:
            print(val.getdata('all'))
    
    def getlast(self, name, num=0):
        return [self.data[-1].time, self.data[-1].getdata(name, num)]
        
    def getline(self, name,num=0):
        ret = []
        d = self.len - self.cnt
        for val in self.data:
            if d > 0:  #数据不够时填充
                for i in range(d):
                    ret.append([val.time,0])
                d = 0
            ret.append([val.time,val.getdata(name, num)])
        return ret


class Device:
    def __init__(self,ip, port,intval=1,samplecnt=120):
        self.timer = None
        self.intval = intval
        self.ip = ip
        self.port = port
        self.samplecnt = samplecnt
        self.zclient = Zclient(clientip = ip, port = port)
        self.connect = self.zclient.checkconnect()

    def start(self):
        self.scan_process()
        self.timer = threading.Timer(self.intval, self.start)
        self.timer.start()

    def scan_process(self):
        #loadavg
        if not hasattr(self,'g_loadavg'):
            self.g_loadavg = RecordDate()
        loadavg = Loadavg(self.zclient)
        loadavg.update()
        self.g_loadavg.add(loadavg)
        
        #stat
        if not hasattr(self,'g_stat'):
            self.g_stat = RecordDate()
        newstat = Stat(self.zclient)
        newstat.update()
        self.g_cpunum = newstat.cpunum
        if len(self.g_stat.data) > 0:
            newstat.diff(self.g_stat.data[-1])
        self.g_stat.add(newstat)
        
        #softirqs
        if not hasattr(self,'g_softirqs'):
            self.g_softirqs = RecordDate()
        newsoftirqs = Softirqs(self.zclient)
        newsoftirqs.update()
        if len(self.g_softirqs.data) > 0:
            newsoftirqs.diff(self.g_softirqs.data[-1])
        self.g_softirqs.add(newsoftirqs)
        
        #interrupts
        if not hasattr(self,'g_interrupts'):
            self.g_interrupts = RecordDate()
        newinterrupts = Interrupts(self.zclient)
        newinterrupts.update()
        if len(self.g_interrupts.data) > 0:
            newinterrupts.diff(self.g_interrupts.data[-1])
        self.g_interrupts.add(newinterrupts)

        #meminfo
        if not hasattr(self,'g_meminfo'):
            self.g_meminfo = RecordDate()
        newmeminfo = Meminfo(self.zclient)
        newmeminfo.update()
        self.g_meminfo.add(newmeminfo)

        #uptime
        if not hasattr(self,'g_uptime'):
            self.g_uptime = RecordDate()
        newuptime = Uptime(self.zclient)
        newuptime.update()
        self.g_uptime.add(newuptime)

        #processes
        if not hasattr(self,'g_processes'):
            self.g_processes = RecordDate()
        newprocesses = Processes(self.zclient)
        newprocesses.scan()
        if len(self.g_processes.data) > 0:
            newprocesses.diff(self.g_processes.data[-1])
        self.g_processes.add(newprocesses)

        #ctx=app.app_context()  
        #ctx.push() 
        #ctx.pop() 
