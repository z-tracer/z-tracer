import os
import time
import graphviz as gv
from .cpu import Stat

class Thread():
    def __init__(self, zclient, **kwargs):
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
        self.zclient = zclient
        if kwargs:
            self.pid = kwargs['pid']
            self.leader = kwargs['leader']
    
    def getstat(self):
        self.time = int(time.time() * 1000)
        data = self.zclient.get_procinfo('/proc/%d/task/%d/stat' % (self.leader,self.pid))
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
        data = self.zclient.get_procinfo('/proc/%d/task/%d/comm' % (self.leader,self.pid))
        return self.comm

    def getcmdline(self):
        data = self.zclient.get_procinfo('/proc/%d/task/%d/cmdline' % (self.leader,self.pid))
        return self.cmdline

    def getenviron(self):
        data = self.zclient.get_procinfo('/proc/%d/task/%d/environ' % (self.leader,self.pid))
        return self.environ

    def getfd(self):
        data = self.zclient.get_procinfo('/proc/%d/task/%d/fd' % (self.leader,self.pid))
        lists = outputs.split('\n')
        self.fdlist = lists
        self.fdnum = len(self.fdlist)

    def getstatus(self):
        data = self.zclient.get_procinfo('/proc/%d/task/%d/status' % (self.leader,self.pid))
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
        data = self.zclient.get_procinfo('/proc/%d/task/%d/statm' % (self.leader,self.pid))
        if data == None:
            return
        data = data.split(' ')
        self.RssFile = int(data[2]) * 4096   #这里假设页大小为4096
        print(self.RssFile)

    def getmaps(self):
        data = self.zclient.get_procinfo('/proc/%d/task/%d/maps' % (self.leader,self.pid))
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
        data = self.zclient.get_procinfo('/proc/%d/task/%d/children' % (self.leader,self.pid))
        if data == None:
            return
        data = data.split(' ')
        while '' in data:
            data.remove('')
        self.children = list(map(int, data))
        print(self.children)

class Process():
    def __init__(self, zclient,**kwargs):
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
        self.zclient = zclient
        if kwargs:
            self.pid = kwargs['pid']
    
    def getstat(self):
        self.time = int(time.time() * 1000)
        data = self.zclient.get_procinfo('/proc/%d/stat' % (self.pid))
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
        self.comm = self.zclient.get_procinfo('/proc/%d/comm' % (self.pid))
        return self.comm

    def getcmdline(self):
        self.cmdline = self.zclient.get_procinfo('/proc/%d/cmdline' % (self.pid))
        return self.cmdline

    def getenviron(self):
        self.environ = self.zclient.get_procinfo('/proc/%d/environ' % (self.pid))
        return self.environ

    def getfd(self):
        outputs = self.zclient.get_cmdout('ls /proc/%d/fd' % (self.pid)) 
        if outputs:
            lists = outputs.split('\n')
            self.fdlist = lists
            self.fdnum = len(self.fdlist)

    def getstatus(self):
        data = self.zclient.get_procinfo('/proc/%d/status' % (self.pid))
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
        data = self.zclient.get_procinfo('/proc/%d/statm' % (self.pid))
        if data == None:
            return
        data = data.split(' ')
        self.RssFile = int(data[2]) * 4096   #这里假设页大小为4096
        print(self.RssFile)

    def getmaps(self):
        data = self.zclient.get_procinfo('/proc/%d/maps' % (self.pid))
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
        outputs = self.zclient.get_cmdout('ls /proc/%d/task' % (self.pid))
        if outputs == None:
            return 
        lists = outputs.split('\n')
        print(lists)
        for list in lists:
            if list.isdigit():
                thread = Thread(self.zclient,pid = int(list),leader = self.pid)
                ret = thread.getstat()
                self.threadcnt += 1
                if ret:
                    thread.getstatus()
                    thread.getchildren()
                    self.threads[thread.pid] = thread
        print("total thread %d"%(self.threadcnt))

class Processes():
    def __init__(self,zclient,**kwargs):
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
        self.zclient = zclient
        if kwargs:
            pass

    def scan(self):
        self.time = int(time.time() * 1000)
        self.pidcnt = 0
        outputs = self.zclient.get_cmdout('ls /proc/') 
        if outputs == None:
            return None
        lists = outputs.split('\n')
        #print(lists)
        for list in lists:
            if list.isdigit():
                process = Process(self.zclient, pid = int(list))
                ret = process.getstat()
                self.pidcnt += 1
                if ret:
                    process.getstatus()
                    self.process_dict[process.pid] = process
        #print("total process %d"%(self.pidcnt))
        self.stat = Stat(self.zclient)
        self.stat.update()
        return self.process_dict

    def scanthread(self):
        self.time = int(time.time() * 1000)
        self.threadcnt = 0
        outputs = self.zclient.get_cmdout('ls /proc/')
        if outputs == None:
            return None
        lists = outputs.split('\n')
        #print(lists)
        for list in lists:
            if list.isdigit():
                outputs = self.zclient.get_cmdout('ls /proc/%s/task/'%(list)) 
                if outputs == None:
                    print('ls /proc/%s/task/ is none '%(list))
                else:
                    thread_lists = outputs.split('\n')
                    for thread_list in thread_lists:
                        if thread_list != '':
                            print(thread_lists)
                            thread = Thread(self.zclient, pid = int(thread_list),leader = int(list))
                            ret = thread.getstat()
                            self.threadcnt += 1
                            if ret:
                                thread.getstatus()
                                thread.getchildren()
                                self.thread_dict[thread.pid] = thread
        print("total thread %d"%(self.threadcnt))
        self.stat = Stat(self.zclient)
        self.stat.update()
        return self.thread_dict

    def diff(self,oldstat):
        if oldstat.pidcnt != 0:
            self.stat.diff(oldstat.stat)
            self.diffcpu = self.stat.difftotal_cputime
            #print(self.diffcpu)
            
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
        fh = open('app/static/cache/pstree', 'w')
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
        os.system("neato -Tsvg -Nfontsize=12 -Elen=1.9 app/static/cache/pstree -o app/static/cache/pstree.svg")

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
        dot.render('app/static/cache/pstree')
