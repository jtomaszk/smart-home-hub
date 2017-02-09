import broadlink
import time

from eve import Eve
from flask import jsonify

app = Eve()
host_addr = "192.168.1.51"
host_mac = "34ea34e7d239"
file_dir = "rm3-codes/"

@app.route('/play/<path:code_name>', methods=['GET'])
def play_code(code_name):
    try:
        file_path = file_dir + code_name
        file = open(file_path, 'r')
        myhex = file.read()

        device = broadlink.rm(host=(host_addr,80), mac=bytearray.fromhex(host_mac))
        device.auth()
        time.sleep(1)
        device.host

        device.send_data(myhex.decode('hex'))
        return jsonify(ok=True)
    except ValueError:
        return jsonify(ok=False, msg="Error when sending")
    except IOError:
        return jsonify(ok=False, msg="Error on read file " + file_path)


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
        #convert code to hex
        myhex = str(ir_packet).encode('hex');

        if ir_packet == None:
            return jsonify(ok=False, msg="No button press read")
        else:  # record learned hex code to file
            f = open(file_path + code_name,'w')
            f.write(myhex)
            f.close()

    except IOError:
        return jsonify(ok=False, msg="Error on write file")

    return jsonify(ok=True)

if __name__ == '__main__':
    app.run()
