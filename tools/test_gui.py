"""Real Chrome GUI tests, isolated profiles; device UAs are simulations only."""
import json
import re
import threading
import time
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from playwright.sync_api import sync_playwright

ROOT=Path(__file__).resolve().parents[1]
SITE=ROOT
OUT=ROOT/'test-artifacts/round2'
OUT.mkdir(parents=True,exist_ok=True)
class Handler(SimpleHTTPRequestHandler):
    def log_message(self,*args): pass
    def do_GET(self):
        try:
            if self.path.split('?')[0].endswith('.mp4') and self.headers.get('Range'):
                path=Path(self.translate_path(self.path))
                if not path.is_file(): return super().do_GET()
                size=path.stat().st_size
                match=re.fullmatch(r'bytes=(\d+)-(\d*)',self.headers['Range'])
                if match:
                    start=int(match[1]); end=min(int(match[2]) if match[2] else size-1,size-1)
                    self.send_response(206)
                    self.send_header('Content-Type','video/mp4')
                    self.send_header('Accept-Ranges','bytes')
                    self.send_header('Content-Range',f'bytes {start}-{end}/{size}')
                    self.send_header('Content-Length',str(end-start+1))
                    self.end_headers()
                    with path.open('rb') as f:
                        f.seek(start); remaining=end-start+1
                        while remaining:
                            block=f.read(min(65536,remaining))
                            self.wfile.write(block); remaining-=len(block)
                    return
            super().do_GET()
        except (ConnectionResetError,BrokenPipeError): pass
server=ThreadingHTTPServer(('127.0.0.1',8772),partial(Handler,directory=str(SITE)))
threading.Thread(target=server.serve_forever,daemon=True).start()
BASE='http://127.0.0.1:8772/'
baseline_config=(SITE/'tools/fixtures/round2-baseline-config.js').read_text(encoding='utf-8')
report={'browser':'Real headed Chrome GUI on Windows','devices':'Viewport / UA simulation only; no physical iPhone, Android or WeChat devices tested','scenarios':[]}

def ready(page):
    page.wait_for_function("document.querySelector('.cover-bg').complete && document.querySelector('.cover-bg').naturalWidth>0")
def story(page):
    page.wait_for_function("document.getElementById('videowrap').hidden",timeout=22000)
    page.wait_for_function("document.getElementById('opening').classList.contains('prologue-running')")
def photo(page,n):
    page.locator(f'[data-index="{n}"]').evaluate('(el)=>el.scrollIntoView({behavior:"instant"})')
    page.wait_for_function(f"document.querySelector('[data-index=\"{n}\"] img').dataset.state==='loaded'")
    page.wait_for_timeout(150)

with sync_playwright() as p:
    browser=p.chromium.launch(executable_path=r'C:\Program Files\Google\Chrome\Application\chrome.exe',headless=False)
    for width,height in [(390,844),(375,667),(320,568),(1440,900)]:
        name=f'{width}x{height}'
        ctx=browser.new_context(viewport={'width':width,'height':height},is_mobile=width<600,has_touch=width<600)
        page=ctx.new_page(); errors=[]; requests=[]
        page.on('pageerror',lambda e:errors.append(str(e)))
        page.on('request',lambda r:requests.append(r.url.removeprefix(BASE)))
        try:
            page.goto(BASE,wait_until='networkidle'); ready(page)
            assert not any('opening.mp4' in r or 'video.mp4' in r for r in requests)
            page.screenshot(path=str(OUT/f'{name}-cover.png'))
            old=page.evaluate('() => {'+baseline_config+'; return CONFIG.memories}')
            new=page.evaluate('CONFIG.memories')
            assert len(new)==12 and all(old[i]==new[i] for i in range(12) if i not in [8,10])
            assert page.locator('video').count()==1 and page.locator('.videoblock').count()==0
            page.locator('#cover').click()
            page.wait_for_function("document.getElementById('openingVideo').currentTime>.25 && !document.getElementById('openingVideo').paused")
            assert page.evaluate("!document.getElementById('openingVideo').muted && document.getElementById('openingVideo').volume===1")
            assert not page.evaluate('prologueStarted')
            page.screenshot(path=str(OUT/f'{name}-playing.png'))
            if width!=390: page.locator('#videoSkip').click()
            story(page)
            page.wait_for_timeout(650)
            page.screenshot(path=str(OUT/f'{name}-prologue-start.png'))
            page.wait_for_timeout(2100)
            assert float(page.locator('.bc-sub').evaluate('(el)=>getComputedStyle(el).opacity'))>.99
            page.screenshot(path=str(OUT/f'{name}-prologue.png'))
            # Actual GUI wheel input before programmatically aligning individual chapters.
            page.mouse.wheel(0,height*2)
            page.wait_for_timeout(300)
            for n in range(1,13):
                photo(page,n)
                assert not page.evaluate('document.documentElement.scrollWidth > innerWidth')
                if n in [1,5,6,9,11,12]:
                    page.wait_for_timeout(1250)
                    page.screenshot(path=str(OUT/f'{name}-chapter-{n:02}.png'))
                    bounds=page.locator(f'[data-index="{n}"]').evaluate('''el => {
                      const text=el.querySelector('.pt-text,.m-text,.f-sub');
                      const r=text.getBoundingClientRect(); return {top:r.top,bottom:r.bottom,height:innerHeight};
                    }''')
                    assert bounds['top']>=0 and bounds['bottom']<=height+2,(name,n,bounds)
            page.locator('#letterwrap').scroll_into_view_if_needed()
            page.wait_for_timeout(250)
            page.screenshot(path=str(OUT/f'{name}-letter.png'))
            assert page.evaluate("getComputedStyle(document.getElementById('replay')).pointerEvents==='none'")
            assert not any(re.search(r'(^|/)video\.mp4',r) for r in requests)
            # Scrolling back does not restart the prologue.
            assert page.evaluate('prologueStarted')
            page.locator('#opening').evaluate('(el)=>el.scrollIntoView()')
            page.wait_for_timeout(100)
            assert page.locator('.intro-piece').first.evaluate("el=>el.getAnimations().every(a=>a.playState==='finished')")
            page.locator('#replay').click()
            page.wait_for_function("document.getElementById('openingVideo').currentTime>.1 && !document.getElementById('openingVideo').paused")
            assert not page.evaluate('prologueStarted')
            page.locator('#videoSkip').click(); story(page)
            assert page.locator('[data-index]').count()==12
            assert not errors,errors
            report['scenarios'].append({'viewport':name,'result':'pass','natural_completion':width==390,'skip_replay':True,'javascript_errors':errors,'requests':requests})
            print('PASS GUI',name,flush=True)
        except Exception:
            page.screenshot(path=str(OUT/f'{name}-FAIL.png'))
            raise
        finally: ctx.close()

    def scenario(name,setup,check):
        ctx=browser.new_context(viewport={'width':390,'height':844})
        page=ctx.new_page()
        try:
            setup(page)
            page.goto(BASE); ready(page)
            check(page)
            page.screenshot(path=str(OUT/f'{name}.png'))
            report['scenarios'].append({'name':name,'result':'pass'})
            print('PASS',name,flush=True)
        finally: ctx.close()
    def fail_video(page):
        page.locator('#cover').click(); story(page)
        assert page.evaluate("!document.documentElement.classList.contains('video-open')")
    scenario('missing-opening',lambda page:page.route('**/opening.mp4',lambda r:r.fulfill(status=404,body='missing')),fail_video)
    scenario('playback-denied',lambda page:page.add_init_script("HTMLMediaElement.prototype.play=function(){return Promise.reject(new DOMException('blocked','NotAllowedError'))}"),fail_video)
    scenario('playback-stalled',lambda page:page.add_init_script("HTMLMediaElement.prototype.play=function(){return new Promise(()=>{})}"),fail_video)

    def early_scroll(page):
        page.locator('#cover').click();page.locator('#videoSkip').click();story(page)
        page.mouse.wheel(0,1200)
        page.wait_for_function('scrollY>500')
        assert page.evaluate('prologueStarted')
    scenario('no-forced-wait',lambda page:None,early_scroll)

    def fade_replay(page):
        page.locator('#cover').click()
        page.wait_for_function("document.getElementById('openingVideo').currentTime>.1")
        page.evaluate('endOpening(false)')
        page.evaluate('playOpening()')
        page.wait_for_timeout(900)
        assert page.evaluate("!document.getElementById('videowrap').hidden")
        page.locator('#videoSkip').click();story(page)
    scenario('old-fade-does-not-hide-replay',lambda page:None,fade_replay)

    for ua_name,ua in [
        ('iphone-safari-simulated','Mozilla/5.0 (iPhone; CPU iPhone OS 18_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/18.0 Mobile/15E148 Safari/604.1'),
        ('android-chrome-simulated','Mozilla/5.0 (Linux; Android 14; Pixel 7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Mobile Safari/537.36'),
        ('wechat-simulated','Mozilla/5.0 (Linux; Android 14; Pixel 7) AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0 Chrome/131.0.0.0 Mobile Safari/537.36 MicroMessenger/8.0.54')]:
        ctx=browser.new_context(viewport={'width':390,'height':844},is_mobile=True,has_touch=True,user_agent=ua)
        page=ctx.new_page();page.goto(BASE);ready(page);page.locator('#cover').click()
        page.wait_for_function("document.getElementById('openingVideo').currentTime>.1 && !document.getElementById('openingVideo').paused")
        page.locator('#videoSkip').click();story(page)
        page.screenshot(path=str(OUT/f'{ua_name}.png'));ctx.close()
        report['scenarios'].append({'name':ua_name,'result':'pass','engine':'Windows Chrome; UA simulation, not real Safari/WeChat'})
        print('PASS',ua_name,flush=True)
    ctx=browser.new_context(viewport={'width':320,'height':568},reduced_motion='reduce')
    page=ctx.new_page();page.goto(BASE);ready(page);page.locator('#cover').click();page.locator('#videoSkip').click();story(page)
    assert page.locator('.intro-piece').first.evaluate("el=>getComputedStyle(el).opacity==='1' && getComputedStyle(el).animationName==='none'")
    page.screenshot(path=str(OUT/'reduced-motion.png'));ctx.close()
    report['scenarios'].append({'name':'reduced-motion','result':'pass'})
    browser.close()
server.shutdown()
(OUT/'results.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
print('ALL PASS',len(report['scenarios']),'scenarios')
