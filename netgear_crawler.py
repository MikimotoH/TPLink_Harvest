# coding: utf-8
import harvest_utils
from harvest_utils import waitClickable, waitVisible, waitText, getElems, \
        getElemText,getFirefox,driver,dumpSnapshot,\
        getText, getNumElem, waitTextChanged, waitElem, \
        waitUntil, clickElem, getElemAttr, hasElem, waitUntilStable, \
        waitUntilA, mouseClickE, waitTextA, UntilTextChanged, mouseOver
from selenium.common.exceptions import NoSuchElementException, TimeoutException,\
        StaleElementReferenceException, WebDriverException
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.support.ui import Select, WebDriverWait
from selenium.webdriver.common.action_chains import ActionChains
import sys
import sqlite3
from os import path
import os
import re
import time
from datetime import datetime
import ipdb,pdb
import traceback
from my_utils import uprint, ulog
from contextlib import suppress
import asyncio
import threading

driver,conn=None,None
startTrail,prevTrail=[],[]
TRY_AGAIN=0
PROC_OK=1
PROC_GIVE_UP=2

def css(path) -> WebElement:
    global driver
    return driver.find_element_by_css_selector(path)
def cssA(path):
    global driver
    return driver.find_elements_by_css_selector(path)

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


class ClickOutOverlayTimer(threading.Thread):
    def __init__(self):
        threading.Thread.__init__(self)
    def run(self):
        while True:
            try:
                driver.find_element_by_css_selector("a.btn.close.fl-left").\
                        click()
                print('overlay terminated')
                return
            except:
                print('no overlay, sleep 1 seconds')
                time.sleep(1)


def storeFile(modelName, fileItem):
    global driver, prevTrail
    try:
        try:
            fileUrl = fileItem.get_attribute('data-durl')
            if fileUrl is None:
                fileUrl = fileItem.get_attribute('href')
        except Exception as ex:
            fileUrl = fileItem.get_attribute('href')
        _, ext = path.splitext(fileUrl)
        if ext in ['.html', '.htm']:
            return
        fileName = fileItem.text.strip()
        vendor='Netgear'
        try:
            fwVer=re.search(r'(?<=Version\ )\d+(\.\d+)+',fileName, flags=re.I)\
                .group(0)
        except Exception as ex:
            fwVer=None
        pageUrl = driver.current_url
        rev=""
        trailStr=str(prevTrail)
        sql("INSERT OR REPLACE INTO TFiles (vendor, model,revision,"
            "fw_ver, file_name, "
            "page_url, file_url, tree_trail) VALUES"
            "(:vendor, :modelName, :rev,"
            ":fwVer,:fileName,"
            ":pageUrl,:fileUrl,:trailStr)",locals())
        ulog('UPSERT "%(modelName)s", '
            ' "%(fileName)s", %(fileUrl)s'%locals())
    except Exception as ex:
        ipdb.set_trace(); traceback.print_exc()
        driver.save_screenshot('netgear_exc.png')


def walkFile():
    global driver, prevTrail
    try:
        try:
            modelName = waitTextChanged('h2#searchResults', None, 5, 1)
        except TimeoutException:
            try:
                modelName = waitText('h2#searchResults', 5, 1)
            except TimeoutException:
                return PROC_GIVE_UP
        ulog('modelName="%s"'%modelName)

        resultsCount = waitText('#LargeFirmware>p')
        # try:
        #     resultsCount = waitTextChanged('#LargeFirmware>p', None, 0.5, 0.25)
        #     ulog('waitTextChanged #LargeFirmware>p')
        # except TimeoutException:
        #     ulog('TimeoutException: #LargeFirmware>p')
        #     resultsCount = waitText('#LargeFirmware>p')
        # except NoSuchElementException:
        #     ulog('NoSuchElementException: #LargeFirmware>p')
        #     resultsCount = waitText('#LargeFirmware>p')
        ulog('resutlsCount=%s'%resultsCount)
        if resultsCount.startswith('No matching'):
            return

        numFiles = int(re.search(r'\d+', resultsCount).group(0))
        ulog('numFiles=%d'%numFiles)

        try:
            waitTextChanged('#LargeFirmware a.navlistsearch',
                            None, 1, 0.5)
            ulog('waitTextChanged #LargeFirmware a.navlistsearch')
        except TimeoutException:
            ulog('TimeoutException: #LargeFirmware a.navlistsearch')
            pass
        except NoSuchElementException:
            ulog('NoSuchElementException #LargeFirmware a.navlistsearch')
            return

        if numFiles > 10:
            ulog('click moreResults because numFiles=%d>10'%numFiles)
            bMoreResultsClicked=False
            for _i in range(10):
                moreResults = waitClickable('#lnkAllDownloadMore')
                try:
                    moreResults.click()
                    ulog('moreResults.click()')
                    bMoreResultsClicked=True
                    break
                except WebDriverException:
                    time.sleep(0.5)
            if not bMoreResultsClicked:
                raise StaleElementReferenceException()

        lastFile = driver.find_element_by_css_selector('#LargeFirmware li:nth-child(%d) a.navlistsearch'%numFiles)
        for _i in range(10):
            if lastFile.is_displayed():
                break
            time.sleep(0.5)

        # try:
        #     waitTextChanged('#LargeFirmware li:nth-child(%d)'%numFiles,
        #                     None, 1, 0.5)
        #     ulog('waitTextChanged #LargeFirmware li:nth-child(%d)'%numFiles)
        # except TimeoutException:
        #     ulog('TimeoutException: #LargeFirmware li:nth-child(%d)'%numFiles)
        #     pass
        # except NoSuchElementException:
        #     ulog('NoSuchElementException #LargeFirmware li:nth-child(%d)'%numFiles)
        #     return
        # waitClickable('#LargeFirmware li:nth-child(%d) a.navlistsearch'
        #               %numFiles)

        files = getElems('#LargeFirmware a.navlistsearch')
        startIdx = getStartIdx()
        # get firmware download URL
        for idx in range(startIdx, numFiles):
            assert files[idx].is_displayed()
            fileName = files[idx].text
            ulog('idx=%d, fileName="%s"'%(idx, fileName))
            if 'firmware' not in fileName.lower():
                continue
            prevTrail+=[idx]
            storeFile(modelName, files[idx])
            prevTrail.pop()
        return PROC_OK
    except (StaleElementReferenceException):
        try:
            driver.find_element_by_css_selector("a.btn.close.fl-left").\
                    click()
            return TRY_AGAIN
        except (NoSuchElementException):
            return TRY_AGAIN
    except TimeoutException as ex:
        raise ex
    except Exception as ex:
        traceback.print_exc(); ipdb.set_trace()
        driver.save_screenshot('netgear_exc.png')


def walkProd():
    global driver, prevTrail
    try:
        # click overlay advertisement popup left button "No Thanks"
        try:
            driver.find_element_by_css_selector("a.btn.close.fl-left").\
                    click()
        except (NoSuchElementException):
            pass

        zpath = ('#ctl00_ctl00_ctl00_mainContent_localizedContent_bodyCenter'+
                 '_adsPanel_lbProduct')
        waitTextChanged(zpath)
        curSel = Select(css(zpath))
        numProds = len(curSel.options)
        ulog("numProds=%d"%numProds)

        startIdx = getStartIdx()
        for idx in range(startIdx, numProds):
            curSel = Select(css(zpath))
            ulog("idx=%s"%idx)
            ulog('select "%s"'%curSel.options[idx].text)
            curSel.select_by_index(idx)
            prevTrail+=[idx]
            while True:
                ret = walkFile()
                if ret != TRY_AGAIN:
                    break
            if ret== PROC_GIVE_UP:
                ulog('"%s" is GIVE UP'% curSel.options[idx].text)
            prevTrail.pop()
        return PROC_OK
    except Exception as ex:
        traceback.print_exc(); ipdb.set_trace()
        driver.save_screenshot('netgear_exc.png')


def walkProdFam():
    global driver, prevTrail
    try:
        # ProductFamily (Middle) Select Control
        zpath = ('#ctl00_ctl00_ctl00_mainContent_localizedContent_bodyCenter'+
                 '_adsPanel_lbProductFamily')
        waitTextChanged(zpath)
        curSel = Select(css(zpath))
        numProdFams = len(curSel.options)
        ulog("numProdFams=%d"%numProdFams)

        startIdx = getStartIdx()
        for idx in range(startIdx, numProdFams):
            curSel = Select(css(zpath))
            ulog("idx=%s"%idx)
            ulog('select "%s"'%curSel.options[idx].text)
            curSel.select_by_index(idx)
            prevTrail+=[idx]
            walkProd()
            prevTrail.pop()
    except Exception as ex:
        traceback.print_exc(); ipdb.set_trace()
        driver.save_screenshot('netgear_exc.png')


def walkProdCat():
    global driver, prevTrail
    try:
        # click "Drilldown"
        waitClickable('#ctl00_ctl00_ctl00_mainContent_localizedContent_bodyCenter_BasicSearchPanel_btnAdvancedSearch')\
            .click()

        zpath = ('#ctl00_ctl00_ctl00_mainContent_localizedContent_bodyCenter_'+
                 'adsPanel_lbProductCategory')
        curSel = Select(css(zpath))
        numProdCats = len(curSel.options)
        ulog('numProdCats=%d'%numProdCats)

        startIdx = getStartIdx()
        for idx in range(startIdx, numProdCats):
            curSel = Select(css(zpath))
            ulog("idx=%s"%idx)
            ulog('select "%s"'%curSel.options[idx].text)
            curSel.select_by_index(idx)
            prevTrail+=[idx]
            walkProdFam()
            prevTrail.pop()
    except Exception as ex:
        traceback.print_exc(); ipdb.set_trace()
        driver.save_screenshot('netgear_exc.png')


def main():
    global startTrail,prevTrail,driver,conn
    try:
        startTrail = [int(re.search(r'\d+', _).group(0)) for _ in sys.argv[1:]]
        uprint('startTrail=%s'%startTrail)
        conn = sqlite3.connect('netgear.sqlite3')
        sql("CREATE TABLE IF NOT EXISTS TFiles("
                "id INTEGER NOT NULL,"
                "vendor TEXT,"
                "model TEXT,"
                "revision TEXT,"
                "fw_date TEXT,"
                "fw_ver TEXT,"
                "file_name TEXT,"
                "file_size TEXT,"
                "page_url TEXT,"
                "file_url TEXT,"
                "tree_trail TEXT,"
                "file_sha1 TEXT,"
                "PRIMARY KEY (id),"
                "UNIQUE(vendor,model,revision,file_name)"
                ");")
        driver = harvest_utils.getFirefox()
        harvest_utils.driver= driver
        driver.get("http://downloadcenter.netgear.com/")
        prevTrail=[]
        # tmr = ClickOutOverlayTimer()
        # tmr.start()
        walkProdCat()
    except Exception as ex:
        traceback.print_exc(); ipdb.set_trace()
        driver.save_screenshot('netgear_exc.png')
    finally:
        driver.quit()
        conn.close()


if __name__=='__main__':
    global driver
    try:
        main()
    except Exception as ex:
        traceback.print_exc(); ipdb.set_trace()
        if driver:
            try:
                driver.save_screenshot('netgear_exc.png')
                driver.quit()
            except Exception:
                pass
