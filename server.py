"""Local-only dashboard with atomic data updates, file parsing and SQL previews."""
import csv
import io
import json
import os
import re
import secrets
import sqlite3
import threading
from copy import deepcopy
from datetime import date, datetime
from pathlib import Path

from flask import Flask, Response, jsonify, request, send_file
from openpyxl import Workbook, load_workbook
from src.model import FIELDS, aggregate, demo, validate
from src.source_guide import render_source_guide

ROOT=Path(__file__).resolve().parent
PUBLIC_DEPLOY=os.environ.get('DASHBOARD_DEPLOY')=='1'
ADMIN_USER=os.environ.get('DASHBOARD_USER','admin')
ADMIN_PASSWORD=os.environ.get('DASHBOARD_PASSWORD','')
ALLOWED_HOSTS={h.strip().lower() for h in os.environ.get('DASHBOARD_ALLOWED_HOSTS',os.environ.get('RENDER_EXTERNAL_HOSTNAME','')).split(',') if h.strip()}
if PUBLIC_DEPLOY and (len(ADMIN_PASSWORD)<16 or not ALLOWED_HOSTS):
    raise RuntimeError('Cloud deployment requires a password of at least 16 characters and allowed hostnames.')
DATA=Path(os.environ.get('DASHBOARD_DATA_DIR',str(ROOT/'local-data'))).resolve()
DATA.mkdir(exist_ok=True)
STATE=DATA/'current.json'
TOKEN=secrets.token_urlsafe(32)
LOCK=threading.RLock()
app=Flask(__name__)
app.config['MAX_CONTENT_LENGTH']=24*1024*1024

def initial():
    tables={}
    for name in FIELDS:
        with (ROOT/'data'/f'{name}.csv').open(encoding='utf-8-sig',newline='') as f:
            tables[name]=list(csv.DictReader(f))
    return {'version':1,'tables':validate(tables),'sources':{k:'内置模拟CSV' for k in FIELDS}}
def read_state(): return json.loads(STATE.read_text(encoding='utf-8')) if STATE.exists() else initial()
def persist(value):
    temp=STATE.with_suffix('.tmp')
    temp.write_text(json.dumps(value,ensure_ascii=False,allow_nan=False),encoding='utf-8')
    os.replace(temp,STATE)
if not STATE.exists(): persist(initial())

def init_sqlite():
    path=DATA/'demo.sqlite'
    if path.exists(): return
    conn=sqlite3.connect(path)
    for table,rows in demo().items():
        fields=FIELDS[table]
        definitions=','.join('"'+k+'" '+('REAL' if isinstance(rows[0][k],(int,float)) else 'TEXT') for k in fields)
        conn.execute(f'CREATE TABLE "{table}" ({definitions})')
        conn.executemany(f'INSERT INTO "{table}" VALUES ({",".join("?" for _ in fields)})',[[r[k] for k in fields] for r in rows])
    conn.commit(); conn.close()
init_sqlite()

@app.before_request
def protect():
    if request.path=='/api/health' and request.method=='GET': return None
    hostname=request.host.split(':')[0].lower()
    if PUBLIC_DEPLOY:
        if hostname not in ALLOWED_HOSTS: return jsonify(error='Host not allowed'),403
        auth=request.authorization
        valid=auth and auth.type=='basic' and secrets.compare_digest((auth.username or '').encode(),ADMIN_USER.encode()) and secrets.compare_digest((auth.password or '').encode(),ADMIN_PASSWORD.encode())
        if not valid:
            return Response('Authentication required',401,{'WWW-Authenticate':'Basic realm="Personal Dashboard", charset="UTF-8"','Cache-Control':'no-store'})
    elif hostname not in ('127.0.0.1','localhost'): return jsonify(error='仅允许本机访问'),403
    if request.method=='POST' and not secrets.compare_digest(request.headers.get('X-Local-Token',''),TOKEN): return jsonify(error='页面已过期，请刷新'),403

@app.after_request
def response_headers(response):
    response.headers['X-Content-Type-Options']='nosniff'
    response.headers['X-Frame-Options']='DENY'
    response.headers['Referrer-Policy']='same-origin'
    if request.path.startswith('/api/') or request.path=='/': response.headers['Cache-Control']='no-store'
    return response

@app.errorhandler(Exception)
def error(exc):
    from werkzeug.exceptions import HTTPException
    if isinstance(exc,HTTPException): return jsonify(error=exc.description),exc.code
    if isinstance(exc,(ValueError,KeyError,TypeError)): return jsonify(error=str(exc)),400
    # Connection errors may include credentials; never return them verbatim.
    return jsonify(error='操作失败。请检查文件格式或连接参数；数据库需只读账户和可用驱动。'),400

def render_html(state):
    html=ROOT.joinpath('src/dashboard.html').read_text(encoding='utf-8')
    payload=aggregate(state['tables'])
    months=sorted({r['month'] for r in payload['datasets']['module_01_overview']})
    encoded=json.dumps(payload,ensure_ascii=False,allow_nan=False).replace('<','\\u003c')
    html=re.sub(r'(<script id="dashboard-data" type="application/json">).*?(</script>)',lambda m:m[1]+encoded+m[2],html,flags=re.S)
    html=html.replace('const MONTHS=["2026-01","2026-02","2026-03","2026-04"];','const MONTHS='+json.dumps(months)+';')
    html=html.replace('month:"2026-04"','month:MONTHS[MONTHS.length-1]')
    html=html.replace('`2026 年 ${monthLabel(m)}`','`${m.slice(0,4)} 年 ${monthLabel(m)}`')
    html=html.replace('state.month==="2026-01"','state.month===MONTHS[0]')
    html=html.replace('TikTok UK 经营监控仪表盘','国内电商经营分析看板')
    simulated=sum('模拟' in s for s in state['sources'].values())
    source_label='全部模拟数据' if simulated==len(FIELDS) else '混合数据源（含模拟）' if simulated else '用户数据源'
    html=html.replace('2026 年 1–4 月',months[0]+' 至 '+months[-1]+' · '+source_label)
    html=html.replace('buyer_username','customer_id')
    html=html.replace('平台归因口径：抖系、淘系、京系可能重叠','订单渠道归因：抖系、淘系、京系互斥')
    html=html.replace('渠道可能重叠，不与管理 GMV 加总对账。','本地订单渠道互斥，各渠道金额可与全店 GMV 对账。')
    html=html.replace('渠道可能重叠。','本地订单渠道互斥。')
    html=html.replace('金额不与管理 GMV 加总对账。','三个渠道金额可与管理 GMV 对账。')
    html=html.replace('订单月回挂 / 分摊','订单明细净收入汇总').replace('仅已匹配结算订单','导入的订单明细净收入')
    html=html.replace('客户标识已脱敏；','模拟统一客户 ID；不代表平台间可识别同一用户。')
    html=html.replace('匹配 Net Sales','订单净收入').replace('1 月左截断','观察窗首月左截断')
    html=html.replace('</nav>','<button class="tab" type="button" role="tab" data-page="sources" aria-selected="false">数据源</button></nav>',1)
    html=html.replace('</main>',ROOT.joinpath('src/sources.html').read_text(encoding='utf-8').replace('<!-- SOURCE_GUIDE -->',render_source_guide(state))+'</main>',1)
    html=html.replace('</head>','<link rel="stylesheet" href="/sources.css"></head>')
    # Preserve all original SVG rendering; expose only refresh and navigation hooks.
    info_patch='''Object.values(INFO).forEach(info=>info.source="本地 orders 表聚合");
      ["ctr","cvr","impressions","page_views","unique_page_views","unique_customers"].forEach(k=>{if(INFO[k])INFO[k].source="本地 traffic 表"});
      INFO.target.source="本地 targets 与 orders 表"; INFO.currency.source="人民币字段契约 · 学习模拟";
      Object.assign(INFO.gmv,{concept:"按订单创建月汇总导入的明细 GMV；本地订单渠道互斥。",formula:"SUM(orders.gmv_cny)"});
      Object.assign(INFO.net_sales,{concept:"订单明细提供的净收入；未接入原始结算账单匹配。保留原版渠道视图的净收入空值展示。",formula:"SUM(orders.net_sales_cny)"});
      Object.assign(INFO.product_gmv_share,{concept:"选中月份当前产品范围的 GMV 占比。产品名称来自导入表，导入时校验必填。"});
      '''
    html=html.replace('initFilters();decorateInfo();renderAll();',info_patch+'initFilters();decorateInfo();renderAll(); window.dashboardPage=setPage; if(location.hash==="#sources")setPage("sources");')
    missing=[r for r in payload['datasets']['module_08_channel_conversion'] if r.get('impressions') is None]
    # Missing traffic must not masquerade as zero or fabricated conversion.
    if missing:
        html=html.replace('multiLine($("channel-customers"),rows,"unique_customers","各渠道客户数月趋势");','multiLine($("channel-customers"),rows,"unique_customers","各渠道客户数月趋势"); ["channel-rate-columns","channel-impressions","channel-pageviews","channel-unique-pageviews","channel-customers"].forEach(id=>$(id).innerHTML=\'<div class="empty">流量表不完整，请在数据源补充月份 × 产品 × 渠道数据后查看转化图表。</div>\');')
    meta={'token':TOKEN,'fields':FIELDS,'demoDatabase':str(DATA/'demo.sqlite')}
    html=html.replace('</body>','<script>window.SOURCE_CONFIG='+json.dumps(meta,ensure_ascii=False).replace('<','\\u003c')+';</script><script src="/sources.js"></script></body>')
    return html

@app.get('/')
def index():
    with LOCK: html=render_html(read_state())
    return Response(html,mimetype='text/html',headers={'Cache-Control':'no-store'})

@app.get('/<name>')
def asset(name):
    if name not in ['sources.js','sources.css']: return '',404
    return send_file(ROOT/'src'/('dashboard.css' if name=='sources.css' else name))

@app.get('/api/state')
def state():
    with LOCK: value=read_state()
    return jsonify(value)

@app.get('/api/health')
def health(): return jsonify(app='domestic-commerce-analytics',ok=True)

@app.post('/api/apply')
def apply():
    body=request.get_json()
    with LOCK:
        current=read_state()
        if body.get('version')!=current['version']: return jsonify(error='其他页面已经修改数据，请重新载入后再应用。'),409
        table=body['table']
        if table not in FIELDS: raise ValueError('未知数据表')
        candidate=deepcopy(current)
        candidate['tables'][table]=body['rows']
        candidate['tables']=validate(candidate['tables'])
        aggregate(candidate['tables'])
        candidate['sources'][table]=str(body.get('source','在线编辑'))[:120]
        candidate['version']+=1
        # A single previous version is enough for a reversible local edit.
        (DATA/'previous.json').write_text(json.dumps(current,ensure_ascii=False),encoding='utf-8')
        persist(candidate)
    return jsonify(version=candidate['version'])

@app.post('/api/restore')
def restore():
    with LOCK:
        current=read_state()
        if request.json.get('version')!=current['version']: return jsonify(error='版本已变化，请刷新'),409
        prev=DATA/'previous.json'
        if not prev.exists(): raise ValueError('没有可撤销的更新')
        value=json.loads(prev.read_text(encoding='utf-8')); value['version']=current['version']+1
        validate(value['tables']); persist(value); prev.unlink()
    return jsonify(ok=True)

@app.post('/api/upload')
def upload():
    file=request.files['file']; raw=file.read(); ext=Path(file.filename).suffix.lower()
    sheets={}
    if ext=='.csv':
        try: text=raw.decode('utf-8-sig')
        except UnicodeDecodeError: text=raw.decode('gb18030')
        try: dialect=csv.Sniffer().sniff(text[:8192],delimiters=',;\t')
        except csv.Error: dialect=csv.excel
        rows=list(csv.reader(io.StringIO(text),dialect)); sheets['CSV']=rows
    elif ext=='.xlsx':
        book=load_workbook(io.BytesIO(raw),read_only=True,data_only=False)
        try:
            if len(book.sheetnames)>20: raise ValueError('工作簿最多 20 个工作表')
            for sheet in book:
                rows=[]
                for values in sheet.iter_rows(values_only=True):
                    if len(rows)>20000 or len(values)>100: raise ValueError('最多 20,000 行、100 列')
                    if any(isinstance(v,str) and v.startswith('=') for v in values): raise ValueError('请将 Excel 公式粘贴为值后导入')
                    rows.append([v.isoformat() if isinstance(v,(date,datetime)) else v for v in values])
                sheets[sheet.title]=rows
        finally: book.close()
    else: raise ValueError('支持 .csv 和 .xlsx；旧版 .xls 请另存为 .xlsx')
    result={}
    for name,rows in sheets.items():
        rows=[r for r in rows if any(v is not None and str(v).strip() for v in r)]
        if not rows: continue
        headers=[str(v or '').strip() for v in rows[0]]
        if len(headers)!=len(set(headers)) or '' in headers: raise ValueError('表头不能为空或重复')
        if len(rows)>20001 or len(headers)>100: raise ValueError('最多 20,000 行、100 列')
        if any(len(r)>len(headers) for r in rows[1:]): raise ValueError('存在多于表头列数的数据行')
        result[name]={'headers':headers,'rows':[dict(zip(headers,r)) for r in rows[1:]]}
    if not result: raise ValueError('文件中没有数据')
    return jsonify(sheets=result)

@app.get('/api/template.xlsx')
def template():
    workbook=Workbook(); workbook.remove(workbook.active)
    with LOCK: tables=read_state()['tables']
    for table,fields in FIELDS.items():
        sheet=workbook.create_sheet(table); sheet.append(fields); sheet.freeze_panes='A2'
        for row_number,row in enumerate(tables[table],2):
            sheet.append([row[k] for k in fields])
            for cell in sheet[row_number]:
                if isinstance(cell.value,str): cell.data_type='s'
    output=io.BytesIO(); workbook.save(output); output.seek(0)
    return send_file(output,download_name='dashboard-data.xlsx',as_attachment=True)

@app.get('/api/export/<table>.csv')
def export(table):
    if table not in FIELDS: return '',404
    out=io.StringIO(); writer=csv.writer(out); writer.writerow(FIELDS[table])
    for row in read_state()['tables'][table]:
        writer.writerow([("'"+v if isinstance(v,str) and v.startswith(('=','+','-','@')) else v) for v in [row[k] for k in FIELDS[table]]])
    return Response('\ufeff'+out.getvalue(),mimetype='text/csv',headers={'Content-Disposition':f'attachment; filename={table}.csv'})

def query_sql(body):
    engine=body.get('engine','sqlite'); query=str(body.get('query','')).strip().rstrip(';')
    if not re.match(r'^SELECT\s',query,re.I) or ';' in query: raise ValueError('仅支持单条 SELECT 查询（可使用 JOIN 和聚合）')
    conn=None
    try:
        if engine=='sqlite':
            path=Path(body.get('path','')).resolve(strict=True)
            conn=sqlite3.connect(path.as_uri()+'?mode=ro',uri=True,timeout=5)
            conn.execute('PRAGMA query_only=ON')
            allowed={sqlite3.SQLITE_SELECT,sqlite3.SQLITE_READ,sqlite3.SQLITE_FUNCTION,sqlite3.SQLITE_RECURSIVE}
            conn.set_authorizer(lambda action,a,b,c,d: sqlite3.SQLITE_OK if action in allowed and not(action==sqlite3.SQLITE_FUNCTION and b in ('load_extension','writefile','readfile')) else sqlite3.SQLITE_DENY)
            import time
            deadline=time.monotonic()+10
            conn.set_progress_handler(lambda: int(time.monotonic()>deadline),1000)
        elif engine=='postgres':
            try: import psycopg
            except ImportError: raise ValueError('尚未安装 PostgreSQL 驱动。运行：python -m pip install "psycopg[binary]"')
            conn=psycopg.connect(host=body['host'],port=int(body.get('port',5432)),dbname=body['database'],user=body['user'],password=body['password'],connect_timeout=8,sslmode='verify-full',autocommit=True)
            conn.execute('BEGIN READ ONLY'); conn.execute("SET LOCAL statement_timeout = '10s'")
        elif engine=='mysql':
            try: import pymysql
            except ImportError: raise ValueError('尚未安装 MySQL 驱动。运行：python -m pip install pymysql')
            import ssl
            conn=pymysql.connect(host=body['host'],port=int(body.get('port',3306)),database=body['database'],user=body['user'],password=body['password'],connect_timeout=8,read_timeout=10,write_timeout=10,ssl=ssl.create_default_context(),autocommit=True)
            conn.cursor().execute('START TRANSACTION READ ONLY')
        else: raise ValueError('不支持的数据库类型')
        cur=conn.cursor(); cur.execute('SELECT * FROM ('+query+'\n) AS dashboard_source LIMIT 20001'); headers=[col[0] for col in cur.description]
        if len(set(headers))!=len(headers): raise ValueError('查询列名重复，请使用 AS 别名')
        rows=cur.fetchmany(20001)
        if len(rows)>20000: raise ValueError('结果超过 20,000 行，请在 SQL 中缩小查询范围')
        return {'headers':headers,'rows':[dict(zip(headers,[v.isoformat() if isinstance(v,(date,datetime)) else float(v) if type(v).__name__=='Decimal' else v for v in row])) for row in rows]}
    finally:
        if conn: conn.close()

@app.post('/api/sql')
def sql(): return jsonify(query_sql(request.get_json()))


@app.get('/report')
def public_report():
    return send_file(ROOT / 'docs' / 'index.html')

if __name__=='__main__':
    print('Local dashboard: http://127.0.0.1:8867',flush=True)
    app.run(host='127.0.0.1',port=8867,debug=False)
