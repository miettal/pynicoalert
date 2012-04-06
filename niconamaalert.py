# -*- coding: utf-8 -*-

import urllib2
import urllib
import socket
import xml2dict

LOGIN_URL = 'https://secure.nicovideo.jp/secure/login?site=nicolive_antenna'
API_BASE_URL = 'http://live.nicovideo.jp/api'

class Api :
  def __init__(self,
               mail=None,
               password=None,
               login_url=LOGIN_URL,
               api_base_url=API_BASE_URL) :
    self.login_url = login_url
    self.api_base_url = api_base_url
    self.comment_host = None
    self.comment_port = None
    self.comment_thread = None
    self.xml2dict = xml2dict.XML2Dict()

    if mail is not None and password is not None :
      self.login(mail, password)
    else :
      self.ticket = None
  
  def login(self, mail, password) :
    query = {'mail':mail, 'password':password}
    res = urllib2.urlopen(self.login_url, urllib.urlencode(query))

    res_dict = self.xml2dict.fromstring(res.read())

    self.ticket = res_dict.nicovideo_user_response.ticket

  def getAlertStatus(self) :
    query = {'ticket':self.ticket}
    res = urllib2.urlopen(API_BASE_URL+'/getalertstatus', urllib.urlencode(query))

    res_dict = self.xml2dict.fromstring(res.read())

    return res_dict

  def getAlertInfo(self) :
    res = urllib2.urlopen(API_BASE_URL+'/getalertinfo')

    res_dict = self.xml2dict.fromstring(res.read())

    return res_dict

  def getStreamList(self) :
    if (self.comment_host is None and
        self.comment_port is None and
        self.comment_thread is None ) :
      alert_info= self.getAlertInfo()
      self.comment_host = alert_info.getalertstatus.ms.addr
      self.comment_port = int(alert_info.getalertstatus.ms.port)
      self.comment_thread = alert_info.getalertstatus.ms.thread

    self.xmlsocket = XMLSocket(self.comment_host, self.comment_port)
    self.xmlsocket.connect()
    self.xmlsocket.send(('<thread thread="%s" version="20061206" res_form="-1"/>'+chr(0)) % self.comment_thread)
    while True :
      res = self.xmlsocket.recv()
      res_dict = self.xml2dict.fromstring(res)
      if 'thread' in res_dict :
        pass
      elif 'chat' in res_dict :
        yield res_dict
      else :
        pass

  def getStreamInfo(self, bloadcast_id) :
    res = urllib2.urlopen(self.api_base_url+'/getstreaminfo/lv'+bloadcast_id)

    res_dict = self.xml2dict.fromstring(res.read())
    
    return res_dict

class XMLSocket :
  def __init__(self, host=None, port=None) :
    self.host = host
    self.port = port
    self.sock = None
    self.buf = ""

  def setHost(self, host) :
    self.host = host

  def setPort(self, port) :
    self.port = port
  
  def connect(self) :
    self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    self.sock.connect((self.host, self.port))
  
  def send(self, string) :
    self.sock.sendall(string+chr(0))

  def recv(self) :
    while self.buf.find(chr(0)) == -1 :
      self.buf += self.sock.recv(1024)
    
    string = self.buf[:self.buf.find(chr(0))]
    self.buf = self.buf[self.buf.find(chr(0))+1:]

    return string
