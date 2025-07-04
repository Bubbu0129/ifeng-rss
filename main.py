import json
import xml.etree.ElementTree as ET
import sys
from datetime import datetime, timezone, timedelta
from urllib import request, error

rfc822='%a, %d %b %Y %H:%M:%S GMT'
def format(date_string):
    # Converts a date string from the API (assumed to be UTC+8)
    # to an RFC 822 formatted string in GMT using only the datetime library.
    cst_timezone = timezone(timedelta(hours=8))
    naive_dt = datetime.strptime(date_string, '%Y-%m-%d %H:%M:%S')
    cst_dt = naive_dt.replace(tzinfo=cst_timezone)
    utc_dt = cst_dt.astimezone(timezone.utc)
    return utc_dt.strftime(rfc822)

if len(sys.argv) != 2:
    print(f"Usage: {sys.argv[0]} <ifeng-id>")
    sys.exit(1)
ifeng_id = sys.argv[1]
link = f"https://ishare.ifeng.com/mediaShare/home/{ifeng_id}/media"

req = request.Request(link, headers={'Cookie': ''})
with request.urlopen(req) as response:
    for b_line in response:
        line = b_line.decode('utf-8').rstrip()
        i = line.find('allData')
        if i != -1:
            break
data = json.loads(line[i+10:-1])['sockpuppetInfo'] #line=".*allData = <json>;"
channel = {
        'title': data['weMediaName'],
        'link': link,
        'description': data['description'],
        'language': 'zh-cn',
        'pubDate': datetime.now(timezone.utc).strftime(rfc822)
}

api = f"https://shankapi.ifeng.com/season/ishare/getShareListData/{ifeng_id}/doc/1/_/getListData"
api_req = request.Request(api, headers={'Cookie': ''})
with request.urlopen(api_req) as api_response:
    api_rsp = api_response.read().decode('utf-8')
api_data = json.loads(api_rsp[12:-1]) #rsp="getListData(<json>)"

rss_root = ET.Element('rss', version='2.0')
ch = ET.SubElement(rss_root, 'channel')
for key, value in channel.items():
    ET.SubElement(ch, key).text = value

for item_data in api_data['data']:
    item = ET.SubElement(ch, 'item')
    ET.SubElement(item, 'title').text = item_data['title']
    item_url = item_data['url']
    if item_url.startswith('//'):
        item_url = 'https:' + item_url
    ET.SubElement(item, 'link').text = item_url
    ET.SubElement(item, 'guid', isPermaLink='false').text = item_data['id']
    item_date = item_data['newsTime']
    ET.SubElement(item, 'pubDate').text = format(item_date)
    thumbnail = item_data.get('thumbnail')
    if thumbnail:
        ET.SubElement(item, 'enclosure', {
            'url': thumbnail, 'length': '0', 'type': 'image/jpeg'
        })

filename = f"{ifeng_id}.xml"
xml_bytes = ET.tostring(rss_root, encoding='utf-8', xml_declaration=True)
with open('assets/'+filename, 'wb') as f:
    f.write(xml_bytes)
