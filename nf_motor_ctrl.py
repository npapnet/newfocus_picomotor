# -*- coding: utf-8 -*-
'''

This class represents a way of communicating with new focus Controller 

Created on 13 Jan 2017

@author: npap <npapnet@gmail.com>
'''


import logging
import time
from datetime import datetime
import threading
from threading import Thread #, Timer


from actuators.new_focus_basic import nfEthConnection, PositionParser

try:
    import Queue
except ImportError: # Python 3
    import queue as Queue
    
class nfThreadedCommandParser(Thread):
    ''' New Focus Controller Threaded Parser 

It uses a nfEthernet Connection to wrap common commands.
    '''
    def __init__(self, **kwargs):# ):
        self.TCP_TIMEOUT = 0.5
        self.config_args = kwargs
        name = self.config_args.get('name','nfCommandParser')
        connection = self.config_args.get('connection',None)
        
        assert isinstance(connection, nfEthConnection)
        self._connection = connection
        self.lockCon = threading.Lock()
        self.configNFParser = dict(verboseLevel = 0)
        
        self.pp = PositionParser()
        self.q = Queue.Queue(10)

        self._stopevent = threading.Event( )

        Thread.__init__(self, name=name)
    
    def run(self):
        self.i =0
        self.failed=0
        self.EmptyQueue=0
        time.sleep(self.TCP_TIMEOUT)
        try:

            while not self._stopevent.isSet( ):
                try:
                    with self.lockCon:
                        self.i +=1
                        try:
                            itm =None
                            itm = self.q.get(block=True, timeout=2)
                        except Queue.Empty:
                            self.EmptyQueue+=1
                            #logging.debug('Queue Empty')
                        if itm is not None:
                            logging.debug('Locking {} at {}'.format(self.i, datetime.utcnow().strftime('%M:%S.%f')[:-3]))    
                            self.printQueueState()
                            if itm[1] is False:
                                self._processCommandInQueue(itm[0])
                            else:
# following print commands are used to log                                 
                            
                                self.QueryPosition(itm[0])
                            logging.debug('Releasing {} at {}'.format(self.i, datetime.utcnow().strftime('%M:%S.%f')[:-3]))
                    
                except:
                    self.failed+=1
                    #print 'x  {} Failure rate: {} out of  {}'.format(datetime.now(), self.failed,self.i)   
                
        except:  #TODO remove except structure
            logging.warning('Exception in run()')
            self._connection.disconnect()
            
    def _add_command(self, message, queryFlag = False):
        '''
        Sends message. (new line character is appended)
        '''
        try:
            self.q.put_nowait((message, queryFlag))
        except:
            logging.warning('Queue full:')
            
    def move_dir(self, Driver, Channel, Direction='+',  Velocity=None, immediately= True):
        '''
        Constructs a message which sets the motor to move to a specific direction
        and optionally sends it to the nf8752
        '''
        
        message = '{Dir} A{Driver} {Velocity} {imm}'.format(Driver=Driver, 
                                                            Dir = 'FOR' if Direction is '+' else 'REV'
                                                            , Velocity= '' if Velocity is None else Velocity
                                                            , imm = 'G' if immediately else ''
                                                            )
        logging.debug(message)
        self._add_command(message, queryFlag = False)
        
    def move_rel(self, Driver, Channel=None, Position=0,  Velocity=None):
        ''' Move with relative position '''
        message = 'REL A{Driver} {Pos} G'.format(Driver=Driver, Pos=Position)
        logging.debug(message)
        self._add_command(message, queryFlag = False)
        
    def conf_driver(self, Driver, Channel=None, Velocity=None):
        ''' configures which driver will be used'''
        self.set_vel(Driver=Driver, Channel=Channel, Velocity=Velocity)
        self.set_driver_channel(Driver=Driver, Channel=Channel)
        
    def set_vel(self, Driver, Channel, Velocity=None):
        ''' Sets the velocity on a specific channel '''
        if Velocity is not None:
            message = 'VEL A{Driver} {Motor}={Velocity}'.format(Driver=Driver, Motor=Channel, Velocity=Velocity)
            self._add_command(message, queryFlag=False)

    def set_driver_channel(self, Driver, Channel):
        ''' Sets the active channel on a motor '''
        if Channel is not None:
            message = 'CHL A{Driver} {Motor} '.format(Driver=Driver, Motor=Channel)
            self._add_command(message, queryFlag=False)
            
    def _processCommandInQueue(self, itm):
        ''' processes a command on the queue

        assumes that there is an item on the queue
        itm is a tuple (command string , query flag)
        '''
        if self.configNFParser['verboseLevel']>1:
            print "! processing CMD: {}".format(itm)
        self._connection.send(itm)
        time.sleep(self.TCP_TIMEOUT)
 

    def printQueueState(self):
        ''' For debugging purposes '''
        mystr ='Queue items {},  Lock: {} '.format(self.q.qsize(), self.lockCon.locked())
        for i in self.q.queue:
            mystr += str(i)
        logging.info(mystr)
        
    def join(self):
        """ Stop the thread and wait for it to end. """
        self.i+=1
        self.q.queue.clear() #empty remaining items.
        self._connection.send('STO')
        self.lockCon.acquire()
        self._connection.disconnect()
        self.lockCon.release()
        #self._stopTime = datetime.now()
        self._stopevent.set( )
        threading.Thread.join(self, 2) # all is done.
        print 'exiting {}'.format(self.name)


    def stop(self):
        self.q.queue.clear() #empty remaining items.
        self._add_command('STO', queryFlag=False)
        
    def QueryPosition(self, cmd_str):
        '''
        processes a position Query 
        '''
        qstr = cmd_str
        cmd_str = 'POS'
        #self._connection.flush()
#         time.sleep(self.TCP_TIMEOUT)
        self._connection.send(cmd_str)
        time.sleep(self.TCP_TIMEOUT)
        mystr = self._connection.receive()
        self.pp.updatePosition(posstr=mystr )
        time.sleep(self.TCP_TIMEOUT)
        if self.configNFParser['verboseLevel']>1:
            print "? Query: {}".format(qstr) #mystr.replace('\r\n','   ').replace('>',''))
        #raise NotImplementedError("nfMotorCtrl.Query")       


def timeout():
    print "stopping ========================================================"
    t.join()
    print("Game over")

    
if __name__ == "__main__":
    #logging.basicConfig(level=logging.INFO)
    logging.basicConfig(level=logging.WARNING)
    s = nfEthConnection(TCP_IP='139.91.195.8', TCP_PORT=23, BUFFER_SIZE=1024)
    #pp = PositionParser()
    t = nfThreadedCommandParser(name= 'npTest', connection = s)
    print "starting ========================================================"
    t.start()
    #t._add_command('FOR A1 G', queryFlag=False)
    t.move_dir(Driver=1, Channel=1, Direction='+', Velocity=1000, immediately=True)
    t.move_dir(Driver=2, Channel=1, Direction='+', Velocity=2000, immediately=True)
    t._add_command('POS0', queryFlag=True)
    t._add_command('POS1', queryFlag=True)
    #t._add_command('STO')  ####****************** IMPORTANT
    # if I comment out/remove the abose Line line on the commit after commit 508f23f15361092f231ffd7e550d51ae0ae9a326 
    # the program will not terminate (the Ready flag is never reset to True)
    ##printPos(s,pp)
    t._add_command('POS1', queryFlag=True)
    t._add_command('POS2', queryFlag=True)
    t._add_command('POS3', queryFlag=True)
    t._add_command('STO')
    t.move_dir(Driver=2, Channel=1, Direction='+', Velocity=2000, immediately=True)
    t._add_command('POS4', queryFlag=True)
    ##printPos(s,pp)
    print "================    10 sec delay"
    t.printQueueState()
    time.sleep(5)
    
    t.printQueueState()
    time.sleep(5)
    
    
#     t2 = Timer(12, timeout)
#     t2.start()
# 
#     t3 = Timer(10, lambda:t.move_dir(Driver=2, Channel=1, Direction='+', Velocity=2000, immediately=True))
#     t3.start()
#     printQueueItems()
#     time.sleep(5)
    print "stopping ========================================================"
    t.join()   
    pass
