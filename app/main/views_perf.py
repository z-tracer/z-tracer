from flask import render_template, request, current_app, jsonify
from . import main
from .forms import PerfForm
from ..record.perf import Perf
import os

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
    cpu=request.form.get('cpu')
    pid=request.form.get('pid')
    gtime=request.form.get('time')
    hz=request.form.get('hz')
    adv=request.form.get('adv')
    if not hasattr(current_app.curr_device,'perf'):
        current_app.curr_device.perf = Perf(current_app.curr_device.zclient)
    if len(cpu) > 0:
        current_app.curr_device.perf.cpu = cpu
    if len(pid) > 0:
        current_app.curr_device.perf.pid = pid
    if len(adv) > 0:
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
    if not hasattr(current_app.curr_device,'perf'):
        current_app.curr_device.perf = Perf(current_app.curr_device.zclient)
    ret = current_app.curr_device.perf.stop()
    if ret == 'ok':
        print('stop')
        return jsonify({'result':'ok'})
    else:
        return jsonify({'result':'error'})

@main.route('/perf/checkdone', methods=['GET', 'POST'])
def perf_checkdone():
    if not hasattr(current_app.curr_device,'perf'):
        current_app.curr_device.perf = Perf(current_app.curr_device.zclient)
    ret = current_app.curr_device.perf.checkdone()
    if ret == "done":
        print('perf done write to app/static/perf/perf.stack')
        data = current_app.curr_device.perf.script()
        if data != None:
            fh = open('app/static/perf/perf.stack', 'wb')
            fh.write(data.encode())
            fh.close()
        return jsonify({'result':'ok'})
    else:
        return jsonify({'result':'error'})

@main.route('/perf/perfscript', methods=['GET', 'POST'])
def perf_perfscript():
    if os.path.exists('app/static/perf/perf.stack'):
        os.remove('app/static/perf/perf.stack')
    cpu=request.form.get('cpu')
    pid=request.form.get('pid')
    gtime=request.form.get('time')
    hz=request.form.get('hz')
    adv=request.form.get('adv')
    if not hasattr(current_app.curr_device,'perf'):
        current_app.curr_device.perf = Perf(current_app.curr_device.zclient)
    if len(cpu) > 0:
        current_app.curr_device.perf.cpu = cpu
    if len(pid) > 0:
        current_app.curr_device.perf.pid = pid
    if len(adv) > 0:
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
