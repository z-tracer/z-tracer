from flask import render_template, request, current_app, jsonify
from . import main
from ..record.task import Process,Processes
import time

@main.route('/task', methods=['GET', 'POST'])
def task():
    return render_template('task_base.html')

@main.route('/tasktree', methods=['GET', 'POST'])
def tasktree():
    if not hasattr(current_app.curr_device,'g_threads'):
        current_app.curr_device.g_threads = Processes(current_app.curr_device.zclient)
    current_app.curr_device.g_threads.scan()
    current_app.curr_device.g_threads.gengraphviz()
    return render_template('task_tree.html',date=time.time())

@main.route('/task/<int:pid>', methods=['GET', 'POST'])
def process_pid(pid):
    if not hasattr(current_app.curr_device,'g_threads'):
        current_app.curr_device.g_threads = Processes(current_app.curr_device.zclient)
    current_app.curr_device.g_threads.scanthread()
    isthread = 0
    process_one = Process(current_app.curr_device.zclient, pid = pid)
    ret = process_one.getstat()
    process_one.getcomm()
    process_one.getcmdline()
    process_one.getstatus()
    process_one.getstatm()
    process_one.getmaps()
    process_one.getenviron()
    process_one.getfd()
    process_one.getthreads()
    return render_template('pid.html', data=process_one, threadlist = current_app.curr_device.g_threads.thread_dict)

@main.route('/process', methods=['GET', 'POST'])
def process():
    if not hasattr(current_app.curr_device,'g_threads'):
        current_app.curr_device.g_threads = Processes(current_app.curr_device.zclient)
    pslist = {}
    pslist = current_app.curr_device.g_threads.scan()
    current_app.curr_device.g_threads.ordered = sorted(pslist.keys())
    return render_template('task_info.html', data=pslist, ordered = current_app.curr_device.g_threads.ordered, isthread=0, num=len(pslist))

@main.route('/process_diffcpu', methods=['GET', 'POST'])
def process_diffcpu():
    ps = []
    if not hasattr(current_app.curr_device,'g_threads'):
        current_app.curr_device.g_threads = Processes(current_app.curr_device.zclient)
        current_app.curr_device.g_threads.scan()
    ps_new = Processes(current_app.curr_device.zclient)
    ps_new.scan()
    for key in current_app.curr_device.g_threads.process_dict:
        if key in ps_new.process_dict:
            ps.append([current_app.curr_device.g_threads.process_dict[key].stat[1],current_app.curr_device.g_threads.process_dict[key].stat[40],\
            ps_new.process_dict[key].cputime - current_app.curr_device.g_threads.process_dict[key].cputime])
    current_app.curr_device.g_threads.scan()
    return render_template('task_diffcpu.html', data=ps,isthread=0)

@main.route('/process_diffmem', methods=['GET', 'POST'])
def process_diffmem():
    if not hasattr(current_app.curr_device,'g_threads'):
        current_app.curr_device.g_threads = Processes(current_app.curr_device.zclient)
        current_app.curr_device.g_threads.scan()
    ps = []
    ps_new = Processes(current_app.curr_device.zclient)
    ps_new.scan()
    for key in current_app.curr_device.g_threads.process_dict:
        if key in ps_new.process_dict and ps_new.process_dict[key].VmPeak:
            diff = ps_new.process_dict[key].VmRSS - current_app.curr_device.g_threads.process_dict[key].VmRSS
            if diff > 0:
                ps.append([current_app.curr_device.g_threads.process_dict[key].stat[1]+'('+str(current_app.curr_device.g_threads.process_dict[key].stat[0])+')',1,diff])
            elif diff < 0:
                ps.append([current_app.curr_device.g_threads.process_dict[key].stat[1]+'('+str(current_app.curr_device.g_threads.process_dict[key].stat[0])+')',0,abs(diff)])
    current_app.curr_device.g_threads.scan()
    return render_template('task_diffmem.html', data=ps,isthread=0)

@main.route('/process_monitor', methods=['GET', 'POST'])
def process_monitor():
    return render_template('task_monitor.html', cpunum = current_app.curr_device.g_cpunum, processes = current_app.curr_device.g_processes)

@main.route('/thread', methods=['GET', 'POST'])
def thread():
    if not hasattr(current_app.curr_device,'g_threads'):
        current_app.curr_device.g_threads = Processes(current_app.curr_device.zclient)
    pslist = {}
    #current_app.curr_device.g_threads.scanthread()
    pslist = current_app.curr_device.g_threads.scanthread()
    current_app.curr_device.g_threads.ordered = sorted(pslist.keys())
    return render_template('task_info.html', data=pslist, ordered = current_app.curr_device.g_threads.ordered,isthread=1, num=len(pslist))

@main.route('/thread_monitor', methods=['GET', 'POST'])
def thread_monitor():
    return render_template('task_monitor.html', cpunum = current_app.curr_device.g_cpunum, processes = current_app.curr_device.g_processes)

@main.route('/thread_diffcpu', methods=['GET', 'POST'])
def thread_diffcpu():
    ps = []
    if not hasattr(current_app.curr_device,'g_threads'):
        current_app.curr_device.g_threads = Processes(current_app.curr_device.zclient)
        current_app.curr_device.g_threads.scanthread()
    ps_new = Processes(current_app.curr_device.zclient)
    ps_new.scanthread()
    for key in current_app.curr_device.g_threads.thread_dict:
        if key in ps_new.thread_dict:
            ps.append([current_app.curr_device.g_threads.thread_dict[key].stat[1],current_app.curr_device.g_threads.thread_dict[key].stat[40],\
            ps_new.thread_dict[key].cputime - current_app.curr_device.g_threads.thread_dict[key].cputime])
    current_app.curr_device.g_threads.scanthread()
    return render_template('task_diffcpu.html', data=ps,isthread=1)

@main.route('/thread_diffmem', methods=['GET', 'POST'])
def thread_diffmem():
    if not hasattr(current_app.curr_device,'g_threads'):
        current_app.curr_device.g_threads = Processes(current_app.curr_device.zclient)
        current_app.curr_device.g_threads.scan()
    ps = []
    ps_new = Processes(current_app.curr_device.zclient)
    ps_new.scan()
    for key in current_app.curr_device.g_threads.process_dict:
        if key in ps_new.process_dict and ps_new.process_dict[key].VmPeak:
            diff = ps_new.process_dict[key].VmRSS - current_app.curr_device.g_threads.process_dict[key].VmRSS
            if diff > 0:
                ps.append([current_app.curr_device.g_threads.process_dict[key].stat[1]+'('+str(current_app.curr_device.g_threads.process_dict[key].stat[0])+')',1,diff])
            elif diff < 0:
                ps.append([current_app.curr_device.g_threads.process_dict[key].stat[1]+'('+str(current_app.curr_device.g_threads.process_dict[key].stat[0])+')',0,abs(diff)])
    current_app.curr_device.g_threads.scan()
    return render_template('task_diffmem.html', data=ps,isthread=1)

@main.route('/update/processes', methods=['GET', 'POST'])
def update_processes():
    data=request.form.get('data')
    id=request.form.get('id')
    if hasattr(current_app,'curr_device'):
        if hasattr(current_app.curr_device,'g_processes'):
            ret = {'result':'ok','time':current_app.curr_device.g_processes.data[-1].time, \
                'process':current_app.curr_device.g_processes.data[-1].diffprocess, \
                'mem':current_app.curr_device.g_processes.data[-1].diffmem, \
                'major':current_app.curr_device.g_processes.data[-1].diffmajor, \
                'minor':current_app.curr_device.g_processes.data[-1].diffminor, \
                'ctxt':current_app.curr_device.g_processes.data[-1].diffctxt, \
                'nctxt':current_app.curr_device.g_processes.data[-1].diffnctxt}
            print(ret)
            return jsonify(ret)
        else:
            return jsonify({'result':'ok'})
    else:
        return jsonify({'result':'error'})

@main.route('/update/pid', methods=['GET', 'POST'])
def update_pid():
    data=request.form.get('data')
    id=request.form.get('id')
    if hasattr(current_app,'curr_device'):
        threadutime = {}
        threadstime = {}
        ps = Process(current_app.curr_device.zclient, pid = int(id) )
        ps.getstat()
        ret = ps.getstatus()
        if ps.nr_threads > 1:
            ps.getthreads()
            for key in ps.threads:
                threadutime[ps.threads[key].pid] = ps.threads[key].utime
                threadstime[ps.threads[key].pid] = ps.threads[key].stime
        print(threadutime)
        print(threadstime)
        return jsonify({'result':'ok','src':ret,'threadu':threadutime,'threads':threadstime})
    else:
        return jsonify({'result':'error'})