import re
import copy
import graphviz as gv

class FuncNode():
    def __init__(self):
        self.name = ''
        self.calltime = 0
        self.rettime = 0
        self.duration = 0
        self.maxtime = 0
        self.mintime = 0
        self.count = 0
        self.sumtime = 0
        self.depth = 0

class Stack():
    def __init__(self):
        self.funkstack = []
        self.len = 0
        self.hit = 0
        self.maxdepth = {}

    def compare(self, stack):
        #print('compare:',self.len,stack.len)
        if self.len == stack.len:
            for i in range(self.len):
                if stack.funkstack[i].name != self.funkstack[i].name:
                    return 0
            return 1
        return 0

    def merge(self, stack):
        self_i = 0
        stack_i = 0
        slen = 0
        topstack = []
        #print('merge:',self.len,stack.len)
        if self.len == 0:
            self.hit = 1
            self.funkstack = copy.deepcopy(stack.funkstack)
            self.len = stack.len
            return

        while self_i < self.len or stack_i < stack.len:
            if self_i < self.len and stack_i < stack.len:
                if stack.funkstack[stack_i].name == self.funkstack[self_i].name and \
                stack.funkstack[stack_i].depth == self.funkstack[self_i].depth:
                    self.funkstack[self_i].count += 1
                    self.funkstack[self_i].sumtime += stack.funkstack[stack_i].duration
                    topstack.append(copy.deepcopy(self.funkstack[self_i]))
                    stack_i += 1
                    self_i += 1
                else:
                    if stack.funkstack[stack_i].depth > self.funkstack[self_i].depth:
                        topstack.append(copy.deepcopy(stack.funkstack[stack_i]))
                        stack_i += 1
                    elif stack.funkstack[stack_i].depth < self.funkstack[self_i].depth:
                        topstack.append(copy.deepcopy(self.funkstack[self_i]))
                        self_i += 1
                    else:
                        stack_new = 0
                        for i in stack.funkstack:   #stack has new
                            if i.name == self.funkstack[self_i].name:
                                stack_new = 1
                        if stack_new == 1:
                            topstack.append(copy.deepcopy(stack.funkstack[stack_i]))
                            stack_i += 1
                        else:
                            topstack.append(copy.deepcopy(self.funkstack[self_i]))
                            self_i += 1
            else:
                if self_i < self.len:
                    topstack.append(copy.deepcopy(self.funkstack[self_i]))
                    self_i += 1
                elif stack_i < stack.len:
                    topstack.append(copy.deepcopy(stack.funkstack[stack_i]))
                    stack_i += 1
            slen += 1
        self.funkstack = topstack
        self.len = slen
        self.hit += 1

    def foldstack(self, stack):
        funcstack = stack
        #for f in funcstack:
        #    print((f.depth*' ')+f.name,f.count,round(f.sumtime,2),'us befor')
        length = len(funcstack)
        if length > 1:
            for depth in range(20, 0, -1):
                foldbegin = 1
                while foldbegin < length:
                    if funcstack[foldbegin].depth == depth:
                        for matchbegin in range(foldbegin-1, 0, -1):
                            if funcstack[matchbegin].name == funcstack[foldbegin].name: #加上不支持递归 and funcstack[matchbegin].depth == funcstack[foldbegin].depth:
                                #print('find matchbegin',matchbegin,foldbegin)
                                match = 1
                                for index in range(0, foldbegin - matchbegin):
                                    if index >= length - foldbegin:
                                        match = 0
                                        break
                                    if funcstack[matchbegin + index].name != funcstack[foldbegin + index].name: #加上不支持递归 or funcstack[matchbegin + index].depth != funcstack[foldbegin + index].depth:
                                        match = 0
                                        break
                                if match == 1:
                                    #print('matchend',index)
                                    for index in range(0, foldbegin - matchbegin):
                                        funcstack[matchbegin + index].count += funcstack[foldbegin].count
                                        funcstack[matchbegin + index].sumtime += funcstack[foldbegin].sumtime
                                        funcstack.pop(foldbegin)
                                    length = length - (foldbegin - matchbegin)
                                    foldbegin -= 1
                    foldbegin += 1
        #for fun in funcstack:
        #    print((fun.depth*' ')+fun.name,fun.count,round(fun.sumtime,2),'us after')

    def print(self):
        print("*********************************stack*********************************************")
        print('merge len and times', self.len, self.hit)
        for fun in self.funkstack:
            print((fun.depth*' ')+fun.name, fun.count, round(fun.sumtime, 2), 'us')

    def gengraphviz(self):
        dot = gv.Digraph(comment='function tree', engine='dot', format='svg')
        dot.graph_attr['rankdir'] = 'LR'
        dot.attr('node', style='filled')
        depthfunc = {}
        for index in range(self.len):
            depthfunc[self.funkstack[index].depth] = index
            if index == self.maxdepth[self.funkstack[index].depth]:
                color = '#ff0033'
            else:
                color = '#96cdcd3f'
            if self.funkstack[index].count >= 0:
                dot.node(str(index), self.funkstack[index].name+'('+ str(round(self.funkstack[index].sumtime, 2))+'us)', color=color, shape='ellipse')
                if self.funkstack[index].depth > 0:
                    dot.edge(str(depthfunc[self.funkstack[index].depth-1]), str(index))
        dot.render('app/static/cache/functree')
        print("generate app/static/cache/functree.svg")

    def findmax(self):
        for index in range(self.len):
            if self.funkstack[index].depth in self.maxdepth:
                if self.funkstack[index].sumtime > self.funkstack[self.maxdepth[self.funkstack[index].depth]].sumtime:
                    self.maxdepth[self.funkstack[index].depth] = index
            else:
                self.maxdepth[self.funkstack[index].depth] = index
        print(self.maxdepth)

STACKLIST = []
LATENCYLIST = []
LATENCY_MAX = 0
LATENCY_MIN = None
STACKTOP = Stack()

class PidFunc():
    def __init__(self, pid, cmdline):
        self.walkstack = []
        self.pid = pid
        self.cmdline = cmdline
        self.len = 0
        self.drop = 0
        self.inprocess = 0
        self.stacklist = []
        self.latencylist = []
        self.count = 0
        self.runtime = 0
        self.stacknum = 0
        self.maxtime = 0
        self.mintime = 0
        self.avgtime = 0
        self.laststack = None
        self.lastlatency = None

    def walkstart(self):
        self.inprocess = 1
        self.len = 0

    def walkend(self):
        self.inprocess = 0

    def iswalk(self):
        return self.inprocess

    def walkreset(self):
        self.len = 0
        self.walkstack = []

    def add(self, funcname, depth, timestamp, duration):
        funcnode = FuncNode()
        funcnode.calltime = timestamp
        funcnode.name = funcname
        funcnode.depth = depth
        funcnode.duration = duration
        self.len += 1
        self.walkstack.append(funcnode)
        if duration is not None:
            funcnode.count += 1
            funcnode.sumtime += duration
            if depth == 0:
                self.commit()
                self.addtotop()
                self.walkend()
                self.walkreset()

    def addend(self, funcname, depth, timestamp, duration):
        for funcnode in reversed(self.walkstack):
            if funcnode.depth == depth:
                if funcnode.duration is not None:
                    print('wrong already have duration', funcnode.name, funcnode.duration)
                    continue
                funcnode.duration = duration
                funcnode.rettime = timestamp
                funcnode.sumtime += duration
                funcnode.count += 1
                break;
        if depth == 0:
            self.commit()
            self.addtotop()
            self.walkend()
            self.walkreset()

    def addtotop(self):
        global LATENCY_MAX
        global LATENCY_MIN
        global LATENCYLIST
        global STACKLIST
        global STACKTOP
        if LATENCY_MAX < self.lastlatency[1]:
            LATENCY_MAX = self.lastlatency[1]
        if LATENCY_MIN is None:
            LATENCY_MIN = self.lastlatency[1]
        elif LATENCY_MIN > self.lastlatency[1]:
            LATENCY_MIN = self.lastlatency[1]
        LATENCYLIST.append(self.lastlatency)
        has = 0
        for i in STACKLIST:
            if i.compare(self.laststack) == 1:
                has = 1
                i.merge(self.laststack)
                break
        if has == 0:
            STACKLIST.append(copy.deepcopy(self.laststack))
        STACKTOP.merge(self.laststack)

    def commit(self):
        for funcnode in reversed(self.walkstack):
            if funcnode.duration is None:
                self.drop += 1
                print(funcnode.name+" did not have end time", funcnode.calltime)
        #print('stack befor fold len=',self.len)
        self.laststack = Stack()
        self.laststack.foldstack(self.walkstack)
        self.len = len(self.walkstack)
        self.laststack.len = self.len
        self.laststack.hit = 1
        self.laststack.funkstack = self.walkstack
        #print('stack after fold len=',self.len)
        self.lastlatency = [self.laststack.funkstack[0].calltime, self.laststack.funkstack[0].duration]
        self.latencylist.append(self.lastlatency)
        has = 0
        for i in self.stacklist:
            if i.compare(self.laststack) == 1:
                has = 1
                i.merge(self.laststack)
                break
        if has == 0:
            self.stacklist.append(self.laststack)

    def stat(self):
        print("*********************************Pidfun************************************************")
        print("pid %d has %d stacks, droped %d stack"%(self.pid, len(self.stacklist), self.drop))
        print("hit %d"%(len(self.latencylist)))
        print(self.latencylist)
        for stack in self.stacklist:
            stack.print()

    def calc(self):
        self.count = len(self.latencylist)
        self.stacknum = len(self.stacklist)
        self.runtime = 0
        for latency in self.latencylist:
            self.runtime += latency[1]
            if self.maxtime < latency[1]:
                self.maxtime = latency[1]
            if self.mintime == 0:
                self.mintime = latency[1]
            elif self.mintime > latency[1]:
                self.mintime = latency[1]
        if self.count != 0:
            self.avgtime = self.runtime / self.count
        return [self.cmdline, self.stacknum, self.count, round(self.runtime, 2), round(self.avgtime, 2), round(self.maxtime, 2), round(self.mintime, 2)]

class Ftrace():
    def __init__(self, zclient):
        self.zclient = zclient
        self.basedir = "/sys/kernel/debug/tracing/"
        self.tracedata = ''
        self.piddict = {}
        self.available_functions = []

    def makecmd(self, file, val):
        return "echo " + val + " > " + self.basedir + file

    def config(self):
        self.zclient.get_cmdout(self.makecmd("current_tracer", "function"))

    def start(self):
        self.zclient.get_cmdout(self.makecmd("tracing_on", "1"))
        return "ok"

    def stop(self):
        self.zclient.get_cmdout(self.makecmd("tracing_on", "0"))
        return "ok"

    def reset(self):
        self.zclient.get_cmdout(self.makecmd("trace", " "))
        self.zclient.get_cmdout(self.makecmd("tracing_on", "0"))
        self.zclient.get_cmdout(self.makecmd("current_tracer", "nop"))
        self.zclient.get_cmdout(self.makecmd("set_ftrace_pid", " "))
        self.zclient.get_cmdout(self.makecmd("max_graph_depth", "0"))
        self.zclient.get_cmdout(self.makecmd("set_ftrace_filter", " "))
        self.zclient.get_cmdout(self.makecmd("set_graph_function", " "))
        self.zclient.get_cmdout(self.makecmd("events/enable", "0"))
        self.zclient.get_cmdout(self.makecmd("tracing_thresh", "0"))
        self.zclient.get_cmdout(self.makecmd("kprobe_events", " "))
        self.zclient.get_cmdout(self.makecmd("options/stacktrace", "0"))
        self.zclient.get_cmdout(self.makecmd("options/userstacktrace", "0"))

    def read(self):
        self.tracedata = self.zclient.get_seqread(self.basedir + "trace")
        if self.tracedata is not None:
            fileh = open('app/static/cache/trace.data', 'wb')
            fileh.write(self.tracedata.encode())
            fileh.close()

    def config_func_graph(self, func, depth):
        if not func in self.available_functions:
            print("do not support:", func)
            return 0
        self.zclient.get_cmdout(self.makecmd("current_tracer", "function_graph"))
        self.zclient.get_cmdout(self.makecmd("max_graph_depth", depth))
        self.zclient.get_cmdout(self.makecmd("set_graph_function", func))
        self.zclient.get_cmdout(self.makecmd("options/funcgraph-overhead", "0"))
        self.zclient.get_cmdout(self.makecmd("options/funcgraph-cpu", "0"))
        self.zclient.get_cmdout(self.makecmd("options/funcgraph-irqs", "0"))
        self.zclient.get_cmdout(self.makecmd("options/funcgraph-proc", "1"))
        self.zclient.get_cmdout(self.makecmd("options/funcgraph-abstime", "1"))
        self.zclient.get_cmdout(self.makecmd("options/funcgraph-duration", "1"))
        return 1

    def config_signal(self):
        self.zclient.get_cmdout(self.makecmd("current_tracer", "nop"))
        self.zclient.get_cmdout(self.makecmd("options/context-info", "1"))
        self.zclient.get_cmdout(self.makecmd("options/irq-info", "0"))
        self.zclient.get_cmdout(self.makecmd("events/signal/enable", "1"))
        return 1

    def get_available_functions(self):
        data = self.zclient.get_seqread(self.basedir + "available_filter_functions")
        self.available_functions = data.split("\n")

    def tostack(self):
        global LATENCY_MAX
        global LATENCY_MIN
        global LATENCYLIST
        global STACKLIST
        global STACKTOP
        STACKLIST = []
        LATENCYLIST = []
        LATENCY_MAX = 0
        LATENCY_MIN = None
        STACKTOP = Stack()

        self.piddict = {}
        pattern = re.compile(r'(\d*\.\d*) \|\s*(([\w|.|-]+)|(<\.*>))-(\d+)\s*\|\s*((\d*(\.\d*)?) us\s*)?\|  (\s*[\w|.|}]*)')
        fileh = open("app/static/cache/trace.data", 'r')
        for line in fileh.readlines():
            match = pattern.match(line)
            if match:
                #print(match.groups())
                timestamp = float(match.group(1))
                cmdline = match.group(2)
                pid = int(match.group(5))
                duration = match.group(7)
                if match.group(7) is not None:
                    duration = float(match.group(7))
                for i in range(len(match.group(9))):
                    if match.group(9)[i] != ' ':
                        funcname = match.group(9)[i:]
                        depth = int(i/2)
                        break

                #print([timestamp,cmdline,pid,duration,depth,funcname])
                if pid in self.piddict:
                    if funcname == '}':
                        if self.piddict[pid].iswalk():
                            self.piddict[pid].addend(funcname, depth, timestamp, duration)
                        else:
                            print("not in process, drop this one")
                    else:
                        if not self.piddict[pid].iswalk() and depth != 0:     #函数不是从零开始
                            print("func not begin with depth 0, drop this one")
                        else:
                            if not self.piddict[pid].iswalk() and depth == 0:
                                self.piddict[pid].walkstart()
                            elif self.piddict[pid].iswalk() and depth == 0:     #上一函数异常结束
                                print("last func did not end property", self.piddict[pid].len)
                                self.piddict[pid].drop += 1
                                self.piddict[pid].walkreset()
                            self.piddict[pid].add(funcname, depth, timestamp, duration)
                elif depth == 0 and funcname != '}':
                    print('create new pid %d'%(pid))
                    self.piddict[pid] = PidFunc(pid, cmdline)
                    self.piddict[pid].walkstart()
                    self.piddict[pid].add(funcname, depth, timestamp, duration)
            else:
                print('unhandled:', line)
        print('\ntotal stack : ', len(STACKLIST))
        #for stack in STACKLIST:
        #    stack.print()
        #print('top stack')
        #STACKTOP.print()
        STACKTOP.findmax()
        STACKTOP.gengraphviz()
        fileh.close()
        return len(STACKLIST)

    def get_pid_latency_dict(self):
        latency_dict = {}
        for key in self.piddict:
            #self.piddict[key].stat()
            latency_dict[key] = self.piddict[key].calc()
        return latency_dict

    def latency(self):
        runtime = 0
        for latency in LATENCYLIST:
            runtime += latency[1]
        print('latency :', len(LATENCYLIST), runtime)

    def list_to_heatmap(self, rows, columns):
        global LATENCY_MAX
        global LATENCY_MIN
        global LATENCYLIST
        global STACKLIST
        global STACKTOP
        if rows == 0 or columns == 0:
            print('rows/columns should not be zero')
            return
        print(LATENCY_MAX, LATENCY_MIN, rows)
        print(LATENCYLIST[0][0], LATENCYLIST[-1][0], columns)
        diffrows = LATENCY_MAX - LATENCY_MIN
        if diffrows == 0:
            print(diffrows)
            return
        diffcolums = int((LATENCYLIST[-1][0] - LATENCYLIST[0][0])*1000000)
        if diffcolums == 0:
            print(diffcolums)
            return
        data = [([0] * columns) for i in range(rows)]
        maxcount = 0
        for dlatency in LATENCYLIST:
            r_index = int((dlatency[1] - LATENCY_MIN) * rows / diffrows)
            if r_index >= rows:
                r_index = rows - 1
            c_index = int((dlatency[0] - LATENCYLIST[0][0]) * 1000000 * columns / diffcolums)
            if c_index >= columns:
                c_index = columns - 1
            #print(dlatency,r_index,c_index)
            data[r_index][c_index] += 1
            if maxcount < data[r_index][c_index]:
                maxcount = data[r_index][c_index]
        return {'data':data, 'label':[LATENCYLIST[0][0], (LATENCYLIST[-1][0] - LATENCYLIST[0][0])/columns, LATENCY_MIN, diffrows/rows, maxcount]}

    def stack_to_flamestack(self):
        root = {}
        #last = root
        lastdepthmap = {}
        #lastdepth = 0
        for fun in STACKTOP.funkstack:
            newframe = {}
            newframe['c'] = []
            newframe['n'] = fun.name
            #newframe['l'] = "kernel"
            newframe['v'] = int(fun.sumtime*1000)
            if fun.depth == 0:
                root = newframe
            if fun.depth-1 in lastdepthmap:
                lastdepthmap[fun.depth-1]['c'].append(newframe)
            lastdepthmap[fun.depth] = newframe
            #last = newframe
        return root

    def signal_analyse(self, processdict=None, pidfilter=None):
        piddict = {}
        pidpattern = re.compile(r'\s*((<([\w\d\.\-\_]*)>)|([\w\d\.\-\_]*))-(\d+)\s*')
        generatepattern = re.compile(r'signal_generate: sig=(\d*) errno=\d* code=\d* comm=(\w*) pid=(\d*) grp=\d* res=(\d*)')
        deliverpattern = re.compile(r'signal_deliver: sig=(\d*)')

        dot = gv.Digraph(comment='signal', engine='dot', format='svg')
        dot.graph_attr['rankdir'] = 'LR'
        dot.attr('node', style='filled')

        fileh = open("app/static/cache/trace.data", 'r')
        for line in fileh.readlines():
            #print(line)
            match = pidpattern.search(line)
            if match:
                #print(line)
                #print(match.groups())
                pid = int(match.group(5))
                comm = match.group(4)
                if comm == '...':
                    comm = None
                if comm is None and processdict is not None:
                    if pid in processdict:
                        comm = processdict[pid].comm
                generatematch = generatepattern.search(line)
                if generatematch:
                    #print(generatematch.groups())
                    sig = int(generatematch.group(1))
                    rname = generatematch.group(2)
                    rpid = int(generatematch.group(3))
                    res = int(generatematch.group(4))
                    if pid not in piddict:
                        piddict[pid] = {}
                        piddict[pid]['name'] = comm
                        piddict[pid]['send'] = 0
                        piddict[pid]['recv'] = 0
                        piddict[pid]['error'] = 0
                        piddict[pid]['map'] = {}
                        if not (pidfilter is not None and pidfilter != pid and pidfilter != rpid):
                            if comm:
                                dot.node(str(pid), str(pid) + "(" + comm + ")", color='#96cdcd3f', shape='ellipse')
                            else:
                                dot.node(str(pid), str(pid), color='#96cdcd3f', shape='ellipse')
                    if not (pidfilter is not None and pidfilter != pid and pidfilter != rpid):
                        dot.edge(str(pid), str(rpid), generatematch.group(1))
                    if rpid in piddict and piddict[rpid]['name'] is None:
                        piddict[rpid]['name'] = rname
                    if res == 0:
                        piddict[pid]['send'] += 1
                        if sig not in piddict[pid]['map']:
                            piddict[pid]['map'][sig] = {}
                            piddict[pid]['map'][sig]['send'] = 0
                            piddict[pid]['map'][sig]['recv'] = 0
                            piddict[pid]['map'][sig]['error'] = 0
                        piddict[pid]['map'][sig]['send'] += 1
                    else:
                        piddict[pid]['error'] += 1
                        if sig not in piddict[pid]['map']:
                            piddict[pid]['map'][sig] = {}
                            piddict[pid]['map'][sig]['send'] = 0
                            piddict[pid]['map'][sig]['recv'] = 0
                            piddict[pid]['map'][sig]['error'] = 0
                        piddict[pid]['map'][sig]['error'] += 1
                else:
                    delivermatch = deliverpattern.search(line)
                    if delivermatch:
                        #print(delivermatch.groups())
                        if pid not in piddict:
                            piddict[pid] = {}
                            piddict[pid]['name'] = comm
                            piddict[pid]['send'] = 0
                            piddict[pid]['recv'] = 0
                            piddict[pid]['error'] = 0
                            piddict[pid]['map'] = {}
                            if not (pidfilter is not None and pidfilter != pid):
                                if comm:
                                    dot.node(str(pid), str(pid) + "(" + comm + ")", color='#96cdcd3f', shape='ellipse')
                                else:
                                    dot.node(str(pid), str(pid), color='#96cdcd3f', shape='ellipse')
                        sig = int(delivermatch.group(1))
                        piddict[pid]['recv'] += 1
                        if sig not in piddict[pid]['map']:
                            piddict[pid]['map'][sig] = {}
                            piddict[pid]['map'][sig]['send'] = 0
                            piddict[pid]['map'][sig]['recv'] = 0
                            piddict[pid]['map'][sig]['error'] = 0
                        piddict[pid]['map'][sig]['recv'] += 1
        #print(piddict)
        if pidfilter is not None:
            dot.render('app/static/cache/signalpid')
        else:
            dot.render('app/static/cache/signal')
        return piddict
