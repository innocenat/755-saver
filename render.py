import json
import os, os.path
from datetime import datetime, timezone, timedelta
import html
import re

JST = timezone(timedelta(hours=9))

PATH = 'saved/{}'

URL = re.compile('((?:(?:https?|ftp|file):\/\/|www\.|ftp\.)(?:\([-A-Z0-9+&@#\/%=~_|$?!:,.]*\)|[-A-Z0-9+&@#\/%=~_|$?!:,.])*(?:\([-A-Z0-9+&@#\/%=~_|$?!:,.]*\)|[A-Z0-9+&@#\/%=~_|$]))', re.I)

def render_sidebar(ml):
    ly = '0000'
    out = '<ul>'
    for m in ml:
        if m[0:4] != ly:
            if ly != '0000':
                out += '</ul></li>'
            out += '<li><strong>{}年</strong><ul>'.format(m[0:4])
            ly = m[0:4]
        out += '<li><a href="{}.html">{}年{}月</a></li>'.format(m, m[0:4], m[5:])
    out += '</ul>'
    return out


def render_body(body):
    out = ''
    cls = ''

    if isinstance(body, list):
        for b in body:
            so, _ = render_body(b)
            out += so
        cls = 'cb'
    elif 'text' in body:
        c = URL.sub('<a href="\\1" target="_blank">\\1</a>', html.escape(body['text']))
        out = '<div>{}</div>'.format(c)
        cls = 'txt'
    elif 'sticker' in body:
        out = '<img src="../{}" class="img-stk">'.format(body['sticker'])
        cls = 'stk'
    elif 'image' in body:
        out = '<img src="../{}" class="img-img">'.format(body['image'])
        cls = 'image'
    elif 'comment' in body:
        ts = datetime.fromtimestamp(body['time'], JST)
        c = URL.sub('<a href="\\1" target="_blank">\\1</a>', html.escape(body['comment']))
        out = '''
        <div class="post post-qa">
            <header class="post-qa-head">
                <div class="post-qa-name post-name">{}</div>
                <div class="post-qa-time post-time">{}</div>
            </header>
            <div class="post-qa-body post-txt">{}</div>
        </div>
        '''.format(html.escape(body['name']), ts.strftime('%Y-%m-%d %-H:%M'), c)
        cls = 'qa'
    elif 'video' in body:
        out = '<video controls src="../{}" class="vid"></video>'.format(body['video'])
        cls = 'video'
    elif 'url' in body:
        out = '<div><a href="{0}" target="_blank">{0}</a></div>'.format(body['url'])
        cls = 'txt'
    return out, cls


def render_html(m, posts, ml):
    output = '''
<!doctype html>
<html lang="jp">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>Subtitle Editor</title>
    <style>
    body {
        font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
        margin: 0;
        padding: 0;
        line-height: 1.6;
        font-size: 18px;
        color: #444;
        background: #eee;
    }
    div {
        margin: 0;
        padding: 0;
    }
    .container {
        display: flex;
        justify-content: center;
        flex-wrap: wrap;
    }
    .container-head {
        width: 100%;
        background: #ec5785;
    }
    .header {
        text-align: center;
        font-weight: bold;
        color: #fff;
        font-size: 180%;
        padding: 0.5em;
    }
    .container-body {
        margin-top: 1em;
    }
    .navbar {
        width: 100%;
        max-width: 200px;
        padding: 15px;
    }
    .content {
        width: 100%;
        max-width: 550px;
    }
    h1 {
        font-size: 150%;
        margin: 15px;
        border-bottom: 1px solid #444;
    }
    nav ul {
        list-style-type: none;
        margin: 0;
        padding: 0;
    }
    nav span {
        display: block;
        margin-top: 15px;
        font-size: 120%;
        font-weight: bold;
    }
    nav a {
        display: inline-block;
        color: #ec5785;
        padding: 5px 0;
        text-decoration: none;
        margin: 5px 0 0 15px;
        padding: 2px 5px;
    }
    nav a:hover {
        text-decoration: underline;
    }
    .post {
        padding: 1em;
    }
    .post header {
        font-size: 90%;
        color: #555;
        display: flex;
        justify-content: flex-start;
        align-items: center;
    }
    .post header div {
        margin-right: 1em;
    }
    .post-time {
        font-size: 90%;
    }
    img, video {
        display: block;
    }
    img.img-stk {
        width: 50%;
        max-width: 150px;
        height: auto;
    }
    img.img-img, video {
        width: 100%;
        height: auto;
    }
    main.post-content {
        border-radius: 0.5em;
    }
    main.post-txt, main.post-cb, main.post-qa, main.post-rt {
        background: #fff;
        word-break: break-all;
    }
    main.post-content > div {
        padding: 1em;
    }
    main.post-orig-content > div:not(.post-qa) {
        padding: 1em 0;
    }
    .post-content > img:first-child, .post-content > video:first-child {
        border-radius: 0.5em 0.5em 0 0;
    }
    .post-video video, .post-image img {
        border-radius: 0.5em !important;
    }
    main.post-stk {
        padding: 1.5em 1em;
    }
    .post-rt > :not(.post-orig-image):not(.post-orig-video):not(.post-orig-stk) {
        padding-bottom: 0;
    }
    .post-qa {
        background: #ddd;
        border-radius: 0.5em 0.5em 0 0
    }
    .post-qa-head {
        margin-bottom: 0.5em;
    }
    .post footer {
        display: flex;
        justify-content: flex-start;
        font-size: 80%;
    }
    .post footer span {
        margin: 0 0.25em;
    }
    .post footer b {
        font-size: 80%;
        color: #555;
        font-variant: small-caps;
        font-weight: normal;
    }
    </style>
</head>
<body>
<div class="container container-head">
    <header class="header">
        755 Archive
    </header>
</div>
<div class="container container-body">
    <main class="content">
'''
    output += '<h1>{}年{}月</h1>'.format(m[0:4], m[5:])
    for post in posts:
        pid = post['id']
        ts = datetime.fromtimestamp(post['time'], JST)
        name = post['name']
        if 'original' in post:
            # Is a retweet
            orig = post['original']
            rts = datetime.fromtimestamp(orig['time'], JST)
            rt_body, rt_bcls = render_body(orig['content'])
            bcls = 'rt'
            body = '''
                <div class="post-orig post-orig-{}">
                    <header>
                        <div class="post-name">RT: {}</div>
                        <div class="post-time" title={}>{}</div>
                    </header>
                    <main class="post-content post-{} post-orig-content">
                        {}
                    </main>
                </div>
            '''.format(rt_bcls, html.escape(orig['name']), orig['id'], rts.strftime('%Y-%m-%d %-H:%M'), rt_bcls, rt_body)
            rtC, lC, cC = orig['rtCount'], orig['likeCount'], orig['commentCount']
        else:
            body, bcls = render_body(post['content'])
            rtC, lC, cC = post['rtCount'], post['likeCount'], post['commentCount']
        output += '''
        <div class="post">
            <header>
                <div class="post-name">{}</div>
                <div class="post-time" title={}>{}</div>
            </header>
            <main class="post-content post-{}">
                {}
            </main>
            <footer>
                <span><b>RT:</b> {}</span>
                <span><b>Like:</b> {}</span>
                <span><b>Comment:</b> {}</span>
            </footer>
        </div>
'''.format(html.escape(name), pid, ts.strftime('%Y-%m-%d %-H:%M'), bcls, body, rtC, lC, cC)
    output += '''
    </main>
    <nav class="navbar">
        {}
    </nav>
</div>
</body>
</html>
'''.format(render_sidebar(ml))
    return output

def sort_by_month(posts):
    months = {}
    for post in posts:
        if 'time' not in post:
            continue
        ts = datetime.fromtimestamp(post['time'], JST)
        k = '{:0>4d}-{:0>2d}'.format(ts.year, ts.month)
        if k in months:
            months[k].append(post)
        else:
            months[k] = [post]
    return months


def render(name):
    d = PATH.format(name)
    infile = d + '/posts.json'
    outfile = d + '/html'
    if not os.path.exists(outfile):
        os.makedirs(outfile)
    data = []
    with open(infile) as fp:
        data = json.load(fp)
    months = sort_by_month(data)
    sorted_month = list(sorted(months.keys()))
    for month in sorted_month:
        out = render_html(month, months[month], sorted_month)
        with open('{}/{}.html'.format(outfile, month), 'w') as fp:
            fp.write(out)
    
if __name__ == '__main__':
    import sys
    if len(sys.argv) < 2:
        print('Usage: python render.py talk_id')
    else:
        print('Rendering {}...'.format(sys.argv[1]))
        render(sys.argv[1])
