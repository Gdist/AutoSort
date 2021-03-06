#-*- coding: utf-8 -*-
#v4.0 20190710 重新整理函數、加入預覽圖下載合併
#v4.1 20190807 資料庫輸出、調整目錄結構
#v4.2 未完成 相同檔案去重(檢查檔案大小)

import os, requests, urllib, time, re
from bs4 import BeautifulSoup
#from fake_useragent import UserAgent
from user_agent import generate_user_agent
import config, search, sql

ua = generate_user_agent()
db_name = "%s\\%s" % (config.LogPath,config.LogName) if config.LogPath else config.LogName #SQL

class Log:
	def NPrint(text):
		os.chdir(mypath)
		print(text)
		with open("error.log","a", encoding = 'utf8') as data:
			data.write(str(text)+"\n")
	def Text(text):
		with open("error.log","a", encoding = 'utf8') as data:
			data.write(str(text)+"\n")
	def SaveList(key,Title):
		fname = ("@FileList.txt" if Title else "@CodeList.txt")
		new = (title if Title else code)

		os.chdir(mypath+"\\@~Sorted\\"+key)
		try: #讀取先前的清單
			with open(fname , "r", encoding = 'utf8') as clog: 
				SaveList = [l.strip() for l in clog ]
		except:
			SaveList = []
		if new not in SaveList :
			SaveList += [new]
		else:
			return
		if len(SaveList) != 0: #如果非空目錄的話
			with open(fname,"w", encoding = 'utf8') as sdata: #寫檔
				for i in sorted(SaveList):
					sdata.write(i+"\n")
def convert_bytes(num):
	for x in ['bytes', 'KB', 'MB', 'GB', 'TB']:
		if num < 1024.0:
			return "%3.1f %s" % (num, x)
		num /= 1024.0
def file_size(file_path):
	if os.path.isfile(file_path):
		file_info = os.stat(file_path)
		return convert_bytes(file_info.st_size)
def GetCode(filename):
	c = key.upper()+"-"
	if c in filename.upper():
		cpos = filename.upper().find(c)
	elif key.upper() in filename.upper():
		c = key.upper()
		cpos = filename.upper().find(c)
		filename = filename.upper().replace(c,c+"-")
		c = c+"-"
	else:
		return None
	for i in range(len(filename[cpos+len(c):])):
		if not filename[cpos+len(c)+i].isdigit():
			code = filename[cpos:cpos+len(c)+i]
			code = code.upper()
			break
	if len(code) == len(c) : #如果找不到番號(番號跟關鍵字長度一樣)
		return None
	return code

#要處理的番號清單
with open("keyword.txt" , "r", encoding = 'utf-8-sig') as keydata: 
	KeyList = [l.strip() for l in keydata if l[0]!="@"]
#KeyList = list(set(KeyList)) #番號去重
if not os.path.isdir(config.tempfolder): #如果不是資料夾
	os.mkdir(config.tempfolder)
'''with open("keyword2.txt" , "r", encoding = 'utf-8-sig') as keydata: #找不到資料庫的特殊番號 (!待新增)
	Key2List = [l.strip().split(",") for l in keydata ]
Key2Dic = {}
for i in Key2List:
	Key2Dic[i[0]]=i[1]'''

mypath = os.getcwd() #執行目錄
for lsdir in sorted(os.listdir(mypath)):
	if not os.path.isdir(mypath+"\\"+lsdir): #如果不是資料夾
		continue
	if lsdir[0]=="@" or lsdir == "__pycache__" or "新作" in lsdir or "合集" in lsdir: #略過根目錄下帶有@的資料夾 (個人化)
		continue
	if not os.path.isdir(mypath+"\\@~Sorted\\"):
		os.mkdir(mypath+"\\@~Sorted\\")
	for root, dirs, files in os.walk(mypath+"\\"+lsdir):
		print("\nPath : "+root)
		for i in files:
			if "padding_file" in i: #跳過冗贅檔案
				continue
			if not re.search(r'.+?\.(mkv|mp4|ts|wmv|avi|flv|rmvb|iso|mov|m2ts|ass|srt)', i.lower()) \
			and not re.match(r'.+?(_|-)?(s|screen|screenshot)\.(jpg|jpeg|png)', i.lower()):
			#and not re.match(r'.+?\.(jpg|jpeg|png)', i.lower()) : #跳過非影像檔和非截圖
				continue
			'''for key2 in Key2Dic.keys(): #對於無資料庫的番號進行處理 (!待新增)
				key2 = key2'''
			for key in KeyList:
				dirpath = mypath
				code = GetCode(i) #從檔名找番號
				if key=="FC2"  and "FC2" in i.upper() and re.search(r'\d{6,7}',i): #特殊番號
					code = "FC2-" + re.search(r'\d{6,7}',i).group(0)
				if not code : #如果不能夠從檔案名稱找出番號
					continue
				if len(code[code.find("-")+1:]) >= 4: #例外處理：部分番號會用4.5位數字，但搜尋時必須為3位
					code = code.replace("-00","-") 
					code = code.replace("-0","-") 
				#if key[0].isdigit() or key =="SIRO" or key =="KIRAY":
					#continue
				print("Code :",code)

				query = sql.query(db_name,'JAV',code) #查詢舊有資料
				if query == None: #若不存在舊有資料→到網路查詢
					if not os.path.isdir(mypath+"\\@~Sorted\\"+key):
						os.mkdir(mypath+"\\@~Sorted\\"+key)
					#result = search.Database1(key,code,mypath)
					if key == "T28": #特殊番號例外處理
						result = search.Database3(key,code.replace("T28-","T-28"),mypath)
						if result['success']:
							result['code'] = result['code'].replace("T-28","T28-")
							result['save'][0] = result['save'][0].replace("T-28","T28-")
					elif key[0].isdigit() or key =="SIRO" or key =="KIRAY":
						result = search.Database2(key,code,mypath)
					elif key=="FC2" and "FC2" in i.upper():
						result = search.Database3(key,code,mypath)
						time.sleep(2)
					else:
						result = search.Database1(key,code,mypath)
					if not result['success']: #如果不存在對應的資料
						print("*Error :",result['error'])
						result = search.Database1(key,code,mypath) if key[0].isdigit() or key =="SIRO" or key =="KIRAY" else search.Database2(key,code,mypath) #調換
						if not result['success']:
							if key not in ["FC2","T28"]:
								result = search.Database3(key,code,mypath)
								if not result['success']:
									print("*Error :",result['error'])
									continue
							else:
								print("*Error :",result['error'])
								continue

					save = result['save']
					sql.input(db_name,'JAV', save)
					dirpath = result['dirpath']
				else:
					if key=="FC2":
						dirpath = mypath+"\\@~Sorted\\@"+key+"\\"+query[7]+"\\"+code
					else:
						number = int(code[code.find("-")+1:])
						order = "%03d~%03d" % (number-100+1,number) if number%100 == 0 else "%03d~%03d" % ((number//100)*100+1,(number//100+1)*100)
						dirpath = mypath+"\\@~Sorted\\"+key+"\\"+order+"\\"+code

				print("File : "+i)
				i2=i #檔案移動處理
				i2=i2.replace("_hhd000.com_免翻_墙免费访问全球最大情_色网站P_ornhub_可看收费内容","")
				i2=i2.replace("@hhd000.com_免翻#墙免费访问全球最大情#色网站P#ornhub,可看收费内容","")

				if not os.path.isfile(dirpath+"\\"+i2): #若檔案不存在
					if not os.path.isdir(dirpath):
						os.makedirs(dirpath)
					try:
						os.rename(root+"\\"+i,dirpath+"\\"+i2)
						print("Move : "+dirpath)
					except FileNotFoundError as e:
						print("*Error : FileNotFound "+i)
						continue
					except PermissionError as e:
						print("*Error : PermissionError "+i)
						continue
				else: #若檔案存在
					file1 = root+"\\"+i
					file2 = dirpath+"\\"+i2
					if config.CheckFile and file_size(file1) == file_size(file2) : #若需要比對檔案，且存在的檔案相同
						os.remove(file1)
						print("*Error : Exist same file \n  *Remove : "+file1)
					else: #若存在的檔案不同
						for j in range(1,10):
							dotpos = i2.rfind(".")
							i3 = i2[:dotpos]+"~"+str(j)+i2[dotpos:]
							if config.CheckFile and file_size(file1) == file_size(dirpath+"\\"+i3) : #若需要比對檔案，且存在的檔案相同
								os.remove(file1)
								break
								print("*Error : Exist same file \n  *Remove : "+file1)
							if not os.path.isfile(dirpath+"\\"+i3):
								try:
									os.rename(root+"\\"+i,dirpath+"\\"+i3)
								except FileNotFoundError:
									print("*Error : FileNotFound "+file1)
									break
								print("*Exist : "+i+"\n *Rename : "+i3)
								print("Move : "+dirpath)
								break
				#sql.input(db_name,'JAV', save)
				break
input("\n整理完成，請按Enter離開")