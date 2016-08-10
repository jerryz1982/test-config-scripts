from flask import Flask, jsonify, make_response, request
import json
import os
import base64
import download_image
import logging
from logging.handlers import RotatingFileHandler
import time
from bs4 import BeautifulSoup

app = Flask(__name__)

@app.route('/build_api/v1/builds', methods=['GET'])
def get_builds():
    try:
        builds = os.listdir(CONFIGS["tftp_path"])
    except Exception, e:
        return jsonify({
            'result': 'error',
            'error_msg': e.__str__() 
        })
    else:
        return jsonify({
            'result': 'ok',
            'builds': builds
        })
    

@app.route('/build_api/v1/latest', methods=['GET'])
def get_latest():
    project_id= request.args.get('project_id') or "123"
    interim = request.args.get('interim') or "false"
    builds_url = "https://info.fortinet.com/builds?build_history_grid_col=0&build_history_grid_q=&magic_grid_id=build_history_grid&project_id=" + project_id + "&show_interim=" + interim + "&version_filter=All&action=build_history&controller=infosite"
    username = CONFIGS["info_site"]["username"]
    password = CONFIGS["info_site"]["password"]
    builds_page = download_image._download_content(username, password, builds_url).text
    parsed_page = BeautifulSoup(builds_page, "html.parser")
    return jsonify({
        'build': parsed_page.table.find_all(link=True)[0].td.contents[0]
    })

@app.route('/build_api/v1/builds/<build_dir>', methods=['POST'])
def post_build(build_dir):
    download_url = request.form['download_url']
    app.logger.info(download_url)
    filename = download_url.split('/')[-1]
    tftp_path = CONFIGS["tftp_path"]
    save_path = os.path.join(tftp_path, build_dir)
    file_path = os.path.join(save_path, filename)
    if os.path.isfile(file_path):
        return jsonify({
            'result': 'ok',
            'build': filename,
            'status': 'existed'
        })
    else:
        app.logger.info('downloading ...')
        try:
            username = CONFIGS["info_site"]["username"]
            password = CONFIGS["info_site"]["password"]
            start_time = time.time()
            download_image.main(username, password, download_url, save_path)
            end_time = time.time()
        except Exception, e:
            return jsonify({
                'result': 'error',
                'error_msg': e.__str__() 
            })

        return jsonify({
            'result': 'ok',
            'build': filename,
            'status': 'downloaded',
            'seconds': round(end_time-start_time,2)
        })
        

@app.route('/')
def hello():
    return '''
example: /build_api/v1/tasks get
some
    '''

@app.route('/status')
def status():
    app.logger.info("status")
    return "running"


@app.errorhandler(404)
def not_found(error):
    return make_response(jsonify({
            'result': 'error',
            'error_msg': 'Not found' 
            }), 404)

class CheckError(Exception): pass

def _check_config(the_config):
    if not os.path.isdir(the_config["tftp_path"]):
        raise CheckError("The path {0} is not a dir!".format(
                the_config["tftp_path"]))
    the_config["info_site"]["password"] = base64.b64decode(
            the_config["info_site"]["encrypted_password"])
    return True

def _before_run():
    global CONFIGS
    CONFIGS = json.load(open('config_server.json'))
    _check_config(CONFIGS)
    # print(CONFIGS)


    # global app
    formatter = logging.Formatter(
        "[%(asctime)s] %(levelname)s - %(message)s")
    handler = RotatingFileHandler('server.log', maxBytes=10000000, backupCount=1)
    handler.setLevel(logging.INFO)
    handler.setFormatter(formatter)
    app.logger.addHandler(handler)




# def main():
#     # print(__name__)
    

if __name__ == '__main__':
    _before_run()
    app.run(debug=True, port=5050, host='0.0.0.0')
    print("ok")
