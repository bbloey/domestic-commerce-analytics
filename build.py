"""Build the standalone domestic commerce report from the included CSV data."""
from pathlib import Path
import argparse, csv, json, re
from src.model import FIELDS, aggregate, demo, validate
from src.source_guide import render_source_guide
ROOT=Path(__file__).resolve().parent

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
    html=html.replace('</head>','<style>'+ROOT.joinpath('src/dashboard.css').read_text(encoding='utf-8')+'</style></head>')
    info_patch='''Object.values(INFO).forEach(info=>info.source="本地 orders 表聚合");
      ["ctr","cvr","impressions","page_views","unique_page_views","unique_customers"].forEach(k=>{if(INFO[k])INFO[k].source="本地 traffic 表"});
      INFO.target.source="本地 targets 与 orders 表"; INFO.currency.source="人民币字段契约 · 学习模拟";
      Object.assign(INFO.gmv,{concept:"按订单创建月汇总导入的明细 GMV；本地订单渠道互斥。",formula:"SUM(orders.gmv_cny)"});
      Object.assign(INFO.net_sales,{concept:"订单明细提供的净收入；未接入原始结算账单匹配。渠道筛选缺少相应口径时显示空值。",formula:"SUM(orders.net_sales_cny)"});
      Object.assign(INFO.product_gmv_share,{concept:"选中月份当前产品范围的 GMV 占比。产品名称来自导入表，导入时校验必填。"});
      '''
    html=html.replace('initFilters();decorateInfo();renderAll();',info_patch+'initFilters();decorateInfo();renderAll(); window.dashboardPage=setPage; if(location.hash==="#sources")setPage("sources");')
    missing=[r for r in payload['datasets']['module_08_channel_conversion'] if r.get('impressions') is None]
    # Missing traffic must not masquerade as zero or fabricated conversion.
    if missing:
        html=html.replace('multiLine($("channel-customers"),rows,"unique_customers","各渠道客户数月趋势");','multiLine($("channel-customers"),rows,"unique_customers","各渠道客户数月趋势"); ["channel-rate-columns","channel-impressions","channel-pageviews","channel-unique-pageviews","channel-customers"].forEach(id=>$(id).innerHTML=\'<div class="empty">流量表不完整，请在数据源补充月份 × 产品 × 渠道数据后查看转化图表。</div>\');')
    config={'offline':True,'fields':FIELDS,'tables':{k:v[:30] for k,v in state['tables'].items()},'counts':{k:len(v) for k,v in state['tables'].items()}}
    html=html.replace('</body>','<script>window.SOURCE_CONFIG='+json.dumps(config,ensure_ascii=False).replace('<','\\u003c')+';</script><script>'+ROOT.joinpath('src/sources.js').read_text(encoding='utf-8')+'</script></body>')
    return html

def build(reset_demo=False):
    if reset_demo:
        for name,rows in demo().items():
            with (ROOT/'data'/f'{name}.csv').open('w',encoding='utf-8-sig',newline='') as f:
                w=csv.DictWriter(f,fieldnames=FIELDS[name]);w.writeheader();w.writerows(rows)
    tables={}
    for name in FIELDS:
        with (ROOT/'data'/f'{name}.csv').open(encoding='utf-8-sig',newline='') as f:
            tables[name]=list(csv.DictReader(f))
    tables=validate(tables)
    result=aggregate(tables)
    state={'version':1,'tables':tables,'sources':{k:'学习模拟CSV' for k in tables}}
    html=render_html(state)
    assert 'source-file' in html and 'source-save' in html
    out=ROOT/'output';out.mkdir(exist_ok=True)
    monthly=result['datasets']['module_01_overview'];checks=[]
    for row in monthly:
        for name,col in [('module_05_product_growth','gmv_cny'),('module_06_sku_growth','sku_gmv_cny'),('module_07_channel_product_gmv','attributed_gmv_cny'),('customer_hour','gmv_cny')]:
            diff=round(sum(r[col] for r in result['datasets'][name] if r['month']==row['month'])-row['gmv_cny'],6)
            checks.append({'month':row['month'],'check':name,'difference_cny':diff,'passed':abs(diff)<.00001})
    assert all(c['passed'] for c in checks)
    with (out/'monthly_metrics.csv').open('w',encoding='utf-8-sig',newline='') as f:
        w=csv.DictWriter(f,fieldnames=list(monthly[0]));w.writeheader();w.writerows(monthly)
    audit={'data_mode':'synthetic learning data','currency':'CNY','table_rows':{k:len(v) for k,v in tables.items()},'quality_checks':checks,'total_gmv_cny':round(sum(r['gmv_cny'] for r in monthly),2)}
    (out/'quality_audit.json').write_text(json.dumps(audit,ensure_ascii=False,indent=2),encoding='utf-8')
    (ROOT/'docs').mkdir(exist_ok=True)
    (ROOT/'docs/index.html').write_text(html,encoding='utf-8')
    print(json.dumps({'html':'docs/index.html','gmv_cny':audit['total_gmv_cny'],'checks':len(checks)},ensure_ascii=False))

if __name__=='__main__':
    parser=argparse.ArgumentParser(description='Build the domestic commerce learning report')
    parser.add_argument('--reset-demo',action='store_true',help='Explicitly replace input CSV files with fresh synthetic examples')
    build(parser.parse_args().reset_demo)
