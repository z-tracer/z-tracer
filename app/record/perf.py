#from app.zclient.zclient import Zclient
import shutil
import re

class Perf():
    def __init__(self, zclient):
        self.zclient = zclient
        self.cpu = None
        self.time = 120
        self.hz = 49
        self.pid = None
        self.adv = None
        self.func = None
        self.exe = None
        self.arg = None
        self.available_functions = None
        self.arglist = []
        self.argmax = 0
        self.argmin = 0
        self.trace_ret = 0
        self.retlist = []
        self.retmax = 0
        self.retmin = 0

    def record(self):
        r_hz = ' -F ' + str(self.hz)
        r_time = ' -- sleep ' + str(self.time)
        if self.cpu is not None:
            r_cpu = ' -C ' + self.cpu
        else:
            r_cpu = ' -a'

        if self.pid is not None:
            r_pid = ' -P ' + str(self.pid)
        else:
            r_pid = ''

        if self.adv is not None:
            r_adv = ' ' + self.adv
        else:
            r_adv = ''
        cmdline = 'perf record -g' + r_adv + r_cpu + r_pid + r_hz + r_time
        print(cmdline)
        if 1:
            data = self.zclient.get_perfscript(cmdline)
            if data is not None:
                fileh = open('app/static/perf/perf.stack', 'wb')
                fileh.write(data.encode())
                fileh.close()
        else:
            self.zclient.get_perfreport(cmdline)
            cmdline2 = 'perf script --header > perf.stack'
            self.zclient.get_perfreport(cmdline2)
            shutil.move('perf.stack', 'app/static/perf/perf.stack')

    def start(self):
        r_hz = ' -F ' + str(self.hz)

        if self.time != '':
            r_time = ' -- sleep ' + str(self.time)
        else:
            r_time = ''

        if self.cpu is not None:
            r_cpu = ' -C ' + self.cpu
        else:
            r_cpu = ' -a'

        if self.pid is not None:
            r_pid = ' -P ' + str(self.pid)
        else:
            r_pid = ''

        if self.adv is not None:
            r_adv = ' ' + self.adv
        else:
            r_adv = ''
        cmdline = 'perf record -g' + r_adv + r_cpu + r_pid + r_hz + r_time
        print(cmdline)
        data = self.zclient.acmdstart(cmdline)
        return data

    def stop(self):
        data = self.zclient.acmdstop()
        return data

    def checkdone(self):
        data = self.zclient.acmdcheckdone()
        return data

    def script(self, arg=''):
        cmdline = "perf script " + arg
        data = self.zclient.acmdresult(cmdline)
        return data

    def addprobe(self):
        if self.exe is not None:
            r_exe = ' -x ' + self.exe
        else:
            r_exe = ''

        if self.arg is not None:
            r_arg = ' zarg1=' + self.arg
        else:
            r_arg = ''
        cmdline = 'perf probe' + r_exe + ' -a \"ztracer:' + self.func +'=' \
                    + self.func + r_arg + '" 2>&1'
        print(cmdline)
        data = self.zclient.acmdresult(cmdline)
        if 'Error' in data:
            return data

        if self.trace_ret == 1:
            r_arg = ' zreturn1=\\$retval'
            cmdline = 'perf probe' + r_exe + ' -a \"ztracer:ret' + self.func +'=' \
                        + self.func + '%return' + r_arg + '" 2>&1'
            print(cmdline)
            data = self.zclient.acmdresult(cmdline)
            if 'Error' in data:
                return data
        return 'ok'

    def delprobe(self):
        if self.trace_ret == 1:
            cmdline = 'perf probe -d ret' + self.func
            print(cmdline)
            self.zclient.acmdresult(cmdline)
            self.trace_ret = 0
        if self.func is not None:
            cmdline = 'perf probe -d ' + self.func
            print(cmdline)
            self.zclient.acmdresult(cmdline)
            self.func = None
        self.exe = None
        self.arg = None

    def delallprobe(self):
        cmdline = 'perf probe -d ztracer:*'
        print(cmdline)
        self.zclient.acmdresult(cmdline)
        self.func = None
        self.exe = None
        self.arg = None

    def probestart(self):
        if self.trace_ret == 1:
            event1 = ' -e ztracer:ret' + self.func
        else:
            event1 = ''
        cmdline = 'perf record -g -a -e ztracer:' + self.func + event1
        print(cmdline)
        data = self.zclient.acmdstart(cmdline)
        return data

    def probe_available_functions(self, exe, func_filter):
        if exe:
            r_exe = ' -x ' + exe
        else:
            r_exe = ''
        if func_filter:
            r_funcs = func_filter
        else:
            r_funcs = ''
        cmdline = 'perf probe' + r_exe + ' --funcs ' + r_funcs + ' 2>&1'
        print(cmdline)
        data = self.zclient.acmdresult(cmdline)
        if data is not None:
            self.available_functions = data.split("\n")
        return data

    def probe_available_args(self, exe, func):
        if exe:
            r_exe = ' -x ' + exe
        else:
            r_exe = ''
        if func:
            r_funcs = func
        else:
            r_funcs = ''
        cmdline = 'perf probe' + r_exe + ' --vars ' + r_funcs + ' 2>&1'
        print(cmdline)
        data = self.zclient.acmdresult(cmdline)
        return data

    def get_arg_varlist(self):
        self.arglist = []
        self.argmax = 0
        self.argmin = -1
        argpattern = re.compile(r'zarg1=([\d]+)')
        timepattern = re.compile(r' +([0-9.]+): .+?:')
        fileh = open("app/static/perf/perf.stack", 'r')
        for line in fileh.readlines():
            match = argpattern.search(line)
            if match:
                argval = int(match.group(1))
                timematch = timepattern.search(line)
                if timematch:
                    self.arglist.append([float(timematch.group(1)), argval])
                    if self.argmax < argval:
                        self.argmax = argval
                    if self.argmin == -1 or self.argmin > argval:
                        self.argmin = argval
        #print(self.arglist, self.argmax, self.argmin)

    def get_arg_heatmap(self, rows, columns):
        self.get_arg_varlist()
        if rows == 0 or columns == 0:
            print('rows/columns should not be zero')
            return
        print(self.argmax, self.argmin, rows)
        print(self.arglist[0][0], self.arglist[-1][0], columns)
        diffrows = self.argmax - self.argmin
        if diffrows == 0:
            diffrows = 1
        diffcolums = int((self.arglist[-1][0] - self.arglist[0][0])*1000000)
        if diffcolums == 0:
            print(diffcolums)
            return
        data = [([0] * columns) for i in range(rows)]
        maxcount = 0
        for arg in self.arglist:
            r_index = int((arg[1] - self.argmin) * rows / diffrows)
            if r_index >= rows:
                r_index = rows - 1
            c_index = int((arg[0] - self.arglist[0][0]) * 1000000 * columns / diffcolums)
            if c_index >= columns:
                c_index = columns - 1
            #print(d,r_index,c_index)
            data[r_index][c_index] += 1
            if maxcount < data[r_index][c_index]:
                maxcount = data[r_index][c_index]
        return {'data':data, 'label':[self.arglist[0][0], (self.arglist[-1][0] - \
                self.arglist[0][0])/columns, self.argmin, diffrows/rows, maxcount]}

    def get_ret_varlist(self):
        self.retlist = []
        self.retmax = 0
        self.retmin = 0
        argpattern = re.compile(r'zreturn1=([\w\d]+)')
        timepattern = re.compile(r' +([0-9.]+): .+?:')
        fileh = open("app/static/perf/perf.stack", 'r')
        for line in fileh.readlines():
            match = argpattern.search(line)
            if match:
                argval = int(match.group(1), 16)
                if argval >= 2147483648:
                    argval = argval - 4294967296
                timematch = timepattern.search(line)
                if timematch:
                    self.retlist.append([float(timematch.group(1)), argval])
                    if self.retmax < argval:
                        self.retmax = argval
                    if self.retmin > argval:
                        self.retmin = argval
        #print(self.retlist, self.retmax, self.retmin)

    def get_ret_heatmap(self, rows, columns):
        self.get_ret_varlist()
        if rows == 0 or columns == 0:
            print('rows/columns should not be zero')
            return
        print(self.retmax, self.retmin, rows)
        print(self.retlist[0][0], self.retlist[-1][0], columns)
        diffrows = self.retmax - 0
        if diffrows == 0:
            diffrows = 1
        diffcolums = int((self.retlist[-1][0] - self.retlist[0][0])*1000000)
        if diffcolums == 0:
            print(diffcolums)
            return
        data = [([0] * columns) for i in range(rows + 1)]
        maxcount = 0
        for arg in self.retlist:
            if arg[1] >= 0:
                r_index = int((arg[1] - 0) * rows / diffrows) + 1
                if r_index >= rows:
                    r_index = rows - 1
                c_index = int((arg[0] - self.retlist[0][0]) * 1000000 * columns / diffcolums)
                if c_index >= columns:
                    c_index = columns - 1
                #print(d,r_index,c_index)
            else:
                r_index = 0
            data[r_index][c_index] += 1
            if maxcount < data[r_index][c_index]:
                maxcount = data[r_index][c_index]
        return {'data':data, 'label':[self.retlist[0][0], \
                (self.retlist[-1][0] - self.retlist[0][0])/columns, \
                self.retmin, diffrows/rows, maxcount]}

    def syscallstart(self, pid_filter='', syscall_filter=''):
        if syscall_filter:
            sys_arg = '\"syscalls:sys_enter_' + syscall_filter +'\"'
        else:
            sys_arg = "\"syscalls:sys_enter_*\" "

        if pid_filter:
            pid_arg = " --filter common_pid==" + pid_filter
        else:
            pid_arg = ''
        cmdline = 'perf record -a -e ' + sys_arg + pid_arg
        print(cmdline)
        data = self.zclient.perfastart(cmdline)
        return data

    def syscallwalk(self):
        piddict = {}
        syscalldict = {}
        fileh = open("app/static/perf/perf.stack", 'r')
        for line in fileh.readlines():
            line = line.split(' ')
            while '' in line:
                line.remove('')
            #print(line)
            pid = int(line[1])
            syscallname = line[2][19:].replace(':', '')
            if pid not in piddict:
                piddict[pid] = {}
                piddict[pid]['comm'] = line[0]
                piddict[pid]['num'] = 1
                piddict[pid]['callmap'] = {}
            else:
                piddict[pid]['num'] += 1
            if syscallname not in piddict[pid]['callmap']:
                piddict[pid]['callmap'][syscallname] = 1
            else:
                piddict[pid]['callmap'][syscallname] += 1

            if syscallname not in syscalldict:
                syscalldict[syscallname] = 1
            else:
                syscalldict[syscallname] += 1
        sortdict = sorted(syscalldict.items(), key=lambda e: e[1], reverse=True)
        return [piddict, syscalldict, sortdict]
