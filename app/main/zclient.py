import json
import socket

class Zclient:
    def __init__(self, server='172.16.136.205', port=1234):
        self.server = server
        self.port = port
        self.bufferSize = 2048
        
    def sendRequest(self, methodName, params):
        sock = None

        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.connect((self.server, self.port))

            input_data = {}
            input_data['method'] = methodName
            input_data['params'] = params

            dumped_data = json.dumps(input_data)

            sock.send(dumped_data.encode())
            data = sock.recv(self.bufferSize)
            serverResponse = data
            responseJsonDecoded = json.loads(serverResponse.decode()) # decode the data received
            if responseJsonDecoded:
                return responseJsonDecoded['result']
            else:
                return None

        except Exception as error:
            print('eeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeer')
            pass

        finally:
            if (sock):
                sock.close()
