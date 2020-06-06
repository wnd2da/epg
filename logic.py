# -*- coding: utf-8 -*-
#########################################################
# python
import os
import sys
import traceback
import time
from datetime import datetime, timedelta
import logging
import urllib
import urllib2
import re
import time
from operator import itemgetter
import threading

# third-party
import requests
from requests.auth import HTTPDigestAuth, HTTPBasicAuth
from flask import Blueprint, request, Response, send_file, render_template, redirect, jsonify
from sqlalchemy import desc
from lxml import etree as ET

# sjva 공용
from framework import app, db, scheduler, path_data, celery
from framework.job import Job
from framework.util import Util
from system.model import ModelSetting as SystemModelSetting

# 패키지
from .plugin import logger, package_name
from .model import ModelSetting
from .model import ModelEpgMakerSetting, ModelEpgMakerChannel, ModelEpgMakerProgram, ModelEpgMakerDaum
from .logic_normal import LogicNormal
#########################################################

class Logic(object):
    db_default = {
        'db_version' : '1',
        'auto_start' : 'False',
        'interval' : '120',

        'updated_tvheadend' : u'No File',
        'updated_klive' : 'No File',
        'updated_hdhomerun' : 'No File',
        'updated_all' : '',

        #'updated_klive_lc' : '',
        #'updated_plex_lc' : '',
    }

    @staticmethod
    def db_init():
        try:
            for key, value in Logic.db_default.items():
                if db.session.query(ModelSetting).filter_by(key=key).count() == 0:
                    db.session.add(ModelSetting(key, value))
            db.session.commit()
            Logic.migration()
        except Exception as e: 
            logger.error('Exception:%s', e)
            logger.error(traceback.format_exc())

    @staticmethod
    def plugin_load():
        try:
            Logic.db_init()
            if ModelSetting.get_bool('auto_start'):
                Logic.scheduler_start()
            from plugin import plugin_info
            Util.save_from_dict_to_json(plugin_info, os.path.join(os.path.dirname(__file__), 'info.json'))   
        except Exception as e: 
            logger.error('Exception:%s', e)
            logger.error(traceback.format_exc())


    @staticmethod
    def plugin_unload():
        pass

    @staticmethod
    def scheduler_start():
        try:
            logger.debug('%s scheduler_start' % package_name)
            job = Job(package_name, package_name, ModelSetting.get('interval'), Logic.scheduler_function, u"EPG 업데이트", False)
            scheduler.add_job_instance(job) 
        except Exception as e: 
            logger.error('Exception:%s', e)
            logger.error(traceback.format_exc())

    
    @staticmethod
    def scheduler_stop():
        try:
            logger.debug('%s scheduler_stop' % package_name)
            scheduler.remove_job(package_name)
        except Exception as e: 
            logger.error('Exception:%s', e)
            logger.error(traceback.format_exc())

    @staticmethod
    def scheduler_function():
        try:
            LogicNormal.scheduler_function()
        except Exception as e:
            logger.error('Exception:%s', e)
            logger.error(traceback.format_exc())

    @staticmethod
    def reset_db():
        try:
            return True
        except Exception as e: 
            logger.error('Exception:%s', e)
            logger.error(traceback.format_exc())
            return False

    
    @staticmethod
    def one_execute():
        try:
            if scheduler.is_include(package_name):
                if scheduler.is_running(package_name):
                    ret = 'is_running'
                else:
                    scheduler.execute_job(package_name)
                    ret = 'scheduler'
            else:
                def func():
                    time.sleep(2)
                    Logic.scheduler_function()
                threading.Thread(target=func, args=()).start()
                ret = 'thread'
        except Exception as e: 
            logger.error('Exception:%s', e)
            logger.error(traceback.format_exc())
            ret = 'fail'
        return ret

    @staticmethod
    def migration():
        pass

    