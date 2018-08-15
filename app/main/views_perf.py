import os
from flask import render_template, request, current_app, jsonify
from app.flamescope.util.stack import generate_stack
from . import main
from .forms import PerfForm
from ..record.perf import Perf


@main.route('/perf', methods=['GET', 'POST'])
def perf():
    form = PerfForm()
    form.cpu.data = None
    form.pid.data = None
    form.time.data = None
    form.hz.data = current_app.config['DEFAULT_PERF_HZ']
    return render_template('perf.html', form=form)

@main.route('/perf/start', methods=['GET', 'POST'])
def perf_start():
    if os.path.exists('app/static/perf/perf.stack'):
        os.remove('app/static/perf/perf.stack')
    cpu = request.form.get('cpu')
    pid = request.form.get('pid')
    gtime = request.form.get('time')
    hz = request.form.get('hz')
    adv = request.form.get('adv')
    if not hasattr(current_app.curr_device, 'perf'):
        current_app.curr_device.perf = Perf(current_app.curr_device.zclient)
    if cpu:
        current_app.curr_device.perf.cpu = cpu
    if pid:
        current_app.curr_device.perf.pid = pid
    if adv:
        current_app.curr_device.perf.adv = adv
    current_app.curr_device.perf.time = gtime
    current_app.curr_device.perf.hz = hz
    ret = current_app.curr_device.perf.start()
    if ret == 'ok':
        print('start ok')
        return jsonify({'result':'ok'})
    else:
        print('start fail')
        return jsonify({'result':'error'})

@main.route('/perf/stop', methods=['GET', 'POST'])
def perf_stop():
    if not hasattr(current_app.curr_device, 'perf'):
        current_app.curr_device.perf = Perf(current_app.curr_device.zclient)
    ret = current_app.curr_device.perf.stop()
    if ret == 'ok':
        print('stop')
        return jsonify({'result':'ok'})
    else:
        return jsonify({'result':'error'})

@main.route('/perf/checkdone', methods=['GET', 'POST'])
def perf_checkdone():
    if not hasattr(current_app.curr_device, 'perf'):
        current_app.curr_device.perf = Perf(current_app.curr_device.zclient)
    ret = current_app.curr_device.perf.checkdone()
    if ret == "done":
        print('perf done write to app/static/perf/perf.stack')
        data = current_app.curr_device.perf.script("--header")
        if data is not None:
            fileh = open('app/static/perf/perf.stack', 'wb')
            fileh.write(data.encode())
            fileh.close()
        return jsonify({'result':'ok'})
    else:
        return jsonify({'result':'error'})

@main.route('/perf/perfscript', methods=['GET', 'POST'])
def perf_perfscript():
    if os.path.exists('app/static/perf/perf.stack'):
        os.remove('app/static/perf/perf.stack')
    cpu = request.form.get('cpu')
    pid = request.form.get('pid')
    gtime = request.form.get('time')
    hz = request.form.get('hz')
    adv = request.form.get('adv')
    if not hasattr(current_app.curr_device, 'perf'):
        current_app.curr_device.perf = Perf(current_app.curr_device.zclient)
    if cpu:
        current_app.curr_device.perf.cpu = cpu
    if pid:
        current_app.curr_device.perf.pid = pid
    if adv:
        current_app.curr_device.perf.adv = adv
    current_app.curr_device.perf.time = gtime
    current_app.curr_device.perf.hz = hz
    current_app.curr_device.perf.record()
    if os.path.exists('app/static/perf/perf.stack'):
        print('file find')
        return jsonify({'result':'ok'})
    else:
        print('file not found')
        return jsonify({'result':'error'})

@main.route('/perf/probestart', methods=['GET', 'POST'])
def perf_probestart():
    if os.path.exists('app/static/perf/perf.stack'):
        os.remove('app/static/perf/perf.stack')
    if not hasattr(current_app.curr_device, 'perf'):
        current_app.curr_device.perf = Perf(current_app.curr_device.zclient)
    current_app.curr_device.perf.delallprobe()
    func = request.form.get('func')
    arg = request.form.get('arg')
    exe = request.form.get('exe')
    retval = request.form.get('retval')
    if func:
        current_app.curr_device.perf.func = func
    else:
        return jsonify({'result':'填写函数名称'})
    if arg:
        current_app.curr_device.perf.arg = arg
    if exe:
        current_app.curr_device.perf.exe = exe
    if retval == 'true':
        current_app.curr_device.perf.trace_ret = 1
    else:
        current_app.curr_device.perf.trace_ret = 0
    ret = current_app.curr_device.perf.addprobe()
    if ret == 'ok':
        ret = current_app.curr_device.perf.probestart()
        if ret == 'ok':
            print('start ok')
            return jsonify({'result':'ok'})
    print('start fail', ret)
    return jsonify({'result':ret})

@main.route('/perf/probestop', methods=['GET', 'POST'])
def perf_probestop():
    if not hasattr(current_app.curr_device, 'perf'):
        current_app.curr_device.perf = Perf(current_app.curr_device.zclient)
    ret = current_app.curr_device.perf.stop()
    if ret == 'ok':
        print('stop')
        ret = current_app.curr_device.perf.checkdone()
        while ret != "done":
            ret = current_app.curr_device.perf.checkdone()
        print('perf done write to app/static/perf/perf.stack')
        data = current_app.curr_device.perf.script()
        if data is not None:
            fileh = open('app/static/perf/perf.stack', 'wb')
            fileh.write(data.encode())
            fileh.close()
        flamedata = generate_stack('perf.stack', None, None)
        if current_app.curr_device.perf.arg is not None:
            heatmap = current_app.curr_device.perf.get_arg_heatmap(20, 50)
        else:
            heatmap = None
        if current_app.curr_device.perf.trace_ret == 1:
            retheatmap = current_app.curr_device.perf.get_ret_heatmap(20, 50)
        else:
            retheatmap = None
        current_app.curr_device.perf.delprobe()
        return jsonify({'result':'ok', 'flamedata':flamedata, 'heatmap':heatmap, \
                        'retheatmap':retheatmap})
    else:
        return jsonify({'result':'error'})

@main.route('/perf/probefunclist', methods=['GET', 'POST'])
def perf_probefunclist():
    func_filter = request.form.get('filter')
    exe = request.form.get('exe')
    if not hasattr(current_app.curr_device, 'perf'):
        current_app.curr_device.perf = Perf(current_app.curr_device.zclient)
    ret = current_app.curr_device.perf.probe_available_functions(exe, func_filter)
    if ret is not None and 'Failed' in ret:
        return jsonify({'result':ret})
    return jsonify({'result':'ok', 'funclist':current_app.curr_device.perf.available_functions})

@main.route('/perf/probearglist', methods=['GET', 'POST'])
def perf_probearglist():
    func = request.form.get('func')
    exe = request.form.get('exe')
    if not hasattr(current_app.curr_device, 'perf'):
        current_app.curr_device.perf = Perf(current_app.curr_device.zclient)
    ret = current_app.curr_device.perf.probe_available_args(exe, func)
    return jsonify({'result':ret})

@main.route('/perf/syscallstart', methods=['GET', 'POST'])
def perf_syscallstart():
    if os.path.exists('app/static/perf/perf.stack'):
        os.remove('app/static/perf/perf.stack')
    if not hasattr(current_app.curr_device, 'perf'):
        current_app.curr_device.perf = Perf(current_app.curr_device.zclient)
    pid = request.form.get('pid')
    syscall = request.form.get('syscall')
    ret = current_app.curr_device.perf.syscallstart(pid, syscall)
    if ret == 'ok':
        print('start ok')
        return jsonify({'result':'ok'})
    else:
        print('start fail', ret)
        return jsonify({'result':ret})

@main.route('/perf/syscallstop', methods=['GET', 'POST'])
def perf_syscallstop():
    if not hasattr(current_app.curr_device, 'perf'):
        current_app.curr_device.perf = Perf(current_app.curr_device.zclient)
    ret = current_app.curr_device.perf.stop()
    if ret == 'ok':
        print('stop')
        ret = current_app.curr_device.perf.checkdone()
        while ret != "done":
            ret = current_app.curr_device.perf.checkdone()
        print('perf done write to app/static/perf/perf.stack')
        data = current_app.curr_device.perf.script('--fields pid,comm,event')
        if data is not None:
            fileh = open('app/static/perf/perf.stack', 'wb')
            fileh.write(data.encode())
            fileh.close()
            ret = current_app.curr_device.perf.syscallwalk()
            print({'result':'ok', 'piddict':ret[0], 'syscalldict':ret[1]})
            return jsonify({'result':'ok', 'piddict':ret[0], 'syscalldict':ret[1], 'sortdict':ret[2]})
    return jsonify({'result':'error'})
