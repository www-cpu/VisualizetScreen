import json
import requests
import pandas as pd
import numpy as np
import time
from datetime import datetime
from pyecharts.charts import *
from pyecharts import options as opts
from pyecharts.commons.utils import JsCode
from pyecharts.globals import ThemeType, ChartType
from pyecharts.charts import Gauge
from bs4 import BeautifulSoup

def catch_data(api_name):
    url = 'https://api.inews.qq.com/newsqa/v1/query/inner/publish/modules/list?modules=' + api_name
    reponse = requests.get(url=url).json()
    return reponse

#============================================================================全国总疫情数据
chinadaylist = catch_data('chinaDayList')
chinadaylist = pd.DataFrame(chinadaylist['data']['chinaDayList'])
chinadaylist['date'] = pd.to_datetime(chinadaylist['y'].astype('str') + '.' + chinadaylist['date'])
chinadaylist = chinadaylist[['date','confirm','heal','dead','noInfectH5','nowConfirm','localConfirm']]
chinadaylist.to_csv('全国疫情数据.csv')

#============================================================================全国一年365天新增数据
#国内每日新增数据
chinanewadd = catch_data('chinaDayAddListNew')
chinanewadd = pd.DataFrame(chinanewadd['data']['chinaDayAddListNew'])
chinanewadd['date'] = pd.to_datetime(chinanewadd['y'].astype('str') + '.' + chinanewadd['date'])
chinanewadd = chinanewadd[['date','confirm','dead','heal','infect','importedCase','localConfirmadd','localinfectionadd']]
chinanewadd.columns = ['日期','新增确诊','新增死亡','新增治愈','新增无症状','新增境外','本土新增确诊','本土新增无症状']
chinanewadd.tail()
chinanewadd.to_csv('全国一年每天新增疫情数据.csv')

#============================================================================省份数据（和各城市用的一个数据接口）
#省份数据明细处理
province_data = pd.DataFrame()
#获取所有城市数据，第一步先处理省数据
Cdata= catch_data('diseaseh5Shelf')
province_catch_data = Cdata['data']['diseaseh5Shelf']['areaTree'][0]['children']
for i in range(len(province_catch_data)):
    province_total = province_catch_data[i]['total'] #省总数据
    province_total['name'] = province_catch_data[i]['name'] #省名
    province_total['adcode'] = province_catch_data[i]['adcode'] #省代码
    province_total['date'] = province_catch_data[i]['date'] #更新日期
    province_today = province_catch_data[i]['today'] #省当日数据
    province_today['name'] = province_catch_data[i]['name'] #省名
    province_total = pd.DataFrame(province_total,index=[i])
    province_today = pd.DataFrame(province_today,index=[i])
    province_today.rename({'confirm':'confirm_add'},inplace=True,axis=1) #today里面的confirm实际是每日新增
    merge_data = province_total.merge(province_today,how='left',on='name') #合并省总数据和当日数据
    province_data = pd.concat([province_data,merge_data]) #拼接省份数据
province_data = province_data[['name','adcode','date','confirm','provinceLocalConfirm','heal','dead','wzz','nowConfirm','confirm_add','local_confirm_add',
                               'wzz_add','abroad_confirm_add','dead_add','mediumRiskAreaNum','highRiskAreaNum','isUpdated']]
province_data.columns = ['省份','代码','日期','累计确诊','本土累计确诊','累计治愈','累计死亡','无症状','现存确诊','新增确诊','本土新增确诊','新增无症状','新增境外','新增死亡','中风险数量','高风险数量','是否更新']
province_data = province_data.sort_values(by='累计确诊',ascending=False,ignore_index=True) #有这一句生成的数据框前面才会从0开始编码0，1，2
province_data.head()
province_data.to_csv("中国省份疫情数据.csv")

#求和全国的总数据 这一块因为数据接口的问题 不能从网页上直接爬取出总全国疫情数据
#ChinaTotalData=[sum(province_data['累计确诊']),sum(province_data['累计治愈']),sum(province_data['累计死亡']),sum(province_data['无症状'])] #这个是列表

ChinaTotalData=[province_data['累计确诊'].sum(),province_data['累计治愈'].sum(),province_data['累计死亡'].sum(),province_data['无症状'].sum()] #这个是列表


#绘制饼图函数数据参数要传入列表
#取出山东的疫情数据做可视化
#shandong=province_data.loc[(province_data['省份'] == '山东')][['confirm','heal','dead','wzz',confirm_add','wzz_add']] #取出来的这一行也是数据框格式
#shangdong.columns = ['确诊','治愈','死亡','无症状','新增确诊','新增无症状']

SD=province_data.loc[(province_data['省份'] == '山东')]
shandongData=[SD.loc[18,'累计确诊'],SD.loc[18,'累计治愈'],SD.loc[18,'累计死亡'],SD.loc[18,'无症状']] #这个是列表
                
#=========================================================================省份中城市数据
df_city_data_total = pd.DataFrame()
for x in range(len(province_catch_data)):
    province_dict = province_catch_data[x]['children']
    province_name = province_catch_data[x]['name']
    df_city_data = pd.DataFrame()
    for i in range(len(province_dict)):
        city_total = province_dict[i]['total']
        city_total['province_name'] = province_name #省名
        city_total['name'] = province_dict[i]['name'] #市区名
        city_total['adcode'] = province_dict[i]['adcode'] #市区代码
        city_total['date'] = province_dict[i]['date'] #更新日期
        city_today = province_dict[i]['today'] #当日数据
        city_today['province_name'] = province_name #省名
        city_today['name'] = province_dict[i]['name'] #市区名
        city_total = pd.DataFrame(city_total,index=[i])
        city_today = pd.DataFrame(city_today,index=[i])
        city_today.rename({'confirm':'confirm_add'},inplace=True,axis=1) #today里面的confirm实际是每日新增
        merge_city = city_total.merge(city_today,how='left',on=['province_name','name'])
        df_city_data = pd.concat([df_city_data,merge_city])
    df_city_data_total = pd.concat([df_city_data_total,df_city_data])

df_city_data_total = df_city_data_total[['province_name','name','adcode','date','confirm','provinceLocalConfirm','heal','dead','nowConfirm','confirm_add','local_confirm_add',
                               'wzz_add','mediumRiskAreaNum','highRiskAreaNum']]
#df_city_data_total.columns = ['省份','城市','代码','日期','累计确诊','本土累计','累计治愈','累计死亡','现有确诊','当日新增','新增本土','新增无症状','中风险数量','高风险数量']
df_city_data_total =df_city_data_total.sort_values(by='confirm',ascending=False,ignore_index=True)
df_city_data_total.to_csv("省份中城市疫情数据.csv")

city_data=df_city_data_total[['name','confirm']]


#================================================================全球疫情数据
#此url中数据结构化非常高 抓取之后直接转换成字典 选取要用到的字段 列表 dataframe
url = 'https://api.inews.qq.com/newsqa/v1/automation/modules/list?modules=FAutoCountryConfirmAdd,WomWorld,WomAboard'
reponse=requests.get(url).json()

#全球疫情数据总和
World_data = reponse['data']['WomWorld']
df_World_data=pd.DataFrame(World_data,index=[0]) #字典转dataframe格式数据
df_World_data = df_World_data[['PubDate','nowConfirm','nowConfirmAdd','confirm','confirmAdd','heal','healAdd','dead','deadAdd']]
df_World_data.columns = ['日期','现存确诊','现存确诊新增','累计确诊','累计确诊新增','累计治愈','治愈新增','死亡','死亡新增']
df_World_data.to_csv("全球疫情数据总和数据.csv")

aboard_data = reponse['data']['WomAboard'] #各国家疫情数据
#两行代码是简单查看数据 
aboard_data = pd.DataFrame(aboard_data) #列表直接转换成dataframe 这一步对于数据处理十分简单
aboard_data_use = aboard_data[['pub_date','continent','name','confirm','dead','heal','nowConfirm','confirmAdd']]
aboard_data_use.columns = ['日期','大洲','国家','累计确诊','累计死亡','累计治愈','现存确诊','新增确诊']

world_name = pd.read_excel("世界各国中英文对照.xlsx") #将国家名字对应表导入

global_data = pd.merge(aboard_data_use, world_name, left_on="国家", right_on="中文", how="inner") #把国家名字导入 绘图的时候要用到国家的英文名字 这个表的两列分别是 英文 中文
global_data = global_data[["国家", "英文", "累计确诊", "累计死亡", "累计治愈","现存确诊","新增确诊"]] 
#将数据保存到根目录下（F盘下的python文件夹下）
global_data.to_csv('全球各国家疫情数据.csv')

#可视化
#全国和山东的饼图 #这里的数据有问题但是找不出来问题
total_pie = (
    Pie(init_opts=opts.InitOpts(theme=ThemeType.LIGHT, width='500px', height='350px', bg_color="transparent"))
        .add("", [list(z) for z in zip(['全国确诊', '全国治愈', '全国死亡', '全国无症状'],[9310455, 453376, 31017, 273146])],
             center=["50%", "60%"], radius=[75, 100], )
        .add("", [list(z) for z in zip(['山东确诊', '山东治愈', '山东死亡', '山东无症状'],[4502, 3982, 8, 6960])], center=["50%", "60%"], radius=[0, 50])
        .set_global_opts(title_opts=opts.TitleOpts(title="全国和山东疫情数据占比", pos_bottom=0,
                                                   title_textstyle_opts=opts.TextStyleOpts(color="#00FFFF")),
                         legend_opts=opts.LegendOpts(textstyle_opts=opts.TextStyleOpts(color="#FFFFFF")))
        .set_series_opts(label_opts=opts.LabelOpts(formatter="{b}:{c}")))

#全球疫情图
#但是这里获取到的全球疫情数据是没有中国的
world_map= (
	Map(init_opts=opts.InitOpts(theme=ThemeType.WESTEROS))
	.add("", [list(z) for z in zip(list(global_data["英文"]), list(global_data["累计确诊"]))], is_map_symbol_show=False,maptype='world')
	.set_global_opts(
            		title_opts = opts.TitleOpts(title='世界各国累计确诊', pos_right='40%', title_textstyle_opts=opts.TextStyleOpts(color='#FFFF99')),
            		visualmap_opts = opts.VisualMapOpts(max_=5000000, textstyle_opts=opts.TextStyleOpts(color='#FFFF99'), pos_left='left'),
            		legend_opts=opts.LegendOpts(textstyle_opts=opts.TextStyleOpts(color='#FFFF99')))
	.set_series_opts(label_opts=opts.LabelOpts(is_show=False)))

# 中国疫情地图绘制
area_map = (
    Map(init_opts=opts.InitOpts(theme=ThemeType.WESTEROS))
        .add("", [list(z) for z in zip(list(province_data["省份"]), list(province_data["现存确诊"]))], "china",
             is_map_symbol_show=False, label_opts=opts.LabelOpts(color="#fff"),
             tooltip_opts=opts.TooltipOpts(is_show=True), zoom=1.2, center=[105, 30])
        .set_series_opts(label_opts=opts.LabelOpts(is_show=False))
        .set_global_opts(title_opts=opts.TitleOpts(title="中国现存确诊疫情分布图", pos_top='5%',
                                                   title_textstyle_opts=opts.TextStyleOpts(color="#FF0000")),
                         visualmap_opts=opts.VisualMapOpts(is_piecewise=True, pos_right=0, pos_bottom=0,
                                                           textstyle_opts=opts.TextStyleOpts(color="#F5FFFA"),
                                                           pieces=[
                                                               {"min": 1001, "label": '>1000', "color": "#893448"},
                                                               {"min": 500, "max": 1000, "label": '500-1000',
                                                                "color": "#ff585e"},
                                                               {"min": 101, "max": 499, "label": '101-499',
                                                                "color": "#fb8146"},
                                                               {"min": 10, "max": 100, "label": '10-100',
                                                                "color": "#ffb248"},
                                                               {"min": 0, "max": 9, "label": '0-9',
                                                                "color": "#fff2d1"}])))

#中国地图城市热力图
#首先把数据整理好 要用到city和confirm
def is_city(item):
    '''
    判断一个城市能否在Geo地图上被找到
    :param item: 城市名
    :return: T/F
    '''

    lists_1 = []
    lists_1.append(item)
    lists_2 = [10]
    geo = Geo()
    geo.add_schema(maptype="china")
    try:
        geo.add("确诊城市", [list(z) for z in zip(lists_1, lists_2)])
        return True
    except Exception:
        return False

city_index = [] #地图上不存在的城市名的dataframe序号index
i = 0
for item in city_data['name']:
    if is_city(item) == False:
        city_index.append(i)
    i += 1

city_data2=city_data.drop(axis=0, index =city_index) #把地图上标记不到的城市删除掉

area_heat_geo = (
    Geo(init_opts=opts.InitOpts(theme=ThemeType.WESTEROS, bg_color='transparent'))
        .add_schema(maptype="china", zoom=1.2, center=[105, 30])
        .add("确诊城市", [list(z) for z in zip(list(city_data2["name"]), list(city_data2["confirm"]))], symbol_size=10)
       
        .add("", [list(z) for z in zip(list(city_data2["name"]), list(city_data2["confirm"]))],
             type_=ChartType.HEATMAP)
        .set_series_opts(label_opts=opts.LabelOpts(is_show=False))
        .set_global_opts(
        visualmap_opts=opts.VisualMapOpts(range_size=[0, 25, 50, 75, 100], max_=4000, orient='horizontal',
                                          pos_bottom=0),
        title_opts=opts.TitleOpts(title="中国累计确诊疫情分布热图", pos_top='5%'),
        legend_opts=opts.LegendOpts(pos_bottom='10%', pos_left=0)))

#全球数据表格
#df_World_data.columns = ['日期','现存确诊','现存确诊新增','累计确诊','累计确诊新增','累计治愈','治愈新增','死亡','死亡新增']

confirms = (Pie().
            set_global_opts(title_opts=opts.TitleOpts(title="确诊", pos_left='center', pos_top='center',
                                                      subtitle="(累计)",item_gap=1,
                                                      subtitle_textstyle_opts=opts.TextStyleOpts(color="#FFFFFF"),
                                                      title_textstyle_opts=opts.TextStyleOpts(color='#FFFFFF'))))
confirms_people = (Pie().
                   set_global_opts(title_opts=opts.TitleOpts(title=(str(df_World_data.loc[0,'累计确诊']) + "   "),
                                                             pos_top='15%', pos_left='center',
                                                             subtitle=("         新增: " + str(df_World_data.loc[0,'累计确诊新增'])),
                                                             item_gap=1,
                                                             title_textstyle_opts=opts.TextStyleOpts(color="#00FFFF",
                                                                                                     font_size=30),
                                                             subtitle_textstyle_opts=opts.TextStyleOpts(color="#00BFFF")
                                                             )))
nowconfirms = (Pie().
            set_global_opts(title_opts=opts.TitleOpts(title="确诊", pos_left='center', pos_top='center',
                                                      subtitle="(现存)",item_gap=1,
                                                      subtitle_textstyle_opts=opts.TextStyleOpts(color="#FFFFFF"),
                                                      title_textstyle_opts=opts.TextStyleOpts(color='#FFFFFF'))))
nowconfirms_people = (Pie().
                   set_global_opts(title_opts=opts.TitleOpts(title=(str(df_World_data.loc[0,'现存确诊']) + "   "),
                                                             pos_top='15%', pos_left='center',
                                                             subtitle=("         新增: " + str(df_World_data.loc[0,'现存确诊新增'])),
                                                             item_gap=1,
                                                             title_textstyle_opts=opts.TextStyleOpts(color="#00FFFF",
                                                                                                     font_size=30),
                                                             subtitle_textstyle_opts=opts.TextStyleOpts(color="#00BFFF")
                                                             )))


deads = (Pie().
         set_global_opts(title_opts=opts.TitleOpts(title="死亡", pos_left='center', pos_top='center',
                                                   subtitle="(累计)",item_gap=1,
                                                   subtitle_textstyle_opts=opts.TextStyleOpts(color="#FFFFFF"),
                                                   title_textstyle_opts=opts.TextStyleOpts(color='#FFFFFF'))))
deads_people = (Pie().
                set_global_opts(title_opts=opts.TitleOpts(title=(str(df_World_data.loc[0,'死亡']) + "   "),
                                                          pos_top='15%', pos_left='center',
                                                          subtitle=("         新增 :" + str(df_World_data.loc[0,'死亡新增'])),
                                                          item_gap=1,
                                                          title_textstyle_opts=opts.TextStyleOpts(color="#FF0000",
                                                                                                  font_size=30),
                                                          subtitle_textstyle_opts=opts.TextStyleOpts(color="#F08080")
                                                          )))
heals = (Pie().
         set_global_opts(title_opts=opts.TitleOpts(title="治愈", pos_left='center', pos_top='center',
                                                   subtitle="(累计)",item_gap=1,
                                                   subtitle_textstyle_opts=opts.TextStyleOpts(color="#FFFFFF"),
                                                   title_textstyle_opts=opts.TextStyleOpts(color='#FFFFFF'))))
heals_people = (Pie().
                set_global_opts(title_opts=opts.TitleOpts(title=(str(df_World_data.loc[0,'累计治愈']) + "   "),
                                                          pos_top='15%', pos_left='center',
                                                          subtitle=("         新增 :" + str(df_World_data.loc[0,'治愈新增'])),
                                                          item_gap=1,
                                                          title_textstyle_opts=opts.TextStyleOpts(color="#00FF00",
                                                                                                  font_size=30),
                                                          subtitle_textstyle_opts=opts.TextStyleOpts(color="#98FB98")
                                                          )))
#全球数据水滴球
sum=df_World_data.loc[0,'累计确诊']+df_World_data.loc[0,'现存确诊']+df_World_data.loc[0,'死亡']+df_World_data.loc[0,'累计治愈']
confirm_liquid = (
    Liquid()
        .add("确诊比例", [df_World_data.loc[0,'累计确诊']/ sum], tooltip_opts=opts.TooltipOpts(),
             label_opts=opts.LabelOpts(color="#00FFFF",
                                       font_size=15,
                                       formatter=JsCode(
                                           """function (param) {
                     return (Math.floor(param.value * 10000) / 100) + '%';
                 }"""
                                       ),
                                       position="inside",
                                       ),
             )
        .set_global_opts(title_opts=opts.TitleOpts(title="全球疫情数据"))
)
nowconfirm_liquid = (
    Liquid()
        .add("现存确诊比例", [df_World_data.loc[0,'现存确诊']/ sum], tooltip_opts=opts.TooltipOpts(),
             label_opts=opts.LabelOpts(color="#00FFFF",
                                       font_size=15,
                                       formatter=JsCode(
                                           """function (param) {
                     return (Math.floor(param.value * 10000) / 100) + '%';
                 }"""
                                       ),
                                       position="inside",
                                       ),
             )
)
dead_liquid = (
    Liquid()
        .add("死亡比例", [df_World_data.loc[0,'死亡'] / sum], tooltip_opts=opts.TooltipOpts(),
             label_opts=opts.LabelOpts(color="#FF0000",
                                       font_size=15,
                                       formatter=JsCode(
                                           """function (param) {
                     return (Math.floor(param.value * 10000) / 100) + '%';
                 }"""
                                       ),
                                       position="inside",
                                       ),
             )
)

heal_liquid = (
    Liquid()
        .add("治愈比例", [df_World_data.loc[0,'累计治愈'] / sum], tooltip_opts=opts.TooltipOpts(),
             label_opts=opts.LabelOpts(color="#00FF00",
                                       font_size=15,
                                       formatter=JsCode(
                                           """function (param) {
                     return (Math.floor(param.value * 10000) / 100) + '%';
                 }"""
                                       ),
                                       position="inside",
                                       ),
             )
)

#注意这里词云的也是地图上要有的城市名称
wc = (
    WordCloud()
        .add("", [list(z) for z in zip(list(city_data2["name"]), list(city_data["confirm"]))],
             word_gap=0, word_size_range=[20, 30]))



big_title = (
    Pie()
        .set_global_opts(
        title_opts=opts.TitleOpts(title="COVID-19实时数据大屏",
                                  title_textstyle_opts=opts.TextStyleOpts(font_size=40, color='#FFFFFF',
                                                                          border_radius=True, border_color="white"),
                                  pos_top=0)))

title = Pie().set_global_opts(title_opts=opts.TitleOpts(title="全球数据表格", title_textstyle_opts=opts.TextStyleOpts(font_size=20, color='#FFFF99'), pos_top=0))


#这里的时间从省份数据中获取
lastUpdateTime=data= Cdata['data']['diseaseh5Shelf']['lastUpdateTime']
times = (
    Pie()
        .set_global_opts(
        title_opts=opts.TitleOpts(subtitle=("截至 " + lastUpdateTime),
                                  subtitle_textstyle_opts=opts.TextStyleOpts(font_size=13, color='#FFFFFF'),
                                  pos_top=0))
)


#整合图片
page = (Page(layout=Page.DraggablePageLayout, page_title="COVID-19")
        .add(total_pie)#0
        .add(world_map)#1
        .add(area_map)#2
        .add(area_heat_geo)#3

        .add(title)#4
        
        .add(big_title)#5
        .add(times)#6
        
        .add(confirms)#7
        .add(confirms_people)#8
        .add(nowconfirms)#9
        .add(nowconfirms_people) #10     
        .add(deads)#11
        .add(deads_people)#12
        .add(heals)#13
        .add(heals_people)#14
        
        .add(confirm_liquid)#15       
        .add(nowconfirm_liquid) #16       
        .add(dead_liquid)#17
        .add(heal_liquid)#18
        .add(wc)#19
        ).render('COVID-19 数据一览2.html')

with open("COVID-19 数据一览2.html", "r+", encoding='utf-8') as html:
    html_bf = BeautifulSoup(html, 'lxml')
    divs = html_bf.select('.chart-container')
    divs[0][
        'style'] = "width:411px;height:303px;position:absolute;top:5px;left:0px;border-style:solid;border-color:#444444;border-width:0px;"
    divs[1][
        "style"] = "width:850px;height:380px;position:absolute;top:45px;left:333px;border-style:solid;border-color:#444444;border-width:0px;"
    divs[2][
        "style"] = "width:600px;height:500px;position:absolute;top:313px;left:1125px;border-style:solid;border-color:#444444;border-width:0px;"
    divs[3][
        "style"] = "width:600px;height:500px;position:absolute;top:310px;left:0px;border-style:solid;border-color:#444444;border-width:0px;"

    divs[4][
        "style"] = "width:646px;height:304px;position:absolute;top:312px;left:312px;border-style:solid;border-color:#444444;border-width:0px;"
    divs[5][
        "style"] = "width:450px;height:55px;position:absolute;top:2px;left:440px;border-style:solid;border-color:#444444;border-width:0px;"
    divs[6][
        "style"] = "width:200px;height:30px;position:absolute;top:11px;left:1000px;border-style:solid;border-color:#444444;border-width:0px;"

    divs[7][
        'style'] = "width:60px;height:75px;position:absolute;top:5px;left:1360px;border-style:solid;border-color:#DC143C;border-width:3px;border-radius:25px 0px 0px 0px"
    divs[8][
        "style"] = "width:200px;height:75px;position:absolute;top:5px;left:1420px;border-style:solid;border-color:#DC143C;border-width:3px;"
    divs[9][
        "style"] = "width:60px;height:75px;position:absolute;top:80px;left:1360px;border-style:solid;border-color:#DC143C;border-width:3px;"
    divs[10][
        "style"] = "width:200px;height:75px;position:absolute;top:80px;left:1420px;border-style:solid;border-color:#DC143C;border-width:3px;"
    divs[11][
        "style"] = "width:60px;height:75px;position:absolute;top:155px;left:1360px;border-style:solid;border-color:#DC143C;border-width:3px;"
    divs[12][
        "style"] = "width:200px;height:75px;position:absolute;top:155px;left:1420px;border-style:solid;border-color:#DC143C;border-width:3px;"
    divs[13][
        "style"] = "width:60px;height:75px;position:absolute;top:230px;left:1360px;border-style:solid;border-color:#DC143C;border-width:3px;"
    divs[14][
        "style"] = "width:200px;height:75px;position:absolute;top:230px;left:1420px;border-style:solid;border-color:#DC143C;border-width:3px;border-radius:0px 0px 25px 0px"

    divs[15][
        "style"] = "width:160px;height:160px;position:absolute;top:-35px;left:1220px;border-style:solid;border-color:#444444;border-width:0px;"
    divs[16][
        "style"] = "width:160px;height:160px;position:absolute;top:40px;left:1165px;border-style:solid;border-color:#444444;border-width:0px;"
    divs[17][
        "style"] = "width:160px;height:160px;position:absolute;top:115px;left:1220px;border-style:solid;border-color:#444444;border-width:0px;"
    divs[18][
        "style"] = "width:160px;height:160px;position:absolute;top:188px;left:1165px;border-style:solid;border-color:#444444;border-width:0px;"
    divs[19][
        "style"] = "width:1280px;height:120px;position:absolute;top:600px;left:0px;border-style:solid;border-color:#444444;border-width:0px;"
    
    body = html_bf.find("body")
    body["style"] = "background-color:#333333;"
    html_new = str(html_bf)
    html.seek(0, 0)
    html.truncate()
    html.write(html_new)
    html.close()
