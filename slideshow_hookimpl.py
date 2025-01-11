import remi.gui as gui
from slideshow import SlideShow
import plugins
import logging as LOGGER
from imgutils import drawText, HAlign, VAlign
from fastapi import APIRouter, HTTPException, File, UploadFile
import os.path as osp

PLUGIN_NAME = "SLIDESHOW" # set plugin name here. This must be the same as prefix of this file.
PLUGIN_FANCY_NAME = "SlideShow" # set fancy name for remote controller here
PLUGIN_CLASS = "BASIC" # Classes are: LOADER (force load after change), DISPLAY (at least one must stay active), REMOTE(can't be unloaded from web)
PLUGIN_SORT_ORDER = "0" #Order for remote controller dialogs. Ascending.

class Remote:
    app : SlideShow = None
    fileName : str = None # Last successfuly uploaded file
    
    def setRemote(self):
        """
        Basic RC widget with load, pause and upload buttons, brightness etc.
        For setting web based remote from plugins. 
        Returns list of remi.Widgets
        """

        self.lbl = gui.Label('Photo Frame started', height=30, margin='10px')
        self.bt_pause = gui.Button('Pause', width=200, height=30, margin='4px')
        self.bt_pause.onclick.do(self.on_bt_pause_pressed)
        self.bt_load = gui.Button('Load', width=200, height=30, margin='4px')
        self.bt_load.onclick.do(self.on_bt_load_pressed)
        self.nextLoad = gui.Progress(1, 100, width=200, height=5)
        delayTxt_lbl = gui.Label('Delay (s):', height=20, style={'text-align':'Left','margin':'4px'})
        self.delayTxt = gui.TextInput(width=60, height=20)
        delayCont = gui.HBox(margin='4px')
        delayCont.append([delayTxt_lbl, self.delayTxt])
        self.delayTxt.onchange.do(self.on_delayTxt_changed)

        self.slider_brightness_lbl = gui.Label('Brightness:', height=20, margin_top='10px', style={'text-align':'Left'})
        self.slider_brightness = gui.Slider(255, 0, 255, 15, width=200, height=10, margin='1px')
        self.slider_brightness.onchange.do(self.on_brightness_changed)

        btUploadPhotoLbl = gui.Label('Upload:', height=20, margin='4px', style={'text-align':'Left'})
        self.btUploadPhoto = gui.FileUploader(self.app.uploadPath, width=200, height=30, margin='4px',accepted_files='*.jpg')
        uploadCont = gui.HBox()
        uploadCont.append([btUploadPhotoLbl, self.btUploadPhoto])
        self.btUploadPhoto.onsuccess.do(self.fileupload_on_success)
        self.btUploadPhoto.onfailed.do(self.fileupload_on_failed)
        bt_saveConfig = gui.Button('Save Config', width=200, height=30, margin='4px')
        bt_saveConfig.onclick.do(self.on_saveConfig)


        return([self.lbl, self.bt_pause, self.bt_load, self.nextLoad, delayCont,self.slider_brightness_lbl, self.slider_brightness, uploadCont, bt_saveConfig])
    
    def setBrightness(self, value : int):
        self.app.setBrightness(int(value))
        self.app.setStage(self.app.Stage.RESIZE)
        self.setBrightnessFB(value)

    def on_saveConfig(self, widget):
        self.app.saveCfgAll()

    def on_brightness_changed(self, widget, value):
            self.setBrightness(value)

    def setBrightnessFB(self, brightness : int):
        if hasattr(self, 'slider_brightness'):
            self.app.remote.secureUpdate(self.slider_brightness.set_value(brightness), brightness=brightness)
        

    def delayTxtFB(self, delay : float):
        self.app.remote.secureUpdate(self.delayTxt.set_text( str(delay)), delay=delay)

    def pauseFB(self, paused : bool):
        text = "Continue" if self.app.paused else "Pause"
        self.app.remote.secureUpdate(self.bt_pause.set_text(text), text=text)
    
    def on_bt_load_pressed(self, widget):
        self.app.forceLoad = True

    def on_bt_pause_pressed(self, widget):
        self.app.paused = not self.app.paused
        self.pauseFB(self.app.paused)
    def on_delayTxt_changed(self, widget, value):
        self.app.delay = float(value)
               
    def fileupload_on_success(self,widget, filename):
        """Event called after file upload"""
        self.lbl.set_text('Photo upload success: ' + filename)
        self.app.fileUpload(filename,PLUGIN_NAME)

    def fileupload_on_failed(self, widget, filename):
            """Event called after file upload"""
            self.lbl.set_text('Photo upload failed: ' + filename)

    def on_file_upload_input(self, widget, file_list):
        # Get the uploaded file
        uploaded_file = file_list[0]
        self.showFile(uploaded_file)
    
    def progress(self, value, limit):
        val = value * 100 // limit
        if hasattr(self, "nextLoad") and self.nextLoad:
            self.nextLoad.set_value(val)

remote : Remote = None

@plugins.hookimpl
def exit(app) -> None:
    """called when application is about to quit
    Placeholder for plugin cleanup
    """

@plugins.hookimpl 
def imageLoader(app):
    """called when a new image is required
    Returns ImgLoader desc. object.
    """

@plugins.hookimpl
def imageChangeAfter(app) -> None:
    """called after image was successfuly changed on the screen
    Intended for effects etc. Image is in app.image
    """

@plugins.hookimpl
def imageChangeBefore(app) -> None:
    """called after image was successfuly changed on the screen
    Intended for effects etc. Image is in app.image
    """
    # add image name
    if remote and app.loadedByPlugin == PLUGIN_NAME and remote.fileName:
        text=f"{remote.fileName}"
        app.image = drawText(text=text, size=app.frameSize, fontSize=12, textColor=(192,192,192,192), align=(HAlign.RIGHT, VAlign.BOTTOM), bgImage=app.image, offset=(10,5))


@plugins.hookimpl
def startup(app) -> None:
    """called after application start
    Placeholder for plugin initialisation
    """

@plugins.hookimpl
def loadCfg(app) -> None:
    """called before startup
    Placeholder for plugin default settings
    Use app.loadCfg(PLUGIN_NAME, dict_with_config)
    """
    defaultConfig = {
        "DELAY" : "60",
    }
    app.loadCfg(PLUGIN_NAME, defaultConfig) #load the real config and merge it with default values
    if hasattr(app.cfg[PLUGIN_NAME], "DELAY") and app.cfg[PLUGIN_NAME].DELAY:
        app.delay = float(app.cfg[PLUGIN_NAME].DELAY)
    

@plugins.hookimpl
def do(app) -> None:
    """called every second when frame is waiting to next frame.
    Intended for showing real time etc.
    """
    if remote:
        remote.progress(app.idleIter, int(app.delay))

@plugins.hookimpl
def showImage(app) -> bool:
    """called when a new image should be shown. Intended use is for display plugins. Returns success or failure.
    """

@plugins.hookimpl
def imageChangeBeforeEffects(app):
    """For post-effects aka NightMode. Called after imageChangeBefore and before showImage. Intended use is for global filters.
    """
    
@plugins.hookimpl
def brightnessChangeAfter(app, brightness : int) -> None:
    """called after brightness value was changed. Brightness is 0-255
    Intended as a feedback for remote
    """
    if remote:
        remote.setBrightnessFB(brightness)

@plugins.hookimpl
def ResizeBefore(app):
    """Called before resize"""

@plugins.hookimpl
def ResizeAfter(app):
    """Called after resize"""

@plugins.hookimpl
def setRemote(app):
    """For setting web based remote from plugins. Returns list of remi.Widgets"""
    global remote
    remote = Remote()
    remote.app = app
    app.slideShowRemote = remote
    widgets : list[gui.Widget]= remote.setRemote()
    remote.delayTxtFB(app.delay)
    remote.setBrightnessFB(app.brightness)

    return widgets

@plugins.hookimpl
def loadAfter(app):
    """Called after successful load"""

@plugins.hookimpl
def saveCfg(app) -> None:
    """called before startup
    Placeholder for plugin settings to be stored.
    Use app.saveCfg(PLUGIN_NAME, dict_with_config)
    """
    app.saveCfg(PLUGIN_NAME, {"DELAY":app.delay})

@plugins.hookimpl
def setAPI(app : SlideShow):
    """
    Placeholder for setting plugin specific REST API calls.
    Should contain:
    router = APIRouter()
    @router.get("/api_point")
        def api_point():
            return {"message": "Not implemented yet"}
    app.api.registerRouter(PLUGIN_NAME, router)
    """
    router = APIRouter()
    @router.get("/load")
    def load():
        app.setStage(None)
        return {"message": "Loading new image"}
    
    @router.get("/run")
    def run():
        return {"message": not app.paused}
    @router.put("/run")
    def runSet(value : bool):
        app.paused = not value
        if remote:
            remote.pauseFB(app.paused)
        return {"message": not app.paused}
    

    @router.get("/delay")
    def delay():
        return {"message": app.delay}
    
    @router.put("/delay")
    def delaySet(value : float):
        app.delay = value
        if remote:
            remote.delayTxtFB(app.delay)
        return {"message": app.delay}
    
    @router.get("/brightness")
    def brightness():
        return {"message": app.brightness}
    
    @router.put("/brightness")
    def brightnessSet(value : float):
        app.setBrightness(int(value))
        app.setStage(app.Stage.RESIZE)
        if remote:
            remote.setBrightnessFB(value)
        return {"message": value}
    
    @router.post("/upload")
    def upload(file: UploadFile = File(...)):
        try:
            fullPath = osp.join(app.uploadPath, file.filename)
            with open(fullPath, 'wb') as f:
                while contents := file.file.read(1024 * 1024):
                    f.write(contents)
        except Exception:
            raise HTTPException(status_code=500, detail='Something went wrong')
        
        app.fileUpload(file.filename, PLUGIN_NAME)
        return {"message": f"Image uploaded {file.filename}"}
    app.api.registerRouter(PLUGIN_NAME, router)
    
