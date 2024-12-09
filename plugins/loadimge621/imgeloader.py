import io
import logging as LOGGER
import loadimg
import pycurl
import certifi
import time
import py621,py621.types
import random

class ImgLoaderE621(loadimg.ImgLoader):
    pages : int = 700
    api : str = "e621"
    tags : list = ["status:active"]
    downloadLimit : float = 10
    url : str = None #URL to be shown
    def __init__(self):
        super().__init__()
        self.lastDownloadAttempt = 0
        

    def download(self, url : str) -> io.BytesIO:
        self.waitUntilWeReSafe()
        imgFile = io.BytesIO()
        try:
            c = pycurl.Curl()
            c.setopt(c.TIMEOUT, 30)
            c.setopt(c.URL, url)
            c.setopt(c.WRITEDATA, imgFile)
            c.setopt(c.CAINFO, certifi.where())
            c.setopt(c.FOLLOWLOCATION, True) # follow redirect
            # Error code: 1010 issue
            custom_headers = ['User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:89.0) Gecko/20100101 Firefox/89.0/8mqLkJuL-86']
            c.setopt(c.HTTPHEADER, custom_headers)
            LOGGER.debug(f"Downloading {url}")
            c.perform()
            c.close()
            
            LOGGER.debug(f"Image downloaded")
        except pycurl.error as e:
            LOGGER.error(f"Downloading Error: {e}")
            return None
        
        self.url = None #filled in do() in hookimpl
        return imgFile

    def getURL(self) -> str:
        # Create an unsafe api instance
        api_type = getattr(py621.types,self.api)
        api = py621.public.api(api_type)
        page : int = random.randint(0, self.pages)
        #choose a random post
        perpages = 70

        # Get posts from the Pool object
        posts = api.getPosts(self.tags,70,page,False) #negative tags don't work with True
        end : int = len(posts)
        LOGGER.debug(f"Found {end} posts")

        if end:
            imageNr : int = random.randint(0, end-1)
            LOGGER.debug(f"ImageNr: {imageNr}")

            post = posts[imageNr] # Select a post from the pool
            return post.sample.url
        else:
            # pages may be missing. Decrease the range
            if page > 1:
                self.pages = page - 1
                LOGGER.debug(f"Nr. of pages decreased to  {self.pages}")

    def nextAttempt(self) -> float:
        now = time.time()
        delta = now - self.lastDownloadAttempt
        return self.downloadLimit - delta
    
    def areWeSafe(self) -> bool:
            return self.nextAttempt() <=0
    
    def waitUntilWeReSafe(self):
        wait = self.nextAttempt()
        if wait>0: # don't spam the server too often
            LOGGER.debug(f"slowdown {wait}")
            time.sleep(wait)
        self.lastDownloadAttempt = time.time()

    def load(self):
        if not self.url:
            #force download
            self.url = self.getURL()
        if self.url:
            image = self.download(self.url)
            return image
    
