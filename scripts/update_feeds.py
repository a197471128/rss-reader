#!/usr/bin/env python3
"""Fetch all RSS feeds and generate data.json for the RSS reader dashboard."""
import json
import time
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from urllib.request import Request, urlopen
from urllib.error import URLError

# ── Feed configuration (mirrors the JS in index.html) ──
CATEGORIES = [
    {"id": "hot",     "icon": "🔥", "label": "实时热点"},
    {"id": "media",   "icon": "📰", "label": "媒体新闻"},
    {"id": "finance", "icon": "💰", "label": "财经资讯"},
    {"id": "tech",    "icon": "💻", "label": "科技前沿"},
    {"id": "edu",     "icon": "🎓", "label": "教育学术"},
    {"id": "culture", "icon": "📚", "label": "文化娱乐"},
    {"id": "other",   "icon": "📡", "label": "其他"},
]

FEEDS = [
    # 🔥 实时热点
    {"cat": "hot", "name": "实时资讯",        "url": "https://dicomp.net/hotnews/"},
    {"cat": "hot", "name": "知乎热榜",        "url": "https://rsshub.dicomp.net/zhihu/hot"},
    {"cat": "hot", "name": "知乎日报",        "url": "https://rsshub.dicomp.net/zhihu/daily"},
    {"cat": "hot", "name": "B站排行榜",       "url": "https://rsshub.dicomp.net/bilibili/ranking/all"},
    {"cat": "hot", "name": "36Kr热榜",        "url": "https://rsshub.dicomp.net/36kr/hot-list"},
    {"cat": "hot", "name": "虎嗅24h",         "url": "https://rsshub.dicomp.net/huxiu/moment"},
    {"cat": "hot", "name": "虎嗅资讯",        "url": "https://rsshub.dicomp.net/huxiu/article"},
    # 📰 媒体新闻
    {"cat": "media", "name": "央视新闻联播",   "url": "https://rsshub.dicomp.net/cctv/tv/lm/xwlb"},
    {"cat": "media", "name": "联合早报中港台", "url": "https://rsshub.dicomp.net/zaobao/realtime/china"},
    {"cat": "media", "name": "联合早报中国",   "url": "https://rsshub.dicomp.net/zaobao/znews/china"},
    {"cat": "media", "name": "人民日报时政",   "url": "http://www.people.com.cn/rss/politics.xml"},
    {"cat": "media", "name": "人民日报社会",   "url": "http://www.people.com.cn/rss/society.xml"},
    {"cat": "media", "name": "人民日报法治",   "url": "http://www.people.com.cn/rss/legal.xml"},
    {"cat": "media", "name": "人民日报国际",   "url": "http://www.people.com.cn/rss/world.xml"},
    {"cat": "media", "name": "人民日报台港澳", "url": "http://www.people.com.cn/rss/haixia.xml"},
    {"cat": "media", "name": "人民日报军事",   "url": "http://www.people.com.cn/rss/military.xml"},
    {"cat": "media", "name": "人民日报全部",   "url": "http://www.people.com.cn/rss/ywkx.xml"},
    {"cat": "media", "name": "参考消息第一关注","url": "https://rsshub.dicomp.net/cankaoxiaoxi/column/diyi"},
    {"cat": "media", "name": "参考消息中国",   "url": "https://rsshub.dicomp.net/cankaoxiaoxi/column/zhongguo"},
    {"cat": "media", "name": "环球网国内",     "url": "https://rsshub.dicomp.net/huanqiu/news/china"},
    {"cat": "media", "name": "环球网国际",     "url": "https://rsshub.dicomp.net/huanqiu/news/world"},
    {"cat": "media", "name": "观察者网",       "url": "https://rsshub.dicomp.net/guancha/gundong"},
    {"cat": "media", "name": "凤凰网",         "url": "https://rsshub.dicomp.net/ifeng/news"},
    {"cat": "media", "name": "南方周末推荐",   "url": "https://rsshub.dicomp.net/infzm/1"},
    {"cat": "media", "name": "南方周末新闻",   "url": "https://rsshub.dicomp.net/infzm/2"},
    {"cat": "media", "name": "中国新闻周刊",   "url": "https://rsshub.dicomp.net/inewsweek/survey"},
    {"cat": "media", "name": "半月谈",         "url": "https://rsshub.dicomp.net/banyuetan/jinritan"},
    {"cat": "media", "name": "求是网",         "url": "https://rsshub.dicomp.net/qstheory/toutiao"},
    {"cat": "media", "name": "人民日报电子版", "url": "https://rsshub.dicomp.net/people/paper"},
    {"cat": "media", "name": "中新网",         "url": "https://www.chinanews.com.cn/rss/scroll-news.xml"},
    {"cat": "media", "name": "中国互联网辟谣", "url": "https://rsshub.dicomp.net/piyao/jrpy"},
    # 💰 财经资讯
    {"cat": "finance", "name": "第一财经",     "url": "https://rsshub.dicomp.net/yicai/news"},
    {"cat": "finance", "name": "财联社头条",   "url": "https://rsshub.dicomp.net/cls/depth/1000"},
    {"cat": "finance", "name": "格隆汇快讯",   "url": "https://rsshub.dicomp.net/gelonghui/live"},
    {"cat": "finance", "name": "金十数据",     "url": "https://rsshub.dicomp.net/jin10"},
    {"cat": "finance", "name": "华尔街见闻",   "url": "https://rsshub.dicomp.net/wallstreetcn/live"},
    {"cat": "finance", "name": "同花顺财经",   "url": "https://rsshub.dicomp.net/10jqka/realtimenews"},
    {"cat": "finance", "name": "36Kr快讯",     "url": "https://rsshub.dicomp.net/36kr/newsflashes"},
    {"cat": "finance", "name": "雪球热帖",     "url": "https://rsshub.dicomp.net/xueqiu/hots"},
    # 💻 科技前沿
    {"cat": "tech", "name": "OPENAI",         "url": "https://rsshub.dicomp.net/openai/news"},
    {"cat": "tech", "name": "每日AI资讯",      "url": "https://rsshub.dicomp.net/ai-bot/daily-ai-news"},
    {"cat": "tech", "name": "AI新闻资讯",      "url": "https://rsshub.dicomp.net/aibase/news"},
    {"cat": "tech", "name": "AI日报",         "url": "https://rsshub.dicomp.net/aibase/daily"},
    {"cat": "tech", "name": "36氪",           "url": "https://36kr.com/feed"},
    {"cat": "tech", "name": "虎嗅",           "url": "https://rss.huxiu.com/"},
    {"cat": "tech", "name": "爱范儿",         "url": "https://rsshub.dicomp.net/ifanr/digest"},
    {"cat": "tech", "name": "数字尾巴",       "url": "https://www.dgtle.com/rss/dgtle.xml"},
    {"cat": "tech", "name": "极客公园",       "url": "https://www.geekpark.net/rss"},
    {"cat": "tech", "name": "IT之家",         "url": "https://www.ithome.com/rss/"},
    {"cat": "tech", "name": "cnBeta",         "url": "https://www.cnbeta.com/backend.php"},
    {"cat": "tech", "name": "品玩",           "url": "https://www.pingwest.com/feed/all"},
    {"cat": "tech", "name": "钛媒体",         "url": "https://www.tmtpost.com/feed"},
    {"cat": "tech", "name": "少数派",         "url": "https://sspai.com/feed"},
    {"cat": "tech", "name": "异次元软件",     "url": "https://feed.iplaysoft.com/"},
    # 🎓 教育学术
    {"cat": "edu", "name": "教育部最新文件",   "url": "https://rsshub.dicomp.net/gov/moe/newest_file"},
    {"cat": "edu", "name": "教育部政策解读",   "url": "https://rsshub.dicomp.net/gov/moe/policy_anal"},
    {"cat": "edu", "name": "教师资格考试",     "url": "https://rsshub.dicomp.net/neea/local/ntce"},
    {"cat": "edu", "name": "PubScholar学术",  "url": "https://rsshub.dicomp.net/pubscholar/explore"},
    # 📚 文化娱乐
    {"cat": "culture", "name": "豆瓣热门书影音","url": "https://rsshub.dicomp.net/douban/list/subject_real_time_hotest"},
    {"cat": "culture", "name": "豆瓣热门电影",  "url": "https://rsshub.dicomp.net/douban/list/movie_real_time_hotest"},
    {"cat": "culture", "name": "豆瓣热门电视",  "url": "https://rsshub.dicomp.net/douban/list/tv_real_time_hotest"},
    {"cat": "culture", "name": "豆瓣热门书籍",  "url": "https://rsshub.dicomp.net/douban/book/rank/fiction"},
    {"cat": "culture", "name": "中文播客榜",    "url": "https://rsshub.dicomp.net/xyzrank"},
    {"cat": "culture", "name": "国博资讯",      "url": "https://rsshub.dicomp.net/chnmuseum/zx/xwzt"},
    {"cat": "culture", "name": "国博要闻",      "url": "https://rsshub.dicomp.net/chnmuseum/zx/xingnew"},
    {"cat": "culture", "name": "煎蛋",          "url": "http://jandan.net/feed"},
    {"cat": "culture", "name": "数英网",        "url": "https://www.digitaling.com/rss"},
    # 📡 其他
    {"cat": "other", "name": "国家统计局",     "url": "http://www.stats.gov.cn/tjsj/zxfb/rss.xml"},
    {"cat": "other", "name": "国务院新闻",     "url": "http://www.gov.cn/govweb/jsonTag/tp/rss.xml"},
    {"cat": "other", "name": "人社部",         "url": "http://www.mohrss.gov.cn/SYrlzyhshbzb/zxhd/RSS/"},
    {"cat": "other", "name": "麦肯锡",         "url": "https://rsshub.dicomp.net/mckinsey/cn"},
    {"cat": "other", "name": "律动",           "url": "https://rsshub.dicomp.net/theblockbeats/newsflash"},
    {"cat": "other", "name": "产品经理",       "url": "http://www.woshipm.com/feed"},
    {"cat": "other", "name": "界面新闻",       "url": "https://a.jiemian.com/index.php?m=article&a=rss"},
    {"cat": "other", "name": "C114通信网",     "url": "http://www.c114.com.cn/rss/"},
]

# Color palette (mirrors JS)
PALETTE = ['#7c9aff','#ff7c7c','#7cffb0','#ffb347','#c97cff','#ff7cd4','#7cfff0','#ffd47c','#7c9aff','#7cff7c']

MAX_ITEMS = 20
TIMEOUT = 20


def fetch_url(url):
    """Fetch a URL and return the text content."""
    req = Request(url, headers={
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) RSS-Reader/1.0',
        'Accept': 'application/xml, text/xml, application/rss+xml, text/html, */*',
    })
    with urlopen(req, timeout=TIMEOUT) as resp:
        return resp.read().decode('utf-8', errors='replace')


def parse_rss(text):
    """Parse RSS/Atom XML and return list of articles."""
    articles = []
    try:
        root = ET.fromstring(text)
    except ET.ParseError:
        return articles

    # RSS 2.0
    channel = root.find('channel')
    if channel is not None:
        feed_title = channel.findtext('title', '')
        for item in channel.findall('item'):
            title = item.findtext('title', '')
            link = ''
            link_el = item.find('link')
            if link_el is not None:
                link = link_el.text or ''
            guid = item.findtext('guid', '')
            summary = item.findtext('description', '') or item.findtext('summary', '') or ''
            pub_date = item.findtext('pubDate', '') or item.findtext('dc:date', '')
            author = item.findtext('author', '') or item.findtext('dc:creator', '')
            # Strip HTML tags from summary
            import re
            plain_summary = re.sub(r'<[^>]*>', '', summary)[:300]
            articles.append({
                'title': title,
                'link': link or guid,
                'summary': plain_summary,
                'pubDate': pub_date,
                'author': author,
                'feedTitle': feed_title,
            })

    # Atom
    if not articles:
        feed = root.find('{http://www.w3.org/2005/Atom}feed')
        if feed is not None:
            feed_title = feed.findtext('{http://www.w3.org/2005/Atom}title', '')
            for entry in feed.findall('{http://www.w3.org/2005/Atom}entry'):
                title = entry.findtext('{http://www.w3.org/2005/Atom}title', '')
                link = ''
                link_el = entry.find('{http://www.w3.org/2005/Atom}link')
                if link_el is not None:
                    link = link_el.get('href', '')
                summary = entry.findtext('{http://www.w3.org/2005/Atom}summary', '') or entry.findtext('{http://www.w3.org/2005/Atom}content', '')
                pub_date = entry.findtext('{http://www.w3.org/2005/Atom}published', '') or entry.findtext('{http://www.w3.org/2005/Atom}updated', '')
                author_el = entry.find('{http://www.w3.org/2005/Atom}author')
                author = author_el.findtext('{http://www.w3.org/2005/Atom}name', '') if author_el is not None else ''
                import re
                plain_summary = re.sub(r'<[^>]*>', '', summary)[:300]
                articles.append({
                    'title': title,
                    'link': link,
                    'summary': plain_summary,
                    'pubDate': pub_date,
                    'author': author,
                    'feedTitle': feed_title,
                })

    return articles[:MAX_ITEMS]


def parse_date(date_str):
    """Parse a date string to ISO format."""
    if not date_str:
        return ''
    # Try common RSS date formats
    from email.utils import parsedate_to_datetime
    try:
        dt = parsedate_to_datetime(date_str)
        return dt.isoformat()
    except (ValueError, TypeError):
        pass
    # Try ISO format
    try:
        from dateutil import parser as dateparser
        return dateparser.parse(date_str).isoformat()
    except (ImportError, ValueError):
        pass
    return date_str


def main():
    # Build feed color mapping
    feed_colors = {}
    for i, feed in enumerate(FEEDS):
        feed_colors[feed['name']] = PALETTE[i % len(PALETTE)]

    # Fetch all feeds
    articles_by_cat = {cat['id']: [] for cat in CATEGORIES}
    total = len(FEEDS)
    success = 0
    fail = 0

    print(f"Fetching {total} RSS feeds...")

    for i, feed in enumerate(FEEDS):
        cat = feed['cat']
        name = feed['name']
        url = feed['url']
        color = feed_colors[name]

        try:
            text = fetch_url(url)
            items = parse_rss(text)
            for item in items:
                item['feedName'] = name
                item['feedColor'] = color
                # Parse date to ISO
                item['pubDate'] = parse_date(item['pubDate'])
            articles_by_cat[cat].extend(items)
            success += 1
            print(f"  [{i+1}/{total}] ✓ {name} ({len(items)} items)")
        except Exception as e:
            fail += 1
            print(f"  [{i+1}/{total}] ✗ {name}: {e}")

        # Small delay to be polite to servers
        time.sleep(0.3)

    # Build output
    output = {
        'updated': datetime.now(timezone.utc).isoformat(),
        'summary': {
            'total': total,
            'success': success,
            'fail': fail,
            'total_articles': sum(len(v) for v in articles_by_cat.values()),
        },
        'articles': articles_by_cat,
    }

    # Write data.json
    with open('data.json', 'w', encoding='utf-8') as f:
        json.dump(output, f, ensure_ascii=False, indent=2)

    print(f"\nDone! {success}/{total} feeds fetched, {output['summary']['total_articles']} articles total.")
    print(f"data.json written ({fail} failures)")


if __name__ == '__main__':
    main()