
import os, datetime

from DropboxWrap import DropboxTerm

# app key y secret de la pagina de desarolladores de dropbox
app_key = ''
app_secret = ''

#Datos para conectarnos a la base de datos
username = ""
password = ""
hostname = ""
database = ""

today = datetime.datetime.today()

#Le damos nombre a la base de datos
filename = database+"-"+today.strftime("%d-%b-%Y-%H:%M:%S.sql")
filename_gz = filename+".gz"

#instanciamos la clase 
d = DropboxTerm(app_key,app_secret)

#comprobamos si esta el usuario logeado o no
if d.is_logged() == False:
    d.login()

#ejecutamos el comando y comprimimos el resultado, para que sea más ligero el archivo
os.popen("mysqldump -u %s --password='%s' -h %s -e --opt -c %s | gzip -c > '%s'" % (username, password, hostname, database, filename_gz))
#os.popen("PGPASSWORD=\"%s\" pg_dump -U %s  -h %s  -d %s -n public | gzip -c > '%s'" % ( password, username, hostname, database, filename_gz))
#montamos el archivo resultante en el dropbox
print d.put(filename_gz,'/database/'+filename_gz)

#listo
