import socket
import zmq
from .utils import *
from .cams import *
from .io import *
from .widgets import *

LOGO = "LABCAMS\n"



class LabCamsGUI(QMainWindow):
    app = None
    cams = []
    def __init__(self,app = None, expName = 'test',
                 parameters = {},
                 server = True,
                 saveOnStart = False,
                 triggered = False,
                 software_trigger = True,
                 updateFrequency = 33):
        '''
        Graphical interface for controling labcams.
        '''
        super().__init__()

        default_parameters = {'recorder_frames_per_file':0,
                              'server_refresh_time': 30,
                              'recorder_path_format': pjoin('{datafolder}','{dataname}','{filename}','{today}_{run}_{nfiles}')}
        self.parameters = {**default_parameters, **parameters}
        
        self.app = app
        self.updateFrequency=updateFrequency
        self.saveOnStart = saveOnStart
        
        self.software_trigger = software_trigger
        self.triggered = Event()
        if triggered:
            self.triggered.set()
        else:
            self.triggered.clear()

        if server:
            self.socket = UDPSocket('0.0.0.0', self.parameters['server_port'])
            socket_timer = QTimer()
            socket_timer.timeout.connect(self.serverActions)
            socket_timer.start(self.parameters['server_refresh_time'])

        self.init_cameras()

        self.initUI()
        
        self.camerasRunning = False
        if hasattr(self,'camstim_widget'):
            self.camstim_widget.ino.start()
            self.camstim_widget.ino.disarm()

        for cam,writer in zip(self.cams[::-1],self.writers[::-1]):
            cam.start()
            if not writer is None:
                writer.init(cam)
                writer.start()
        
        camready = 0
        while camready != len(self.cams):
            camready = np.sum([cam.camera_ready.is_set() for cam in self.cams])
        display('Initialized cameras.')

        if hasattr(self,'camstim_widget'):
            self.camstim_widget.ino.arm()

        self.triggerCams(soft_trigger = self.software_trigger,
                         save=self.saveOnStart)
    
    def init_cameras(self):

        self.camQueues = []
        self.saveflags = []
        self.writers = []
        connected_avt_cams = []
        
        cam_descriptions = self.parameters.get('cams', [])
        for c,cam in enumerate(self.cam_descriptions):
            display("Connecting to camera [" + str(c) + '] : '+cam['name'])
            
            default_settings = {'Save': True, 'recorder': 'tiff', 'compress': 0}
            cam = {**default_settings, **cam}

            if 'saveMethod' in cam:
                cam['recorder'] = cam['saveMethod']
                
            self.saveflags.append(cam['Save'])
            self.camQueues.append(Queue())
            
            if 'noqueue' in cam['recorder']:
                recorderpar = {'recorder': cam['recorder'],
                               'datafolder': self.parameters['recorder_path'],
                               'framesperfile': self.parameters['recorder_frames_per_file'],
                               'pathformat': self.parameters['recorder_path_format'],
                               'compression': cam['compress'],
                               'filename': expName,
                               'dataname': cam['description'])}
                if 'ffmpeg' in cam['recorder'] and 'hwaccel' in cam:
                    recorderpar['hwaccel'] = cam['hwaccel']
            else:
                display('Using the queue for recording.')
                recorderpar = None

            if cam['driver'].lower() == 'avt':
                try:
                    avtids,avtnames = AVT_get_ids()
                except Exception as e:
                    display('[ERROR] AVT  camera error? Connections? Parameters?')
                    print(e)
                camids = [(camid,name) for (camid,name) in zip(avtids,avtnames) 
                          if (cam['name'] in name and not camid[0] in connected_avt_cams)]
                if len(camids) == 0:
                    display('Could not find or already connected to: '+cam['name'])
                    display('Available AVT cameras:')
                    print('\n                -> '+
                          '\n                -> '.join(avtnames))
                    print('EXITING')
                    sys.exit()
                    
                cam['name'] = camids[0][1]
                
                default_avt_settings = {'TriggerSource': 'Line1', 'TriggerMode': 'LevelHigh',
                                        'TriggerSelector': 'FrameStart', 'AcquisitionMode': 'Continuous',
                                        'AcquisitionFrameCount': 1000, 'nFrameBuffers': 6}
                cam = {**default_avt_settings, **cam}
                
                key_src2dst = {'frameRate': 'frame_rate', 'gain': 'gain', 'TriggerSource': 'triggerSource',
                               'TriggerMode': 'triggerMode', 'TriggerSelector': 'triggerSelector',
                               'AcquisitionMode', 'acquisitionMode', 'AcquisitionFrameCount': 'nTriggeredFrames',
                               'nFrameBuffers': 'nFrameBuffers'}
                cam_params = {}
                for key in key_src2dst:
                    if key in cam:
                        cam_params[key] = cam[key]
                
                self.cams.append(AVTCam(camId=camids[0][0], params = cam_params))
                connected_avt_cams.append(camids[0][0])
                
            elif cam['driver'].lower() == 'qimaging':
                if not 'binning' in cam.keys():
                    cam['binning'] = 2
                self.cams.append(QImagingCam(camId=cam['id'],
                                             outQ = self.camQueues[-1],
                                             exposure=cam['exposure'],
                                             gain=cam['gain'],
                                             binning = cam['binning'],
                                             triggerType = cam['triggerType'],
                                             triggered = self.triggered,
                                             recorderpar = recorderpar))
                                        
            elif cam['driver'].lower() == 'opencv':
                self.cams.append(OpenCVCam(camId=cam['id'],
                                           outQ = self.camQueues[-1],
                                           triggered = self.triggered,
                                           **cam,
                                           recorderpar = recorderpar))
            elif cam['driver'].lower() == 'pco':
                if 'CamStimTrigger' in cam:
                    if not cam['CamStimTrigger'] is None:
                        self.camstim_widget = CamStimTriggerWidget(
                            port = cam['CamStimTrigger']['port'],
                            outQ = self.camQueues[-1])
                        camstim = self.camstim_widget.ino
                else:
                    camstim = None
                self.cams.append(PCOCam(camId=cam['id'],
                                        params = {'binning': cam.get('binning', None),
                                                  'exposure': cam['exposure'],
                                                  'triggered': self.triggered},
                                        format = {'n_chan': camstim.nchannels}))
            else: 
                display('[WARNING] -----> Unknown camera driver' + cam['driver'])
                self.camQueues.pop()
                self.saveflags.pop()
            
            if not 'recorder_sleep_time' in self.parameters:
                self.parameters['recorder_sleep_time'] = 0.3
            if 'SaveMethod' in cam:
                cam['recorder'] = cam['SaveMethod']
                display('SaveMethod is deprecated, use recorder instead.')
            if not 'noqueue' in cam['recorder']:
                towriter = dict(inQ = self.camQueues[-1],
                                datafolder=self.parameters['recorder_path'],
                                pathformat = self.parameters['recorder_path_format'],
                                framesperfile=self.parameters['recorder_frames_per_file'],
                                sleeptime = self.parameters['recorder_sleep_time'],
                                filename = expName,
                                dataname = cam['description'])
                if  cam['recorder'] == 'tiff':
                    display('Recording to TIFF')
                    self.writers.append(TiffWriter(compression = cam['compress'],
                                                   **towriter))
                elif cam['recorder'] == 'ffmpeg':
                    display('Recording with ffmpeg')
                    if not 'hwaccel' in cam:
                        cam['hwaccel'] = None
                    self.writers.append(FFMPEGWriter(compression = cam['compress'],
                                                     hwaccel = cam['hwaccel'],
                                                     **towriter))
                elif cam['recorder'] == 'binary':
                    display('Recording binary')
                    self.writers.append(BinaryWriter(**towriter))
                elif cam['recorder'] == 'opencv':
                    display('Recording opencv')
                    self.writers.append(OpenCVWriter(compression = cam['compress'],**towriter))
                else:
                    print(''' 

The available recorders are:
    - tiff (multiple tiffstacks - the default)   
    - binary 
    - ffmpeg  Records video format using ffmpeg (hwaccel options: intel, nvidia - remove for no hardware acceleration)
    - opencv  Records video format using openCV

The recorders can be specified with the '"recorder":"ffmpeg"' option in each camera setting of the config file.
''')
                    raise ValueError('Unknown recorder {0} '.format(cam['recorder']))
            else:
                self.writers.append(None)
                
            if 'CamStimTrigger' in cam:
                self.camstim_widget.outQ = self.camQueues[-1]
            # Print parameters
            display('\t Camera: {0}'.format(cam['name']))
            for k in np.sort(list(cam)):
                if not k == 'name' and not k == 'recorder':
                    display('\t\t - {0} {1}'.format(k,cam[k]))
                    
                    
                    
    def setExperimentName(self,expname):
        # Makes sure that the experiment name has the right slashes.
        if os.path.sep == '/':
            expname = expname.replace('\\',os.path.sep)
        expname = expname.strip(' ')
        for flg,writer,cam in zip(self.saveflags,self.writers,self.cams):
            if flg:
                if not writer is None:
                    writer.set_filename(expname)
                else:
                    display('Setting serial recorder filename.')
                    cam.eventsQ.put('filename='+expname)
        #time.sleep(0.15)
        self.recController.experimentNameEdit.setText(expname)
        
    def serverActions(self):
        msg, address = self.socket.receive()
        msg = msg.decode().split('=')
        message = dict(action=msg[0])
        if len(msg) > 1:
            message = dict(message,value=msg[1])
        #display('Server received message: {0}'.format(message))
        if message['action'].lower() == 'expname':
            self.setExperimentName(message['value'])
            self.socket.send(b'ok=expname',address)
        elif message['action'].lower() == 'softtrigger':
            self.recController.softTriggerToggle.setChecked(
                int(message['value']))
            self.socket.send(b'ok=software_trigger',address)
        elif message['action'].lower() == 'trigger':
            for cam in self.cams:
                cam.stop_acquisition()
            # make sure all cams closed
            for c,(cam,writer) in enumerate(zip(self.cams,self.writers)):
                cam.stop_saving()
                #if not writer is None: # Logic moved to inside camera.
                #    writer.write.clear()
            self.triggerCams(soft_trigger = self.software_trigger,save = True)
            self.socket.send(b'ok=save_hardwaretrigger',address)
        elif message['action'].lower() == 'settrigger':
            self.recController.camTriggerToggle.setChecked(
                int(message['value']))
            self.socket.send(b'ok=hardware_trigger',address)
        elif message['action'].lower() in ['setmanualsave','manualsave']:
            self.recController.saveOnStartToggle.setChecked(
                int(message['value']))
            self.socket.send(b'ok=save',address)
        elif message['action'].lower() == 'log':
            for cam in self.cams:
                cam.eventsQ.put('log={0}'.format(message['value']))
            # write on display
            #self.camwidgets[0].text_remote.setText(message['value'])
            self.socket.send(b'ok=log',address)
            self.recController.udpmessages.setText(message['value'])
        elif message['action'].lower() == 'ping':
            display('Server got PING.')
            self.socket.send(b'pong',address)
        elif message['action'].lower() == 'quit':
            self.socket.send(b'ok=bye',address)
            self.close()
    def triggerCams(self,soft_trigger = True, save=False):
        # stops previous saves if there were any
        display("Waiting for the cameras to be ready.")
        for c,cam in enumerate(self.cams):
            while not cam.camera_ready.is_set():
                time.sleep(0.001)
            display('Camera [{0}] ready.'.format(c))
        display('Doing save ({0}) and trigger'.format(save))
        if save:
            for c,(cam,flg,writer) in enumerate(zip(self.cams,
                                                    self.saveflags,
                                                    self.writers)):
                if flg:
                    cam.saving.set()
                    if not writer is None:
                        writer.write.set()
        else:
            for c,(cam,flg,writer) in enumerate(zip(self.cams,
                                                    self.saveflags,
                                                    self.writers)):
                if flg:
                    if not writer is None:
                        cam.stop_saving()
                    #writer.write.clear() # cam stops writer
        #time.sleep(2)
        if soft_trigger:
            for c,cam in enumerate(self.cams):
                cam.start_trigger.set()
            display('Software triggered cameras.')
        
    def experimentMenuTrigger(self,q):
        if q.text() == 'Set refresh time':
            self.timer.stop()
            res = QInputDialog().getDouble(self,"What refresh period do you want?","GUI refresh period",
                                           self.updateFrequency)
            if res[1]:
                self.updateFrequency = res[0]
            self.timer.start(self.updateFrequency)
            #display(q.text()+ "clicked. ")
        
    def initUI(self):
        # Menu
        self.setDockOptions(QMainWindow.AllowTabbedDocks |
                            QMainWindow.AllowNestedDocks
)
        bar = self.menuBar()
        editmenu = bar.addMenu("Options")
        editmenu.addAction("Set refresh time")
        editmenu.triggered[QAction].connect(self.experimentMenuTrigger)
        self.setWindowTitle("labcams")
        self.tabs = []
        self.camwidgets = []
        self.recController = RecordingControlWidget(self)
        #self.setCentralWidget(self.recController)
        self.recControllerTab = QDockWidget("",self)
        self.recControllerTab.setWidget(self.recController)
        self.addDockWidget(
            Qt.TopDockWidgetArea,
            self.recControllerTab)
        self.recController.setFixedHeight(self.recController.layout.sizeHint().height())
        for c,cam in enumerate(self.cams):
            tt = ''
            if self.saveflags[c]:
                tt +=  ' - ' + self.cam_descriptions[c]['description'] +' ' 
            self.tabs.append(QDockWidget("Camera: "+str(c) + tt,self))
            self.camwidgets.append(CamWidget(frame = np.zeros((cam.h,cam.w,cam.nchan),
                                                              dtype=cam.dtype),
                                             iCam = c,
                                             parent = self,
                                             parameters = self.cam_descriptions[c]))
            self.tabs[-1].setWidget(self.camwidgets[-1])
            self.tabs[-1].setFloating(False)
            self.tabs[-1].setAllowedAreas(Qt.LeftDockWidgetArea |
                                          Qt.RightDockWidgetArea |
                                          Qt.BottomDockWidgetArea |
                                          Qt.TopDockWidgetArea)
            self.tabs[-1].setFeatures(QDockWidget.DockWidgetMovable |
                                      QDockWidget.DockWidgetFloatable)
            self.addDockWidget(
                Qt.BottomDockWidgetArea,
                self.tabs[-1])
            self.tabs[-1].setMinimumHeight(300)
            # there can only be one of these for now?
            if hasattr(self,'camstim_widget'):
                self.camstim_tab = QDockWidget("Camera excitation control",self)
                self.camstim_tab.setWidget(self.camstim_widget)
                self.addDockWidget(
                    Qt.LeftDockWidgetArea,
                self.camstim_tab)
            display('Init view: ' + str(c))
        timer = QTimer()
        timer.timeout.connect(self.timerUpdate)
        timer.start(self.updateFrequency)
        #self.move(0, 0)
        self.show()
            
    def timerUpdate(self):
        for c,cam in enumerate(self.cams):
            try:
                frame = cam.get_img()
                if not frame is None:
                    self.camwidgets[c].image(frame,cam.nframes.value) #frame
            except Exception as e:
                display('Could not draw cam: {0}'.format(c))
                exc_type, exc_obj, exc_tb = sys.exc_info()
                fname = os.path.split(
                    exc_tb.tb_frame.f_code.co_filename)[1]
                print(e, fname, exc_tb.tb_lineno)

    def closeEvent(self,event):
        if hasattr(self,'camstim_widget'):
            self.camstim_widget.ino.disarm()
            self.camstim_widget.close()
            
        display('Acquisition stopped (close event).')
        for c,(cam,flg,writer) in enumerate(zip(self.cams,
                                            self.saveflags,
                                            self.writers)):
            if flg:
                cam.stop_saving()
                #writer.write.clear() # logic moved inside writer
                if not writer is None:
                    writer.stop()
            cam.close()
        for c in self.cams:
            c.join()
        for c,(cam,flg,writer) in enumerate(zip(self.cams,
                                                self.saveflags,
                                                self.writers)):
            if flg:
                if not writer is None:
                    writer.join()
        pg.setConfigOption('crashWarning', False)
        event.accept()


def main():

    from argparse import ArgumentParser, RawDescriptionHelpFormatter
    import os
    import json
    parser = ArgumentParser(description=LOGO + '\n\n  Multiple camera control and recording.',formatter_class=RawDescriptionHelpFormatter)
    parser.add_argument('file',
                        metavar='file',
                        type=str,
                        default=None,
                        nargs="?")
    parser.add_argument('-d','--make-config',
                        type=str,
                        default = None,
                        action='store')
    parser.add_argument('-w','--wait',
                        default = False,
                        action='store_true')
    parser.add_argument('-t','--triggered',
                        default=False,
                        action='store_true')
    parser.add_argument('-c','--cam-select',
                        type=int,
                        default=None,
                        nargs='+',
                        action='store')
    parser.add_argument('--no-server',
                        default=False,
                        action='store_true')
    parser.add_argument('--bin-to-mj2',
                        default=False,
                        action='store_true')
    parser.add_argument('--mj2-rate',
                        default=30.,
                        action='store')
    
    opts = parser.parse_args()

    if opts.bin_to_mj2:
        fname = opts.file
        
        assert not fname is None, "Need to supply a binary filename to compress."
        assert os.path.isfile(fname), "File {0} not found".format(fname)
        ext = os.path.splitext(fname)[-1]
        assert ext in ['.dat','.bin'], "File {0} needs to be binary.".format(fname)  
        stack = mmap_dat(fname)
        stack_to_mj2_lossless(stack, fname, rate = opts.mj2_rate)
        print('Converted {0}'.format(fname.replace(ext,'.mov')))
        sys.exit(0)
        
    if not opts.make_config is None:
        from .widgets import SettingsDialog
        app = QApplication(sys.argv)
        s = SettingsDialog(getPreferences())
        sys.exit(app.exec_())
        fname = opts.make_config
        getPreferences(fname, create=True)
        sys.exit(s.exec_())
    parameters = getPreferences(opts.file)

    if not opts.cam_select is None:
        parameters['cams'] = [parameters['cams'][i] for i in opts.cam_select]

    app = QApplication(sys.argv)
    w = LabCamsGUI(app = app,
                   parameters = parameters,
                   server = not opts.no_server,
                   software_trigger = not opts.wait,
                   triggered = opts.triggered)
    sys.exit(app.exec_())



if __name__ == '__main__':
    import multiprocessing
    multiprocessing.set_start_method('spawn')
    main()
