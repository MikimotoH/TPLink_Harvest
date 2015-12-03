#!/usr/bin/env python3
# coding:utf-8
import sqlite3
import psycopg2
from psycopg2 import errorcodes
import sys
from my_utils import uprint
from GridIotCredentials import GridIotConnStr
import ipdb
import traceback

ouconn=None
def ousql(query,var=None):
    global ouconn
    oucsr=ouconn.cursor()
    try:
        oucsr.execute(query,var)
        if not query.startswith('SELECT'):
            ouconn.commit()
        if query.startswith('SELECT') or 'RETURNING' in query:
            return oucsr.fetchall()
        else:
            return
    except psycopg2.Error as ex:
        oucsr.execute('ABORT')
        raise ex

def main():
    brand='TP-Link'
    source='www.tp-link.com/en'
    startInRowIdx=int(sys.argv[1]) if len(sys.argv)>1 else 0
    
    with sqlite3.connect('tplink.sqlite3') as inconn:
        incsr = inconn.cursor()
        global ouconn
        ouconn= psycopg2.connect(GridIotConnStr)
        inRows = incsr.execute(
            "SELECT model, revision, fw_desc, file_size,fw_ver,fw_date,"
            "file_sha1, file_url, file_name, page_url FROM TFiles "
            " ORDER BY id LIMIT -1 OFFSET %d"%startInRowIdx)
        for inRowIdx, inRow in enumerate(inRows,startInRowIdx):
            model,rev,fwDesc,fileSize,fwVer,fwDate,fileSha1,\
                    fileUrl,fileName,pageUrl= inRow
            uprint('inRowIdx=%s, model="%s","%s", "%s","%s"'%(
                inRowIdx, model,rev,fileName,fwVer))

            # UPSERT new Device
            devId=ousql(
                "UPDATE TDevice SET source=%(source)s "
                "WHERE brand=%(brand)s AND model=%(model)s AND"
                " revision=%(rev)s RETURNING id" ,locals())
            if devId:
                devId=devId[0][0]
            else:
                devId=ousql(
                    "INSERT INTO TDevice (brand,model,revision,source"
                    ") VALUES (%(brand)s,%(model)s,%(rev)s, "
                    "%(source)s) RETURNING id",
                    locals())
                devId=devId[0][0]
            uprint("UPSERT brand='%(brand)s', model=%(model)s"
                ",source=%(source)s RETURNING devId=%(devId)s"%locals())

            # UPSERT new Firmware
            # if fwVer is None:
            #    fwVer=''
            fwId=ousql(
                "UPDATE TFirmware SET file_sha1=%(fileSha1)s,"
                "include_prev=false,file_size=%(fileSize)s,"
                "release_date=%(fwDate)s, file_url=%(fileUrl)s,"
                "desc_url=%(pageUrl)s, description=%(fwDesc)s,"
                "file_path=%(fileName)s WHERE"
                "  device_id=%(devId)s AND version=%(fwVer)s AND"
                "  exclude_self=false RETURNING id",locals())
            if fwId:
                fwId=fwId[0][0]
            else:
                fwId=ousql(
                    "INSERT INTO TFirmware("
                    "device_id, version, exclude_self, "
                    "  file_sha1, file_size, release_date, "
                    "  file_url, description, desc_url, file_path) "
                    "VALUES ( %(devId)s, %(fwVer)s, false, "
                    " %(fileSha1)s, %(fileSize)s, %(fwDate)s,"
                    " %(fileUrl)s, %(fwDesc)s, %(pageUrl)s, %(fileName)s"
                    ") RETURNING id", locals())
                fwId=fwId[0][0]
            uprint("UPSERT TFirmware devId='%(devId)d', fwVer='%(fwVer)s',"
                " sha1='%(fileSha1)s', fwId=%(fwId)d"%locals())


if __name__=='__main__':
    main()
