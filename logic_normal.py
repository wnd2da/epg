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
import threading

# third-party
import requests
from flask import Blueprint, request, Response, send_file, render_template, redirect, jsonify
from sqlalchemy import desc
from lxml import etree as ET

# sjva 공용
from framework import app, db, scheduler, path_data, celery, socketio
from framework.job import Job
from framework.util import Util
from system.model import ModelSetting as SystemModelSetting

# 패키지
from .plugin import logger, package_name
from .model import ModelSetting
from .model import ModelEpgMakerSetting, ModelEpgMakerChannel, ModelEpgMakerProgram, ModelEpgMakerDaum
#########################################################

class LogicNormal(object):

    @staticmethod
    def scheduler_function():
        try:
            from framework.common.util import SJVASupportControl
            ret = SJVASupportControl.epg_refresh()
            logger.debug(ret)
            try:
                import klive
                if ret == 'refresh' or (ret=='recent' and os.path.exists(os.path.join(path_data, 'output', 'xmltv_klive.xml')) == False):
                    LogicNormal.make_xml('klive')
            except:
                pass
            
            try:
                import tvheadend
                if ret == 'refresh' or (ret=='recent' and os.path.exists(os.path.join(path_data, 'output', 'xmltv_tvheadend.xml')) == False):
                    LogicNormal.make_xml('tvheadend')
            except:
                pass

            try:
                import hdhomerun
                if ret == 'refresh' or (ret=='recent' and os.path.exists(os.path.join(path_data, 'output', 'xmltv_hdhomerun.xml')) == False):
                    LogicNormal.make_xml('hdhomerun')
            except:
                pass
            
            """
            if app.config['config']['server']:
                if ret == 'refresh' or (ret=='recent' and os.path.exists(os.path.join(path_data, 'output', 'xmltv_all.xml')) == False):
                    if LogicNormal.make_xml('all'):
                        SJVASupportControl.epg_upload()
                        logger.debug('all epg make..')
            """
        except Exception as e: 
            logger.error('Exception:%s', e)
            logger.error(traceback.format_exc())

    
    @staticmethod
    def make_xml(call_from, show_msg=False):
        try:
            if app.config['config']['use_celery']:
                def thread_function():
                    ret = LogicNormal.make_xml_task.apply_async((call_from,))
                    #lock 이 걸림
                    result = ret.get()
                    if show_msg:
                        if result == True:
                            data = {'type':'success', 'msg' : u'%s EPG 생성이 완료되었습니다.' % call_from}
                            socketio.emit("notify", data, namespace='/framework', broadcast=True)   
                        else :
                            data = {'type':'warning', 'msg' : u'%s EPG 생성이 실패하였습니다.<br>%s' % (call_from, result)}
                            socketio.emit("notify", data, namespace='/framework', broadcast=True)   
                t = threading.Thread(target=thread_function, args=())
                t.start()
            else:
                LogicNormal.make_xml_task(call_from)
            return True
        except Exception as e: 
            logger.error('Exception:%s', e)
            logger.error(traceback.format_exc())
            
        return False
    
    @staticmethod
    @celery.task
    def make_xml_task(call_from):
        if call_from == 'tvheadend':
            try:
                import tvheadend
                channel_list = db.session.query(ModelEpgMakerChannel).all()
                tvh_list = tvheadend.LogicNormal.channel_list()
                if tvh_list is None:
                    return 'not setting tvheadend'
                for tvh_ch in tvh_list['lineup']:
                    search_name = ModelEpgMakerChannel.util_get_search_name(tvh_ch['GuideName'])
                    #logger.debug('%s %s', search_name, type(search_name))
                    for t in channel_list:
                        #logger.debug(t.search_name.split('|')) 
                        if search_name in t.search_name.split('|'):
                            tvh_ch['channel_instance'] = t
                            break
                    if 'channel_instance' not in tvh_ch:
                        logger.debug('NOT MATCH : %s', tvh_ch['GuideName'])
            except Exception as e: 
                logger.error('Exception:%s', e)
                logger.error(traceback.format_exc())

            try:
                generated_on = str(datetime.now())
                logger.debug(generated_on)
                #channel_list = db.session.query(ModelEpgMakerChannel).all()
                #for channel in channel_list:

                root = ET.Element('tv')
                root.set('generator-info-name', SystemModelSetting.get('ddns'))
                
                for tvh in tvh_list['lineup']:
                #for channel in channel_list:
                    logger.debug(tvh['GuideName'])
                    logger.debug(tvh)
                    if 'channel_instance' not in tvh:
                        logger.debug('no channel_instance :%s', tvh['GuideName'])
                        continue
                    #channel = tvh['channel_instance']
                    channel_tag = ET.SubElement(root, 'channel') 
                    #channel_tag.set('id', '%s' % channel.id)
                    

                    channel_tag.set('id', '%s' % tvh['uuid'])
                    if 'channel_instance' not in tvh:
                        logger.debug('no channel_instance :%s', tvh)
                        continue
                    icon_tag = ET.SubElement(channel_tag, 'icon')
                    icon_tag.set('src', tvh['channel_instance'].icon)
                    display_name_tag = ET.SubElement(channel_tag, 'display-name') 
                    #display_name_tag.text = channel.name
                    display_name_tag.text = tvh['GuideName']
                    display_name_tag = ET.SubElement(channel_tag, 'display-name') 
                    display_name_tag.text = str(tvh['GuideNumber'])

                for tvh in tvh_list['lineup']:
                #for channel in channel_list:
                    #logger.debug(tvh['GuideName'])
                    if 'channel_instance' not in tvh:
                        logger.debug('no channel_instance :%s', tvh)
                        continue
                    channel = tvh['channel_instance']
                    LogicNormal.make_channel(root, channel, tvh['uuid'])
            except Exception as e: 
                logger.error('Exception:%s', e)
                logger.error(traceback.format_exc())
                return traceback.format_exc()

        elif call_from == 'klive':
            try:
                import klive
                query = db.session.query(klive.ModelCustom)
                query = query.order_by(klive.ModelCustom.number)
                query = query.order_by(klive.ModelCustom.epg_id)
                klive_channel_list = query.all()
                root = ET.Element('tv')
                root.set('generator-info-name', SystemModelSetting.get('ddns'))
                
                for klive_channel in klive_channel_list:
                    epg_entity = ModelEpgMakerChannel.get_instance_by_name(klive_channel.epg_name)
                    if epg_entity is None:
                        # 2020-06-14
                        tmp = ModelEpgMakerChannel.get_match_name(klive_channel.title)
                        #tmp = ModelEpgMakerChannel.get_match_name(klive_channel.epg_name)
                        if tmp is not None :
                            epg_entity = ModelEpgMakerChannel.get_instance_by_name(tmp[0])
                    #if epg_entity is None:
                    #    logger.debug('no channel_instance :%s', klive_channel.title)
                    #    #continue
                    #    # 2020-06-08
                    #    # Plex dvr같은 경우 내용은 없어도 채널태그는 있어야함.
                    channel_tag = ET.SubElement(root, 'channel') 
                    channel_tag.set('id', '%s|%s' % (klive_channel.source, klive_channel.source_id))
                    if epg_entity is not None:
                        icon_tag = ET.SubElement(channel_tag, 'icon')
                        icon_tag.set('src', epg_entity.icon)
                    display_name_tag = ET.SubElement(channel_tag, 'display-name') 
                    display_name_tag.text = klive_channel.title
                    display_name_tag = ET.SubElement(channel_tag, 'display-name') 
                    display_name_tag.text = str(klive_channel.number)
                    display_name_tag = ET.SubElement(channel_tag, 'display-number') 
                    display_name_tag.text = str(klive_channel.number)

                for klive_channel in klive_channel_list:
                    epg_entity = ModelEpgMakerChannel.get_instance_by_name(klive_channel.epg_name)
                    if epg_entity is None:
                        tmp = ModelEpgMakerChannel.get_match_name(klive_channel.title)
                        if tmp is not None :
                            epg_entity = ModelEpgMakerChannel.get_instance_by_name(tmp[0])
                    if epg_entity is None:
                        logger.debug('no channel_instance :%s', klive_channel.title)
                        continue
                                     
                    LogicNormal.make_channel(root, epg_entity, '%s|%s' % (klive_channel.source, klive_channel.source_id), category=klive_channel.group)
            except Exception as e: 
                logger.error('Exception:%s', e)
                logger.error(traceback.format_exc())
                return traceback.format_exc()

        elif call_from == 'hdhomerun':
            try:
                import hdhomerun as hdhomerun
                channel_list = hdhomerun.LogicHDHomerun.channel_list(only_use=True)

                root = ET.Element('tv')
                root.set('generator-info-name', SystemModelSetting.get('ddns'))
                
                for channel in channel_list:
                    if channel.match_epg_name == '':
                        continue
                    epg_entity = ModelEpgMakerChannel.get_instance_by_name(channel.match_epg_name)
                    channel_tag = ET.SubElement(root, 'channel') 
                    channel_tag.set('id', '%s' % channel.id)
                    
                    if epg_entity is not None:
                        icon_tag = ET.SubElement(channel_tag, 'icon')
                        icon_tag.set('src', epg_entity.icon)
                    display_name_tag = ET.SubElement(channel_tag, 'display-name') 
                    display_name_tag.text = channel.scan_name
                    display_name_tag = ET.SubElement(channel_tag, 'display-name') 
                    display_name_tag.text = str(channel.ch_number)
                    display_name_tag = ET.SubElement(channel_tag, 'display-number') 
                    display_name_tag.text = str(channel.ch_number)

                for channel in channel_list:
                    epg_entity = ModelEpgMakerChannel.get_instance_by_name(channel.match_epg_name)
                    if epg_entity is None:
                        continue                    
                    LogicNormal.make_channel(root, epg_entity, '%s' % channel.id)
                   
            except Exception as e: 
                logger.error('Exception:%s', e)
                logger.error(traceback.format_exc())
                return traceback.format_exc()
        
        elif call_from == 'all':
            try:
                channel_list = ModelEpgMakerChannel.get_channel_list()
                root = ET.Element('tv')
                root.set('generator-info-name', SystemModelSetting.get('ddns'))
                for channel in channel_list:
                    channel_tag = ET.SubElement(root, 'channel') 
                    channel_tag.set('id', '%s' % channel.id)
                    icon_tag = ET.SubElement(channel_tag, 'icon')
                    icon_tag.set('src', channel.icon)
                    display_name_tag = ET.SubElement(channel_tag, 'display-name') 
                    display_name_tag.text = channel.name
                    display_name_tag = ET.SubElement(channel_tag, 'display-number') 
                    display_name_tag.text = str(channel.id)
                for channel in channel_list:
                    LogicNormal.make_channel(root, channel, '%s' % channel.id)
            except Exception as e: 
                logger.error('Exception:%s', e)
                logger.error(traceback.format_exc())
                return traceback.format_exc()
        try:
            tree = ET.ElementTree(root)
            filename = os.path.join(path_data, 'output', 'xmltv_%s.xml' % call_from)
            if os.path.exists(filename):
                os.remove(filename)
            tree.write(filename, pretty_print=True, xml_declaration=True, encoding="utf-8")
            ret = ET.tostring(root, pretty_print=True, xml_declaration=True, encoding="utf-8")

            ModelSetting.set('updated_%s' % call_from, datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
            db.session.commit()
            logger.debug('EPG2XML end....')
            return True
        except Exception as e: 
            logger.error('Exception:%s', e)
            logger.error(traceback.format_exc())

   
    @staticmethod
    def make_channel(root, channel_instance, channel_id, category=None):
        try:
            logger.debug('CH : %s', channel_instance.name)
            for program in channel_instance.programs:
                program_tag = ET.SubElement(root, 'programme')
                program_tag.set('start', program.start_time.strftime('%Y%m%d%H%M%S') + ' +0900')
                program_tag.set('stop', program.end_time.strftime('%Y%m%d%H%M%S') + ' +0900')
                program_tag.set('channel', '%s' % channel_id)
                title_tag = ET.SubElement(program_tag, 'title')
                title_tag.set('lang', 'ko')
                if program.re is not None and program.re:
                    title_tag.text = program.title + ' (재)'
                else:
                    title_tag.text = program.title
                if program.daum_info is not None:
                    if program.daum_info.poster is not None:
                        icon_tag = ET.SubElement(program_tag, 'icon')
                        icon_tag.set('src', program.daum_info.poster)
                    if program.daum_info.desc is not None:
                        desc_tag = ET.SubElement(program_tag, 'desc')
                        desc_tag.set('lang', 'ko')
                        desc_tag.text = program.daum_info.desc
                    if program.daum_info.actor is not None:
                        credits_tag = ET.SubElement(program_tag, 'credits')
                        for actor in program.daum_info.actor.split('|'):
                            try:
                                actor_tag = ET.SubElement(credits_tag, 'actor')
                                #logger.debug(actor)
                                name, role = actor.split(',')
                                actor_tag.set('role', role.strip())
                                actor_tag.text = name.strip()
                            except:
                                pass
                else:
                    if program.poster is not None:
                        icon_tag = ET.SubElement(program_tag, 'icon')
                        icon_tag.set('src', program.poster)
                    if program.desc is not None:
                        desc_tag = ET.SubElement(program_tag, 'desc')
                        desc_tag.set('lang', 'ko')
                        desc_tag.text = program.desc
                    if program.actor is not None:
                        credits_tag = ET.SubElement(program_tag, 'credits')
                        for actor in program.actor.split('|'):
                            try:
                                actor_tag = ET.SubElement(credits_tag, 'actor')
                                #logger.debug(actor)
                                name, role = actor.split(',')
                                actor_tag.set('role', role.strip())
                                actor_tag.text = name.strip()
                            except:
                                pass

                category_tag = ET.SubElement(program_tag, 'category')
                category_tag.set('lang', 'ko')
                category_tag.text = category if category is not None else channel_instance.category
                # TODO 영화부터 분기, 영화가 아니라면 모두 에피소드 처리해야함
                if not program.is_movie:
                    if program.episode_number is not None:
                        episode_num_tag = ET.SubElement(program_tag, 'episode-num')
                        episode_num_tag.set('system', 'onscreen')
                        episode_num_tag.text = program.episode_number
                        episode_num_tag = ET.SubElement(program_tag, 'episode-num')
                        episode_num_tag.set('system', 'xmltv_ns')
                        episode_num_tag.text = '0.%s.' % (int(program.episode_number.split('-')[0]) - 1)
                    else:
                        episode_num_tag = ET.SubElement(program_tag, 'episode-num')
                        episode_num_tag.set('system', 'onscreen')
                        tmp = program.start_time.strftime('%Y%m%d')
                        episode_num_tag.text = tmp
                        episode_num_tag = ET.SubElement(program_tag, 'episode-num')
                        episode_num_tag.set('system', 'xmltv_ns')
                        episode_num_tag.text = '%s.%s.' % (int(tmp[:4])-1, int(tmp[4:]) - 1)
        except Exception as e: 
            logger.error('Exception:%s', e)
            logger.error(traceback.format_exc())


    

    """
    @staticmethod
    def delete_xml(req):
        try:
            filename = req.form['filename']
            logger.debug(filename)
            filename = os.path.join(path_data, 'output', 'xmltv_%s.xml' % filename)
            logger.debug(filename)
            if os.path.exists(filename):
                os.remove(filename)
                return 'success'
            else:
                return 'no'

        except Exception as e: 
            logger.error('Exception:%s', e)
            logger.error(traceback.format_exc())
            return 'fail'
    """