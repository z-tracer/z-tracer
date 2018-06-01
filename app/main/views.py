from flask import render_template, redirect, url_for, abort, flash, request,\
    current_app, make_response, g, jsonify
from . import main
from ..record import Record, Loadavg,Process,Processes,Stat,ScanTimer
#from .. import db
from datetime import datetime
import os,random
import pygal
import time

#g.g_timer = ScanTimer()
g_loadavg = Loadavg()
g_stat = Stat()
g_processes = Processes()

@main.before_request
def before_request():
    pass
    
@main.route('/', methods=['GET', 'POST'])
def index():
    if not hasattr(current_app,'g_timer'):
        current_app.g_timer = ScanTimer()
        current_app.g_timer.start()
    
    
    return render_template('index.html',loadavg = current_app.g_loadavg, stat = current_app.g_stat)

@main.route('/cpu', methods=['GET', 'POST'])
def cpu():
    return render_template('cpu_base.html')

@main.route('/cpus', methods=['GET', 'POST'])
def cpus():
    return render_template('cpus.html',stat = current_app.g_stat)

@main.route('/loadavg', methods=['GET', 'POST'])
def loadavg():
    chart= g_loadavg.draw()
    return render_template('loadavg.html', chart = chart)
    
@main.route('/update/loadavg', methods=['GET', 'POST'])
def update_loadavg():
    chart= g_loadavg.draw()
    return jsonify({'result':'ok','src':chart})

@main.route('/softirqs', methods=['GET', 'POST'])
def softirqs():
    return render_template('softirqs.html',cpunum = current_app.g_cpunum,softirqs = current_app.g_softirqs)

@main.route('/interrupts', methods=['GET', 'POST'])
def interrupts():
    return render_template('interrupts.html',cpunum = current_app.g_cpunum,interrupts = current_app.g_interrupts)

@main.route('/process', methods=['GET', 'POST'])
def process():
    pslist = {}
    pslist = g_processes.scan()
    g_processes.gengv()
    g_processes.ordered = sorted(pslist.keys())
    return render_template('process.html', data=pslist, ordered = g_processes.ordered, date=time.time())

@main.route('/process_diffcpu', methods=['GET', 'POST'])
def process_diffcpu():
    ps = []
    ps_new = Processes()
    ps_new.scan()
    for key in g_processes.process_dict:
        if key in ps_new.process_dict:
            ps.append([g_processes.process_dict[key].stat[1],g_processes.process_dict[key].stat[40],\
            ps_new.process_dict[key].cputime - g_processes.process_dict[key].cputime])
    g_processes.scan()
    return render_template('process_diffcpu.html', data=ps)

@main.route('/process_diffmem', methods=['GET', 'POST'])
def process_diffmem():
    ps = []
    ps_new = Processes()
    ps_new.scan()
    for key in g_processes.process_dict:
        if key in ps_new.process_dict and ps_new.process_dict[key].VmPeak:
            diff = ps_new.process_dict[key].VmRSS - g_processes.process_dict[key].VmRSS
            if diff > 0:
                ps.append([g_processes.process_dict[key].stat[1],1,diff])
            elif diff < 0:
                ps.append([g_processes.process_dict[key].stat[1],0,abs(diff)])
    g_processes.scan()
    return render_template('process_diffmem.html', data=ps)

@main.route('/process_monitor', methods=['GET', 'POST'])
def process_monitor():
    return render_template('process_monitor.html', cpunum = current_app.g_cpunum, processes = current_app.g_processes)

@main.route('/process/<int:pid>', methods=['GET', 'POST'])
def process_pid(pid):
    process_one = Process( pid = pid)
    ret = process_one.getstat()
    process_one.getcomm()
    process_one.getcmdline()
    process_one.getstatus()
    process_one.getstatm()
    process_one.getmaps()
    return render_template('pid.html', data=process_one)

@main.route('/update/all', methods=['GET', 'POST'])
def update_all():
    data=request.form.get('data')
    id=request.form.get('id')
    if data =='loadavg':
        #负载统计
        print('get loadavg')
        ret = g_loadavg.update()
        #cpu时间统计
        newstat = Stat()
        newstat.getstat()
        if g_stat.cpunum != 0:
            diff_user = newstat.cpu['all'][0] - g_stat.cpu['all'][0]
            diff_nice = newstat.cpu['all'][1] - g_stat.cpu['all'][1]
            diff_system = newstat.cpu['all'][2] - g_stat.cpu['all'][2]
            diff_idle = newstat.cpu['all'][3] - g_stat.cpu['all'][3]
            diff_iowait = newstat.cpu['all'][4] - g_stat.cpu['all'][4]
            diff_irq = newstat.cpu['all'][5] - g_stat.cpu['all'][5]
            diff_softirq = newstat.cpu['all'][6] - g_stat.cpu['all'][6]
            diff_steal = newstat.cpu['all'][7] - g_stat.cpu['all'][7]
            sum = diff_user+diff_nice+diff_system+diff_idle+diff_iowait+diff_irq+diff_softirq+diff_steal
            if sum != 0:
                diff = [round(diff_user*100/sum,2),round(diff_nice*100/sum,2),\
                        round(diff_system*100/sum,2),round(diff_idle*100/sum,2),\
                        round(diff_iowait*100/sum,2),round(diff_irq*100/sum,2),\
                        round(diff_softirq*100/sum,2),round(diff_steal*100/sum,2)]
                print(diff)
        g_stat.getstat()
        return jsonify({'result':'ok','loadavg':ret,'stat':diff})
    
    if data =='pidvmmem':
        ps = Process( pid = int(id) )
        ps.getstat()
        ret = ps.getstatus()
        print(ret)
        return jsonify({'result':'ok','src':ret})
    
    if data =='pidtreemap':
        ps = []
        for key in g_processes.process_dict:
            print(key)
            ps.append([g_processes.process_dict[key].stat[0],g_processes.process_dict[key].stat[40],g_processes.process_dict[key].cputime])
        print(ps)
        #return jsonify({'result':'ok','src':ps})
        return render_template('process_diff.html', data=g_processes.process_dict)

    if data == 'index':
        ret = []
        diff=[]
        misc=[]
        softirq=[]
        irq=[]
        if hasattr(current_app,'g_loadavg'):
            ret = current_app.g_loadavg.getlast('all')
        if hasattr(current_app,'g_stat'):
            diff = current_app.g_stat.getlast('utilization')
            misc = current_app.g_stat.getlast('misc')
            softirq = current_app.g_stat.getlast('s_softirq')
            irq = current_app.g_stat.getlast('h_irq')
        return jsonify({'result':'ok','loadavg':ret,'stat':diff,'ctxt':misc, 'softirq':softirq, 'intr':irq})

    if data == 'percpu':
        ret = {}
        if hasattr(current_app,'g_stat'):
            for i in range(current_app.g_stat.data[-1].cpunum):
                ret[i] = current_app.g_stat.getlast('utilization',i+1)
        return jsonify({'result':'ok','percpu':ret})

    if data == 'softirqs':
        ret = {}
        if hasattr(current_app,'g_softirqs'):
            for i in range(current_app.g_softirqs.data[-1].cpunum):
                ret[i] = current_app.g_softirqs.getlast('s_softirq',i)
        return jsonify({'result':'ok','softirqs':ret})

    if data == 'interrupts':
        ret = []
        if hasattr(current_app,'g_interrupts'):
            ret = current_app.g_interrupts.getlast('interrupts')
            print(ret)
        return jsonify({'result':'ok','interrupts':ret})

    if data == 'processes':
        ret = []
        if hasattr(current_app,'g_processes'):
            ret = {'result':'ok','time':current_app.g_processes.data[-1].time, \
                'process':current_app.g_processes.data[-1].diffprocess, \
                'mem':current_app.g_processes.data[-1].diffmem, \
                'major':current_app.g_processes.data[-1].diffmajor, \
                'minor':current_app.g_processes.data[-1].diffminor, \
                'ctxt':current_app.g_processes.data[-1].diffctxt, \
                'nctxt':current_app.g_processes.data[-1].diffnctxt}
            print(ret)
            return jsonify(ret)
        else:
            return jsonify({'result':'ok'})