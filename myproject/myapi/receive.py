import xml.etree.ElementTree as ET

def parse_xml(web_data):
    if len(web_data) == 0:
        return None
    xmlData = ET.fromstring(web_data)
    msg_type = xmlData.find('MsgType').text
    if msg_type == 'text':
        return TextMsg(xmlData)
    elif msg_type == 'image':
        return ImageMsg(xmlData)
    elif msg_type == 'event':
        print('-- msg_type = event --')
        return EventMsg(xmlData)
    else:
        print('-- msg_type other --')
        return OtherMsg(xmlData)

class Msg(object):
    def __init__(self, xmlData):
        self.ToUserName = xmlData.find('ToUserName').text
        self.FromUserName = xmlData.find('FromUserName').text
        self.CreateTime = xmlData.find('CreateTime').text
        self.MsgType = xmlData.find('MsgType').text
        self.MsgId = xmlData.find('MsgId').text

class TextMsg(Msg):
    def __init__(self, xmlData):
        Msg.__init__(self, xmlData)
        self.Content = xmlData.find('Content').text.encode('utf-8')

class Subscribe(object):
    def __init__(self, xmlData):
        self.ToUserName = xmlData.find('ToUserName').text
        self.FromUserName = xmlData.find('FromUserName').text
        self.CreateTime = xmlData.find('CreateTime').text
        self.MsgType = xmlData.find('MsgType').text
        self.Event = xmlData.find('Event').text

class EventMsg(Msg):
    def __init__(self, xmlData):
        Subscribe.__init__(self, xmlData)

class ImageMsg(Msg):
    def __init__(self, xmlData):
        Msg.__init__(self, xmlData)
        self.PicUrl = xmlData.find('PicUrl').text
        self.MediaId = xmlData.find('MediaId').text
 
class OtherMsg(Msg):
    def __init__(self, xmlData):
        self.ToUserName = xmlData.find('ToUserName').text
        self.FromUserName = xmlData.find('FromUserName').text
        self.MsgType = xmlData.find('MsgType').text



#http://mmbiz.qpic.cn/mmbiz_jpg/uT2R7nia0cunPIBiabRbSD4ujicyNpjC2vl8682YVXDxDQQHvwMVXFzvmdEOWRKJTGxQ879lxfwZTku2kdgyXvtWg/0

'''

method -- POST
in POST
Handle POST webData is:  
b'
<xml>
    <ToUserName>
        <![CDATA[gh_81e2d9938466]]>
    </ToUserName>\n
    <FromUserName>
        <![CDATA[oSsul5nSE1djiyNHEgMpCMQL1XpQ]]>
    </FromUserName>\n
    <CreateTime>
        1625132301
    </CreateTime>\n
    <MsgType>
        <![CDATA[voice]]>
    </MsgType>\n
    <MediaId>
        <![CDATA[Ve_PjD-CnL6SQoDkej_6mDvCzTJteAOMf7QTfs0l0pAwvJAssXEPikcXgY-BjZAb]]>
    </MediaId>\n
    <Format>
        <![CDATA[amr]]>
    </Format>\n
    <MsgId>
        6979890084468228096
    </MsgId>\n
    <Recognition>
        <![CDATA[\xe5\x93\x88\xe5\x96\xbd\xe5\x93\x88\xe5\x96\xbd\xe5\x93\x88\xe5\x96\xbd\xe5\x93\x88\xe5\x96\xbd\xe3\x80\x82]]>
    </Recognition>\n
</xml>'
-- recMsg --  None
'NoneType' object has no attribute 'MsgType'
[01/Jul/2021 17:38:22] "POST /wechat/oa?signature=4b67352bfb0f3c6a5d7b7f285cf77a183dd5047a&timestamp=1625132301&nonce=2046759987&openid=oSsul5nSE1djiyNHEgMpCMQL1XpQ HTTP/1.0" 200 4



method -- POST
in POST
Handle POST webData is:  
b'
<xml>
    <ToUserName>
        <![CDATA[gh_81e2d9938466]]>
    </ToUserName>\n
    <FromUserName>
        <![CDATA[oSsul5nSE1djiyNHEgMpCMQL1XpQ]]>
    </FromUserName>\n
    <CreateTime>
        1625132337
    </CreateTime>\n
    <MsgType>
        <![CDATA[video]]>
    </MsgType>\n
    <MediaId>
        <![CDATA[Ve_PjD-CnL6SQoDkej_6mHyk2fLnM9h419bXvZ1MvARUrBNRTqrb6FwfcgjHb1Fl]]>
    </MediaId>\n
    <ThumbMediaId>
        <![CDATA[Ve_PjD-CnL6SQoDkej_6mIAiuOB-qqPcTlJTllagj066BGevcmfOsFXXKNH2Qb5D]]>
    </ThumbMediaId>\n
    <MsgId>
        23266300788560571
    </MsgId>\n
</xml>'
-- recMsg --  None
'NoneType' object has no attribute 'MsgType'
[01/Jul/2021 17:38:59] "POST /wechat/oa?signature=f8c51d5d595f724c16b9b46b85591aa0694a9144&timestamp=1625132338&nonce=1277891585&openid=oSsul5nSE1djiyNHEgMpCMQL1XpQ HTTP/1.0" 200 4



method -- POST
in POST
Handle POST webData is:  
b'
<xml>
    <ToUserName>
        <![CDATA[gh_81e2d9938466]]>
    </ToUserName>\n
    <FromUserName>
        <![CDATA[oSsul5nSE1djiyNHEgMpCMQL1XpQ]]>
    </FromUserName>\n
    <CreateTime>
        1625132352
    </CreateTime>\n
    <MsgType>
        <![CDATA[image]]>
    </MsgType>\n
    <PicUrl>
        <![CDATA[http://mmbiz.qpic.cn/mmbiz_jpg/uT2R7nia0cunPIBiabRbSD4ujicyNpjC2vl8682YVXDxDQQHvwMVXFzvmdEOWRKJTGxQ879lxfwZTku2kdgyXvtWg/0]]>
    </PicUrl>\n
    <MsgId>
        23266299194148591
    </MsgId>\n
    <MediaId>
        <![CDATA[Ve_PjD-CnL6SQoDkej_6mHbGOsJvmH3WvFmOO4KYjura7SneeL9lwm1g-qzRRE45]]>
    </MediaId>\n
</xml>'
-- recMsg --  None
'NoneType' object has no attribute 'MsgType'

'''

