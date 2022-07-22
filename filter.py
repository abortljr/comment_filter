import sys, regex as re, requests, pymorphy2
from lxml.html import fromstring, parse, submit_form
from django.conf import settings
from django.template.loader import get_template
from datetime import datetime, timedelta
from django.utils import timezone
from copy import copy
from hashlib import md5
from smtplib import SMTP_SSL
from email.mime.text import MIMEText

from settings_private import *

import django
django.setup()

from comments.models import *


smtp = None
template = None
subject_template = None

def test_spam(comment):
    return re.findall(TEST_RE, comment.text, re.IGNORECASE)

LJR_URL = 'http://lj.rossia.org/'
UNITS = dict(months=30, monthes=30, years=365)

regexes = [re.compile(w) for w in WORDS.split()]

morph = pymorphy2.MorphAnalyzer()

s = requests.Session()

while True:
    resp = s.get(LJR_URL + 'tools/recent_comments.bml')
    if not resp.ok:
        r=s.get(LJR_URL + 'login.bml')
        doc=fromstring(r.text)
        doc.make_links_absolute(LJR_URL)
        form=doc.forms[0]
        form.fields['user'] = USERNAME
        form.fields['password'] = ''
        form.fields['response'] = md5(form.fields['chal'].encode('utf-8') + md5(PASSWORD.encode('utf-8')).hexdigest().encode('utf-8')).hexdigest()
        response = submit_form(form, open_http=s.request)
        r = s.post(LJR_URL + 'login.bml', dict(form.fields))
        if not r.ok:
            print("Cannot login")
            sys.exit(-1)
        continue
    break

doc=fromstring(resp.text)
for tr in doc.xpath('//tr[@id]'): 
    author = tr.xpath('string(td[1]/span[@class="ljuser"]/a/b)')
    if not author and not tr.xpath('td[1]/text()[1] = "Anonymous"'):
        continue
    ago = tr.xpath('string(td[1]/br[1]/following-sibling::text()[1])')
    delta, units = ago.split(' ')[:2]
    delta = int(delta)
    if units[-1] != 's':
        units += 's'
    if units in UNITS:
        delta = timedelta(days=UNITS[units]*delta)
    else:
        delta = timedelta(**{units: delta})
    comment, created = Comment.objects.get_or_create(cmtid=tr.attrib['id'][8:], 
            defaults=dict(postid=tr.xpath('substring-before(td[2]/strong[position() <= 2]/a/@href, ".html")').split('/')[-1],
            screened=tr.xpath('contains(td[1]/a/img[@alt="Screen"]/@src, "btn_unscr")'),
            subject=tr.xpath('string(td[2]/br[1]/following-sibling::br[1]/following-sibling::cite[1])'),
            author=author or None,
            date=timezone.now() - delta,
            text='\n'.join(tr.xpath('(td[2]/text()|td[2]/*)[preceding-sibling::strong/a and following-sibling::text() = "("]/descendant-or-self::text()'))))
    if not created or author == USERNAME and not EMAIL_OWN:
        continue

    if USE_EMAIL and EMAIL and SMTP_HOST:
        if smtp is None:
            smtp = SMTP_SSL(SMTP_HOST, SMTP_PORT)
            if SMTP_USERNAME and SMTP_PASSWORD:
                smtp.login(SMTP_USERNAME, SMTP_PASSWORD)
        if template is None:
            template = get_template('email.txt')
        if subject_template is None:
            subject_template = get_template('subject.txt')
        ctx = copy(vars(comment))
        ctx['me'] = USERNAME
        mime = MIMEText(template.render(ctx).encode('utf-8'), _charset='utf-8')
        mime['Subject'] = subject_template.render(ctx) #'LJR comment' + (' from ' + comment.author if comment.author else '') + (' -- ' + comment.subject if comment.subject else '')
        mime['From'] = SMTP_EMAIL
        mime['To'] = EMAIL

        smtp.sendmail(SMTP_EMAIL, [EMAIL], mime.as_string())

    if author and FILTER_ANONYMOUS_ONLY:
        continue

    
    todelete = tofreeze = False
    if test_spam(comment):
        tofreeze = True
    for word in re.split(r'[[:blank:][:punct:]\n]+', comment.text):
        if re.match('^\p{L}+$', word) and not (re.match('^\p{Latin}+$', word) or re.match('^[\p{Cyrillic}i]+$', word)):
            tofreeze = True
        for m in morph.parse(word):
            for re1 in regexes:
                if re1.match(m.normal_form) and m.tag.POS == 'NOUN':
                    todelete = True

    if todelete:
        print("Delete:", comment.text)

    if tofreeze:
        print("Freeze:", comment.text)

    if tofreeze or todelete:
        print(s.post(f'{LJR_URL}talkscreen.bml?mode=screen&journal={USERNAME}&talkid={comment.cmtid}&jsmode=1', dict(confirm='Y')).text)
