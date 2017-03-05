import broadlink
import time, os, sys, traceback

from pioneer_python_cli.telnet import Connection
from pioneer_python_cli.telnet import ReadThread


from eve import Eve
from flask import jsonify
from eve_swagger import swagger, add_documentation

app = Eve()
app.register_blueprint(swagger)

# required. See http://swagger.io/specification/#infoObject for details.
app.config['SWAGGER_INFO'] = {
    'title': 'smart-home-hub API',
    'version': '1.0',
    'description': 'an API description',
    'termsOfService': 'BSD',
    'contact': {
        'name': 'jtomaszk',
    },
    'license': {
        'name': 'BSD',
        'url': 'https://github.com/nicolaiarocci/eve-swagger/blob/master/LICENSE',
    }
}

add_documentation({'paths': {'/play' : {'get': {'parameters': [
    {
        'code_name': 'string'
    }]
}}}})

host_addr = "192.168.1.51"
host_mac = "34ea34e7d239"
file_dir = "rm3-codes/"

#@app.route('/app', methods=['GET'])
#def index():
#    return app.send_static_file('index.html')

HOST = "192.168.1.52"
c = Connection(HOST)

readThread = ReadThread(c)
readThread.daemon = True
readThread.start()

@app.route('/send/<command>', methods=['GET'])
def send(command):
    r = c.run_command(command)
    if r is not None and r.ok and r.status == "read":
        r = c.read_response(1)
    return jsonify(r)


@app.route('/play/<path:code_name>', methods=['GET'])
def play_code(code_name):
    try:
        file_path = file_dir + code_name + '.hex'
        file = open(file_path, 'r')
        myhex = file.read()

        device = broadlink.rm(host=(host_addr,80), mac=bytearray.fromhex(host_mac))
        device.auth()
        time.sleep(1)
        device.host

        hex_decoded = myhex.decode('hex')
        device.send_data(hex_decoded)
        return jsonify(ok=True)
    except ValueError:
        return jsonify(ok=False, msg="Error when sending")
    except IOError:
        traceback.print_exc(file=sys.stdout)
        return jsonify(ok=False, msg="Error on read file " + file_path)


@app.route('/list', methods=['GET'])
def list():
    d = dict()
    for root, dirs, files in os.walk(file_dir):
        for file in files:
            if file.endswith(".hex"):
                file_path = os.path.join(root, file)
                dirname = os.path.dirname(file_path)
                d.setdefault(dirname[len(file_dir):], []).append(file[:-4])
    return jsonify(ok=True, list=d)

def mkdirs(file_path):
    if not os.path.exists(os.path.dirname(file_path)):
        try:
            os.makedirs(os.path.dirname(file_path))
        except OSError as exc: # Guard against race condition
            if exc.errno != errno.EEXIST:
                raise


@app.route('/record/<path:code_name>', methods=['GET'])
def record_code(code_name):
    try:
        device = broadlink.rm(host=(host_addr,80), mac=bytearray.fromhex(host_mac))
        device.auth()
        time.sleep(1)
        device.host
        device.enter_learning()
        time.sleep(5)
        ir_packet = device.check_data()

        if ir_packet == None:
            return jsonify(ok=False, msg="No button press read")
        else:  # record learned hex code to file
            #convert code to hex
            myhex = str(ir_packet).encode('hex');

            file_path = file_dir + code_name + '.hex'
            mkdirs(file_path)

            with open(file_path, 'w') as f:
                f.write(myhex)
                f.close()

    except IOError:
        traceback.print_exc(file=sys.stdout)
        return jsonify(ok=False, msg="Error on write file")

    return jsonify(ok=True)

if __name__ == '__main__':
    app.run(host='0.0.0.0')
