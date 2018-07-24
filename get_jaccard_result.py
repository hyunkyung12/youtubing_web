import konlpy
from konlpy.tag import *
from konlpy.utils import pprint

import nltk

import io
import os
import pandas as pd
import numpy as np
import pickle
import json
import csv
import re

from collections import Counter
from ast import literal_eval

from itertools import chain

from gensim.models import Word2Vec
from sklearn.metrics.pairwise import *

import sqlite3

# file_name = sys.argv[1]
# sentence = sys.argv[2]
# num = sys.argv[3]

# 2.
## 자카드 유사도
def jaccard(s1, s2):
    c = len(set(s1)&set(s2)) # s2 = set("Hello")이면 s2={'e', 'H', 'l', 'o'}
    return float(c) / float(len(set(s1)|set(s2))) # float 소수점 포함

## subtitle 비교
def compare_subtitle_kkma(sentence, num): # 꼬꼬마로 index

    distance = []
    kkma = Kkma()
    print(input_file.shape)
    kms = kkma.morphs(sentence)
#    for i in range(len(input_file)):
#        distance.append(jaccard(kkma.morphs(sentence), input_file[i]))
    input_file['distance'] = input_file.apply(lambda row : jaccard(row['tt'], kms), axis=1)
    distance = input_file['distance'].values
    print('debuging...')
    result = []
    for i in range(num):
        max_index = np.argmax(distance)
        print('max value : ', distance[max_index])
        if distance[max_index] == 0:
            return result
        distance[max_index] = -1
        result.append(max_index)
    return result

def write_csv(sentence, num):
    print('-----------------------------------'+sentence)
    print(int(num))
    index = compare_subtitle_kkma(sentence, int(num))
    print('-------------------------------------debuging_write_csv')
    
    sentence_list = []
    start = []
    end = []
    url_list = []

    for i in index:
        sentence_list.append(demo['sentence'][i])
        start.append(demo['start_time'][i])
        end.append(demo['end_time'][i])
        url_list.append(get_url(demo['subtitle_id'][i]))

    output = {'subtitle' : sentence_list, 'start' : start, 'end' : end, 'url' : url_list}
    print('-------------------------------------output')

    print('output : ', output)

    Output1 = pd.DataFrame(output).reset_index()
    Output1.to_csv('./data/jaccard_checklist.csv', index=False)
    print("=================write jaccard_checklist================")

def get_url(sid):
    cur = con.cursor()
    
    sql = "SELECT video_id FROM subtitle_meta WHERE subtitle_id = " + str(sid)
    cur.execute(sql)
    vid = cur.fetchall()[0][0]

    sql = "SELECT url FROM video_meta WHERE video_id = " + str(vid)
    cur.execute(sql)
    return cur.fetchall()[0][0]    

def write_json():
    csvfile = open('./data/jaccard_checklist.csv', 'r')

    jsonfile = open('file.json', 'w')

    #fieldnames = ("num","url","start_time","end","subtitle")
    fieldnames = ("num","end","start_time","subtitle","url")
    reader = csv.DictReader( csvfile, fieldnames)
    out = json.dumps( [ row for row in reader ] )
    jsonfile.write(out)

def read_json():

    write_json()
    with open('file.json', 'r') as f:
    #    txt = f.read()
        rtn = json.load(f)
    #rtn = json.load(txt)
    
    #return json.dumps(rtn, ensure_ascii=False).encode('utf8')
    return rtn    

def custom_set(li):
    set_list = []
    count_list = []
    for ob in li:
        if ob in set_list:
            count_list[set_list.index(ob)] += 1
        else:
            set_list.append(ob)
            count_list.append(1)
    return set_list, count_list

def make_new_json():
    
    check_list = read_json()

    check_list = check_list[1:]
    url_list = [a['url'] for a in check_list]
    url_list = [c.replace('watch?v=','embed/') for c in url_list]
    url_list = [re.sub(r'&index?.*','',c) for c in url_list]
    url_list = [re.sub(r'&list?.*','',c) for c in url_list]

#     cnt = Counter()
#     for word in url_list:
#         cnt[word] += 1
#     cnt = list(cnt.items())
#     print('------------ cnt : ', cnt)
#     cleaned = []

#     for i in range(0,len(url_list)):
#         if(i == len(url_list)-1):
#             cleaned.append(url_list[i])
#         else:
#             if url_list[i] != url_list[i+1]:
#                 cleaned.append(url_list[i])

#     count = []

#     for url in cleaned:
#         for c in cnt:
#             if(c[0] == url):
#                 count.append(c[1])
    cleaned, count = custom_set(url_list)
    
    data = {}  
    data['num'] = []  
    data['url'] = []  
    data['start_time'] = []  
    data['end_time'] = []  
    data['subtitle'] = []  
    data['count'] = []  

    i = 0
    j = 0
    while(i<len(check_list)):
        for c in count:
            sub_data = check_list[i:i+c]
            sub_num = []; sub_start = []; sub_end = []; sub_sub = [];
            for sub in sub_data:
                h, m, s = sub['start_time'].split(':')
                s, ms = s.split(',')
                if len(h) < 2:
                    h = '0' + h
                if len(m) < 2:
                    m = '0' + m
                if len(s) < 2:
                    s = '0' + s
                sub['start_time'] = h + ':' + m + ':' + s + ',' + ms
                sub_num.append(sub['num'])
                sub_start.append(sub['start_time'])   
                sub_end.append(sub['end'])   
                sub_sub.append(sub['subtitle']) 
            if len(sub_num) == 0:
                continue  
            data['num'].append(sub_num); data['start_time'].append(sub_start); 
            data['end_time'].append(sub_end); data['subtitle'].append(sub_sub); 
            data['count'].append(c)
            data['url'].append(cleaned[j])
            i = i+c  
            j = j+1


    with open('new.json', 'w') as outfile:
        json.dump(data, outfile)      

    with open('new.json', 'r', encoding='utf-8') as f:
        rtn = json.load(f)
    print("====================================")
    #print(rtn['count'][0])
    print("====================================")

    return json.dumps(rtn, ensure_ascii=False).encode('utf8')


if __name__ != "__main__":
    con = sqlite3.connect('data/youtubing.db', check_same_thread=False)
    sql = "SELECT * FROM sentence_meta"
    demo = pd.read_sql(sql, con)

    demo['tt'] = demo.apply(lambda row:literal_eval(row['text_token']), axis=1)
    input_file = demo[['sentence_id', 'subtitle_id', 'tt']]
    print
    print('-----------------------------DB loaded')
# 1. 파일 불러오기