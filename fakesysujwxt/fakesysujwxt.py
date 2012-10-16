#!/usr/bin/env python
# -*- coding: utf-8 -*-

import urllib
import pycurl
import re
import StringIO

__version__ = '0.1'

def retrive_data(url, cookie, request_json):
    ch = pycurl.Curl()
    ch.setopt(pycurl.URL, url)
    ch.setopt(pycurl.TIMEOUT, 20)
    ch.setopt(pycurl.POST, True)
    ch.setopt(pycurl.POSTFIELDS, request_json)
    ret = StringIO.StringIO()
    ch.setopt(pycurl.WRITEFUNCTION, ret.write)
    ch.setopt(pycurl.HTTPHEADER, ['Content-Type: multipart/form-data', 'render: unieap'])
    ch.setopt(pycurl.COOKIE, "JSESSIONID="+cookie)

    try:
        ch.perform()
    except pycurl.error, e:
        print "LoginError: ", e[0], e[1]
        return (False, 'timeout')

    ret_code = ch.getinfo(pycurl.HTTP_CODE)
    ret_body = ret.getvalue() 
    ch.close()
    if (ret_body.startswith('THE-NODE-OF-SESSION-TIMEOUT', 5)):
        return (False, 'expired')
    else:
        return (True, ret_body)

def login(username, passward):
    print 'Login:', username, passward
    url = 'http://uems.sysu.edu.cn/jwxt/j_unieap_security_check.do'
    ch = pycurl.Curl()
    ch.setopt(pycurl.URL, url)
    ch.setopt(pycurl.TIMEOUT, 15)
    ch.setopt(pycurl.POST, True)
    data = urllib.urlencode({'j_username': username, 'j_password': passward})
    ch.setopt(pycurl.POSTFIELDS, data)
    ret = StringIO.StringIO()
    ch.setopt(pycurl.WRITEFUNCTION, ret.write)
    ch.setopt(pycurl.HEADER, True) # add header to ret value

    try:
        ch.perform()
    except pycurl.error, e:
        print "LoginError: ", e[0], e[1]
        return (False, 'timeout')

    ret_code = ch.getinfo(pycurl.HTTP_CODE)
    ch.close()
    if ret_code == 200:
        return (False, 'errorpass')
    else:
        ret_header = ret.getvalue() 
        cookies = re.findall(r'^Set-Cookie: (.*);', ret_header, re.MULTILINE)
        cookie = cookies[0][11:]
        return (True, cookie)

# get score
def get_score(cookie, sno, year, term):
    print "Getting Score: ", sno, year, term, cookie
    url = 'http://uems.sysu.edu.cn/jwxt/xscjcxAction/xscjcxAction.action?method=getKccjList'
    query_json = """
    {
        body: {
            dataStores: {
                kccjStore: {
                    rowSet: {
                        "primary": [],
                        "filter": [],
                        "delete": []
                    },
                    name: "kccjStore",
                    pageNumber: 1,
                    pageSize: 100,
                    rowSetName: "pojo_com.neusoft.education.sysu.xscj.xscjcx.model.KccjModel",
                    order: "kclb asc"
                }
            },
            parameters: {
                "kccjStore-params": [
                    {
                        "name": "Filter_t.pylbm_0.1950409999148804",
                        "type": "String",
                        "value": "'01'",
                        "condition": " = ",
                        "property": "t.pylbm"
                    },
                    {
                        "name": "Filter_t.xn_0.3563793106347481",
                        "type": "String",
                        "value": "'%s'",
                        "condition": " = ",
                        "property": "t.xn"
                    },
                    {
                        "name": "Filter_t.xq_0.7983325881237213",
                        "type": "String",
                        "value": "'%s'",
                        "condition": " = ",
                        "property": "t.xq"
                    },
                    {
                        "name": "xh",
                        "type": "String",
                        "value": "'%s'",
                        "condition": " = ",
                        "property": "t.xh"
                    }
                ],
                "args": [
                    "student"
                ]
            }
        }
    }
    """ %(year, term, sno)
    return retrive_data(url, cookie, query_json)

def get_course_schedule(cookie, year, term):
    print "Getting course schedule: ", year, term, cookie
    url = 'http://uems.sysu.edu.cn/jwxt/sysu/xk/xskbcx/xskbcx.jsp'
    ch = pycurl.Curl()
    ch.setopt(pycurl.URL, url+'?'+urllib.urlencode({'xnd':year, 'xq':term}))
    ret = StringIO.StringIO()
    ch.setopt(pycurl.WRITEFUNCTION, ret.write)
    ch.setopt(pycurl.COOKIE, "JSESSIONID="+cookie)

    try:
        ch.perform()
    except pycurl.error, e:
        print "LoginError: ", e[0], e[1]
        return (False, 'timeout')

    ret_code = ch.getinfo(pycurl.HTTP_CODE)
    ret_body = ret.getvalue() 
    ch.close()

    if (ret_body.startswith('THE-NODE-OF-SESSION-TIMEOUT', 5)):
        return (False, 'expired')
    else:
        # add course time to schedule table
        pat = r'^var jcshowdata.*$'
        sub = """var jcshowdata=["","第一节<br>08:00-08:45","第二节<br>08:55-09:40","第三节<br>09:50-10:35","第四节<br>10:45-11:30","第五节<br>11:40-12:25","第六节<br>12:35-13:20","第七节<br>13:30-14:15","第八节<br>14:25-15:10","第九节<br>15:20-16:05","第十节<br>16:15-17:00","第十一节<br>17:10-17:55","第十二节<br>18:05-18:50","第十三节<br>19:00-19:45","第十四节<br>19:55-20:40","第十五节<br>20:50-21:35"];\r"""
        html = re.sub(pat, sub, ret_body, flags=re.M)
        return (True, html)

def get_info(cookie):
    """
    获取[学号], [年级], [教学号]
    """
    print "Getting info:", cookie
    url = 'http://uems.sysu.edu.cn/jwxt/xscjcxAction/xscjcxAction.action?method=judgeStu'
    query_json = """
    {
        header: {
            "code": -100,
            "message": {
                "title": "",
                "detail": ""
            }
        },
        body: {
            dataStores: {
                tempStore: {
                    rowSet: {
                        "primary": [],
                        "filter": [],
                        "delete": []
                    },
                    name: "tempStore",
                    pageNumber: 1,
                    pageSize: 2147483647,
                    recordCount: 0,
                    rowSetName: "pojo_com.neusoft.education.sysu.xy.xyjy.model.OnecolumModel"
                }
            },
            parameters: {
                "args": [],
                "responseParam": "result"
            }
        }
    }
    """
    return retrive_data(url, cookie, query_json)

def get_overall_credit(cookie, grade, tno):
    """
    获取总学分
    """
    url = 'http://uems.sysu.edu.cn/jwxt/xscjcxAction/xscjcxAction.action?method=getZyxf'
    query_json = """
    {
        header: {
            "code": -100,
            "message": {
                "title": "",
                "detail": ""
            }
        },
        body: {
            dataStores: {
                zxzyxfStore: {
                    rowSet: {
                        "primary": [],
                        "filter": [],
                        "delete": []
                    },
                    name: "zxzyxfStore",
                    pageNumber: 1,
                    pageSize: 2147483647,
                    recordCount: 0,
                    rowSetName: "pojo_com.neusoft.education.sysu.djks.ksgl.model.TwoColumnModel"
                }
            },
            parameters: {
                "zxzyxfStore-params": [
                    {
                        "name": "pylbm",
                        "type": "String",
                        "value": "'01'",
                        "condition": " = ",
                        "property": "x.pylbm"
                    },
                    {
                        "name": "nj",
                        "type": "String",
                        "value": "'%s'",
                        "condition": " = ",
                        "property": "x.nj"
                    },
                    {
                        "name": "zyh",
                        "type": "String",
                        "value": "'%s'",
                        "condition": " = ",
                        "property": "x.zyh"
                    }
                ],
                "args": []
            }
        }
    }
    """ %(grade, tno)
    return retrive_data(url, cookie, query_json)

def get_obtained_credit(cookie, sno):
    """
    获取已取得的学分
    """
    url = 'http://uems.sysu.edu.cn//jwxt/xscjcxAction/xscjcxAction.action?method=getAllXf'
    query_json = """
    {
        header: {
            "code": -100,
            "message": {
                "title": "",
                "detail": ""
            }
        },
        body: {
            dataStores: {
                allJdStore: {
                    rowSet: {
                        "primary": [],
                        "filter": [],
                        "delete": []
                    },
                    name: "allJdStore",
                    pageNumber: 1,
                    pageSize: 2147483647,
                    recordCount: 0,
                    rowSetName: "pojo_com.neusoft.education.sysu.djks.ksgl.model.TwoColumnModel"
                }
            },
            parameters: {
                "args": ["%s", "", "", ""]
            }
        }
    }
    """ %(sno)
    return retrive_data(url, cookie, query_json)

def get_gpa(cookie, sno):
    """
    获取已取得的总基点: 专必 公必 公选 专选
    """
    url = 'http://uems.sysu.edu.cn/jwxt/xscjcxAction/xscjcxAction.action?method=getAllJd'
    query_json = """
    {
        header: {
            "code": -100,
            "message": {
                "title": "",
                "detail": ""
            }
        },
        body: {
            dataStores: {
                allJdStore: {
                    rowSet: {
                        "primary": [],
                        "filter": [],
                        "delete": []
                    },
                    name: "allJdStore",
                    pageNumber: 1,
                    pageSize: 2147483647,
                    recordCount: 0,
                    rowSetName: "pojo_com.neusoft.education.sysu.djks.ksgl.model.TwoColumnModel"
                }
            },
            parameters: {
                "args": ["%s", "", "", ""]
            }
        }
    }
    """ %(sno)
    return retrive_data(url, cookie, query_json)

def get_selecting_course(cookie, year, term, course_type, campus):
    print "Getting selecting course: ", year, term, course_type, cookie
    url = 'http://uems.sysu.edu.cn/jwxt/xsxk/xsxk.action?method=getJxbxxFunc'
    if course_type == '30':
        campus_para = """
        {
            "name": "curxiaoqu",
            "type": "String",
            "value": "'%s'",
            "condition": " = ",
            "property": "A.SKJSSZXQ"
        }
        """ %(campus)
    else: 
        campus_para = ""

    query_json = """
    {
        header: {
            "code": -100,
            "message": {
                "title": "",
                "detail": ""
            }
        },
        body: {
            dataStores: {
                table1kxkcStore: {
                    rowSet: {
                        "primary": [],
                        "filter": [],
                        "delete": []
                    },
                    name: "table1kxkcStore",
                    pageNumber: 1,
                    pageSize: 280,
                    recordCount: 9,
                    rowSetName: "pojo_com.neusoft.education.sysu.xk.zxxkgg.model.KkblbModel"
                }
            },
            parameters: {
                "table1kxkcStore-params": [""" + campus_para +"""],
                "args": [
                    "%s",
                    "%s",
                    "%s"
                ]
            }
        }
    }
    """ %(year, term, course_type)
    return retrive_data(url, cookie, query_json)

def get_course_result(cookie, year, term):
    print "Getting course result: ", year, term, cookie
    url = 'http://uems.sysu.edu.cn/jwxt/xstk/xstk.action?method=getXkxkjglistByxh'
    query_json = """
    {
        header: {
            "code": -100,
            "message": {
                "title": "",
                "detail": ""
            }
        },
        body: {
            dataStores: {
                xsxkjgStore: {
                    rowSet: {
                        "primary": [],
                        "filter": [],
                        "delete": []
                    },
                    name: "xsxkjgStore",
                    pageNumber: 1,
                    pageSize: 100,
                    recordCount: 0,
                    rowSetName: "pojo_com.neusoft.education.sysu.xk.drxsxkjg.entity.XkjgEntity",
                    order: "xnd desc,xq desc,kclbm asc"
                }
            },
            parameters: {
                "xsxkjgStore-params": [
                    {
                        "name": "xnd",
                        "type": "String",
                        "value": "'%s'",
                        "condition": " = ",
                        "property": "xnd"
                    },
                    {
                        "name": "xq",
                        "type": "String",
                        "value": "'%s'",
                        "condition": " = ",
                        "property": "xq"
                    }
                ],
                "args": []
            }
        }
    }
    """ %(year, term)
    return retrive_data(url, cookie, query_json)

def get_detailed_info(cookie):
    print "Getting detailed info:", cookie
    url = "http://uems.sysu.edu.cn/jwxt/WhzdAction/WhzdAction.action?method=getGrwhxxList"
    query_json = """
    {
        header: {
            "code": -100,
            "message": {
                "title": "",
                "detail": ""
            }
        },
        body: {
            dataStores: {
                xsxxStore: {
                    rowSet: {
                        "primary": [],
                        "filter": [],
                        "delete": []
                    },
                    name: "xsxxStore",
                    pageNumber: 1,
                    pageSize: 10,
                    recordCount: 0,
                    rowSetName: "pojo_com.neusoft.education.sysu.xj.grwh.model.Xsgrwhxx"
                }
            },
            parameters: {
                "args": [""]
            }
        }
    }
    """
    return retrive_data(url, cookie, query_json)

def reset_password(cookie, new_password):
    print "Resetting passward:", new_password, cookie
    url = 'http://uems.sysu.edu.cn/jwxt/GbmmAction/GbmmAction.action?method=gbmm'
    query_json = """
    {
        header: {
            "code": -100,
            "message": {
                "title": "",
                "detail": ""
            }
        },
        body: {
            dataStores: {
                
            },
            parameters: {
                "args": [
                    "%s"
                ],
                "responseParam": "rs"
            }
        }
    }
    """ %(new_password)
    return retrive_data(url, cookie, query_json)

def remove_course(cookie, id):
    print "Removing course: ", id, cookie
    url = 'http://uems.sysu.edu.cn/jwxt/xsxk/xsxk.action?method=delXsxkjgFuncChanged'
    query_json = """
    {
        header: {
            "code": -100,
            "message": {
                "title": "",
                "detail": ""
            }
        },
        body: {
            dataStores: {},
            parameters: {
                "args": ["%s"],
                "responseParam": "dataSave"
            }
        }
    }
    """ %(id)
    return retrive_data(url, cookie, query_json)

def select_course(cookie, id, year, term):
    print "Selecting course: ", id, cookie, year, term
    url = 'http://uems.sysu.edu.cn/jwxt/xsxk/xsxk.action?method=selectCoursesChanged'
    query_json = """
    {
        header: {
            "code": -100,
            "message": {
                "title": "",
                "detail": ""
            }
        },
        body: {
            dataStores: {},
            parameters: {
                "args": [
                    "%s",
                    "",
                    "",
                    "%s",
                    "%s",
                    "",
                    "",
                    "",
                    "",
                    "",
                    ""
                ],
                "responseParam": "dataSave"
            }
        }
    }
    """ %(id, year, term)
    return retrive_data(url, cookie, query_json)

# all following methods left for future usage
def get_aaa(cookie):
    url = 'http://uems.sysu.edu.cn/jwxt/xsxk/xsxk.action?method=getJxjhByxh'
    query_json = """
{header:{"code": -100, "message": {"title": "", "detail": ""}},body:{dataStores:{},parameters:{"args": [], "responseParam": "xfms"}}}
    """
    return retrive_data(url, cookie, query_json)

def get_bbb(cookie):
    url = 'http://uems.sysu.edu.cn/jwxt/xsxk/xsxk.action?method=getKclb'
    query_json = """
{header:{"code": -100, "message": {"title": "", "detail": ""}},body:{dataStores:{fkclbStore:{rowSet:{"primary":[],"filter":[],"delete":[]},name:"fkclbStore",pageNumber:1,pageSize:2147483647,recordCount:0,rowSetName:"pojo_com.neusoft.education.sysu.xk.zxxk.entity.KclbxxModel"}},parameters:{"args": ["2012-2013", "1", "02"]}}}
    """
    return retrive_data(url, cookie, query_json)

selected_course_url = 'http://uems.sysu.edu.cn/jwxt/xsxk/xsxk.action?method=getTab1YxkcByxndxqkclbmpylbmxh'
def get_selected_course(year, term, course_type, cookie):
    srt = '{header:{"code": -100, "message": {"title": "", "detail": ""}},body:{dataStores:{table1yxkcStore:{rowSet:{"primary":[],"filter":[],"delete":[]},name:"table1yxkcStore",pageNumber:1,pageSize:10,recordCount:0,rowSetName:"pojo_com.neusoft.education.sysu.xk.drxsxkjg.entity.XkjgAndSsjhModel"}},parameters:{"args": ["01", "'+course_type+'", "'+year+'", "'+term+'"]}}}'
    ch = pycurl.Curl()
    ch.setopt(pycurl.URL, selected_course_url)
    ch.setopt(pycurl.POST, True)
    ch.setopt(pycurl.POSTFIELDS, srt)
    ret = StringIO.StringIO()
    ch.setopt(pycurl.WRITEFUNCTION, ret.write)
    ch.setopt(pycurl.HTTPHEADER, ['Content-Type: multipart/form-data', 'render: unieap'])
    ch.setopt(pycurl.COOKIE, "JSESSIONID="+cookie)
    ch.perform()
    ret_code = ch.getinfo(pycurl.HTTP_CODE)
    ret_body = ret.getvalue() 
    ch.close()
    return ret_body
