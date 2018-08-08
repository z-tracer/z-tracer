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

    def script(self):
        data = self.zclient.acmdresult("perf script --header")
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
        cmdline = 'perf probe' + r_exe + ' -a \"ztracer:' + self.func +'=' + self.func + r_arg + '" 2>&1'
        print(cmdline)
        data = self.zclient.acmdresult(cmdline)
        if 'Error' in data:
            return data
        else:
            return 'ok'

    def delprobe(self):
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
        cmdline = 'perf record -g -a -e ztracer:' + self.func
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
        return {'data':data, 'label':[self.arglist[0][0], (self.arglist[-1][0] - self.arglist[0][0])/columns, self.argmin, diffrows/rows, maxcount]}
