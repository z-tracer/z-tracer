from app.zclient.zclient import Zclient
import shutil

#tracing_cpumask
#set_ftrace_pid
#
#set_ftrace_filter
#set_ftrace_notrace
#
#set_graph_function
#set_graph_notrace
#max_graph_depth
#
#
#

class Ftrace():
    def __init__(self, zclient,**kwargs):
        self.zclient = zclient
        self.basedir = "/sys/kernel/debug/tracing/"

    def makecmd(self, file, val):
        return "echo " + val + " > " + self.basedir + file

    def config(self):
        self.zclient.get_cmdout(self.makecmd("current_tracer","function"))

    def start(self):
        self.zclient.get_cmdout(self.makecmd("tracing_on","1"))

    def stop(self):
        self.zclient.get_cmdout(self.makecmd("tracing_on","0"))

    def reset(self):
        self.zclient.get_cmdout(self.makecmd("tracing_on","0"))
        self.zclient.get_cmdout(self.makecmd("current_tracer","nop"))
        self.zclient.get_cmdout(self.makecmd("set_ftrace_pid"," "))
        self.zclient.get_cmdout(self.makecmd("max_graph_depth","0"))

    def read(self):
        print(self.zclient.get_procinfo(self.basedir + "trace"))