# -*- coding: utf-8 -*-
#########################################################
# python
import os
import sys
import traceback
import threading
import time
from datetime import datetime, timedelta

# third-party
import requests
from flask import Blueprint, request, Response, render_template, redirect, jsonify, redirect, send_file
from flask_login import login_user, logout_user, current_user, login_required

# sjva 공용
from framework.logger import get_logger
from framework import app, db, scheduler, path_data, socketio, path_app_root, check_api
            
# 패키지
package_name = __name__.split('.')[0]
logger = get_logger(package_name)
from .model import ModelSetting
from .logic import Logic
from .logic_normal import LogicNormal

#########################################################
from .model import ModelEpgMakerChannel

blueprint = Blueprint(package_name, package_name, url_prefix='/%s' %  package_name, template_folder=os.path.join(os.path.dirname(__file__), 'templates'))

menu = {
    'main' : [package_name, 'EPG'],
    'sub' : [
        ['setting', '설정'], ['log', '로그']
    ], 
    'category' : 'tv'
}  

plugin_info = {
    'version' : '1.0',
    'name' : 'epk',
    'category_name' : 'tv',
    'developer' : 'soju6jan',
    'description' : 'EPG 생성 플러그인',
    'home' : 'https://github.com/soju6jan/epg',
    'more' : '',
}

def plugin_load():
    Logic.plugin_load()

def plugin_unload():
    Logic.plugin_unload()


#########################################################
# WEB Menu   
#########################################################
@blueprint.route('/')
def home():
    return redirect('/%s/setting' % package_name)

@blueprint.route('/<sub>')
@login_required
def detail(sub): 
    if sub == 'setting':
        arg = ModelSetting.to_dict()
        arg['scheduler'] = str(scheduler.is_include(package_name))
        arg['is_running'] = str(scheduler.is_running(package_name))
        from system.model import ModelSetting as SystemModelSetting
        ddns = SystemModelSetting.get('ddns')  
        arg['ddns'] = ddns
        apikey = None
        if SystemModelSetting.get_bool('auth_use_apikey'):
            apikey = SystemModelSetting.get('auth_apikey')
        for tmp in ['tvheadend', 'klive', 'hdhomerun']:
            arg[tmp] = '{ddns}/{package_name}/api/{sub}'.format(ddns=ddns, package_name=package_name, sub=tmp)
            if apikey is not None:
                arg[tmp] += '?apikey=' + apikey
        return render_template('{package_name}_{sub}.html'.format(package_name=package_name, sub=sub), arg=arg)
    elif sub == 'log':
        return render_template('log.html', package=package_name)
    return render_template('sample.html', title='%s - %s' % (package_name, sub))

#########################################################
# For UI                                                          
#########################################################
@blueprint.route('/ajax/<sub>', methods=['GET', 'POST'])
@login_required
def ajax(sub):
    logger.debug('AJAX %s %s', package_name, sub)
    try:
        if sub == 'setting_save':
            ret = ModelSetting.setting_save(request)
            return jsonify(ret)
        elif sub == 'scheduler':
            go = request.form['scheduler']
            if go == 'true':
                Logic.scheduler_start()
            else:
                Logic.scheduler_stop()
            return jsonify(go)
        elif sub == 'one_execute':
            ret = Logic.one_execute()
            return jsonify(ret)
        elif sub == 'make_xml':
            sub = request.form['sub']
            ret = LogicNormal.make_xml(sub, show_msg=True)
            return jsonify(ret)
        elif sub == 'get_channel_list':
            ret = ModelEpgMakerChannel.get_channel_list()
            logger.debug('channel_list :%s', len(ret))
             
            return jsonify([x.as_dict() for x in ret])
            # return [x.as_dict() for x in ret]

    except Exception as e: 
        logger.error('Exception:%s', e)
        logger.error(traceback.format_exc())


#########################################################
# API
#########################################################
@blueprint.route('/api/<sub>', methods=['GET', 'POST'])
@check_api
def api(sub):
    try:
        filename = os.path.join(path_data, 'output', 'xmltv_%s.xml' % sub)
        if not os.path.exists(filename):
            LogicNormal.make_xml(sub)
        return send_file(filename, mimetype='application/xml')
    except Exception as e: 
        logger.error('Exception:%s', e)
        logger.error(traceback.format_exc())
