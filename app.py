import mysql.connector
import os
from dotenv import load_dotenv
from flask import Flask,render_template,jsonify,make_response,request,json
import jwt
import time
from flask_cors import CORS
from flask import redirect
import requests

app=Flask(
			__name__,
			static_folder="static",
			static_url_path="/"
		)
CORS(app)
app.config["JSON_AS_ASCII"]=False
app.config["TEMPLATES_AUTO_RELOAD"]=True

load_dotenv()
databaseUsername=os.getenv("databaseUsername")
databasePassword=os.getenv("databasePassword")
key=os.getenv("key")

mysql_pool=mysql.connector.pooling.MySQLConnectionPool(
            pool_name="mypool", pool_size=15, 
            host="localhost", database="taipei_attractions",
            user=databaseUsername, password=databasePassword,
            pool_reset_session=True)

# Pages
@app.route("/")
def index():
	return render_template("index.html")
@app.route("/attraction/<id>")
def attraction(id):
	return render_template("attraction.html")
@app.route("/booking")
def booking():
	return render_template("booking.html")
@app.route("/thankyou")
def thankyou():
	return render_template("thankyou.html")
@app.route("/api/orders/<orderNumber>",methods=["GET"])
def getOrderInfoByNumber(orderNumber):
	getToken=request.cookies.get("token")
	if(getToken):
		try:
			conn = mysql_pool.get_connection() #get connection from connect pool
			cursor = conn.cursor(buffered=True)
			sql='select json_object("id",attraction.id,"name",attraction.name,"address",attraction.address,"image",image.imageUrl),orderinfo.date,orderinfo.time,orderinfo.price,orderinfo.paymentStatus,orderinfo.memberId from orderinfo inner join attraction inner join image on attraction.id=image.attraction_id and attraction.id = orderinfo.attractionId where orderinfo.orderId=%s'
			cursor.execute(sql,[orderNumber])
			attractionInfo = cursor.fetchone()

			sql='select json_object("name",member.username,"email",member.email,"phone",orderinfo.member_phone) from orderinfo inner join member on orderinfo.memberId=member.id where orderinfo.orderId=%s'
			cursor.execute(sql,[orderNumber])
			getMemberInfo = cursor.fetchone()
			if attractionInfo and getMemberInfo:
				if attractionInfo[4]=="paid":
					statusRecord=0
				else:
					statusRecord=1
				responseData={
					"number":orderNumber,
					"price":attractionInfo[3],
					"trip":{
						"attraction":attractionInfo[0],
						"date":attractionInfo[1],
						"time":attractionInfo[2]
					},
					"contact":getMemberInfo[0],
					"status":statusRecord
				}
				response = make_response(jsonify({"data":responseData} ),200 )  
			else:
				response = make_response(jsonify({"data":False} ),200 )
		except Exception as e:
			print(e)
			response = make_response(jsonify({"error":True,"message":"Can't connect to database."} ),500 )   
			response.headers["Content-Type"] = "application/json"
			return response
		finally: # must close cursor and conn!!
			cursor.close()
			conn.close()
	else:
		response = make_response(jsonify({"error":True,"message":"You didn't login. Please login for this service."}),403 )   
	response.headers["Content-Type"] = "application/json"
	return response
@app.route("/api/orders",methods=["POST"])
def creatOrder():
	getToken=request.cookies.get("token")
	if(getToken):
		try:
			payload=jwt.decode(getToken,key,algorithms='HS256')
		except jwt.ExpiredSignatureError as e:
			response = make_response(jsonify({"error":True,"message":e}),403 )   
			response.headers["Content-Type"] = "application/json"
			return response

		orderInfo = request.get_data().decode("utf-8") 
		orderInfo=json.loads(orderInfo)
		orderId=round(time.time())
		#Add order to database
		try:
			conn = mysql_pool.get_connection() #get connection from connect pool
			cursor = conn.cursor()
			sql ="INSERT INTO orderinfo(orderId,paymentStatus,memberId,attractionId,date,time,price,member_phone)VALUES (%s, %s, %s, %s, %s, %s, %s,%s)"
			val=(orderId,"unpaid",payload["id"],orderInfo["order"]["trip"]["attraction"]["id"],orderInfo["order"]["trip"]["date"],orderInfo["order"]["trip"]["time"],orderInfo["order"]["price"],orderInfo["order"]["contact"]["phone"])
			cursor.execute(sql,val)	
			count = cursor.rowcount 
			conn.commit()		
		except Exception as e:
			print(e)
			response = make_response(jsonify({"error":True,"message":"Can't connect to database."} ),500 )   
			response.headers["Content-Type"] = "application/json"
			return response
		finally: # must close cursor and conn!!
			cursor.close()
			conn.close()	

		if(count==1):
			#Sent request to TapPay server#
			partnerKey=os.getenv("partnerKey")
			merchantId=os.getenv("merchantId")
			TapPayUrl="https://sandbox.tappaysdk.com/tpc/payment/pay-by-prime"
			# 測試環境 URL: https://sandbox.tappaysdk.com/tpc/payment/pay-by-prime
			# 正式環境 URL: https://prod.tappaysdk.com/tpc/payment/pay-by-prime
			headers={ 
				"Content-Type": "application/json",
				"x-api-key": partnerKey
			} 
			paymentInfo={
				"bank_transaction_id":round(time.time()),
				"order_number":orderId,
				"prime": orderInfo["prime"],
				"partner_key": partnerKey,
				"merchant_id": merchantId,
				"details":"TapPay Test",
				"amount": orderInfo["order"]["price"],
				"currency": "TWD",
				"details":"TapPay Test",		
				"cardholder": {
					"phone_number":orderInfo["order"]["contact"]["phone"],
					"name": orderInfo["order"]["contact"]["name"],
					"email": orderInfo["order"]["contact"]["email"],
					"zip_code": "",
					"address": "",
					"national_id": ""
					},
			}
			paymentResponse=requests.post(TapPayUrl,headers=headers,data=json.dumps(paymentInfo))
			responseFromTapPay=json.loads(paymentResponse.text) 
			#print(responseFromTapPay)
			if responseFromTapPay["status"]==0:
				print("Payment success!")
				responseData={"data":{"number":orderId,"payment":{"status": responseFromTapPay["status"],"message": "付款成功"}}}
				try:
					conn = mysql_pool.get_connection() #get connection from connect pool
					cursor = conn.cursor()
					sql="UPDATE orderinfo SET paymentStatus=%s WHERE orderId=%s"
					val=("paid",orderId)
					cursor.execute(sql,val)	
					conn.commit()	
					#Record this history
					sql ="INSERT INTO transactionhistory(order_number, status, msg, rec_trade_id, bank_transaction_id, transaction_time_millis, bank_result_code, bank_result_msg)VALUES (%s, %s, %s, %s, %s, %s, %s, %s)"
					val=(orderId,responseFromTapPay["status"],responseFromTapPay["msg"],responseFromTapPay["rec_trade_id"],responseFromTapPay["bank_transaction_id"],responseFromTapPay["transaction_time_millis"],responseFromTapPay["bank_result_code"],responseFromTapPay["bank_result_msg"])
					cursor.execute(sql,val)	
					conn.commit()		
					#Delete booking car		
					sql='DELETE FROM booking WHERE memberId=%s'
					cursor.execute(sql,[payload["id"]])
					conn.commit()			
				except Exception as e:
					print(e)
					response = make_response(jsonify({"error":True,"message":"Can't connect to database."} ),500 )   
					response.headers["Content-Type"] = "application/json"
					return response
			else:
				print("Payment failed!")
				responseData={"data":{"number":orderId,"payment":{"status":responseFromTapPay["status"] ,"message": "付款失敗"}}}
			cursor.close()
			conn.close()	
			response = make_response(jsonify(responseData),200 )   
			response.headers["Content-Type"] = "application/json"
			return response
		else:
			response = make_response(jsonify({"error":True,"message":"Can't store order to database."} ),400 )   
			response.headers["Content-Type"] = "application/json"
			return response
		
	else:
		response = make_response(jsonify({"error":True,"message":"You didn't login. Please login for this service."}),403 )   
		response.headers["Content-Type"] = "application/json"
		return response

@app.route("/api/booking",methods=["GET"])
def getBookingInfo():
	getToken=request.cookies.get("token")
	if(getToken):
		try:
			payload=jwt.decode(getToken,key,algorithms='HS256')
		except jwt.ExpiredSignatureError as e:
			response = make_response(jsonify({"error":True,"message":e}),403 )   
			response.headers["Content-Type"] = "application/json"
			return response
		try:
			conn = mysql_pool.get_connection() #get connection from connect pool
			cursor = conn.cursor()
			sql='select json_object("id",attraction.id,"name",attraction.name,"address",attraction.address,"image",image.imageUrl), booking.date, booking.time, booking.price from booking inner join attraction inner join image on attraction.id=image.attraction_id and attraction.id = booking.attractionId where booking.memberId=%s limit 1'
			cursor.execute(sql,[payload["id"]])
			attractionInfo = cursor.fetchone()
		except Exception as e:
			print(e)
			response = make_response(jsonify({"error":True,"message":"Can't connect to database."} ),500 )   
			response.headers["Content-Type"] = "application/json"
			return response
		finally: # must close cursor and conn!!
			cursor.close()
			conn.close()
		if attractionInfo:
			bookingAttraction=attractionInfo[0]
			bookingDate=attractionInfo[1]
			bookingTime=attractionInfo[2]
			bookingPrice=attractionInfo[3]
			response = make_response(jsonify({"data":{"attraction":bookingAttraction,
														"date": bookingDate,
														"time": bookingTime,
														"price": bookingPrice
													}
											}),200 
									)    
			response.headers["Content-Type"] = "application/json"
			return response
		else:
			response = make_response(jsonify({"data":None}),200 )   
			response.headers["Content-Type"] = "application/json"
			return response
	else:
		response = make_response(jsonify({"error":True,"message":"You didn't login. Please login for this service."}),403 )   
		response.headers["Content-Type"] = "application/json"
		return response
@app.route("/api/booking",methods=["POST"])
def creatBooking():
	getToken=request.cookies.get("token")
	if(getToken):
		try:
			payload=jwt.decode(getToken,key,algorithms='HS256')
		except jwt.ExpiredSignatureError as e:
			response = make_response(jsonify({"error":True,"message":e}),403 )   
			response.headers["Content-Type"] = "application/json"
			return response

		bookingInfo = request.get_data().decode("utf-8") 
		bookingInfo=json.loads(bookingInfo)

		#add booking info to database
		try:
			conn = mysql_pool.get_connection() #get connection from connect pool
			cursor = conn.cursor()
			sql='select memberId from booking where memberId=%s'
			cursor.execute(sql,[payload["id"]])
			checkDuplicate = cursor.fetchone()
			if checkDuplicate:
				#delete duplicate
				sql='DELETE FROM booking WHERE memberId=%s'
				cursor.execute(sql,[payload["id"]])
				conn.commit()	

			sql ="INSERT INTO booking(memberId,attractionId,date,time,price)VALUES (%s, %s, %s, %s, %s)"
			val=(payload["id"],bookingInfo["attractionId"],bookingInfo["date"],bookingInfo["time"],bookingInfo["price"])
			cursor.execute(sql, val)		
			count = cursor.rowcount 
			conn.commit()		
		except Exception as e:
			print(e)
			response = make_response(jsonify({"error":True,"message":"Can't connect to database."} ),500 )   
			response.headers["Content-Type"] = "application/json"
			return response
		finally: # must close cursor and conn!!
			cursor.close()
			conn.close()

		if(count==1):
			response = make_response(jsonify({"ok":True}),200 )   
			response.headers["Content-Type"] = "application/json"
			return response
		else:
			response = make_response(jsonify({"error":True,"message":"Can't store to database."} ),400 )   
			response.headers["Content-Type"] = "application/json"
			return response
	else:
		response = make_response(jsonify({"error":True,"message":"You didn't login. Please login for this service."}),403 )   
		response.headers["Content-Type"] = "application/json"
		return response

@app.route("/api/booking",methods=["DELETE"])
def deleteBooking():
	getToken=request.cookies.get("token")
	if(getToken):
		try:
			payload=jwt.decode(getToken,key,algorithms='HS256')
		except jwt.ExpiredSignatureError as e:
			response = make_response(jsonify({"error":True,"message":e}),403 )   
			response.headers["Content-Type"] = "application/json"
			return response
		try:
			conn = mysql_pool.get_connection() #get connection from connect pool
			cursor = conn.cursor()	
			sql='DELETE FROM booking WHERE memberId=%s'
			cursor.execute(sql,[payload["id"]])
			conn.commit()		
			count = cursor.rowcount 
			conn.commit()		
			#print(count)
		except Exception as e:
			print(e)
			response = make_response(jsonify({"error":True,"message":"Can't connect to database."} ),500 )   
			response.headers["Content-Type"] = "application/json"
			return response
		finally: # must close cursor and conn!!
			cursor.close()
			conn.close()
		response = make_response(jsonify({"ok":True}),200 )   
		response.headers["Content-Type"] = "application/json"
		return response
	else:
		response = make_response(jsonify({"error":True,"message":"You didn't login. Please login for this service."}),403 )   
		response.headers["Content-Type"] = "application/json"
		return response

@app.route("/api/user",methods=["POST"])
def registerAccount():
	registerInfo = request.get_data().decode("utf-8") 
	registerInfo=json.loads(registerInfo)
	if(registerInfo['name'] and registerInfo['password'] and registerInfo['email']):
		#check databases
		try:
			conn = mysql_pool.get_connection() #get connection from connect pool
			cursor = conn.cursor()
			sql = 'select id from member WHERE email=%s'
			cursor.execute(sql, [registerInfo['email']])
			checkEmail = cursor.fetchone() 
		except Exception as e:
			print(e)
			response = make_response(jsonify({"error":True,"message":"Can't connect to database."} ),500 )   
			response.headers["Content-Type"] = "application/json"
			return response
		finally:
			cursor.close()
			conn.close()
		if checkEmail:
			response = make_response(jsonify({"error":True,"message":"這個email已經註冊過囉!"} ),400 )   
			response.headers["Content-Type"] = "application/json"
			return response	
		else:
			#add member to database
			try:
				conn = mysql_pool.get_connection() #get connection from connect pool
				cursor = conn.cursor()
				sql ="INSERT INTO member(username,password,email)VALUES (%s, %s, %s)"
				cursor.execute(sql, (registerInfo['name'], registerInfo['password'],registerInfo['email']))		
				count = cursor.rowcount 
				conn.commit()		
			except Exception as e:
				print(e)
				response = make_response(jsonify({"error":True,"message":"Can't connect to database."} ),500 )   
				response.headers["Content-Type"] = "application/json"
				return response
			finally: # must close cursor and conn!!
				cursor.close()
				conn.close()	
			if(count==1):
					response = make_response(jsonify({"ok":True}),200 )   
					response.headers["Content-Type"] = "application/json"
					return response
			response = make_response(jsonify({"error":True,"message":"Can't store data to database."} ),500 )   
			response.headers["Content-Type"] = "application/json"
			return response
	else:
		response = make_response(jsonify({"error":True,"message":"Please input username, password and email."} ),400 )   
		response.headers["Content-Type"] = "application/json"
		return response


@app.route("/api/user/auth",methods=["GET"])
def getAccountInfo():
	getToken=request.cookies.get("token")
	if(getToken):
		try:
			payload=jwt.decode(getToken,key,algorithms='HS256')
		except jwt.ExpiredSignatureError as e:
			response = make_response(jsonify({"data":None} ),200 )   
			response.headers["Content-Type"] = "application/json"
			return response
		#get member information from database
		try:
			conn = mysql_pool.get_connection() #get connection from connect pool
			cursor = conn.cursor()
			sql='select json_object("id",id,"name",username,"email",email) from member where id=%s'
			cursor.execute(sql,[payload["id"]])
			getmemberData = cursor.fetchone()
		except Exception as e:
			print(e)
		finally:
			cursor.close()
			conn.close()
		response = make_response(jsonify({"data":getmemberData[0]} ),200 )   
		response.headers["Content-Type"] = "application/json"
		return response
	response = make_response(jsonify({"data":None} ),200 )   
	response.headers["Content-Type"] = "application/json"
	return response

@app.route("/api/user/auth",methods=["PUT"])
def loginAccount():
	loginInfo = request.get_data().decode("utf-8") 
	loginInfo=json.loads(loginInfo)
	#Get id from database
	try:
		conn = mysql_pool.get_connection() #get connection from connect pool
		cursor = conn.cursor()
		sql = 'select id from member WHERE email=%s and password=%s'
		val=(loginInfo['email'],loginInfo['password'])
		cursor.execute(sql,val)
		loginMember = cursor.fetchone() 
	except Exception as e:
		print(e)
		response = make_response(jsonify({"error":True,"message":"Can't connect to database."} ),500 )   
		response.headers["Content-Type"] = "application/json"
		return response
	finally:
		cursor.close()
		conn.close()

	if loginMember:		
		now = time.time()
		expiretime = 60 * 60
		payload = {
			"exp": now + expiretime,
			"id":loginMember[0],
		}
		encodedToken = jwt.encode(payload, key, algorithm='HS256')
		response = make_response(jsonify({"ok":True}),200 )   
		response.set_cookie('token',encodedToken, max_age=7*24*60*60) # 7天
		response.headers["Content-Type"] = "application/json"
		return response
	else:
		response = make_response(jsonify({"error":True,"message":"登入失敗，帳號或密碼錯誤"} ),400 )   
		response.headers["Content-Type"] = "application/json"
		return response

@app.route("/api/user/auth",methods=["DELETE"])
def logoutAccount():
	print("DELETE")
	response = make_response(jsonify({"ok":True}),200 )   
	response.set_cookie('token','', expires=0) 
	response.headers["Content-Type"] = "application/json"
	return response
	

@app.route("/api/attractions")
def getAttractions():
	try:
		pageParameter=int(request.args.get("page",0)) 
	except ValueError as ex:
		print(ex)
		response = make_response(jsonify({"error":True,"message":"The page parameter you provied is not a digit."} ),400 )   
		response.headers["Content-Type"] = "application/json"
		return response

	keywordParameter=request.args.get("keyword","")
	if pageParameter<0:
		pageParameter=0
	dataCountPerPage=12
	
	try:
		conn = mysql_pool.get_connection() #get connection from connect pool
		cursor = conn.cursor()
		startId=pageParameter*dataCountPerPage
		
		if keywordParameter:
			keywordParameter=keywordParameter.replace("\"","")
			#check category
			sql='select id from category where name=%s'
			cursor.execute(sql,[keywordParameter])
			resultCategoryId = cursor.fetchone()
			
			dataAll=[]
			nextPage=pageParameter+1
			if resultCategoryId:
				#get id, name, description, address, transport, latitude, longitude, mrt, category
				sql='select json_object("id",attraction.id,"name",attraction.name,"description",attraction.description,"address",attraction.address,"transport",attraction.transport,"lat",attraction.latitude,"lng",attraction.longitude,"category",category.name,"mrt",mrt.name) from attraction left JOIN category ON attraction.category_id=category.id left JOIN mrt ON attraction.mrt_id=mrt.id where category_id=%s limit %s,%s'
				val=(resultCategoryId[0],startId,dataCountPerPage)
				cursor.execute(sql,val)
				resultFromAttraction= cursor.fetchall()
			else:
				#check attraction name
				#get id, name, description, address, transport, latitude, longitude, mrt, category
				sql='select json_object("id",attraction.id,"name",attraction.name,"description",attraction.description,"address",attraction.address,"transport",attraction.transport,"lat",attraction.latitude,"lng",attraction.longitude,"category",category.name,"mrt",mrt.name) from attraction left JOIN category ON attraction.category_id=category.id left JOIN mrt ON attraction.mrt_id=mrt.id where attraction.name like %s limit %s,%s'
				val=("%"+keywordParameter+"%",startId,dataCountPerPage)
				cursor.execute(sql,val)
				resultFromAttraction= cursor.fetchall()
			resultQuery={}
			for idx in range(0,dataCountPerPage):
				resultQuery={}
				if idx>=len(resultFromAttraction):
					nextPage=None
					break		
				resultQuery.update(json.loads(resultFromAttraction[idx][0]))

				#get images
				sql='select imageUrl from image where attraction_id=%s'
				cursor.execute(sql,[resultQuery["id"]])
				resultImages = cursor.fetchall()
				getImages=[]
				for idx in range(0,len(resultImages)):
					getImages.append(resultImages[idx][0])
				resultQuery["images"]=getImages
				dataAll.append(resultQuery)	
		else:	
			nextPage=pageParameter+1
			#get id, name, description, address, transport, latitude, longitude, mrt, category
			sql='select json_object("id",attraction.id,"name",attraction.name,"description",attraction.description,"address",attraction.address,"transport",attraction.transport,"lat",attraction.latitude,"lng",attraction.longitude,"category",category.name,"mrt",mrt.name) from attraction left JOIN category ON attraction.category_id=category.id left JOIN mrt ON attraction.mrt_id=mrt.id limit %s,%s'
			val=(startId,dataCountPerPage)
			cursor.execute(sql,val)
			resultFromAttraction= cursor.fetchall()
			
			dataAll=[]
			for idx in range(0,dataCountPerPage):
				if idx>=len(resultFromAttraction):
					nextPage=None
					break
				result={}
				result.update(json.loads(resultFromAttraction[idx][0]))
				#get images
				sql='select imageUrl from image where attraction_id=%s'
				cursor.execute(sql,[result["id"]])
				resultImages = cursor.fetchall()
				getImages=[]
				for idx in range(0,len(resultImages)):
					getImages.append(resultImages[idx][0])
				result["images"]=getImages
				dataAll.append(result)
		if dataAll:
			response = make_response(jsonify({"nextPage":nextPage,"data":dataAll} ),200 ) 
		else:
			response = make_response(jsonify({"nextPage":None,"data":dataAll} ),200 ) 
	except Exception as e:
		print(e)
		response = make_response(jsonify({"error":True,"message":"Can't connect to database."} ),500 )   
	finally:
		cursor.close()
		conn.close()
		response.headers["Content-Type"] = "application/json"
		return response
		
@app.route("/api/attraction/<attractionId>")
def getAttractionByAttractionId(attractionId):
	
	try:
		conn = mysql_pool.get_connection() #get connection from connect pool
		cursor = conn.cursor()
		sql='select id from attraction where id=%s'
		cursor.execute(sql,[attractionId])
		checkAttractionIdValid = cursor.fetchone()
	except Exception as e:
		print(e)
		response = make_response(jsonify({"error":True,"message":"Can't connect to database."} ),500 )   
		response.headers["Content-Type"] = "application/json"
		cursor.close()
		conn.close()
		return response
	
	if checkAttractionIdValid:
		resultQuery={}
		#get id, name, description, address, transport, latitude, longitude, mrt, category
		sql='select json_object("id",attraction.id,"name",attraction.name,"description",attraction.description,"address",attraction.address,"transport",attraction.transport,"lat",attraction.latitude,"lng",attraction.longitude,"category",category.name,"mrt",mrt.name) from attraction left JOIN category ON attraction.category_id=category.id left JOIN mrt ON attraction.mrt_id=mrt.id where attraction.id=%s'
		cursor.execute(sql,[attractionId])
		resultFromAttraction= cursor.fetchone()
		resultQuery.update(json.loads(resultFromAttraction[0]))
		#get images
		sql='select imageUrl from image where attraction_id=%s'
		cursor.execute(sql,[attractionId])
		resultImages = cursor.fetchall()
		getImages=[]
		for idx in range(0,len(resultImages)):
			getImages.append(resultImages[idx][0])
		resultQuery["images"]=getImages		
		response = make_response(jsonify({"data":resultQuery}),200 )   
	else:
		response = make_response(jsonify({"error":True,"message":"This attractionId is invalid."} ),400 )   
	cursor.close()
	conn.close()
	response.headers["Content-Type"] = "application/json"
	return response
	

@app.route("/api/categories")
def getCategories():
	try:
		conn = mysql_pool.get_connection() #get connection from connect pool
		cursor = conn.cursor()
		sql="select name from category"
		cursor.execute(sql)
		result = cursor.fetchall()
	except Exception as e:
		print(e)
		response = make_response(jsonify({"error":True,"message":"Can't connect to database."} ),500 )   
		response.headers["Content-Type"] = "application/json"
		return response
	finally:
		cursor.close()
		conn.close()

	if result:
		categories=[]		
		for idx in range(0,len(result)):
			categories.append(result[idx][0])
		response = make_response(jsonify({"data":categories} ),200 )   
		response.headers["Content-Type"] = "application/json"
		return response
	else:
		response = make_response(jsonify({"data":None} ),200 )  
		response.headers["Content-Type"] = "application/json"
		return response
#app.run(ssl_context='adhoc')
app.run(host="0.0.0.0",port=3000)
