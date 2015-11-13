#!/usr/bin/env python3
# coding: utf-8
import harvest_utils
from harvest_utils import waitClickable, waitVisible, waitText, getElems, \
        getElemText,getFirefox,driver,dumpSnapshot,\
        getText,getNumElem,waitTextChanged,waitElem,\
        waitUntil,clickElem,getElemAttr,hasElem,waitUntilStable,\
        waitUntilA,mouseClickE,waitTextA,UntilTextChanged,mouseOver
from selenium.common.exceptions import NoSuchElementException, \
        TimeoutException, StaleElementReferenceException, \
        WebDriverException
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.support.ui import WebDriverWait,Select
from selenium.webdriver.common.action_chains import ActionChains
import sys
import sqlite3
from os import path
import os
import re
import time
from datetime import datetime
import ipdb
import traceback
from my_utils import uprint,ulog
from contextlib import suppress

driver,conn=None,None
startTrail=[]
prevTrail=[]

def glocals()->dict:
    """ globals() + locals()
    """
    import inspect
    outer = dict(inspect.stack()[1][0].f_locals)
    outer.update(globals())
    return outer

def getScriptName():
    from os import path
    return path.splitext(path.basename(__file__))[0]


def getStartIdx():
    global startTrail
    if startTrail:
        return startTrail.pop(0)
    else:
        return 0

def sql(query:str, var=None):
    global conn
    csr=conn.cursor()
    try:
        if var:
            rows = csr.execute(query,var)
        else:
            rows = csr.execute(query)
        if not query.startswith('SELECT'):
            conn.commit()
        if query.startswith('SELECT'):
            return rows.fetchall()
        else:
            return
    except sqlite3.Error as ex:
        print(ex)
        raise ex

def cssWithText(css:str,txt:str)->WebElement:
    global driver
    return next((_ for _ in driver.find_elements_by_css_selector(css) if  
        _.text == txt), None)


def guessDate(txt:str)->datetime:
    """ txt = '22/10/15' """
    try:
        return datetime.strptime(txt, '%d/%m/%y')
    except Exception as ex:
        ipdb.set_trace()
        print('txt=',txt)

def guessFileSize(txt:str)->int:
    """ txt='6.56 MB'
    """
    try:
        m = re.search(r'(\d*[.])?\d+', txt, re.I)
        if not m:
            ulog('error txt="%s"'%txt)
            return 0
        unitDic=dict(MB=1024**2,KB=1024)
        unitTxt = txt[m.span()[1]:].strip()
        return int(float(m.group(0)) * unitDic[unitTxt] )
    except Exception as ex:
        ipdb.set_trace()
        print('txt=',txt)

def fileWalker():
    global driver,prevTrail
    try:
        modelName = waitText('h1 strong.model')
        modelRev = waitText('h1')
        revName = modelRev.split(modelName)[-1].strip()

        tabbtn = cssWithText('ul.row li a', 'Firmware')
        if not tabbtn:
            ulog('no firmware download for "%s"'%modelName)
            driver.close()
            driver.switch_to.window(driver.window_handles[-1])
            return
        tabbtn.click()
        pageUrl=driver.current_url
        tables=getElems('#content_firmware table')
        #waitUntil( lambda:ulog('is_displayed()=%s'%[_.is_displayed() for 
        #    _ in tables])>=0 )
        startIdx = getStartIdx()
        numTables=len(tables)
        for idx in range(startIdx,numTables):
            table=tables[idx]
            if not table.is_displayed():
                continue
            ulog('trail=%s'%(prevTrail+[idx]))
            basicInfo=table.find_element_by_css_selector('tr.basic-info').text
            fileName,_,dateStr,_,lang,_,fileSize = basicInfo.splitlines()
            fwDate=guessDate(dateStr)
            fwVer = fileName.split('_')[-1].strip()
            fileSize=guessFileSize(fileSize)
            fileLink=table.find_element_by_css_selector('a')
            fileUrl=fileLink.get_attribute('href')
            ulog('fileName="%s"'%fileName)

            fwDesc='\n'.join(_.text for _ in 
                    table.find_elements_by_css_selector('tr.more-info'))
            trailStr=str(prevTrail+[idx])
            sql("INSERT OR REPLACE INTO TFiles (model,revision,"
                "fw_date, fw_ver, fw_desc, file_name,file_size, "
                "page_url,file_url,tree_trail) VALUES"
                "(:modelName, :revName, "
                ":fwDate,:fwVer,:fwDesc,:fileName,:fileSize,"
                ":pageUrl,:fileUrl,:trailStr)",locals())
            ulog('UPSERT "%(modelName)s", "%(revName)s", "%(fwDate)s", '
                ' "%(fileName)s", %(fileSize)s,%(fileUrl)s'%locals())
        driver.close()
        driver.switch_to.window(driver.window_handles[-1])
        return
    except Exception as ex:
        ipdb.set_trace()
        traceback.print_exc()
        driver.save_screenshot(getScriptName()+'_'+getFuncName()+'_exc.png')
        

def modelWalker():
    global driver,prevTrail
    try:
        models = getElems('.list ul li a')
        numModels=len(models)
        ulog('numModels=%s'%numModels) 
        startIdx = getStartIdx()
        for idx in range(startIdx,numModels):
            modelName = models[idx].text
            ulog('enter %s,"%s"'%(idx,modelName))
            prevTrail+=[idx]
            models[idx].click()
            waitUntil(lambda:len(driver.window_handles)==2)
            driver.switch_to.window(driver.window_handles[-1])
            fileWalker()
            prevTrail.pop()
            models = getElems('.list ul li a')
    except Exception as ex:
        ipdb.set_trace()
        traceback.print_exc()
        driver.save_screenshot(getScriptName()+'_'+getFuncName()+'_exc.png')

def marketSelect():
    global driver,prevTrail
    try:
        showEol=waitVisible('#showEndLife')
        if not showEol.is_selected():
            showEol.click()
        selMkt= Select(waitVisible('.product-cat-box select:nth-child(1)'))
        startIdx=getStartIdx()
        numMkts = len(selMkt.options)
        curSel = selMkt.all_selected_options[0].text
        ulog('current Selected="%s"'%curSel)
        for idx in range(startIdx, numMkts):
            selMkt.select_by_index(idx)
            nextSel=selMkt.options[idx].text
            ulog('gonna select "%s"'%nextSel)
            btn = waitVisible('button.round-button.go')
            with UntilTextChanged('.content-box',9,0.4):
                btn.click()
            prevTrail+=[idx]
            modelWalker()
            prevTrail.pop()
            showEol=waitVisible('#showEndLife')
            if not showEol.is_selected():
                showEol.click()
            selMkt= Select(waitVisible('.product-cat-box select:nth-child(1)'))
    except Exception as ex:
        ipdb.set_trace()
        traceback.print_exc()
        driver.save_screenshot(getScriptName()+'_'+getFuncName()+'_exc.png')

def main():
    global startTrail,prevTrail, driver,conn
    try:
        startTrail = [int(re.search(r'\d+', _).group(0)) for _ in sys.argv[1:]]
        uprint('startTrail=%s'%startTrail)
        conn=sqlite3.connect('tplink.sqlite3')
        sql(
            "CREATE TABLE IF NOT EXISTS TFiles("
            "id INTEGER NOT NULL,"
            "model TEXT,"
            "revision TEXT,"
            "fw_date DATE,"
            "fw_ver TEXT,"
            "fw_desc TEXT,"
            "file_name TEXT,"
            "file_size INTEGER,"
            "page_url TEXT,"
            "file_url TEXT,"
            "tree_trail TEXT,"
            "file_sha1 TEXT,"
            "PRIMARY KEY (id)"
            "UNIQUE(model,revision,file_name)"
            ");")
        driver=harvest_utils.getFirefox()
        harvest_utils.driver=driver
        driver.get('http://www.tp-link.com/en/download-center.html')
        prevTrail=[]
        marketSelect()
        driver.quit()
        conn.close()
    except Exception as ex:
        ipdb.set_trace()
        traceback.print_exc()
        driver.save_screenshot(getScriptName()+'_'+getFuncName()+'_exc.png')

if __name__=='__main__':
    try:
        main()
    except Exception as ex:
        ipdb.set_trace()
        print(ex); traceback.print_exc()
        try:
            driver.save_screenshot(getScriptName()+'_exc.png')
            driver.quit()
        except Exception:
            pass

