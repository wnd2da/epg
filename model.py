# -*- coding: utf-8 -*-
#########################################################
# python
import os
import traceback
from datetime import datetime
import json

# third-party
from sqlalchemy import or_, and_, func, not_
from sqlalchemy.orm import backref

# sjva 공용
from framework import db, path_app_root, app
from framework.util import Util

# 패키지
from .plugin import logger, package_name
#########################################################

plugin_package_name = '%s_plugin' % package_name

app.config['SQLALCHEMY_BINDS'][package_name] = 'sqlite:///%s' % (os.path.join(path_app_root, 'data', 'db', '%s.db' % package_name))
app.config['SQLALCHEMY_BINDS'][plugin_package_name] = 'sqlite:///%s' % (os.path.join(path_app_root, 'data', 'db', '%s.db' % plugin_package_name))

# EPG 플러그인이 사용하는 데이터
class ModelSetting(db.Model):
    __tablename__ = '%s_setting' % plugin_package_name
    __table_args__ = {'mysql_collate': 'utf8_general_ci'}
    __bind_key__ = plugin_package_name

    id = db.Column(db.Integer, primary_key=True)
    key = db.Column(db.String(100), unique=True, nullable=False)
    value = db.Column(db.String, nullable=False)
 
    def __init__(self, key, value):
        self.key = key
        self.value = value

    def __repr__(self):
        return repr(self.as_dict())

    def as_dict(self):
        return {x.name: getattr(self, x.name) for x in self.__table__.columns}

    @staticmethod
    def get(key):
        try:
            return db.session.query(ModelSetting).filter_by(key=key).first().value.strip()
        except Exception as e:
            logger.error('Exception:%s %s', e, key)
            logger.error(traceback.format_exc())
            
    
    @staticmethod
    def get_int(key):
        try:
            return int(ModelSetting.get(key))
        except Exception as e:
            logger.error('Exception:%s %s', e, key)
            logger.error(traceback.format_exc())
    
    @staticmethod
    def get_bool(key):
        try:
            return (ModelSetting.get(key) == 'True')
        except Exception as e:
            logger.error('Exception:%s %s', e, key)
            logger.error(traceback.format_exc())

    @staticmethod
    def set(key, value):
        try:
            item = db.session.query(ModelSetting).filter_by(key=key).with_for_update().first()
            if item is not None:
                item.value = value.strip()
                db.session.commit()
            else:
                db.session.add(ModelSetting(key, value.strip()))
        except Exception as e:
            logger.error('Exception:%s %s', e, key)
            logger.error(traceback.format_exc())

    @staticmethod
    def to_dict():
        try:
            ret = Util.db_list_to_dict(db.session.query(ModelSetting).all())
            ret['package_name'] = package_name
            return ret 
        except Exception as e:
            logger.error('Exception:%s ', e)
            logger.error(traceback.format_exc())


    @staticmethod
    def setting_save(req):
        try:
            for key, value in req.form.items():
                logger.debug('Key:%s Value:%s', key, value)
                if key in ['scheduler', 'is_running']:
                    continue
                entity = db.session.query(ModelSetting).filter_by(key=key).with_for_update().first()
                entity.value = value
            db.session.commit()
            return True                  
        except Exception as e: 
            logger.error('Exception:%s', e)
            logger.error(traceback.format_exc())
            logger.debug('Error Key:%s Value:%s', key, value)
            return False


class ModelEpgMakerSetting(db.Model):
    __tablename__ = '%s_setting' % package_name
    __table_args__ = {'mysql_collate': 'utf8_general_ci'}
    __bind_key__ = package_name

    id = db.Column(db.Integer, primary_key=True)
    key = db.Column(db.String(100), unique=True, nullable=False)
    value = db.Column(db.String, nullable=False)
 
    def __init__(self, key, value):
        self.key = key
        self.value = value

    def __repr__(self):
        return repr(self.as_dict())

    def as_dict(self):
        return {x.name: getattr(self, x.name) for x in self.__table__.columns}

    @staticmethod
    def get(key):
        try:
            return db.session.query(ModelEpgMakerSetting).filter_by(key=key).first().value.strip()
        except Exception as e:
            logger.error('Exception:%s %s', e, key)
            logger.error(traceback.format_exc())
            
    
    @staticmethod
    def get_int(key):
        try:
            return int(ModelEpgMakerSetting.get(key))
        except Exception as e:
            logger.error('Exception:%s %s', e, key)
            logger.error(traceback.format_exc())
    
    @staticmethod
    def get_bool(key):
        try:
            return (ModelEpgMakerSetting.get(key) == 'True')
        except Exception as e:
            logger.error('Exception:%s %s', e, key)
            logger.error(traceback.format_exc())

    @staticmethod
    def set(key, value):
        try:
            item = db.session.query(ModelEpgMakerSetting).filter_by(key=key).with_for_update().first()
            if item is not None:
                item.value = value.strip()
                db.session.commit()
            else:
                db.session.add(ModelEpgMakerSetting(key, value.strip()))
        except Exception as e:
            logger.error('Exception:%s %s', e, key)
            logger.error(traceback.format_exc())

    @staticmethod
    def to_dict():
        try:
            ret = Util.db_list_to_dict(db.session.query(ModelEpgMakerSetting).all())
            ret['package_name'] = package_name
            return ret 
        except Exception as e:
            logger.error('Exception:%s ', e)
            logger.error(traceback.format_exc())


    @staticmethod
    def setting_save(req):
        try:
            for key, value in req.form.items():
                logger.debug('Key:%s Value:%s', key, value)
                if key in ['scheduler', 'is_running']:
                    continue
                entity = db.session.query(ModelEpgMakerSetting).filter_by(key=key).with_for_update().first()
                entity.value = value
            db.session.commit()
            return True                  
        except Exception as e: 
            logger.error('Exception:%s', e)
            logger.error(traceback.format_exc())
            logger.debug('Error Key:%s Value:%s', key, value)
            return False

       
   
class ModelEpgMakerChannel(db.Model):
    __tablename__ = '%s_channel' % package_name
    __table_args__ = {'mysql_collate': 'utf8_general_ci'}
    __bind_key__ = package_name

    id = db.Column(db.Integer, primary_key=True)
    created_time = db.Column(db.DateTime)
    update_time = db.Column(db.DateTime)
    json = db.Column(db.JSON)
    #############################################
    name = db.Column(db.String)
    category = db.Column(db.String)
    search_name = db.Column(db.String)
    epg_from = db.Column(db.String)
    icon = db.Column(db.String)

    daum_name = db.Column(db.String)
    daum_id = db.Column(db.String)

    lgu_name = db.Column(db.String)
    lgu_id = db.Column(db.String)
    
    skb_name = db.Column(db.String)
    skb_id = db.Column(db.String)

    kt_name = db.Column(db.String)
    kt_id = db.Column(db.String)

    wavve_name = db.Column(db.String)
    wavve_id = db.Column(db.String)

    tving_name = db.Column(db.String)
    tving_id = db.Column(db.String)

    videoportal_name = db.Column(db.String)
    videoportal_id = db.Column(db.String)

    everyon_name = db.Column(db.String)
    everyon_id = db.Column(db.String)
    programs = db.relationship('ModelEpgMakerProgram', backref='channel', lazy=True)

    def __init__(self, d, site_count):
        self.created_time = datetime.now()
        self.json = d

        self.name = d['name']
        self.category = d['category']
        self.search_name = '|'.join(d['search_name_list'])
        self.icon = d['icon']
        if 'daum' in d['site_info']:
            self.daum_name = d['site_info']['daum'][0]
            self.daum_id = d['site_info']['daum'][1]
            site_count['daum'] += 1
        if 'lgu' in d['site_info']:
            self.lgu_name = d['site_info']['lgu'][0]
            self.lgu_id = d['site_info']['lgu'][1]
            site_count['lgu'] += 1
        if 'skb' in d['site_info']:
            self.skb_name = d['site_info']['skb'][0]
            self.skb_id = d['site_info']['skb'][1]
            site_count['skb'] += 1
        if 'kt' in d['site_info']:
            self.kt_name = d['site_info']['kt'][0]
            self.kt_id = d['site_info']['kt'][1]
            site_count['kt'] += 1
        if 'wavve' in d['site_info']:
            self.wavve_name = d['site_info']['wavve'][0]
            self.wavve_id = d['site_info']['wavve'][1]
            site_count['wavve'] += 1
        if 'tving' in d['site_info']:
            self.tving_name = d['site_info']['tving'][0]
            self.tving_id = d['site_info']['tving'][1]
            site_count['tving'] += 1
        if 'videoportal' in d['site_info']:
            self.videoportal_name = d['site_info']['videoportal'][0]
            self.videoportal_id = d['site_info']['videoportal'][1]
            site_count['videoportal'] += 1
        if 'everyon' in d['site_info']:
            self.everyon_name = d['site_info']['everyon'][0]
            self.everyon_id = d['site_info']['everyon'][1]
            site_count['everyon'] += 1

    def __repr__(self):
        return repr(self.as_dict())

    def as_dict(self):
        ret = {x.name: getattr(self, x.name) for x in self.__table__.columns}
        ret['created_time'] = self.created_time.strftime('%m-%d %H:%M:%S') 
        ret['update_time'] = self.update_time.strftime('%m-%d %H:%M:%S') if self.update_time is not None else None
        ret['json'] = ret['json'] if isinstance(ret['json'], dict) else  json.loads(ret['json'])
        return ret

    @staticmethod
    def save(data):
        site_count = {"daum":0,"skb":0,"lgu":0,"kt":0,"wavve":0,"tving":0,"videoportal":0,"everyon":0}
        try:
            data = data['list']
            for d in data:
                c = ModelEpgMakerChannel(d, site_count)
                db.session.add(c)
            db.session.commit()
            return site_count
        except Exception as e: 
            logger.error('Exception:%s', e)
            logger.error(traceback.format_exc()) 

    @staticmethod
    def get_instance_by_name(name):
        try:
            return db.session.query(ModelEpgMakerChannel).filter_by(name=name).first()
        except Exception as e: 
            logger.error('Exception:%s', e)
            logger.error(traceback.format_exc())

    @staticmethod
    def get_channel_list():
        try:
            channel_list = db.session.query(ModelEpgMakerChannel).all()
            #ret = [x.as_dict() for x in channel_list]
            return channel_list
        except Exception as e: 
            logger.error('Exception:%s', e)
            logger.error(traceback.format_exc())

    

    
    @staticmethod
    def get_match_name(search_name):
        try:
            search_name = ModelEpgMakerChannel.util_get_search_name(search_name)
            channel_list = db.session.query(ModelEpgMakerChannel).all()
            for c in channel_list:
                if search_name in c.search_name.split('|'):
                    return [c.name, c.category]
        except Exception as e: 
            logger.error('Exception:%s', e)
            logger.error(traceback.format_exc())

    @staticmethod
    def util_get_search_name(s):
        return s.lower().replace('uhd', '').strip().replace('-', '').replace(' ', '')



# 실제 EPG 내용이다
# 아래 테이블은 EPG에서 daum_info 로 참조한다.
class ModelEpgMakerProgram(db.Model):
    __tablename__ = '%s_program' % package_name
    __table_args__ = {'mysql_collate': 'utf8_general_ci'}
    __bind_key__ = package_name

    id = db.Column(db.Integer, primary_key=True)
    created_time = db.Column(db.DateTime)
    json = db.Column(db.JSON)
    #############################################

    #channel_id = db.Column(db.Integer, db.ForeignKey('%s_channel.id' % package_name))
    #channel_name = db.Column(db.Integer, db.ForeignKey('epg.%s_channel.name' % package_name))
    channel_name = db.Column(db.Integer, db.ForeignKey('%s_channel.name' % package_name))
    #channel = db.relationship('ModelEpgMakerChannel')
    start_time = db.Column(db.DateTime)
    end_time = db.Column(db.DateTime)
    title = db.Column(db.String)
    episode_number = db.Column(db.String)
    part_number = db.Column(db.String)
    rate = db.Column(db.String)
    re = db.Column(db.Boolean)

    is_movie = db.Column(db.Boolean)
    #daum_href = db.Column(db.String)
    #daum_is_movie = db.Column(db.Boolean)
    #daum_title = db.Column(db.String)
    #daum_id = db.Column(db.String)
    #daum_id = db.Column(db.String, db.ForeignKey('epg.%s_daum.daum_id' % package_name))
    daum_id = db.Column(db.String, db.ForeignKey('%s_daum.daum_id' % package_name))
    daum_info = db.relationship('ModelEpgMakerDaum', backref='programs', lazy=True)

    #daum_poster = db.Column(db.String)
    #daum_desc = db.Column(db.String)

    # 다음 이외의 것들
    poster = db.Column(db.String)
    desc = db.Column(db.String)
    genre = db.Column(db.String)
    actor = db.Column(db.String)


    def __init__(self):
        self.created_time = datetime.now()
        self.is_movie = False

        
    def __repr__(self):
        return repr(self.as_dict())

    def as_dict(self):
        ret = {x.name: getattr(self, x.name) for x in self.__table__.columns}
        ret['created_time'] = self.created_time.strftime('%m-%d %H:%M:%S') 
        ret['json'] = ret['json'] if isinstance(ret['json'], dict) else  json.loads(ret['json'])
        return ret

    @staticmethod
    def save(data):
        try:
            data = data['list']
            for d in data:
                c = ModelEpgMakerChannel(d)
                db.session.add(c)
            db.session.commit()
        except Exception as e: 
            logger.error('Exception:%s', e)
            logger.error(traceback.format_exc()) 



class ModelEpgMakerDaum(db.Model):
    __tablename__ = '%s_daum' % package_name
    __table_args__ = {'mysql_collate': 'utf8_general_ci'}
    __bind_key__ = package_name

    id = db.Column(db.Integer, primary_key=True)
    created_time = db.Column(db.DateTime)
    json = db.Column(db.JSON)
    #############################################
    
    is_movie = db.Column(db.Boolean)
    daum_title = db.Column(db.String)
    daum_id = db.Column(db.String)
    daum_href = db.Column(db.String)

    poster = db.Column(db.String)
    desc = db.Column(db.String)
    genre = db.Column(db.String)

    actor = db.Column(db.String)
    director = db.Column(db.String)
    producer = db.Column(db.String)
    writer = db.Column(db.String)

    def __init__(self):
        self.created_time = datetime.now()

