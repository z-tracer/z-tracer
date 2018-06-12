from flask import render_template, redirect, url_for, abort, flash, request,\
    current_app, make_response, g, jsonify
import os,random
import pygal
import threading
import sys
from . import app
import time
import graphviz as gv
from app.main.zclient import Zclient

def get_procinfo(filename):
    if 1:
        params = {}
        params['path'] = filename
        client = Zclient()
        data = client.sendRequest('readfile',params)
        if data != None:
            if len(data) == 0:
                return None
        return data
    else:
        try:
          fh = open(filename, 'r')
          data = fh.read()
        except IOError:
          print("Error: cant open file %s" % (filename))
          return None
        else:
          fh.close()
        return data

def get_cmdout(cmdline):
    if 1:
        params = {}
        params['cmd'] = cmdline
        client = Zclient()
        outputs = client.sendRequest('runcmd',params)
        if outputs != None:
            if len(outputs) == 0:
                return None
        return outputs
    else:
        try:
          file = os.popen(cmdline) 
          outputs = file.read()
        except IOError:
          print("Error: cant run cmd %s" % (cmdline))
          return None
        else:
          file.close()
        return outputs

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
    
#定义二维数组，存放固定长度的数据
class Record():
    data = []
    rows = 1
    columns = 10
    cnt = [0]

    def __init__(self, **kwargs):
        if kwargs:
            self.rows = kwargs['rows']
            self.columns = kwargs['columns']
            self.data = [([] * self.columns) for i in range(self.rows)] #二维数组的创建方法
            self.cnt = [0 for i in range(self.rows)]
            
    def add(self, row, val):
        if self.cnt[row] >= self.columns:
            self.data[row].pop(0)
        else:
            self.cnt[row]+=1
        self.data[row].append(val)

class Loadavg():
    rec = Record(rows=3,columns=50)

    def __init__(self, **kwargs):
        self.load1 = 0 
        self.load5 = 0
        self.load15 = 0
        self.time = 0
        self.nr_threads = 0  #所有进程线程总数
    
    def update(self):
        self.time = int(time.time() * 1000)
        data = get_procinfo('/proc/loadavg')
        if data == None:
            return
        data = data.split(' ')
        self.load1 = float(data[0])
        self.load5 = float(data[1])
        self.load15 = float(data[2])
        self.rec.add(0,self.load1)
        self.rec.add(1,self.load5)
        self.rec.add(2,self.load15)
        ind = data[3].find('/')
        self.nr_threads = int(data[3][ind+1:])
        return [self.load1,self.load5,self.load15]
        #print(self.rec.data[0])
        #print(self.rec.data[1])
        #print(self.rec.data[2])
    
    def getdata(self,name,num=0):
        if name == 'load1':
            return self.load1
        elif name == 'load5':
            return self.load5
        elif name == 'load15':
            return self.load15
        elif name == 'nr_threads':
            return self.nr_threads
        else:
            return [self.load1,self.load5,self.load15,self.nr_threads]
    
    def draw(self):
        self.update()
        line_chart = pygal.Line(height=200)
        line_chart.title = 'Load Avg'
        line_chart.x_labels = map(str, range(0, 50))
        line_chart.add('1分钟', self.rec.data[0])
        line_chart.add('5分钟', self.rec.data[1])
        line_chart.add('15分钟', self.rec.data[2])

        #chart = bar_chart.render(disable_xml_declaration = True) #直接写入svg格式数据，存在不能交互的问题
        #return bar_chart.render_response() 直接返回xml格式的页面
        line_chart.render_to_file('app/static/loadavg.svg') 
        return line_chart.render_data_uri() #编码成base uri格式，以嵌入到html代码中

class Uptime():
    def __init__(self, **kwargs):
        self.uptime = 0  #系统启动以来的时间
        self.idletime = 0 #所有cpu空闲时间之和

    def update(self):
        self.time = int(time.time() * 1000)
        data = get_procinfo('/proc/uptime')
        if data == None:
            return
        data = data.split(' ')
        self.uptime = float(data[0])
        self.idletime = float(data[1])

    def getdata(self,name,num=1):
        if name == 'uptime':
            return self.uptime
        elif name == 'idletime':
            return self.idletime/num
        else:
            return [self.uptime,self.idletime/num]

class Stat():
    def __init__(self, **kwargs):
        self.cpunum = 0
        self.cpu = {}
        self.total_cputime = {}
        self.intr = []
        self.ctxt = 0
        self.btime = 0
        self.processes = 0
        self.procs_running = 0
        self.procs_blocked = 0
        self.softirq = []
        self.time = 0
        self.diffcpu = []
        self.diffctxt = 0
        self.diffprocesses = 0
        self.difftime = 0
        self.diffsoftirq = []
        self.diffintr = {}
        self.diffpercpu = {}
        self.difftotal_cputime = {}

    def getstat(self):
        self.time = int(time.time() * 1000)
        data = get_procinfo('/proc/stat')
        if data == None:
            return
        data = data.split('\n')
        self.cpunum = 0
        for line in data:
            line = line.split(' ')
            while '' in line:
                line.remove('')
            if line:
                if 'cpu' in line[0]:
                    if line[0] == 'cpu' :
                        self.cpu['all'] = list(map(int, line[1:]))
                        self.total_cputime['all'] = 0
                        for i in range(0,8):
                            self.total_cputime['all'] += self.cpu['all'][i]
                    else:
                        num = int(line[0][3:])
                        self.cpu[num] = list(map(int, line[1:]))
                        self.cpunum +=1
                        self.total_cputime[num] = 0
                        for i in range(0,8):
                            self.total_cputime[num] += self.cpu[num][i]
                elif 'intr' in line[0]:
                    self.intr = list(map(int, line[1:]))
                elif 'softirq' in line[0]:
                    self.softirq = list(map(int, line[1:]))
                elif 'ctxt' in line[0]:
                    self.ctxt = int(line[1])
                elif 'btime' in line[0]:
                    self.btime = int(line[1])
                elif 'processes' in line[0]:
                    self.processes = int(line[1])
                elif 'procs_running' in line[0]:
                    self.procs_running = int(line[1])
                elif 'procs_blocked' in line[0]:
                    self.procs_blocked = int(line[1])

    def diff(self,oldstat):
        if oldstat.cpunum != 0:
            #all cpu
            diff_user = self.cpu['all'][0] - oldstat.cpu['all'][0]
            diff_nice = self.cpu['all'][1] - oldstat.cpu['all'][1]
            diff_system = self.cpu['all'][2] - oldstat.cpu['all'][2]
            diff_idle = self.cpu['all'][3] - oldstat.cpu['all'][3]
            diff_iowait = self.cpu['all'][4] - oldstat.cpu['all'][4]
            diff_irq = self.cpu['all'][5] - oldstat.cpu['all'][5]
            diff_softirq = self.cpu['all'][6] - oldstat.cpu['all'][6]
            diff_steal = self.cpu['all'][7] - oldstat.cpu['all'][7]
            sum = diff_user+diff_nice+diff_system+diff_idle+diff_iowait+diff_irq+diff_softirq+diff_steal
            if sum != 0:
                self.diffcpu = [round(diff_user*100/sum,2),round(diff_nice*100/sum,2),\
                        round(diff_system*100/sum,2),round(diff_idle*100/sum,2),\
                        round(diff_iowait*100/sum,2),round(diff_irq*100/sum,2),\
                        round(diff_softirq*100/sum,2),round(diff_steal*100/sum,2)]
                #print(self.diffcpu)
            self.difftotal_cputime['all'] =  self.total_cputime['all'] - oldstat.total_cputime['all']

            #percpu
            for i in range(self.cpunum):
                diff_user = self.cpu[i][0] - oldstat.cpu[i][0]
                diff_nice = self.cpu[i][1] - oldstat.cpu[i][1]
                diff_system = self.cpu[i][2] - oldstat.cpu[i][2]
                diff_idle = self.cpu[i][3] - oldstat.cpu[i][3]
                diff_iowait = self.cpu[i][4] - oldstat.cpu[i][4]
                diff_irq = self.cpu[i][5] - oldstat.cpu[i][5]
                diff_softirq = self.cpu[i][6] - oldstat.cpu[i][6]
                diff_steal = self.cpu[i][7] - oldstat.cpu[i][7]
                sum = diff_user+diff_nice+diff_system+diff_idle+diff_iowait+diff_irq+diff_softirq+diff_steal
                if sum != 0:
                    self.diffpercpu[i] = [round(diff_user*100/sum,2),round(diff_nice*100/sum,2),\
                            round(diff_system*100/sum,2),round(diff_idle*100/sum,2),\
                            round(diff_iowait*100/sum,2),round(diff_irq*100/sum,2),\
                            round(diff_softirq*100/sum,2),round(diff_steal*100/sum,2)]
                    #print(self.diffpercpu[i])
                self.difftotal_cputime[i] =  self.total_cputime[i] - oldstat.total_cputime[i]

            #misc
            self.diffctxt = self.ctxt - oldstat.ctxt
            self.diffprocesses = self.processes - oldstat.processes
            self.difftime = self.time - oldstat.time
            #softirq
            self.diffsoftirq=[]  
            for i in range(0,len(oldstat.softirq)):  
                summm=self.softirq[i] - oldstat.softirq[i]
                self.diffsoftirq.append(summm) 
            #hwirq
            self.diffintr={}  
            for i in range(0,len(oldstat.intr)):  
                summm=self.intr[i] - oldstat.intr[i]
                if summm > 0:
                    self.diffintr[i] = summm

    def getdata(self,name,num=0):
        if name == 'h_irq' or name == 'h_all':
            if len(self.diffintr) > 0:
                if name == 'h_irq':
                    num = int(num)
                    if num in self.diffintr:
                        return self.diffintr[num]
                elif name == 'h_all':
                    return self.diffintr
        else:
            if num == 0:
                if len(self.diffcpu) > 0:
                    if name == 'user':
                        return self.diffcpu[0]
                    elif name == 'nice':
                        return self.diffcpu[1]
                    elif name == 'system':
                        return self.diffcpu[2]
                    elif name == 'idle':
                        return self.diffcpu[3]
                    elif name == 'iowait':
                        return self.diffcpu[4]
                    elif name == 'irq':
                        return self.diffcpu[5]
                    elif name == 'softirq':
                        return self.diffcpu[6]
                    elif name == 'steal':
                        return self.diffcpu[7]
                    elif name == 'utilization':
                        return self.diffcpu
            else:
                num = int(num-1)
                if len(self.diffpercpu) > 0:
                    if name == 'user':
                        return self.diffpercpu[num][0]
                    elif name == 'nice':
                        return self.diffpercpu[num][1]
                    elif name == 'system':
                        return self.diffpercpu[num][2]
                    elif name == 'idle':
                        return self.diffpercpu[num][3]
                    elif name == 'iowait':
                        return self.diffpercpu[num][4]
                    elif name == 'irq':
                        return self.diffpercpu[num][5]
                    elif name == 'softirq':
                        return self.diffpercpu[num][6]
                    elif name == 'steal':
                        return self.diffpercpu[num][7]
                    elif name == 'utilization':
                        return self.diffpercpu[num]

        if name == 'run':
            return self.procs_running
        elif name == 'blocked':
            return self.procs_blocked
        elif name == 'ctxt':
            return self.diffctxt
        elif name == 'fork':
            return self.diffprocesses
        elif name == 'misc':
            return [self.diffctxt, self.diffprocesses,self.procs_running,self.procs_blocked]
        
        if len(self.diffsoftirq) > 0:
            if name == 's_hi':
                return self.diffsoftirq[1]
            elif name == 's_timer':
                return self.diffsoftirq[2]
            elif name == 's_net_tx':
                return self.diffsoftirq[3]
            elif name == 's_net_rx':
                return self.diffsoftirq[4]
            elif name == 's_block':
                return self.diffsoftirq[5]
            elif name == 's_block_iopoll':
                return self.diffsoftirq[6]
            elif name == 's_tasklet':
                return self.diffsoftirq[7]
            elif name == 's_sched':
                return self.diffsoftirq[8]
            elif name == 's_hrtimer':
                return self.diffsoftirq[9]
            elif name == 's_rcu':
                return self.diffsoftirq[10]
            elif name == 's_softirq':
                return self.diffsoftirq
        
        return 0

class Softirqs():
    def __init__(self, **kwargs):
        self.softirq = {}
        self.diffsoftirq = {}
        self.time = 0
        self.cpunum = 0
    
    def update(self):
        self.time = int(time.time() * 1000)
        data = get_procinfo('/proc/softirqs')
        if data == None:
            return
        data = data.split('\n')
        #calc cpu num
        line = data[0].split(' ')
        while '' in line:
            line.remove('')
        self.cpunum = len(line)
        #delt data
        for line in data[1:]:
            line = line.split(' ')
            while '' in line:
                line.remove('')
            if line:
                if 'HI' in line[0]:
                    num = 0
                elif 'TIMER' in line[0] and 'HRTIMER' not in line[0]:
                    num = 1
                elif 'NET_TX' in line[0]:
                    num = 2
                elif 'NET_RX' in line[0]:
                    num = 3
                elif 'BLOCK' in line[0] and 'POLL' not in line[0]:
                    num = 4
                elif 'POLL' in line[0]:#new:IRQ_POLL ,old:BLOCK_IOPOLL
                    num = 5
                elif 'TASKLET' in line[0]:
                    num = 6
                elif 'SCHED' in line[0]:
                    num = 7
                elif 'HRTIMER' in line[0]:
                    num = 8
                elif 'RCU' in line[0]:
                    num = 9
                self.softirq[num] = list(map(int, line[1:]))
        #print(self.softirq)
    
    def diff(self,oldstat):
        if oldstat.cpunum != 0:
            #softirq
            self.diffsoftirq={}
            for softtype in range(0,10):
                tmp = []
                for i in range(0,len(oldstat.softirq[softtype])):  
                    summm=self.softirq[softtype][i] - oldstat.softirq[softtype][i]
                    tmp.append(summm) 
                self.diffsoftirq[softtype] = tmp

    def getdata(self,name,num=0):
        if len(self.diffsoftirq) > 0 :
            if name == 's_hi':
                return self.diffsoftirq[0][num]
            elif name == 's_timer':
                return self.diffsoftirq[1][num]
            elif name == 's_net_tx':
                return self.diffsoftirq[2][num]
            elif name == 's_net_rx':
                return self.diffsoftirq[3][num]
            elif name == 's_block':
                return self.diffsoftirq[4][num]
            elif name == 's_block_iopoll':
                return self.diffsoftirq[5][num]
            elif name == 's_tasklet':
                return self.diffsoftirq[6][num]
            elif name == 's_sched':
                return self.diffsoftirq[7][num]
            elif name == 's_hrtimer':
                return self.diffsoftirq[8][num]
            elif name == 's_rcu':
                return self.diffsoftirq[9][num]
            elif name == 's_softirq':
                return [self.diffsoftirq[0][num],self.diffsoftirq[1][num],self.diffsoftirq[2][num],\
                self.diffsoftirq[3][num],self.diffsoftirq[4][num],self.diffsoftirq[5][num],self.diffsoftirq[6][num],\
                self.diffsoftirq[7][num],self.diffsoftirq[8][num],self.diffsoftirq[9][num]]
        return 0

class irq():
    def __init__(self, **kwargs):
        self.irqnum = ''
        self.data = []
        self.picname = ''
        self.irqname = ''
        self.edge = ''
        self.affinity = 0

class Interrupts():
    def __init__(self, **kwargs):
        self.interrupts = []
        self.diffirq = {}
        self.time = 0
        self.cpunum = 0
        self.irqnum = 0
    
    def update(self):
        self.time = int(time.time() * 1000)
        data = get_procinfo('/proc/interrupts')
        if data == None:
            return
        data = data.split('\n')
        #calc cpu num
        line = data[0].split(' ')
        while '' in line:
            line.remove('')
        self.cpunum = len(line)
        #delt data
        self.interrupts = []
        self.irqnum = 0
        for line in data[1:]:
            line = line.split(' ')
            while '' in line:
                line.remove('')
            if line:
                irqnum = line[0].replace(':','')
                data = list(map(int, line[1:self.cpunum+1]))
                if irqnum.isdigit():
                    self.irqnum += 1
                    picname = line[self.cpunum+1]
                    edge = line[self.cpunum+2]
                    irqname = ''.join(line[self.cpunum+3:])
                    self.interrupts.append({'irqnum':irqnum,'data':data,'picname':picname,'edge':edge,'irqname':irqname})
                else:
                    irqname = ''.join(line[self.cpunum+1:])
                    self.interrupts.append({'irqnum':irqnum,'data':data,'irqname':irqname})
   
    def diff(self,oldstat):
        if oldstat.cpunum != 0:
            #softirq
            self.diffirq={}
            for interrupt in self.interrupts:
                irqnum = interrupt['irqnum']
                if irqnum.isdigit():
                    for oldinterrupt in oldstat.interrupts:
                        if irqnum == oldinterrupt['irqnum']:
                            tmp = []
                            for i in range(self.cpunum):
                                summm=interrupt['data'][i] - oldinterrupt['data'][i]
                                tmp.append(summm) 
                            self.diffirq[irqnum] = tmp
            #print(self.diffirq)


    def getdata(self,name,num=0):
        if len(self.diffirq) > 0 :
            if name.isdigit() :
                return self.diffirq[name][num]
            elif name == 'interrupts':
                return self.diffirq

        return 0

class Thread():
    def __init__(self, **kwargs):
        self.stat = []
        self.maps = []
        self.status = {}
        self.pid = 1
        self.ppid = 0
        self.pgid = 0
        self.sid = 0
        self.VmPeak = None
        self.RssFile = 0
        self.utime = 0
        self.stime = 0
        self.cputime = 0
        self.time = 0
        self.runcpu = 0
        self.comm = ''
        self.major = 0
        self.minor = 0
        self.ctxt = 0
        self.nctxt = 0
        self.fdlist = []
        self.fdnum = 0
        self.leader = 0
        self.children = []
        if kwargs:
            self.pid = kwargs['pid']
            self.leader = kwargs['leader']
    
    def getstat(self):
        self.time = int(time.time() * 1000)
        data = get_procinfo('/proc/%d/task/%d/stat' % (self.leader,self.pid))
        if data == None:
            return 
        data=data[:-1]                   #去除回车
        first_parenthesis = data.find('(')
        last_parenthesis = data.rfind(')')
        temp = data[last_parenthesis+2:]
        self.stat.append(int(data[0:first_parenthesis-1]))   #获取pid
        self.stat.append(data[first_parenthesis+1:last_parenthesis]) #获取进程名
        self.stat.extend(temp.split(' ')) #列表加列表需要使用extend
        #print(self.stat)
        self.utime = int(self.stat[13])
        self.stime = int(self.stat[14])
        self.cputime = self.utime + self.stime
        self.runcpu = int(self.stat[38])
        self.comm = self.stat[1]
        self.major = int(self.stat[11])
        self.minor = int(self.stat[9])
        self.nr_threads = int(self.stat[19])
        #self.cputime = pow(self.cputime, 1/3)
        return self.stat

    def getcomm(self):
        data = get_procinfo('/proc/%d/task/%d/comm' % (self.leader,self.pid))
        return self.comm

    def getcmdline(self):
        data = get_procinfo('/proc/%d/task/%d/cmdline' % (self.leader,self.pid))
        return self.cmdline

    def getenviron(self):
        data = get_procinfo('/proc/%d/task/%d/environ' % (self.leader,self.pid))
        return self.environ

    def getfd(self):
        data = get_procinfo('/proc/%d/task/%d/fd' % (self.leader,self.pid))
        lists = outputs.split('\n')
        self.fdlist = lists
        self.fdnum = len(self.fdlist)

    def getstatus(self):
        data = get_procinfo('/proc/%d/task/%d/status' % (self.leader,self.pid))
        if data == None:
            return
        data = data.split('\n')
        for line in data:
            if line:
                line=line.replace('\t','')
                line=line.split(':')
                self.status[line[0]] = line[1]
                if line[0] == 'VmPeak':
                    self.VmPeak = int(self.status['VmPeak'].replace('kB',''))*1024
                elif line[0] == 'VmSize':
                    self.VmSize = int(self.status['VmSize'].replace('kB',''))*1024
                elif line[0] == 'VmHWM':
                    self.VmHWM = int(self.status['VmHWM'].replace('kB',''))*1024
                elif line[0] == 'VmRSS':
                    self.VmRSS = int(self.status['VmRSS'].replace('kB',''))*1024
                elif line[0] == 'VmData':
                    self.VmData = int(self.status['VmData'].replace('kB',''))*1024
                elif line[0] == 'VmStk':
                    self.VmStk = int(self.status['VmStk'].replace('kB',''))*1024
                elif line[0] == 'VmLck':
                    self.VmLck = int(self.status['VmLck'].replace('kB',''))*1024
                elif line[0] == 'VmPin':
                    self.VmPin = int(self.status['VmPin'].replace('kB',''))*1024
                elif line[0] == 'VmExe':
                    self.VmExe = int(self.status['VmExe'].replace('kB',''))*1024
                elif line[0] == 'VmLib':
                    self.VmLib = int(self.status['VmLib'].replace('kB',''))*1024
                elif line[0] == 'VmPTE':
                    self.VmPTE = int(self.status['VmPTE'].replace('kB',''))*1024
                elif line[0] == 'VmSwap':
                    self.VmSwap = int(self.status['VmSwap'].replace('kB',''))*1024
                elif line[0] == 'voluntary_ctxt_switches':
                    self.ctxt = int(self.status['voluntary_ctxt_switches'])
                elif line[0] == 'nonvoluntary_ctxt_switches':
                    self.nctxt = int(self.status['nonvoluntary_ctxt_switches'])
        if self.VmPeak:
            return [self.VmSize,self.VmStk,self.VmData,self.VmLib,self.VmExe,self.utime,self.stime,self.VmRSS]

    def getstatm(self):
        data = get_procinfo('/proc/%d/task/%d/statm' % (self.leader,self.pid))
        if data == None:
            return
        data = data.split(' ')
        self.RssFile = int(data[2]) * 4096   #这里假设页大小为4096
        print(self.RssFile)

    def getmaps(self):
        data = get_procinfo('/proc/%d/task/%d/maps' % (self.leader,self.pid))
        if data == None:
            return
        data = data.split('\n')
        for line in data:
            if line:
                line=line.split(' ')
                while '' in line:
                    line.remove('')
                self.maps.append(line)
        print(self.maps)

    def getchildren(self):
        data = get_procinfo('/proc/%d/task/%d/children' % (self.leader,self.pid))
        if data == None:
            return
        data = data.split(' ')
        while '' in data:
            data.remove('')
        self.children = list(map(int, data))
        print(self.children)

class Process():
    def __init__(self, **kwargs):
        self.stat = []
        self.maps = []
        self.status = {}
        self.pid = 1
        self.ppid = 0
        self.pgid = 0
        self.sid = 0
        self.VmPeak = None
        self.RssFile = 0
        self.utime = 0
        self.stime = 0
        self.cputime = 0
        self.time = 0
        self.runcpu = 0
        self.comm = ''
        self.major = 0
        self.minor = 0
        self.ctxt = 0
        self.nctxt = 0
        self.fdlist = []
        self.fdnum = 0
        self.nr_threads = 0
        self.threads = {}
        if kwargs:
            self.pid = kwargs['pid']
    
    def getstat(self):
        self.time = int(time.time() * 1000)
        data = get_procinfo('/proc/%d/stat' % (self.pid))
        if data == None:
            return 
        data=data[:-1]                   #去除回车
        first_parenthesis = data.find('(')
        last_parenthesis = data.rfind(')')
        temp = data[last_parenthesis+2:]
        self.stat.append(int(data[0:first_parenthesis-1]))   #获取pid
        self.stat.append(data[first_parenthesis+1:last_parenthesis]) #获取进程名
        self.stat.extend(temp.split(' ')) #列表加列表需要使用extend
        #print(self.stat)
        self.ppid  = int(self.stat[3])
        self.utime = int(self.stat[13])
        self.stime = int(self.stat[14])
        self.cputime = self.utime + self.stime
        self.runcpu = int(self.stat[38])
        self.comm = self.stat[1]
        self.major = int(self.stat[11])
        self.minor = int(self.stat[9])
        self.nr_threads = int(self.stat[19])
        #self.cputime = pow(self.cputime, 1/3)
        return self.stat

    def getcomm(self):
        self.comm = get_procinfo('/proc/%d/comm' % (self.pid))
        return self.comm

    def getcmdline(self):
        self.cmdline = get_procinfo('/proc/%d/cmdline' % (self.pid))
        return self.cmdline

    def getenviron(self):
        self.environ = get_procinfo('/proc/%d/environ' % (self.pid))
        return self.environ

    def getfd(self):
        outputs = get_cmdout('ls /proc/%d/fd' % (self.pid)) 
        lists = outputs.split('\n')
        self.fdlist = lists
        self.fdnum = len(self.fdlist)

    def getstatus(self):
        data = get_procinfo('/proc/%d/status' % (self.pid))
        if data == None:
            return
        data = data.split('\n')
        for line in data:
            if line:
                line=line.replace('\t','')
                line=line.split(':')
                self.status[line[0]] = line[1]
                if line[0] == 'VmPeak':
                    self.VmPeak = int(self.status['VmPeak'].replace('kB',''))*1024
                elif line[0] == 'VmSize':
                    self.VmSize = int(self.status['VmSize'].replace('kB',''))*1024
                elif line[0] == 'VmHWM':
                    self.VmHWM = int(self.status['VmHWM'].replace('kB',''))*1024
                elif line[0] == 'VmRSS':
                    self.VmRSS = int(self.status['VmRSS'].replace('kB',''))*1024
                elif line[0] == 'VmData':
                    self.VmData = int(self.status['VmData'].replace('kB',''))*1024
                elif line[0] == 'VmStk':
                    self.VmStk = int(self.status['VmStk'].replace('kB',''))*1024
                elif line[0] == 'VmLck':
                    self.VmLck = int(self.status['VmLck'].replace('kB',''))*1024
                elif line[0] == 'VmPin':
                    self.VmPin = int(self.status['VmPin'].replace('kB',''))*1024
                elif line[0] == 'VmExe':
                    self.VmExe = int(self.status['VmExe'].replace('kB',''))*1024
                elif line[0] == 'VmLib':
                    self.VmLib = int(self.status['VmLib'].replace('kB',''))*1024
                elif line[0] == 'VmPTE':
                    self.VmPTE = int(self.status['VmPTE'].replace('kB',''))*1024
                elif line[0] == 'VmSwap':
                    self.VmSwap = int(self.status['VmSwap'].replace('kB',''))*1024
                elif line[0] == 'voluntary_ctxt_switches':
                    self.ctxt = int(self.status['voluntary_ctxt_switches'])
                elif line[0] == 'nonvoluntary_ctxt_switches':
                    self.nctxt = int(self.status['nonvoluntary_ctxt_switches'])
        if self.VmPeak:
            return [self.VmSize,self.VmStk,self.VmData,self.VmLib,self.VmExe,self.utime,self.stime,self.VmRSS]

    def getstatm(self):
        data = get_procinfo('/proc/%d/statm' % (self.pid))
        data = data.split(' ')
        self.RssFile = int(data[2]) * 4096   #这里假设页大小为4096
        print(self.RssFile)

    def getmaps(self):
        data = get_procinfo('/proc/%d/maps' % (self.pid))
        if data == None:
            return
        data = data.split('\n')
        for line in data:
            if line:
                line=line.split(' ')
                while '' in line:
                    line.remove('')
                self.maps.append(line)
        print(self.maps)

    def getthreads(self):
        self.threadcnt = 0
        outputs = get_cmdout('ls /proc/%d/task' % (self.pid)) 
        lists = outputs.split('\n')
        print(lists)
        for list in lists:
            if list.isdigit():
                thread = Thread(pid = int(list),leader = self.pid)
                ret = thread.getstat()
                self.threadcnt += 1
                if ret:
                    thread.getstatus()
                    thread.getchildren()
                    self.threads[thread.pid] = thread
        print("total thread %d"%(self.threadcnt))

class Processes():
    def __init__(self, **kwargs):
        self.pidcnt = 0   #进程总数，/proc/pid是不包括线程的
        self.threadcnt = 0   #线程总数
        self.process_dict = {}
        self.thread_dict = {}
        self.ordered = []
        self.diffcpu = {}
        self.diffprocess = {}
        self.diffmem = {}
        self.diffmajor = {}
        self.diffminor = {}
        self.diffctxt = {}
        self.diffnctxt = {}
        self.time = 0
        if kwargs:
            pass

    def scan(self):
        self.time = int(time.time() * 1000)
        self.pidcnt = 0
        outputs = get_cmdout('ls /proc/') 
        lists = outputs.split('\n')
        #print(lists)
        for list in lists:
            if list.isdigit():
                process = Process(pid = int(list))
                ret = process.getstat()
                self.pidcnt += 1
                if ret:
                    process.getstatus()
                    self.process_dict[process.pid] = process
        print("total process %d"%(self.pidcnt))
        self.stat = Stat()
        self.stat.getstat()
        return self.process_dict

    def scanthread(self):
        self.time = int(time.time() * 1000)
        self.threadcnt = 0
        outputs = get_cmdout('ls /proc/') 
        lists = outputs.split('\n')
        #print(lists)
        for list in lists:
            if list.isdigit():
                outputs = get_cmdout('ls /proc/%s/task/'%(list)) 
                if outputs == None:
                    print('ls /proc/%s/task/ is none '%(list))
                else:
                    thread_lists = outputs.split('\n')
                    for thread_list in thread_lists:
                        if thread_list != '':
                            thread = Thread(pid = int(thread_list),leader = int(list))
                            ret = thread.getstat()
                            self.threadcnt += 1
                            if ret:
                                thread.getstatus()
                                thread.getchildren()
                                self.thread_dict[thread.pid] = thread
        print("total thread %d"%(self.threadcnt))
        self.stat = Stat()
        self.stat.getstat()
        return self.thread_dict

    def diff(self,oldstat):
        if oldstat.pidcnt != 0:
            self.stat.diff(oldstat.stat)
            self.diffcpu = self.stat.difftotal_cputime
            print(self.diffcpu)
            
            nr_thread = 0
            for key in self.process_dict:
                if key in oldstat.process_dict:
                    difftime = self.process_dict[key].cputime - oldstat.process_dict[key].cputime
                    if difftime != 0:
                        self.diffprocess[key] = [round(difftime*100/self.diffcpu[self.process_dict[key].runcpu],2), self.process_dict[key].runcpu,self.process_dict[key].comm]
                    diffmaj = self.process_dict[key].major - oldstat.process_dict[key].major
                    if diffmaj != 0:
                        self.diffmajor[key] = [diffmaj,self.process_dict[key].comm]
                    diffminor = self.process_dict[key].minor- oldstat.process_dict[key].minor
                    if diffminor != 0:
                        self.diffminor[key] = [diffminor,self.process_dict[key].comm]
                    diffctxt = self.process_dict[key].ctxt- oldstat.process_dict[key].ctxt
                    if diffctxt > 10:  #将小于10的过滤掉，否则显示太多
                        self.diffctxt[key] = [diffctxt,self.process_dict[key].comm]
                    diffnctxt = self.process_dict[key].nctxt- oldstat.process_dict[key].nctxt
                    if diffnctxt != 0:
                        self.diffnctxt[key] = [diffnctxt,self.process_dict[key].comm]
                    if self.process_dict[key].VmPeak:
                        diffvss = self.process_dict[key].VmRSS- oldstat.process_dict[key].VmRSS
                        if diffvss != 0:
                            self.diffmem[key] = [self.process_dict[key].VmRSS, self.process_dict[key].comm]
                    nr_thread += int(self.process_dict[key].stat[19])
            #print(self.diffprocess)
            #print(self.diffmajor)
            #print(self.diffminor)
            #print(self.diffctxt)
            #print(self.diffnctxt)
            #print(self.diffmem)

    def getdata(self,name,num=0):
        return 0

    def gengv(self):
        fh = open('app/static/pstree', 'w')
        fh.write("digraph ptree {\n node [ style = filled ];\n")
        for key in self.process_dict:
            if self.process_dict[key].stat[40] == '0':
                color = '#96cdcd3f'
            elif self.process_dict[key].stat[40] == '1':
                color = '#cdaf953f'
            elif self.process_dict[key].stat[40] == '2':
                color = '#7ccd7c3f'
            elif self.process_dict[key].stat[40] == '3':
                color = '#ffa07a3f'
            elif self.process_dict[key].stat[40] == '5':
                color = '#6ca6cd3f'
            else:
                color = '#FFFFFFFF'
            fh.write("    \"%s\" -> \"%s\" [ ];\n"%(self.process_dict[key].stat[3],self.process_dict[key].stat[0]))
            fh.write("    \"%s\" [ label = \"%s\" color = \"%s\" ];\n"%(self.process_dict[key].stat[0],self.process_dict[key].stat[1],color))
        fh.write("}")
        fh.close()
        os.system("neato -Tsvg -Nfontsize=12 -Elen=1.9 app/static/pstree -o app/static/pstree.svg")

    def gengexf(self):
        pass

    def gengraphviz(self):
        dot = gv.Digraph(comment='process tree', engine='dot', format='svg') #首行注释,layout,输出格式
        dot.graph_attr['rankdir'] = 'LR'
        dot.attr('node', style='filled')
        for key in self.process_dict:
            if self.process_dict[key].stat[40] == '0':
                color = '#96cdcd3f'
            elif self.process_dict[key].stat[40] == '1':
                color = '#cdaf953f'
            elif self.process_dict[key].stat[40] == '2':
                color = '#7ccd7c3f'
            elif self.process_dict[key].stat[40] == '3':
                color = '#ffa07a3f'
            elif self.process_dict[key].stat[40] == '5':
                color = '#6ca6cd3f'
            else:
                color = '#FFFFFFFF'

            if self.process_dict[key].nr_threads > 1:
                cmdline = self.process_dict[key].getcmdline()
                dot.node('p'+str(self.process_dict[key].stat[0]), \
                    cmdline.replace('\x00','\n'), color = color,shape='box')
                dot.edge(self.process_dict[key].stat[3], 'p'+str(self.process_dict[key].stat[0]))
                self.process_dict[key].getthreads()
                for th in self.process_dict[key].threads:
                    if self.process_dict[key].threads[th].stat[40] == '0':
                        pcolor = '#96cdcd3f'
                    elif self.process_dict[key].threads[th].stat[40] == '1':
                        pcolor = '#cdaf953f'
                    elif self.process_dict[key].threads[th].stat[40] == '2':
                        pcolor = '#7ccd7c3f'
                    elif self.process_dict[key].threads[th].stat[40] == '3':
                        pcolor = '#ffa07a3f'
                    elif self.process_dict[key].threads[th].stat[40] == '5':
                        pcolor = '#6ca6cd3f'
                    else:
                        pcolor = '#FFFFFFFF'
                    dot.node(str(self.process_dict[key].threads[th].stat[0]),\
                     self.process_dict[key].threads[th].stat[1]+'('+str(self.process_dict[key].threads[th].stat[0])+')',\
                     color = pcolor,shape='proteinstab')
                    dot.edge('p'+str(self.process_dict[key].stat[0]), str(self.process_dict[key].threads[th].stat[0]))
                    if self.process_dict[key].stat[3] != self.process_dict[key].threads[th].stat[3]:
                        print('errrrrrrrrrrrrrrrrrrrrrrrror')
            else:
                dot.node(str(self.process_dict[key].stat[0]), \
                    self.process_dict[key].stat[1]+'('+str(self.process_dict[key].stat[0])+')',\
                    color = color,shape='ellipse')
                dot.edge(self.process_dict[key].stat[3], str(self.process_dict[key].stat[0]))

        #print(dot.source) 
        dot.render('app/static/pstree')

class Meminfo():
    def __init__(self, **kwargs):
        self.MemTotal = []
        self.meminfo = {}
        self.time = 0

    def update(self):
        self.time = int(time.time() * 1000)
        data = get_procinfo('/proc/meminfo')
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


class ScanTimer():
    timer = None
    intval = 1

    def start(self):
        self.scan_process()
        timer = threading.Timer(self.intval, self.start)
        timer.start()

    def scan_process(self):
        ctx=app.app_context()  
        ctx.push() 
        #loadavg
        if not hasattr(current_app,'g_loadavg'):
            current_app.g_loadavg = RecordDate()
        loadavg = Loadavg()
        loadavg.update()
        current_app.g_loadavg.add(loadavg)
        
        #stat
        if not hasattr(current_app,'g_stat'):
            current_app.g_stat = RecordDate()
        newstat = Stat()
        newstat.getstat()
        current_app.g_cpunum = newstat.cpunum
        if len(current_app.g_stat.data) > 0:
            newstat.diff(current_app.g_stat.data[-1])
        current_app.g_stat.add(newstat)
        
        #softirqs
        if not hasattr(current_app,'g_softirqs'):
            current_app.g_softirqs = RecordDate()
        newsoftirqs = Softirqs()
        newsoftirqs.update()
        if len(current_app.g_softirqs.data) > 0:
            newsoftirqs.diff(current_app.g_softirqs.data[-1])
        current_app.g_softirqs.add(newsoftirqs)
        
        #interrupts
        if not hasattr(current_app,'g_interrupts'):
            current_app.g_interrupts = RecordDate()
        newinterrupts = Interrupts()
        newinterrupts.update()
        if len(current_app.g_interrupts.data) > 0:
            newinterrupts.diff(current_app.g_interrupts.data[-1])
        current_app.g_interrupts.add(newinterrupts)
        
        #processes
        if not hasattr(current_app,'g_processes'):
            current_app.g_processes = RecordDate()
        newprocesses = Processes()
        newprocesses.scan()
        if len(current_app.g_processes.data) > 0:
            newprocesses.diff(current_app.g_processes.data[-1])
        current_app.g_processes.add(newprocesses)
        
        #meminfo
        if not hasattr(current_app,'g_meminfo'):
            current_app.g_meminfo = RecordDate()
        newmeminfo = Meminfo()
        newmeminfo.update()
        current_app.g_meminfo.add(newmeminfo)

        #uptime
        if not hasattr(current_app,'g_uptime'):
            current_app.g_uptime = RecordDate()
        newuptime = Uptime()
        newuptime.update()
        current_app.g_uptime.add(newuptime)
        
        ctx.pop() 