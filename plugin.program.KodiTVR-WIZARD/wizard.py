#!/usr/bin/python
# -*- coding: utf-8 -*-
import xbmc,xbmcaddon,xbmcgui,xbmcplugin,os,sys,urllib,re,time

if xbmc.getCondVisibility('system.platform.android') and int(xbmc.getInfoLabel('System.BuildVersion')[:2]) >= 18:import fixetzipfile as zipfile
else:import origzipfile as zipfile

def de_en_code_path(path):
    if sys.platform.startswith('win'):
        return xbmc.translatePath( path ).decode('utf-8')
    else:
        return xbmc.translatePath( path ).encode('utf-8')

addon = xbmcaddon.Addon()
addon_id = addon.getAddonInfo('id')
addon_path = de_en_code_path(addon.getAddonInfo('path'))

backup_zip_full_path = os.path.join(addon_path,'resources','backup','backup.zip')
home_path = de_en_code_path('special://home/')


# server url ?
server_data_url = 'http://sgkodi.de/Wizard-Daten/Backup/wizard_data.txt'
# server data structure( http://xxx/xxx/wizard_data.txt ):

# title=""
# url=""
# image="" 

# u.s.w...

def read_server_data(server_url):
    try:
        return urllib.urlopen(server_url).read()
    except Exception as e:
        xbmcgui.Dialog().ok('SERVER DATA ERROR !',str(e))
        sys.exit(0)

def add_dir(name,url,mode,iconimage):
    u=sys.argv[0]+'?url='+urllib.quote_plus(url)+'&mode='+str(mode)+'&name='+urllib.quote_plus(name)+'&iconimage='+urllib.quote_plus(iconimage)
    liz=xbmcgui.ListItem(name,iconImage='DefaultFolder.png',thumbnailImage=iconimage)
    liz.setInfo( type='Picture',infoLabels={ 'Title': name } )
    xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]),url=u,listitem=liz,isFolder=True)

def add_dir_regex(content,view_mode):
    if not content:sys.exit(0)
    content = content.replace("'",'"')
    for title,url,img in re.findall('title="(.*?)"[\s\S].*?url="(.*?)"[\s\S].*?image="(.*?)"',content,re.DOTALL):
        add_dir(title.strip(),url.strip(),1,img.strip())
    xbmc.executebuiltin('Container.SetViewMode('+ view_mode +')')

def delete_file(file):
    if os.path.isfile(file):
        try:
            os.remove(file)
        except:
            pass

def clean_data(home_path,self_id):
    dp = xbmcgui.DialogProgress()
    dp.create('FRESH START','Bereinige Daten !','Bitte warten ...')
    dp.update(0)
    filesList = []
    save_list_array = []
    try:
        skin_id = xbmc.getSkinDir()
        if not self_id == '':
            save_list_array.append(self_id)
        if not skin_id == '':
            save_list_array.append(skin_id)
        save_list_array.append('Addons26.db')
        save_list_array.append('Addons27.db')
        save_list_array.append('Textures13.db')
        save_list_array.append('commoncache.db')
        save_list_array.append('metadata.album.universal')
        save_list_array.append('metadata.artists.universal')
        save_list_array.append('metadata.common.musicbrainz.org')
        save_list_array.append('metadata.common.imdb.com')
        save_list_array.append('inputstream.adaptive')
        filesList = list(os.walk(home_path,topdown=False,onerror=None,followlinks=True))
        count = int(0)
        filesCount = float(0)
        filesCount += float(len(filesList))
        for pathentry in filesList:
            for dir in pathentry[1]:
                path = os.path.join(pathentry[0],dir)
                if not any((x in path for x in save_list_array)):
                    if os.path.islink(path):
                        try:
                            os.unlink(path)
                        except:
                            pass
                    else:
                        try:
                            os.rmdir(path)
                        except:
                            pass
            for file in pathentry[2]:
                path = os.path.join(pathentry[0],file)
                if not any((x in path for x in save_list_array)):
                    try:
                        os.unlink(path)
                    except:
                        pass
            count += 1
            update = count / filesCount * 100
            dp.update(int(update))
            if dp.iscanceled():
                dp.close()
                sys.exit(1)
    except Exception as e:
        dp.close()
        xbmcgui.Dialog().ok('ERROR !', str(e))
        sys.exit(1)
    dp.close()

def download_zip(zip_download_url,zip_download_full_path):
    try:
        start_time = time.time()
        dp = xbmcgui.DialogProgress()
        dp.create('KodiTVR-WIZARD','Lade Backup!','Bitte warten...')
        dp.update(0)
        urllib.urlretrieve(zip_download_url,zip_download_full_path,lambda nb,bs,fs:_pbhook(nb,bs,fs,dp,start_time,zip_download_full_path))
    except Exception as e:
        dp.close()
        xbmcgui.Dialog().ok('DOWNLOAD ERROR !',str(e))
        sys.exit(1)
def _pbhook(numblocks,blocksize,filesize,dp,start_time,zip_download_full_path):
    try:
        percent = min(numblocks * blocksize * 100 / filesize, 100)
        currently_downloaded = float(numblocks) * blocksize / 1048576
        kbps_speed = numblocks * blocksize / (time.time() - start_time)
        if kbps_speed > 0:
            eta = (filesize - numblocks * blocksize) / kbps_speed
        else:
            eta = 0
        kbps_speed = kbps_speed / 1024
        mbps_speed = kbps_speed / 1024
        total = float(filesize) / 1048576
        mbs = 'Geladen: %.02f MB von %.02f MB' % (currently_downloaded,total)
        e = 'Geschwindigkeit: %.02f Mb/s ' % mbps_speed
        ee = 'Verbleibende Zeit: %02d:%02d Min' % divmod(eta,60)
        dp.update(percent,mbs,e,ee)
    except:
        percent = 100
        dp.update(percent)
        dp.close()
    if dp.iscanceled():
        dp.close()
        sys.exit(1)

def extract_zip(zip_file_full_path,home_path,self_id,zip_pwd=None):
    if not os.path.exists(zip_file_full_path):
        xbmcgui.Dialog().ok('ZIP EXTRACT ERROR !','File not found !')
        sys.exit(0) 
    dp = xbmcgui.DialogProgress()
    dp.create('KodiTVR-WIZARD','Entpacke Daten!','Bitte warten...')
    dp.update(0)
    count = int(0)
    try:
        zip = zipfile.ZipFile(zip_file_full_path,mode='r',compression=zipfile.ZIP_STORED,allowZip64=True)
        nFiles = float(len(zip.infolist()))
        for item in zip.infolist():
            count += 1
            update = count / nFiles * 100
            dp.update(int(update))
            try:
                if str(self_id) not in str(item.filename):
                    zip.extract(item,path=home_path,pwd=zip_pwd)
            except:
                pass
            if dp.iscanceled():
                dp.close()
                sys.exit(1)
    except Exception as e:
        dp.close()
        xbmcgui.Dialog().ok('ZIP EXTRACT ERROR !',str(e))
        sys.exit(1)
    dp.close()
    zip.close()

def kill_xbmc():
    myplatform = None
    if xbmc.getCondVisibility('system.platform.android'):
        myplatform = 'android'
    if xbmc.getCondVisibility('system.platform.linux'):
        myplatform = 'linux'
    if xbmc.getCondVisibility('system.platform.windows'):
        myplatform = 'windows'
    if xbmc.getCondVisibility('system.platform.osx'):
        myplatform = 'osx'
    if xbmc.getCondVisibility('system.platform.atv'):
        myplatform = 'atv2'
    if xbmc.getCondVisibility('system.platform.atv2'):
        myplatform = 'atv2'
    if xbmc.getCondVisibility('system.platform.atv3'):
        myplatform = 'atv3'
    if xbmc.getCondVisibility('system.platform.atv4'):
        myplatform = 'atv4'
    if xbmc.getCondVisibility('system.platform.ios'):
        myplatform = 'ios'
    i = xbmcgui.Dialog().yesno('KODI BEENDEN', 'Sie sind dabei Kodi zu schlie\xc3\x9fen !', 'M\xc3\xb6chten Sie fortfahren ?', nolabel='NEIN', yeslabel='JA')
    if i < 1:
        sys.exit(0)
    if myplatform == 'osx':
        try:
            os.system('killall -9 Kodi')
        except:
            pass
        xbmcgui.Dialog().ok('[COLOR red]ACHTUNG ![/COLOR]','Kodi konnte nicht beendet werden !' + '\n\n' + 'Schlie\xc3\x9fen Sie Kodi \xc3\xbcber den [COLOR red]Taskmanager[/COLOR] oder' + '\n' + 'starten Sie das Ger\xc3\xa4t manuell neu !' + '\n\n' + '[COLOR red]Verwenden Sie nicht die Kodi Quit / Exit Optionen ![/COLOR]')
        sys.exit(0)
    elif myplatform == 'linux':
        try:
            os.system('killall Kodi')
        except:
            pass
        try:
            os.system('killall -9 kodi.bin')
        except:
            pass
        xbmcgui.Dialog().ok('[COLOR red]ACHTUNG ![/COLOR]','Kodi konnte nicht beendet werden !' + '\n\n' + 'Schlie\xc3\x9fen Sie Kodi \xc3\xbcber den [COLOR red]Taskmanager[/COLOR] oder' + '\n' + 'starten Sie das Ger\xc3\xa4t manuell neu !' + '\n\n' + '[COLOR red]Verwenden Sie nicht die Kodi Quit / Exit Optionen ![/COLOR]')
        sys.exit(0)
    elif myplatform == 'android':
        try:
            os.system('adb shell am force-stop org.xbmc.kodi')
        except:
            pass
        try:
            os.system('adb shell am kill org.xbmc.kodi')
        except:
            pass
        try:
            os.system('Process.killProcess(android.os.Process.org.xbmc.kodi());')
        except:
            pass
        try:
            os.system('adb shell am force-stop com.semperpax.spmc16')
        except:
            pass
        try:
            os.system('adb shell am kill com.semperpax.spmc16')
        except:
            pass
        try:
            os.system('Process.killProcess(android.os.Process.com.semperpax.spmc16());')
        except:
            pass
        try:
            os.system('adb shell am force-stop com.semperpax.spmc17')
        except:
            pass
        try:
            os.system('adb shell am kill com.semperpax.spmc17')
        except:
            pass
        try:
            os.system('Process.killProcess(android.os.Process.com.semperpax.spmc17());')
        except:
            pass
        xbmcgui.Dialog().ok('[COLOR red]ACHTUNG ![/COLOR]','Kodi konnte nicht beendet werden !' + '\n\n' + 'Schlie\xc3\x9fen Sie Kodi \xc3\xbcber den [COLOR red]Taskmanager[/COLOR] oder' + '\n' + 'starten Sie das Ger\xc3\xa4t manuell neu !' + '\n\n' + '[COLOR red]Verwenden Sie nicht die Kodi Quit / Exit Optionen ![/COLOR]')
        xbmc.executebuiltin('StartAndroidActivity("","android.settings.APPLICATION_SETTINGS","","")')
        sys.exit(0)
    elif myplatform == 'windows':
        try:
            os.system('@ECHO off')
            os.system('tskill Kodi.exe')
        except:
            pass
        try:
            os.system('@ECHO off')
            os.system('TASKKILL /im Kodi.exe /f')
        except:
            pass
        xbmcgui.Dialog().ok('[COLOR red]ACHTUNG ![/COLOR]','Kodi konnte nicht beendet werden !' + '\n\n' + 'Schlie\xc3\x9fen Sie Kodi \xc3\xbcber den [COLOR red]Taskmanager[/COLOR] oder' + '\n' + 'starten Sie das Ger\xc3\xa4t manuell neu !' + '\n\n' + '[COLOR red]Verwenden Sie nicht die Kodi Quit / Exit Optionen ![/COLOR]')
        sys.exit(0)
    else:
        try:
            os.system('killall AppleTV')
        except:
            pass
        try:
            os.system('sudo initctl stop kodi')
        except:
            pass
        xbmcgui.Dialog().ok('[COLOR red]ACHTUNG ![/COLOR]','Kodi konnte nicht beendet werden !' + '\n\n' + 'Schlie\xc3\x9fen Sie Kodi \xc3\xbcber den [COLOR red]Taskmanager[/COLOR] oder' + '\n' + 'starten Sie das Ger\xc3\xa4t manuell neu !' + '\n\n' + '[COLOR red]Verwenden Sie nicht die Kodi Quit / Exit Optionen ![/COLOR]')
        sys.exit(0)
    sys.exit(0)

def get_params():
    param=[]
    paramstring=sys.argv[2]
    if len(paramstring)>=2:
        params=sys.argv[2]
        cleanedparams=params.replace('?','')
        if (params[len(params)-1]=='/'):
            params=params[0:len(params)-2]
        pairsofparams=cleanedparams.split('&')
        param={}
        for i in range(len(pairsofparams)):
            splitparams={}
            splitparams=pairsofparams[i].split('=')
            if (len(splitparams))==2:
                param[splitparams[0]]=splitparams[1]                         
        return param		
params=get_params()

url=None
name=None
mode=None
iconimage=None

try:
    url=urllib.unquote_plus(params["url"])
except:
    pass
try:
    name=urllib.unquote_plus(params["name"])
except:
    pass
try:
    iconimage=urllib.unquote_plus(params["iconimage"])
except:
    pass
try:        
    mode=int(params["mode"])
except:
    pass

if mode == None:
    add_dir_regex(read_server_data(server_data_url),'500')
if mode == 1:
    clean_data(home_path,addon_id)
    time.sleep(1)
    download_zip(url,backup_zip_full_path)
    time.sleep(1)
    extract_zip(backup_zip_full_path,home_path,addon_id)
    time.sleep(1)
    delete_file(backup_zip_full_path)
    kill_xbmc()

xbmcplugin.endOfDirectory(int(sys.argv[1]),succeeded=True,updateListing=False,cacheToDisc=False)