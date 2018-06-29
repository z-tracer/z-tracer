from app.zclient.zclient import Zclient
import shutil

class Perf():
    def __init__(self, zclient,**kwargs):
        self.zclient = zclient
        self.cpu = None
        self.time = 120
        self.hz = 49
        self.pid = None
        self.adv = None

    def record(self):
        r_hz = ' -F ' + str(self.hz)
        r_time = ' -- sleep ' + str(self.time)
        if self.cpu != None:
            r_cpu = ' -C ' + self.cpu
        else:
            r_cpu = ' -a'

        if self.pid != None:
            r_pid = ' -P ' + str(self.pid)
        else:
            r_pid = ''

        if self.adv != None:
            r_adv = ' ' + self.adv
        else:
            r_adv = ''
        cmdline = 'perf record -g' + r_adv + r_cpu + r_pid + r_hz + r_time
        print(cmdline)
        if 1:
            data = self.zclient.get_perfscript(cmdline)
            if data != None:
                fh = open('app/static/perf/perf.stack', 'wb')
                fh.write(data.encode())
                fh.close()
        else:
            self.zclient.get_perfreport(cmdline)
            cmdline2 = 'perf script --header > perf.stack'
            self.zclient.get_perfreport(cmdline2)
            shutil.move('perf.stack','app/static/perf/perf.stack')

    def start(self):
        r_hz = ' -F ' + str(self.hz)

        if self.time != '':
            r_time = ' -- sleep ' + str(self.time)
        else:
            r_time = ''

        if self.cpu != None:
            r_cpu = ' -C ' + self.cpu
        else:
            r_cpu = ' -a'

        if self.pid != None:
            r_pid = ' -P ' + str(self.pid)
        else:
            r_pid = ''

        if self.adv != None:
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