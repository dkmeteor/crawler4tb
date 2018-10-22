#encoding=utf-8
#抓取代码部分修改自 ref: https://github.com/wojiushimogui/get_tiebaContent
#计算贴吧活跃度
#活跃度定义: 指定日期开始至今天用户回复数总和
#日期在代码中直接指定,未提供配置
import urllib2
import urllib
import re
from urllib import quote
import sys
import time

reload(sys)
sys.setdefaultencoding('utf-8')
def replace(x):
	#去除img标签，7位长空格
	removeImg=re.compile('<img.*?>| {7}|')
	#去除超链接标签
	removeAddr=re.compile('<a.*?>|</a>')
	#把换行的标签换为\n
	replaceLine=re.compile('<tr>|<div>|</div>|</p>')
	#将表格制表<td>替换为\t
	replaceTD=re.compile('<td>')
	#把段落开头换为\n加空两格
	replacePara=re.compile('<p.*?>')
	#将换行符或双换行符替换为\n
	replaceBR=re.compile('<br><br>|<br>')
	#将其余标签删除
	removeExtraTag=re.compile('<.*?>')
	x=re.sub(removeImg,"",x)
	x=re.sub(removeAddr,"",x)
	x=re.sub(replaceLine,"\n",x)
	x=re.sub(replaceTD,"\t",x)
	x=re.sub(replacePara,"\n  ",x)
	x=re.sub(replaceBR,"\n",x)
	x=re.sub(removeExtraTag,"",x)
	return x.strip()

#定义一个类
def fetch(url):
	user_agent="Mozilla/5.0 (Windows NT 6.1)"
	headers={"User-Agent":user_agent}
	print url
	try:
		request=urllib2.Request(url,headers=headers)
		response=urllib2.urlopen(request,timeout=30)
		content=response.read().decode("utf-8")
		# print content  #测试输出
		content=content.replace("\n","")
		content=content.replace("\r","")
		return content
	except urllib2.URLError,e:
			if hasattr(e,"reason"):
				print e.reason
			print e
			return ''
	except BaseException,e:
		print e
		return fetch(url)
def getRegResult(content,reg):
		pattern=re.compile(reg,re.S)
		items=re.findall(pattern,content)
		result=[]
		for item in items:
			#去除标签
			text=replace(item)
			result.append(text)
		# print result
		return result
class BaiduTieBa:
	#初始化，传入地址
	def __init__(self):
		#全局的文件变量
		self.file=None
		self.newFileAccTitle()
	#根据传入的页码来获取该页的帖子列表
	def getPageContent(self,url,pageNum):
		url=url +"&pn="+str(pageNum*50)
		return fetch(url)
	
	#获取帖子回复数列表
	def getReplyCounts(self,content):
		return getRegResult(content,r'<span class="threadlist_rep_num center_text".*?</span>')
	#获取帖子创建时间
	def getPostCreatedTime(self,content):
		return getRegResult(content,r'<span class="pull-right is_show_create_time" .*?>.*?</span>')
	def getTotalPostCount(self,content):
		return getRegResult(content,r'<span class="card_infoNum".*?>.*?</span>')
	def getTotalFollowerCount(self,content):
		return getRegResult(content,r'<span class="card_menNum".*?>.*?</span>')
	#将内容写入文件中保存
	def writedata2File(self,result):
		self.file.write(result)
		self.file.flush()
	#根据获取网页帖子的标题来在目录下建立一个同名的.txt文件
	def newFileAccTitle(self):
		self.file=open("result.txt","w+")
	#写一个抓取贴吧的启动程序
	def getTiebaData(self,target):
		#先获取html代码
		pageIndex = 0
		isContinue = True
		totalReplyCount = 0
		postCount = 0
		totalPostCount = 0
		totalFollowerCount = 0
		target=target.replace('\n','')
		url="https://tieba.baidu.com/f?kw="+quote(target)+"&ie=utf-8"
		while isContinue :
			content=self.getPageContent(url,pageIndex)
			replys=self.getReplyCounts(content)
			# self.getTitles(content)
			dates=self.getPostCreatedTime(content)
			if totalPostCount==0:
				temp = self.getTotalPostCount(content)
				if len(temp) >0:
					totalPostCount = self.getTotalPostCount(content)[0].replace(',','')
			if totalFollowerCount==0:
				temp=self.getTotalFollowerCount(content)
				if len(temp) >0:
					totalFollowerCount = self.getTotalFollowerCount(content)[0].replace(',','')
			pageIndex=pageIndex+1
			#若本页所有帖子发帖时间大于7天,则不继续遍历后面的页面
			isContinue = False
			for i in range(len(dates)):
				#时间有3种格式 hh:MM mm:dd yyyy-mm,忽略yyyy-mm类型的数据,必定时间超过1年,以时分形式显示的数据,必定在7天之内
				if len(dates[i])==4 and dates[i]>'9-22' :
					isContinue=True 
				if dates[i]>'9-22' or dates[i].find(':')>0:
					totalReplyCount =  totalReplyCount+int(replys[i])
					postCount = postCount +1
			
		output = target.encode("utf-8")+','+str(totalFollowerCount)+","+str(totalPostCount)+","+str(postCount)+","+str(totalReplyCount)+'\n'
		print output
		self.writedata2File(output)
	def start(self):
		for line in open("names.txt"):
			self.getTiebaData(line)
def getAllTiebaCategories():
	content = fetch('http://tieba.baidu.com/f/index/forumclass')
	#<a rel="noopener" class="class-item-title" href="/f/index/forumpark?pcn=娱乐明星&amp;pci=0&amp;ct=1">娱乐明星</a>
	categories = getRegResult(content,r'<a rel="noopener" class="class-item-title" href=.*?">.*?</a>')
	return categories
#获取分类下page页的所有贴吧名称  page从1开始计数
def getCategoriesResult(categoryName,page):
	url = 'http://tieba.baidu.com/f/index/forumpark?cn=&st=new&ci=0&pcn='+quote(categoryName.encode('utf-8'))+'&pci=0&ct=1&pn='+str(page)
	print url
	content = fetch(url)
	#<p class="ba_name" style="user-select: auto;">张杰吧</p>
	names = getRegResult(content,r'<p class="ba_name".*?>.*?</p>')
	return names
#获取所有贴吧分类
def prepareAllTieBa():
	categories = getAllTiebaCategories()
	names = []

	fileNames=open("names.txt","w+")
	for item in categories:
		#获取该分类下 前10页贴吧名称 => 200个左右
		isContinue = True
		index = 1
		while isContinue:
			curPageTiebaNames = getCategoriesResult(item,index)
			print curPageTiebaNames
			names.append(curPageTiebaNames)
			index = index+1
			for itemName in curPageTiebaNames:
				fileNames.write(itemName.encode('utf-8')+'\n')
			if len(curPageTiebaNames)<19 or index>=10:
				isContinue = False

# prepareAllTieBa()
baidutieba=BaiduTieBa() #实例化一个对象
baidutieba.start()