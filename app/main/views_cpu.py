from flask import render_template, current_app
from . import main

@main.route('/cpu', methods=['GET', 'POST'])
def cpu():
    return render_template('cpu_base.html')

@main.route('/cpus', methods=['GET', 'POST'])
def cpus():
    return render_template('cpus.html', stat=current_app.curr_device.g_stat)

#@main.route('/loadavg', methods=['GET', 'POST'])
#def loadavg():
    #chart = g_loadavg.draw()
    #return render_template('loadavg.html', chart=chart)

#@main.route('/update/loadavg', methods=['GET', 'POST'])
#def update_loadavg():
    #chart = g_loadavg.draw()
    #return jsonify({'result':'ok', 'src':chart})

@main.route('/softirqs', methods=['GET', 'POST'])
def softirqs():
    return render_template('softirqs.html', cpunum=current_app.curr_device.g_cpunum, \
    softirqs=current_app.curr_device.g_softirqs)

@main.route('/interrupts', methods=['GET', 'POST'])
def interrupts():
    return render_template('interrupts.html', cpunum=current_app.curr_device.g_cpunum, \
    interrupts=current_app.curr_device.g_interrupts)

@main.route('/syscalls', methods=['GET', 'POST'])
def syscalls():
    return render_template('syscalls.html')

@main.route('/signal', methods=['GET', 'POST'])
def signal():
    return render_template('signal.html')
