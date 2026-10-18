"""Render native Draw.io XML, including embedded vector stencils, with mxGraph."""
from pathlib import Path
import argparse
import base64
import json
import os
import re
import subprocess
import uuid
import xml.etree.ElementTree as ET
import zlib
from PIL import Image
import tempfile
BASE = Path(__file__).resolve().parent.parent
OUT = BASE / '配图'
WORK = None


def render(number):
    source=next(OUT.glob(f'图{number}-*.drawio'))
    work=WORK/f'figure-{number}'
    work.mkdir(exist_ok=True)
    model=ET.parse(source).find('.//mxGraphModel')
    width=int(float(model.get('pageWidth')));height=int(float(model.get('pageHeight')))
    encoded=base64.b64encode(ET.tostring(model,encoding='utf-8')).decode()
    stencils={}
    geometry={}
    for c in model.findall('.//mxCell'):
        style=dict(p.split('=',1) for p in c.get('style','').split(';') if '=' in p)
        shape=style.get('shape','')
        if shape.startswith('stencil('):stencils[shape]=zlib.decompress(base64.b64decode(shape[8:-1]),-15).decode()
        if c.get('vertex'):
            g=c.find('mxGeometry');geometry[c.get('id')]=[float(g.get(k,'0')) for k in ('x','y','width','height')]
    js=(BASE/'维护工具/lib/mxClient.js').as_uri()
    page='''<!doctype html><meta charset="utf-8"><style>html,body{margin:0;padding:0;background:white;overflow:hidden}#graph{width:WIDTHpx;height:HEIGHTpx}svg{overflow:visible}</style><script>var mxLoadResources=false;var mxLoadStylesheets=false;</script><script src="JSPATH"></script><div id="graph"></div><script>
try {
for(const [name,xml] of Object.entries(STENCILS))mxStencilRegistry.addStencil(name,new mxStencil(mxUtils.parseXml(xml).documentElement));
const graph=new mxGraph(document.getElementById('graph'));graph.setEnabled(false);graph.setHtmlLabels(false);
new mxCodec(mxUtils.parseXml(new TextDecoder().decode(Uint8Array.from(atob('ENCODED'),c=>c.charCodeAt(0))))).decode(mxUtils.parseXml(new TextDecoder().decode(Uint8Array.from(atob('ENCODED'),c=>c.charCodeAt(0)))).documentElement,graph.getModel());graph.refresh();
const target=document.implementation.createDocument('http://www.w3.org/2000/svg','svg',null),svg=target.documentElement;
svg.setAttribute('xmlns','http://www.w3.org/2000/svg');svg.setAttribute('width','172mm');svg.setAttribute('height','MMHEIGHTmm');svg.setAttribute('viewBox','0 0 WIDTH HEIGHT');
const bg=target.createElementNS('http://www.w3.org/2000/svg','rect');bg.setAttribute('width','WIDTH');bg.setAttribute('height','HEIGHT');bg.setAttribute('fill','white');svg.appendChild(bg);
new mxImageExport().drawState(graph.getView().getState(graph.model.root),new mxSvgCanvas2D(svg));
const el=document.createElement('script');el.id='svg-export';el.type='application/json';el.textContent=JSON.stringify(new XMLSerializer().serializeToString(svg));document.body.appendChild(el);
const boxes=[];Object.values(graph.model.cells).forEach(c=>{let st=graph.view.getState(c);if(st&&st.text&&st.text.boundingBox){let b=st.text.boundingBox;boxes.push({id:c.id,text:c.value,x:b.x,y:b.y,w:b.width,h:b.height});}});
const m=document.createElement('script');m.id='text-metrics';m.type='application/json';m.textContent=JSON.stringify(boxes);document.body.appendChild(m);document.body.dataset.renderStatus='ok';
}catch(e){document.body.dataset.renderStatus='error';document.body.append(String(e));}
</script>'''
    page=page.replace('MMHEIGHT',str(172*height/width)).replace('WIDTH',str(width)).replace('HEIGHT',str(height)).replace('JSPATH',js).replace('STENCILS',json.dumps(stencils)).replace('ENCODED',encoded)
    html_path=work/'render.html';html_path.write_text(page,encoding='utf-8')
    profile=work/('chrome-'+uuid.uuid4().hex);profile.mkdir()
    shot=work/'native.png'
    args=['C:/Program Files/Google/Chrome/Application/chrome.exe','--headless=new','--disable-gpu','--disable-extensions','--no-first-run','--no-default-browser-check','--disable-background-networking','--hide-scrollbars','--force-device-scale-factor=2',f'--window-size={width},{height+120}','--virtual-time-budget=1000','--user-data-dir='+str(profile.resolve()),'--screenshot='+str(shot.resolve()),'--dump-dom',html_path.resolve().as_uri()]
    result=subprocess.run(args,capture_output=True,timeout=55,creationflags=subprocess.CREATE_NO_WINDOW if os.name=='nt' else 0)
    dom=result.stdout.decode('utf-8',errors='replace')
    (work/'render.log').write_text(result.stderr.decode('utf-8',errors='replace'),encoding='utf-8')
    assert result.returncode==0 and 'data-render-status="ok"' in dom,dom[-2000:]
    svg=json.loads(re.search(r'<script id="svg-export" type="application/json">(.*?)</script>',dom,re.S)[1]);ET.fromstring(svg)
    source.with_suffix('.svg').write_text(svg,encoding='utf-8')
    metrics=json.loads(re.search(r'<script id="text-metrics" type="application/json">(.*?)</script>',dom,re.S)[1])
    overflow=[]
    for b in metrics:
        if b['id'] not in geometry:continue
        x,y,w,h=geometry[b['id']]
        if b['x']<x-4 or b['y']<y-4 or b['x']+b['w']>x+w+4 or b['y']+b['h']>y+h+4:overflow.append(b)
    im=Image.open(shot).convert('RGB').crop((0,0,width*2,height*2))
    im.save(source.with_suffix('.png'),dpi=(im.width/(172/25.4),)*2)
    im.thumbnail((1800,1800));im.save(OUT/(source.stem+'-预览.png'))
    info={'figure':number,'canvas':[width,height],'stencil_types':len(stencils),'metrics':metrics,'overflow':overflow}
    (work/'render-record.json').write_text(json.dumps(info,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps({k:v for k,v in info.items() if k!='metrics'},ensure_ascii=False))
    return info


if __name__=='__main__':
    p=argparse.ArgumentParser()
    p.add_argument('--figures', default='1,2,3,4,5,6')
    a=p.parse_args()
    numbers=[int(n) for n in a.figures.split(',')]
    assert all(1 <= n <= 6 for n in numbers)
    with tempfile.TemporaryDirectory(prefix='llm-figure-export-') as folder:
        WORK=Path(folder)
        for n in numbers:
            render(n)
            source=next(OUT.glob(f'图{n}-*.drawio'))
            (OUT/'图片').mkdir(exist_ok=True)
            for ext in ('.png','.svg'):
                source.with_suffix(ext).replace(OUT/'图片'/source.with_suffix(ext).name)
            (OUT/(source.stem+'-预览.png')).unlink(missing_ok=True)
