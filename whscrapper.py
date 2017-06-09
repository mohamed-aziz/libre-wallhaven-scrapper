#!/usr/bin/env python2

# Libre wallhaven scrapper
# Author: Mohamed Aziz Knani; medazizknani[at]gmail.com
# Feel free to fork, Happy coding
import wx
from os.path import expanduser, join, isfile
from glob import glob
import urllib2, re
from bs4 import BeautifulSoup
import imghdr
import threading


# The default path
PATH = '/home/mohamed/wallpapers/'

class Wallhaven(object):
    # Get home directory, this is cross platform
    home = expanduser('~')

    def __init__(self, resolution, searchterm):
        self.resolution = 'x'.join(resolution)
        self.term = searchterm

    def crawl(self, page) :
        # refactor this code
   	url = 'http://alpha.wallhaven.cc/search?categories=111&purity=100&q=%s&resolutions=%s&sorting=random&order=desc&page=%s' % (self.term, self.resolution, page)
	req = urllib2.Request(url, headers={ 'User-Agent': 'Mozilla/5.0' })
	html = urllib2.urlopen(req).read()
	soup = BeautifulSoup(html, 'html')
	ss = soup.findAll('a', {'class' : 'preview' })
        for s in ss :
            # the filename is always some type of a numeric value I use this regex to get it
            filename = re.search(r'\d+', s['href']).group(0)
	    url = 'http://wallpapers.wallhaven.cc/wallpapers/full/wallhaven-%s.jpg' % filename
            yield (url, filename)

    def loadpath(self):
        try:
            with open(join(self.home, '.lws'), 'r') as myfile:
                return myfile.read().strip()
        except:
            return "/tmp"

    def save_path(self, pth):
        with open(join(self.home, '.lws'), 'w') as myfile:
            myfile.write(pth)

class Directory(object):

    def __init__(self, path):
        self.path = path

    def GetimageFiles(self):
        """
        Gets valid image files from self.path
        """
        # You can extend the extensions list here
        ImageFiles = ['*.jpg', '*.png', '*.bmp']
        l = list()
        for ImageFile in ImageFiles:
            l.extend(glob(join(self.path, ImageFile)))
        # Make sure all the image files are valid
        return filter(self.isvalidFile, l)

    def save(self, url, filename):
	self.sv = join(self.path, filename + '.' + 'jpg')
        # check if the server returns OK (code 200) and the file does not exist then download the image
        req = urllib2.Request(url, headers={ 'User-Agent': 'Mozilla/5.0' })
        try:
            if (urllib2.urlopen(req).getcode()==200) and (not self.isvalidFile(self.sv)):
                # Check if this little fuck works!
                with open(self.sv, 'wb') as myfile:
                    myfile.write(urllib2.urlopen(req).read())
        except urllib2.HTTPError:
            pass

    def isvalidFile(self, path):
        return isfile(path) and imghdr.what(path) in ['gif', 'png', 'jpeg']



class DownloadThread(threading.Thread):
    def __init__(self, parent):
        threading.Thread.__init__(self)
        self._parent = parent
        self.stopped = False

    def run(self):
        disp = map(str, self._parent.resolution.GetValue().split('x'))

        self.mywh = Wallhaven(disp, self._parent.searchterm.Value)
        pages = self._parent.pages.GetValue()
        for i in xrange(1, pages+1):
            for el in self.mywh.crawl(i):
                if self.stopped:
                    return
                self._parent.dire.save( *el)
                self._parent.lv.Append([self._parent.dire.sv])

    def stop(self):
        self.stopped = True

class Window(wx.Frame):

    def __init__(self, *args, **kwargs):
        super(self.__class__, self).__init__(*args, **kwargs)
        self.mywh = Wallhaven([], '')
        # Inherits a Directory class and sets the path as '/tmp' if no config file is loaded
        self.dire = Directory(self.mywh.loadpath())

        self.panel = wx.Panel(self)
        vbox = wx.BoxSizer(wx.VERTICAL)
        hbox = wx.BoxSizer(wx.HORIZONTAL)
        hbox2 = wx.BoxSizer(wx.HORIZONTAL)

        self.lv = wx.ListView(self.panel, wx.ID_ANY, style=wx.LC_REPORT)
        self.lv.InsertColumn(0, 'Path')

        for el in self.dire.GetimageFiles():
            self.lv.Append([el])

        self.lv.SetColumnWidth(0, wx.LIST_AUTOSIZE)

        self.pages = wx.SpinCtrl(self.panel, wx.ID_ANY, min=1)
        self.resolution = wx.TextCtrl(self.panel, wx.NewId(),
            value='x'.join(map(str, list(wx.DisplaySize()))))

        self.pathinput = wx.TextCtrl(self.panel, id=wx.ID_ANY, value=self.dire.path)

        self.searchterm = wx.TextCtrl(self.panel, id=wx.ID_ANY)
        self.download  = wx.Button(self.panel, id=wx.ID_ANY, label="Fire")
        hbox.Add(wx.StaticText(self.panel, label='Save Path'), 0 ,5)
        hbox.Add(self.pathinput, 1, wx.ALL, 5)
        hbox.Add(wx.StaticText(self.panel, label='Search term'), 0 ,5)
        hbox.Add(self.searchterm, 1, wx.ALL, 5)
        hbox.Add(wx.StaticText(self.panel, label="Screen size"), 0, 5)
        hbox.Add(self.resolution, 0, wx.ALL, 5)
        hbox.Add(wx.StaticText(self.panel, label="Page number"), 0, 5)
        hbox.Add(self.pages, 0 , wx.ALL, 5)
        hbox.Add(self.download, 0, wx.ALL, 5)

        #self.png = wx.Image('/', type=wx.BITMAP_TYPE_ANY)
        self.png = wx.EmptyImage(300, 300, clear=True)
        #self.image = wx.StaticBitmap(self.panel, -1, self.png.Scale(300, 300).ConvertToBitmap())
        self.image = wx.StaticBitmap(self.panel, -1, self.png.ConvertToBitmap())

        hbox2.Add(self.lv, 2, wx.ALIGN_LEFT | wx.EXPAND | wx.ALL, 5)
        hbox2.Add(self.image, 1, wx.ALIGN_RIGHT | wx.ALL| wx.EXPAND, 5)

        self.wall = Wallhaven([], '')

        vbox.Add(hbox, 1, wx.ALL | wx.EXPAND, 5)
        vbox.Add(hbox2, 0, wx.ALL|wx.EXPAND|wx.TOP, 5)
        self.panel.SetSizer(vbox)
        vbox.Fit(self)
        self.Bind(wx.EVT_CLOSE, self.OnClose)
        self.lv.Bind(wx.EVT_LIST_ITEM_RIGHT_CLICK, self.MouseRightClick)
        self.download.Bind(wx.EVT_BUTTON, self.Fire)
        self.lv.Bind(wx.EVT_LIST_ITEM_SELECTED, self.DrawImage)
        self.Show(True)


    def OnClose(self, event):
        # On window close event save the path to the "config" file
        self.mywh.save_path(self.pathinput.Value)
        self.Destroy()

    def Fire(self, event):
        try:
            self.worker.stop()
            self.worker = None
            self.download.SetLabel('Fire')
        except:
            self.worker = DownloadThread(self)
            self.worker.start()
            self.download.SetLabel('Stop')

    def DrawImage(self, event):
        filepath = self.lv.GetItemText(self.lv.GetFirstSelected())
        # checks if the file exists and is valid image file
        if self.dire.isvalidFile(filepath):
            self.png.LoadFile(filepath, wx.BITMAP_TYPE_ANY)
            self.image.SetBitmap(self.png.Scale(300, 300).ConvertToBitmap())

    def MouseRightClick(self, event):
        self.selectedimage = event.GetText()
        menu = wx.Menu()
        item = wx.MenuItem(menu, wx.NewId(), 'Change background')
        menu.AppendItem(item)
        menu.Bind(wx.EVT_MENU, self.ChangeBack, item)
        # This will fix it for a while ?
        pos = event.GetPosition()
        self.PopupMenu(menu)
        menu.Destroy()

    def ChangeBack(self, event):
        import os
        if os.environ.has_key('DESKTOP_SESSION'):
          k = os.environ['DESKTOP_SESSION']
          # Works under my xfce 4.12
          if k=='xfce':
            os.system("xfconf-query -c xfce4-desktop -p /backdrop/screen0/monitorLVDS1/workspace0/last-image -s %s"\
                      % self.selectedimage)
          if k == 'gnome':
            os.system("gsettings set org.gnome.desktop.background picture-uri file://%s" % self.selectedimage)
          elif k == 'mate':
            os.system('gsettings set org.mate.background picture-filename %s' % self.selectedimage)
        else:
            os.system('feh --bg-fill %s' % self.selectedimage)

if __name__ == '__main__':
    myApp = wx.App()
    Window(None, title="Libre Wallhaven Scrapper (LWS) Ver. 0.1",
           size=(400, 300), style=wx.DEFAULT_FRAME_STYLE ^ wx.RESIZE_BORDER)
    myApp.MainLoop()
