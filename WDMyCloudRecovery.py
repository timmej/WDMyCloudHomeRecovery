#!/usr/bin/python3
from os.path import join as joinpath
import os
import os.path
import sqlite3
import shutil
import argparse

class MyCloudFile:
    def __init__(self,id,parentID,contentID,fileName,mimeType):
        self.id = id
        self.parentID = parentID
        self.contentID = contentID
        self.fileName = fileName
        self.mimeType = mimeType
        
    def get_myclouddrive_file_path(self, source_root):
        return joinpath(source_root, 'restsdk', 'data', 'files', self.contentID[0], self.contentID)

class MyCloudDriveDB:
    def __init__(self,dbfile):
        self.dbfile = dbfile
        if (not os.path.exists(dbfile)):
            raise Exception(f"Unable to find index.db at: {dbfile}")
    
        self.connection = sqlite3.connect(dbfile)
        self.cursor = self.connection.cursor()

    def get_db_file_list(self):
        all_files = self.cursor.execute("SELECT id,parentID,contentID,name,mimeType FROM Files WHERE mimeType != 'application/x.wd.dir'").fetchall()
        return [MyCloudFile(file[0],file[1],file[2],file[3],file[4]) for file in all_files]

    def get_restored_file_path(self, parentID):
        parent = MyCloudFile(*self.cursor.execute("SELECT id,parentID,contentID,name,mimeType FROM Files WHERE id = ?", (parentID,)).fetchone())
        if (parent.parentID is None):
            return ''

        return joinpath((self.get_restored_file_path(parent.parentID)), parent.fileName)

    def close(self):
        self.cursor.close()
        self.connection.close()

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Copy WD My Cloud Home data over a direct (SATA) connection from Linux. Requires disassembly of MyCloudHome enclosure.')
    parser.add_argument('mycloudhome_root', help='The root of the WD My Cloud Home drive.')
    parser.add_argument('destination', help='The target directory to which files are copied.')
    args = parser.parse_args()

    db_location = joinpath(args.mycloudhome_root,'restsdk/data/db/index.db')
    drive_db_connection = MyCloudDriveDB(dbfile=db_location)

    all_files = drive_db_connection.get_db_file_list()

    for file in all_files:
        source_file = file.get_myclouddrive_file_path(args.mycloudhome_root)
        dest_file = joinpath(args.destination, drive_db_connection.get_restored_file_path(file.id))
        
        dest_directory = (os.path.split(dest_file))[0]
        os.makedirs(dest_directory, exist_ok=True)

        print(f"Copying {source_file} to {dest_file}")
        shutil.copy2(source_file, dest_file)
        
    drive_db_connection.close()