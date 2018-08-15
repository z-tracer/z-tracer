import json
import socket
import threading
import os

class Zclient:
    def __init__(self, clientip, port):
        self.clientip = clientip
        self.port = port
        self.buffersize = 8192
        self.lock = threading.Lock()
        self.connect = 0
        self.sock = None

    def sendrequestraw(self, methodname, params):
        data = ''
        try:
            self.lock.acquire()
            input_data = {}
            input_data['method'] = methodname
            if params is not None:
                input_data['params'] = params
            #print(input_data)

            dumped_data = json.dumps(input_data)
            self.sock.send(dumped_data.encode())
            server_response = str.encode("")
            end = str.encode("sometimewhenitrains")
            while True:
                data = self.sock.recv(self.buffersize)
                if data == b'':
                    print('connect out')
                    self.connect = 0
                    return None
                server_response = server_response + data
                if end in server_response:
                    server_response = server_response.replace(end, str.encode(""))
                    break
            response_json_decoded = json.loads(server_response.decode())
            if response_json_decoded:
                return response_json_decoded['result']
            else:
                return None

        except Exception as error:
            print('eeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeer'+str(error))
            return None

        finally:
            self.lock.release()

    def sendrequest(self, methodname, params):
        if self.connect != 0:
            return self.sendrequestraw(methodname, params)
        else:
            return None

    def close(self):
        if self.sock:
            self.sock.close()

    def checkconnect(self):
        try:
            self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.sock.connect((self.clientip, self.port))
            print('check connect...')
            data = self.sendrequestraw('checkconnect', None)
            if data == 'done!':
                self.connect = 1
                print('ok!')
                return 1
            else:
                return 0
        except Exception as error:
            print('eeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeer'+str(error))
            return 0
        finally:
            pass

    def get_procinfo(self, filename):
        if 1:
            params = {}
            params['path'] = filename
            data = self.sendrequest('readfile', params)
            if data is not None:
                if not data:
                    return None
            return data
        else:
            try:
                fileh = open(filename, 'r')
                data = fileh.read()
            except IOError:
                print("Error: cant open file %s" % (filename))
                return None
            else:
                fileh.close()
            return data

    def get_cmdout(self, cmdline):
        if 1:
            params = {}
            params['cmd'] = cmdline
            outputs = self.sendrequest('runcmd', params)
            if outputs is not None:
                if not outputs:
                    return None
            return outputs
        else:
            try:
                file = os.popen(cmdline)
                outputs = file.read()
            except IOError:
                print("Error: cant run cmd %s" % (cmdline))
                return None
            else:
                file.close()
            return outputs

    def get_perfreport(self, cmdline):
        if 1:
            params = {}
            params['cmd'] = cmdline
            outputs = self.sendrequest('perfreport', params)
            if outputs is not None:
                if not outputs:
                    return None
            return outputs
        else:
            try:
                os.system(cmdline)
            except IOError:
                print("Error: cant run cmd %s" % (cmdline))
                return None
            else:
                pass

    def get_perfscript(self, cmdline):
        if 1:
            params = {}
            params['cmd'] = cmdline
            self.buffersize = 1024*1024   #在这里临时将数据缓冲扩大，不然传输会很慢
            outputs = self.sendrequest('perfscript', params)
            self.buffersize = 8192
            if outputs is not None:
                if not outputs:
                    return None
            return outputs
        else:
            try:
                os.system(cmdline)
            except IOError:
                print("Error: cant run cmd %s" % (cmdline))
                return None
            else:
                pass

    #use for don't trace perf self, in syscall trace too many write while record
    def perfastart(self, cmdline):
        params = {}
        params['cmd'] = cmdline
        outputs = self.sendrequest('perfastart', params)
        if outputs is not None:
            if not outputs:
                return None
        return outputs

    def acmdstart(self, cmdline):
        params = {}
        params['cmd'] = cmdline
        outputs = self.sendrequest('acmdstart', params)
        if outputs is not None:
            if not outputs:
                return None
        return outputs

    def acmdstop(self):
        params = {}
        outputs = self.sendrequest('acmdstop', params)
        if outputs is not None:
            if not outputs:
                return None
        return outputs

    def acmdcheckdone(self):
        params = {}
        outputs = self.sendrequest('acmdcheckdone', params)
        if outputs is not None:
            if not outputs:
                return None
        return outputs

    def acmdwait(self):
        params = {}
        outputs = self.sendrequest('acmdwait', params)
        if outputs is not None:
            if not outputs:
                return None
        return outputs

    def acmdresult(self, cmdline):
        params = {}
        params['cmd'] = cmdline
        self.buffersize = 1024*1024
        outputs = self.sendrequest('acmdresult', params)
        self.buffersize = 8192
        if outputs is not None:
            if not outputs:
                return None
        return outputs

    def get_seqread(self, filename):
        if 1:
            params = {}
            params['path'] = filename
            data = self.sendrequest('seqread', params)
            if data is not None:
                if not data:
                    return None
            return data
        else:
            try:
                fileh = open(filename, 'r')
                data = fileh.read()
            except IOError:
                print("Error: cant open file %s" % (filename))
                return None
            else:
                fileh.close()
            return data
