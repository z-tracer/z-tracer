from flask import render_template, redirect, url_for, abort, flash, request,\
    current_app, make_response, g, jsonify
from . import main
from .forms import EditProfileForm
from ..record.cpu import Stat
from ..device import Device

@main.before_request
def before_request():
    if '/profile' not in request.url:
        if not hasattr(current_app,'curr_device'):
            return redirect(url_for('.profile'))
    
@main.route('/', methods=['GET', 'POST'])
def index():
    return render_template('flamescope.html')

@main.route('/summary', methods=['GET', 'POST'])
def summary():
    if not hasattr(current_app,'curr_device'):
        return redirect(url_for('.profile'))
        device = Device(current_app.config['DEFAULT_CLIENT_IP'],current_app.config['DEFAULT_CLIENT_PORT'])
        device.scan_process()
        device.start()
        current_app.curr_device = device
    
    #return  '<h1>Home</h1>'
    return render_template('index.html',loadavg = current_app.curr_device.g_loadavg, stat = current_app.curr_device.g_stat, \
        meminfo = current_app.curr_device.g_meminfo, uptime = current_app.curr_device.g_uptime,cpunum = current_app.curr_device.g_cpunum)

@main.route('/profile', methods=['GET', 'POST'])
def profile():
    form = EditProfileForm()
    if form.validate_on_submit():
        print(form.ip.data+':'+form.port.data)
        if not hasattr(current_app,'curr_device') or \
            not hasattr(current_app,'devices') or \
            (hasattr(current_app,'devices') and form.ip.data+':'+form.port.data not in current_app.devices):
            device = Device(form.ip.data, int(form.port.data))
            current_app.curr_device = device
            if device.connect == 1:
                if not hasattr(current_app,'devices'):
                    current_app.devices = {}
                current_app.devices[form.ip.data+':'+form.port.data] = device
                current_app.curr_device.scan_process()
                current_app.curr_device.start()
                flash('connect to %s:%s success!'%(form.ip.data,form.port.data))
            else:
                flash('connect to %s:%s fail!'%(form.ip.data,form.port.data))
        else:
            current_app.curr_device = current_app.devices[form.ip.data+':'+form.port.data]
            flash('update %s:%s success!'%(form.ip.data,form.port.data))
        current_app.curr_device.intval = int(form.timeval.data)
        current_app.curr_device.samplecnt = int(form.cnt.data)
        return redirect(url_for('.profile'))
    if hasattr(current_app,'curr_device'):
        form.ip.data = current_app.curr_device.ip
        form.port.data = current_app.curr_device.port
        form.timeval.data = current_app.curr_device.intval
        form.cnt.data = current_app.curr_device.samplecnt
    else:
        form.ip.data = current_app.config['DEFAULT_CLIENT_IP']
        form.port.data = current_app.config['DEFAULT_CLIENT_PORT']
        form.timeval.data = current_app.config['DEFAULT_TIME_INT']
        form.cnt.data = current_app.config['DEFAULT_SAMPLE_SIZE']
    if hasattr(current_app,'devices'):
        return render_template('profile.html', form=form, devices = current_app.devices)
    else:
        return render_template('profile.html', form=form, devices = None)


@main.route('/cpu', methods=['GET', 'POST'])
def cpu():
    return render_template('cpu_base.html')

@main.route('/cpus', methods=['GET', 'POST'])
def cpus():
    return render_template('cpus.html',stat = current_app.curr_device.g_stat)

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
    return render_template('softirqs.html',cpunum = current_app.curr_device.g_cpunum,softirqs = current_app.curr_device.g_softirqs)

@main.route('/interrupts', methods=['GET', 'POST'])
def interrupts():
    return render_template('interrupts.html',cpunum = current_app.curr_device.g_cpunum,interrupts = current_app.curr_device.g_interrupts)

@main.route('/update/all', methods=['GET', 'POST'])
def update_all():
    data=request.form.get('data')
    id=request.form.get('id')
    if hasattr(current_app,'curr_device'):
        if data =='loadavg':
            #负载统计
            print('get loadavg')
            ret = g_loadavg.update()
            #cpu时间统计
            newstat = Stat(current_app.curr_device.zclient)
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
        
        if data == 'index':
            ret = []
            diff=[]
            misc=[]
            softirq=[]
            irq=[]
            mem=[]
            uptime=[]
            if hasattr(current_app.curr_device,'g_loadavg'):
                ret = current_app.curr_device.g_loadavg.getlast('all')
            if hasattr(current_app.curr_device,'g_stat'):
                diff = current_app.curr_device.g_stat.getlast('utilization')
                misc = current_app.curr_device.g_stat.getlast('misc')
                softirq = current_app.curr_device.g_stat.getlast('s_softirq')
                irq = current_app.curr_device.g_stat.getlast('h_all')
                mem= current_app.curr_device.g_meminfo.getlast('mem')
                uptime= current_app.curr_device.g_uptime.getlast('all',num=current_app.curr_device.g_cpunum)
            return jsonify({'result':'ok','loadavg':ret,'stat':diff,'ctxt':misc, 
                'softirq':softirq, 'intr':irq, 'mem':mem, 'uptime':uptime})

        if data == 'percpu':
            ret = {}
            if hasattr(current_app.curr_device,'g_stat'):
                for i in range(current_app.curr_device.g_stat.data[-1].cpunum):
                    ret[i] = current_app.curr_device.g_stat.getlast('utilization',i+1)
            return jsonify({'result':'ok','percpu':ret})

        if data == 'softirqs':
            ret = {}
            if hasattr(current_app.curr_device,'g_softirqs'):
                for i in range(current_app.curr_device.g_softirqs.data[-1].cpunum):
                    ret[i] = current_app.curr_device.g_softirqs.getlast('s_softirq',i)
            return jsonify({'result':'ok','softirqs':ret})

        if data == 'interrupts':
            ret = []
            if hasattr(current_app.curr_device,'g_interrupts'):
                ret = current_app.curr_device.g_interrupts.getlast('interrupts')
                print(ret)
            return jsonify({'result':'ok','interrupts':ret})
    else:
        return jsonify({'result':'error'})