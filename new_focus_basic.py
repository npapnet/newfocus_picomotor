# -*- coding: utf-8 -*-
'''
Created on 30 Δεκ 2016

@author: npap
'''
import socket
import time
import threading
import logging

class nfEthConnection(object):
    ''' New Focus Controller ethernet Connection'''
    def __init__(self, TCP_IP = None, TCP_PORT = 23, BUFFER_SIZE = 1024):
        self.TCP_IP =TCP_IP
        self.TCP_PORT =TCP_PORT
        self.BUFFER_SIZE =BUFFER_SIZE
        self.TCP_TIMEOUT = 0.1
        self._isConnected = False
        self.ErrorOnExit= False
        self.initConnect()
    
    def initConnect(self):
        if (self.TCP_IP is not None) and not self.isConnected:
            try:
                print 'Connecting to {}....'.format(self.TCP_IP)
                self._s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                self._s.connect((self.TCP_IP, self.TCP_PORT)) # needs to be tuple
                self.isConnected = True
                print 'Connected to {}'.format(self.TCP_IP)
            except:
                print 'Connection to {} Failed.'.format(self.TCP_IP),
                self.TCP_IP = None                
                print 'Defaulting to {} '.format(self.TCP_IP)
                self.isConnected = False
        else:
            pass
            print '======================== Simulation Mode'
            
    def send(self, message):
        '''
        Sends message. (new line character is appended)
        '''
        try:
            self._s.send(message + '\n')
        except:
            print 'Failed Sending: {}'.format(message)
            pass
        
    def receive(self, buffSize = None):
        '''
        Sends message. (new line character is appended)
        '''
        if self.isConnected:
            buffSize =buffSize if buffSize is not None else self.BUFFER_SIZE
            return self._s.recv(self.BUFFER_SIZE)
        else:
            return None
        
    def flush(self):
        self.receive(1024)
    
    @property
    def isConnected(self):
        return self._isConnected
    
    @isConnected.setter
    def isConnected(self, val):
        self._isConnected = val
            
    def disconnect(self):
        ''' shutdown and disconnect '''
        #if self.TCP_IP is not '0':
        time.sleep(self.TCP_TIMEOUT)  # this only reasonable in Testing conditions
        try:
            self._s.close()
            self.isConnected = False
            print 'disconnected from {IP}:{PORT}'.format(IP=self.TCP_IP,PORT=self.TCP_PORT)
        except:
            self.ErrorOnExit= True
            logging.warning('Failed to disconnect from {IP}:{PORT}'.format(IP=self.TCP_IP,PORT=self.TCP_PORT))
            pass

class PositionParser(object):
    ''' Class which parses return output (string) from nf8752'''
    def __init__(self):
        self.d ={}
        pass

    def ParsePosLine(self, line):
        '''
        splits a line which contains a =
        splits a line which contains a = 
        '''
        els = line.split('=')
        if len(els)==2:
            self.d[els[0].replace('>','')] = els[1]
         
    
    def updatePosition(self, posstr=''):
        for line in posstr.splitlines():
            self.ParsePosLine(line)
        for k in self.d:
            print 'Driver {Driver}: {Pos} \t'.format(Driver = k, Pos =self.d[k]),
        print ''


    
def printPos(sc = None,#nfEthConnection(),
              pp=PositionParser()):
    '''
    sc: nf Socket Connection
    '''
    sc.send('POS')
    time.sleep(0.5)# this is required to not create a timeout. 
    mystr = sc.receive()
    pp.updatePosition(posstr=mystr )
    

if __name__=='__main__':
    s = nfEthConnection(TCP_IP='139.91.195.8')
    pp = PositionParser()
    time.sleep(0.1)
    if s.isConnected:
        s.send('FOR A1 G')
        time.sleep(0.1)
        try:
            print 'start thread'
            t=threading.Thread(target=printPos, args=(s,pp))
            t.daemon = True
            t.start()
            i=0
            while i<10:
                t=threading.Thread(target=printPos, args=(s,pp))
                #t.setDaemon(True)
                t.start()
                time.sleep(1)
                i+=1
            s.send('STO')
        except Exception as e:
            print e
            pass
        finally:
            s.disconnect()
        
