# -*- coding: utf-8 -*-
import json
import os
import mysql.connector
from dotenv import load_dotenv

load_dotenv()
databaseUsername=os.getenv("databaseUsername")
databasePassword=os.getenv("databasePassword")
pwdPath=os.path.dirname(os.path.abspath(__file__))
dataPath=os.path.join(pwdPath,"taipei-attractions.json")

with open(dataPath, 'r', encoding='utf-8') as f:
    data=json.load(f)

mysql_pool=mysql.connector.pooling.MySQLConnectionPool(
            pool_name="mypool", pool_size=5, 
     database="taipei_attractions",
            host="localhost",user=databaseUsername, password=databasePassword,
            pool_reset_session=True)

try:
    conn = mysql_pool.get_connection() #get connection from connect pool
    cursor = conn.cursor()
except Exception as e:
    print(e)

# #For category table
for idx in range(0,len(data["result"]["results"])):
    dataName=data["result"]["results"][idx]["CAT"]
    dataName="".join(dataName.split())
    sql="select id from category where name=%s"
    cursor.execute(sql,[dataName])
    result = cursor.fetchall()
    if len(result)==0:
        sql ="INSERT INTO category(name)VALUES (%s)"
        cursor.execute(sql, [dataName])
        conn.commit()
#For mrt table
for idx in range(0,len(data["result"]["results"])):
    dataName=data["result"]["results"][idx]["MRT"]
    if dataName:
        sql="select id from mrt where name=%s"
        cursor.execute(sql,[dataName])
        result = cursor.fetchall()
        if len(result)==0:
            sql ="INSERT INTO mrt(name)VALUES (%s)"
            cursor.execute(sql, [dataName])
            conn.commit()

#For attraction table
for idx in range(0,len(data["result"]["results"])):
    dataId=data["result"]["results"][idx]["_id"]
    dataName=data["result"]["results"][idx]["name"]
    dataDescription=data["result"]["results"][idx]["description"]
    dataAddress=data["result"]["results"][idx]["address"]
    dataTransport=data["result"]["results"][idx]["direction"]
    dataLatitude=data["result"]["results"][idx]["latitude"]  
    dataLongitude=data["result"]["results"][idx]["longitude"]
    dataCategory=data["result"]["results"][idx]["CAT"]
    dataCategory="".join(dataCategory.split())
    dataMrt=data["result"]["results"][idx]["MRT"]
    
    #category_id
    sql='select id from category where name=%s'
    cursor.execute(sql,[dataCategory])
    categoryId = cursor.fetchone()
    #mrt_id
    sql='select id from mrt where name=%s'
    cursor.execute(sql,[dataMrt])
    mrtId = cursor.fetchone()
    if mrtId:
        mrtId=mrtId[0]
 
    
    sql ="INSERT INTO attraction(id,name,description,address,transport,latitude,longitude,category_id,mrt_id)VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)"
    val = (dataId,dataName,dataDescription,dataAddress,dataTransport,dataLatitude,dataLongitude,categoryId[0],mrtId)
    cursor.execute(sql, val)
    conn.commit()

#For image table
for idx in range(0,len(data["result"]["results"])):
    dataName=data["result"]["results"][idx]["file"]
    dataId=data["result"]["results"][idx]["_id"]
    dataNames=dataName.split("https://")
    for item in dataNames:
        if item and ( "jpg" in item.lower() or "png" in item.lower() ):
            imageUrl="https://"+item
            sql="select id from image where imageUrl=%s"
            cursor.execute(sql,[imageUrl])
            result = cursor.fetchall()
            if len(result)==0:
                sql ="INSERT INTO image(attraction_id,imageUrl)VALUES (%s,%s)"
                val = (dataId,imageUrl)
                cursor.execute(sql,val)
                conn.commit()

cursor.close()
conn.close()
