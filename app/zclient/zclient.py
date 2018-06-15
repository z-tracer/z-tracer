import json
import socket
import time
import threading
import os

class Zclient:
    def __init__(self, clientip, port):
        self.clientip = clientip
        self.port = port
        self.bufferSize = 2048
        self.lock = threading.Lock()
        self.connect = 0

    def sendRequest(self, methodName, params):
        data = ''
        try:
            self.lock.acquire()
            input_data = {}
            input_data['method'] = methodName
            if params != None:
                input_data['params'] = params
            #print(input_data)
            
            dumped_data = json.dumps(input_data)
            self.sock.send(dumped_data.encode())
            serverResponse = str.encode("")
            end = str.encode("sometimewhenitrains")
            while True:
                data = self.sock.recv(self.bufferSize)
                serverResponse = serverResponse + data
                if end in serverResponse:
                    serverResponse = serverResponse.replace(end,str.encode(""))
                    break
            responseJsonDecoded = json.loads(serverResponse.decode()) # decode the data received
            if responseJsonDecoded:
                return responseJsonDecoded['result']
            else:
                return None

        except Exception as error:
            print('eeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeer'+str(error))
            return None

        finally:
            self.lock.release()
            pass

    def close(self):
         if (self.sock):
            self.sock.close()

    def checkconnect(self):
        try:
            self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.sock.connect((self.clientip, self.port))
            print('check connect...')
            data = self.sendRequest('checkconnect',None)
            if data == 'done!':
                self.connect = 1
                print('ok!')
                return 1
            else:
                return 0
        except Exception as error:
            return 0
        finally:
            pass

    def get_procinfo(self, filename):
        if 1:
            params = {}
            params['path'] = filename
            data = self.sendRequest('readfile',params)
            if data != None:
                if len(data) == 0:
                    return None
            return data
        else:
            try:
              fh = open(filename, 'r')
              data = fh.read()
            except IOError:
              print("Error: cant open file %s" % (filename))
              return None
            else:
              fh.close()
            return data

    def get_cmdout(self, cmdline):
        if 1:
            params = {}
            params['cmd'] = cmdline
            outputs = self.sendRequest('runcmd',params)
            if outputs != None:
                if len(outputs) == 0:
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