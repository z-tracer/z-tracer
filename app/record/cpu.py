import pygal
import time

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

    def __init__(self, zclient,**kwargs):
        self.load1 = 0 
        self.load5 = 0
        self.load15 = 0
        self.time = 0
        self.nr_threads = 0  #所有进程线程总数
        self.zclient = zclient

    def update(self):
        self.time = int(time.time() * 1000)
        data = self.zclient.get_procinfo('/proc/loadavg')
        if data == None:
            return 0
        data = data.split(' ')
        self.load1 = float(data[0])
        self.load5 = float(data[1])
        self.load15 = float(data[2])
        self.rec.add(0,self.load1)
        self.rec.add(1,self.load5)
        self.rec.add(2,self.load15)
        ind = data[3].find('/')
        self.nr_threads = int(data[3][ind+1:])
        return 1
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
    def __init__(self, zclient, **kwargs):
        self.uptime = 0  #系统启动以来的时间
        self.idletime = 0 #所有cpu空闲时间之和
        self.zclient = zclient

    def update(self):
        self.time = int(time.time() * 1000)
        data = self.zclient.get_procinfo('/proc/uptime')
        if data == None:
            return 0
        data = data.split(' ')
        self.uptime = float(data[0])
        self.idletime = float(data[1])
        return 1

    def getdata(self,name,num=1):
        if name == 'uptime':
            return self.uptime
        elif name == 'idletime':
            return self.idletime/num
        else:
            return [self.uptime,self.idletime/num]

class Stat():
    def __init__(self, zclient, **kwargs):
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
        self.zclient = zclient

    def update(self):
        self.time = int(time.time() * 1000)
        data = self.zclient.get_procinfo('/proc/stat')
        if data == None:
            return 0
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
        return 1

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
    def __init__(self, zclient,**kwargs):
        self.softirq = {}
        self.diffsoftirq = {}
        self.time = 0
        self.cpunum = 0
        self.zclient = zclient

    def update(self):
        self.time = int(time.time() * 1000)
        data = self.zclient.get_procinfo('/proc/softirqs')
        if data == None:
            return 0
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
        return 1

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
    def __init__(self, zclient,**kwargs):
        self.interrupts = []
        self.diffirq = {}
        self.time = 0
        self.cpunum = 0
        self.irqnum = 0
        self.zclient = zclient

    def update(self):
        self.time = int(time.time() * 1000)
        data = self.zclient.get_procinfo('/proc/interrupts')
        if data == None:
            return 0
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
        return 1

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


