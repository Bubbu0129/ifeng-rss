import config
import json
import xml.etree.ElementTree as ET
import sys
from datetime import datetime, timezone, timedelta
from urllib import request, error

sys.stdout.reconfigure(encoding='utf-8')

rfc822="%a, %d %b %Y %H:%M:%S GMT"
now = datetime.now(timezone.utc).strftime(rfc822)
config.channel_info["pubDate"] = now
config.channel_info["lastBuildDate"] = now

config.channel_info["link"] = f"https://wemedia.ifeng.com/zhengming/{config.ifeng_id}_0/list.shtml"
api = f"https://shankapi.ifeng.com/season/ishare/getShareListData/{config.ifeng_id}/doc/1/ifengnewsh5/getListData?callback=getListData&_=120"

def format(date_string):
    # Converts a date string from the API (assumed to be UTC+8)
    # to an RFC 822 formatted string in GMT using only the datetime library.
    if not date_string:
        return ''
    try:
        cst_timezone = timezone(timedelta(hours=8))
        naive_dt = datetime.strptime(date_string, "%Y-%m-%d %H:%M:%S")
        cst_dt = naive_dt.replace(tzinfo=cst_timezone)
        utc_dt = cst_dt.astimezone(timezone.utc)
        return utc_dt.strftime(rfc822)
    except (ValueError, TypeError):
        return date_string

try:
    req = request.Request(api, headers={'Cookie': ''})
    with request.urlopen(req) as response:
        rsp = response.read().decode('utf-8')
    api_data = json.loads(rsp[12:-1]) #rsp="getListData({json})"

    rss_root = ET.Element('rss', version='2.0')
    channel = ET.SubElement(rss_root, 'channel')
    for key, value in config.channel_info.items():
        ET.SubElement(channel, key).text = value

    for item_data in api_data.get('data', []):
        item = ET.SubElement(channel, 'item')
        ET.SubElement(item, 'title').text = item_data.get('title', '')
        item_url = item_data.get('url', '')
        if item_url.startswith('//'):
            item_url = 'https:' + item_url
        ET.SubElement(item, 'link').text = item_url
        ET.SubElement(item, 'guid', isPermaLink="true").text = item_url
        item_date = item_data.get('newsTime')
        ET.SubElement(item, 'pubDate').text = format(item_date)
        thumbnail = item_data.get('thumbnail')
        if thumbnail:
            ET.SubElement(item, 'enclosure', {
                'url': thumbnail, 'length': '0', 'type': 'image/jpeg'
            })

    filename = f"{config.ifeng_id}.xml"
    xml_bytes = ET.tostring(rss_root, encoding='utf-8', xml_declaration=True)
    with open(filename, 'wb') as f:
        f.write(xml_bytes)

except error.URLError as e:
    print(f"Error: Could not fetch data from API {api}. {e}", file=sys.stderr)
except (ValueError, json.JSONDecodeError) as e:
    print(f"Error: Could not parse data from response. {e}", file=sys.stderr)
except Exception as e:
    print(f"An unexpected error occurred. {e}", file=sys.stderr)
