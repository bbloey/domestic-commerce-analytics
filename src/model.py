"""Synthetic domestic commerce data, validation and aggregation."""
import calendar
import math
import random
from collections import defaultdict
from datetime import datetime, timezone

FIELDS = {
    'orders': ['line_id', 'order_id', 'order_date', 'customer_id', 'product', 'sku', 'channel', 'quantity', 'returned_quantity', 'gmv_cny', 'net_sales_cny'],
    'traffic': ['month', 'product', 'channel', 'impressions', 'page_views', 'unique_page_views', 'unique_customers'],
    'targets': ['month', 'target_gmv_cny'],
}
CHANNELS = ['douyin', 'taobao', 'jd']
NUMBERS = {'quantity', 'returned_quantity', 'gmv_cny', 'net_sales_cny', 'impressions', 'page_views', 'unique_page_views', 'unique_customers', 'target_gmv_cny'}
INTEGERS = {'quantity', 'returned_quantity', 'impressions', 'page_views', 'unique_page_views', 'unique_customers'}

def month_range(orders):
    values=sorted({r['order_date'][:7] for r in orders})
    if not values: return []
    start=int(values[0][:4])*12+int(values[0][5:])-1
    end=int(values[-1][:4])*12+int(values[-1][5:])-1
    if end-start>=60: raise ValueError('本项目最多支持连续 60 个月，请缩小日期范围')
    return [f'{i//12:04}-{i%12+1:02}' for i in range(start,end+1)]


def demo():
    rng = random.Random(20261116)
    tables = {k: [] for k in FIELDS}
    products = ['便携榨汁杯', '恒温电热水壶', '无线吸尘器', '空气炸锅', '桌面循环扇', '智能体脂秤']
    prices = [199, 299, 699, 599, 199, 149]
    for m, count in enumerate([720, 860, 790, 1080], 1):
        month = f'2026-{m:02}'
        for i in range(count):
            p = rng.randrange(len(products)); qty = rng.choices([1, 2, 3], [80, 16, 4])[0]
            returned = 1 if rng.random() < .065 else 0
            gmv = round(prices[p] * qty * rng.uniform(.85, 1.05), 2)
            tables['orders'].append(dict(zip(FIELDS['orders'], [f'L{m}{i:05}', f'O{m}{i:05}', f'{month}-{rng.randint(1,calendar.monthrange(2026,m)[1]):02}T{rng.randrange(24):02}:00:00', f'C{rng.randint(1,520):04}', products[p], products[p] + rng.choice([' · 标准款', ' · 升级款']), rng.choices(CHANNELS, [58, 28, 14])[0], qty, returned, gmv, round(gmv * (qty-returned)/qty * .91, 2)])))
        for p in products:
            for c in CHANNELS:
                customers = len({r['customer_id'] for r in tables['orders'] if r['order_date'].startswith(month) and r['product']==p and r['channel']==c})
                uv = int(customers * rng.uniform(9, 18)); pv = int(uv * rng.uniform(1.1, 1.6)); imp = int(pv * rng.uniform(8, 16))
                tables['traffic'].append(dict(zip(FIELDS['traffic'], [month,p,c,imp,pv,uv,customers])))
        tables['targets'].append({'month':month, 'target_gmv_cny':[350000,450000,400000,500000][m-1]})
    return validate(tables)


def validate(tables):
    clean = {}
    for table, fields in FIELDS.items():
        rows=tables.get(table)
        if not isinstance(rows,list) or len(rows)>20000: raise ValueError(f'{table}: 必须是表格，最多 20,000 行')
        clean[table]=[]
        for i,row in enumerate(rows,1):
            out={}
            for f in fields:
                value=row.get(f)
                if value is None or str(value).strip()=='': raise ValueError(f'{table} 第 {i} 行缺少 {f}')
                if f in NUMBERS:
                    try: value=float(value)
                    except (TypeError,ValueError): raise ValueError(f'{table} 第 {i} 行 {f} 必须是数字')
                    if not math.isfinite(value) or value<0: raise ValueError(f'{table} 第 {i} 行 {f} 必须为有限非负数')
                    if f in INTEGERS:
                        if value!=int(value): raise ValueError(f'{f} 必须为整数')
                        value=int(value)
                else: value=str(value).strip()
                out[f]=value
            if 'month' in out:
                if len(out['month'])!=7: raise ValueError('月份格式必须是 YYYY-MM')
                datetime.strptime(out['month'],'%Y-%m')
            if table=='orders':
                dt=datetime.fromisoformat(out['order_date'])
                if dt.tzinfo: raise ValueError('order_date 请使用当地营业时间，不带时区')
                if out['quantity']<=0 or out['returned_quantity']>out['quantity']: raise ValueError('购买件数必须大于零且退货件数不能超过购买件数')
            if table=='traffic' and not(out['unique_customers']<=out['unique_page_views']<=out['page_views']<=out['impressions']): raise ValueError('流量应满足：客户 ≤ 去重浏览 ≤ 浏览 ≤ 曝光')
            if 'channel' in out and out['channel'] not in CHANNELS: raise ValueError('channel 只能是 douyin、taobao 或 jd')
            clean[table].append(out)
    if not clean['orders']: raise ValueError('订单表不能为空')
    for table, keys in [('orders',['line_id']),('traffic',['month','product','channel']),('targets',['month'])]:
        values=[tuple(r[k] for k in keys) for r in clean[table]]
        if len(values)!=len(set(values)): raise ValueError(f'{table} 唯一键重复：{keys}')
    order_meta={}; sku_meta={}
    for r in clean['orders']:
        meta=(r['customer_id'],r['order_date'],r['channel'])
        if order_meta.setdefault(r['order_id'],meta)!=meta: raise ValueError('同一 order_id 的客户、时间和渠道必须一致')
        if sku_meta.setdefault(r['sku'],r['product'])!=r['product']: raise ValueError('同一 SKU 只能属于一个产品')
    months=set(month_range(clean['orders']))
    for table in ['targets']:
        missing=months-{r['month'] for r in clean[table]}
        if missing: raise ValueError(f'请先在 {table} 表补充月份：{", ".join(sorted(missing))}')
    return clean


def aggregate(tables):
    orders=tables['orders']; months=month_range(orders)
    names=['headline','module_01_overview','module_02_product_gmv_share','module_03_monthly_revenue','module_04_product_sales_share','module_05_product_growth','module_06_sku_growth','module_07_channel_product_gmv','module_08_channel_conversion','module_09_channel_conversion_trend','filter_product_sku','scope_month_sku','customer_month','customer_top_profile','customer_rfm_segments','customer_hour','customer_frequency','mapping_quality_month','customer_quality','coverage']
    d={k:[] for k in names}
    def total(rows,key): return round(sum(r[key] for r in rows), 6)
    def count(rows,key): return len({r[key] for r in rows})
    def ratio(a,b): return a/b if b else None
    def groups(rows,keys):
        g=defaultdict(list)
        for r in rows: g[tuple(r[k] for k in keys)].append(r)
        return g.items()
    def stats(rows):
        return dict(gmv_cny=total(rows,'gmv_cny'),net_sales_cny=total(rows,'net_sales_cny'),order_count=count(rows,'order_id'),gross_items=total(rows,'quantity'),net_items=total(rows,'quantity')-total(rows,'returned_quantity'))
    catalog=sorted({(r['product'],r['sku']) for r in orders})
    sku_ids={sku:f'S{i:04}' for i,(_,sku) in enumerate(catalog)}
    for p,s in catalog: d['filter_product_sku'].append(dict(product_label=p,sku_label=s,sku_id=sku_ids[s]))
    targets={r['month']:r['target_gmv_cny'] for r in tables['targets']}
    traffic={(r['month'],r['product'],r['channel']):r for r in tables['traffic']}
    previous_products={}; previous_skus={}; previous_channels={}; historical_customers=set()
    for month in months:
        current=[r for r in orders if r['order_date'].startswith(month)]
        hist=[r for r in orders if r['order_date'][:7]<=month]
        base={'month':month,'display_month':month}; s=stats(current)
        full={**base,**s,'product_export_gmv_cny':s['gmv_cny'],'target_gmv_cny':targets[month],'gmv_target_attainment':ratio(s['gmv_cny'],targets[month]),'statement_month_net_sales_cny':s['net_sales_cny'],'matched_settled_orders':s['order_count'],'data_status':'本地数据源'}
        d['module_01_overview'].append(full); d['headline'].append(full); d['module_03_monthly_revenue'].append(full)
        for (product,),rows in groups(current,['product']):
            a=stats(rows); prev=previous_products.get(product)
            item={**base,**a,'product_id':product,'product_name':product,'product_label':product,'items_sold':a['net_items'],'orders':a['order_count'],'gmv_share':ratio(a['gmv_cny'],s['gmv_cny']),'gmv_mom':ratio(a['gmv_cny'],prev['gmv_cny'])-1 if prev and prev['gmv_cny'] else None,'items_mom':ratio(a['net_items'],prev['net_items'])-1 if prev and prev['net_items'] else None}
            for k in ['module_02_product_gmv_share','module_04_product_sales_share','module_05_product_growth']: d[k].append(item)
        previous_products={r['product_label']:r for r in d['module_05_product_growth'] if r['month']==month}
        for (product,sku),rows in groups(current,['product','sku']):
            a=stats(rows); item={**base,**a,'sku_id':sku_ids[sku],'sku_label':sku,'sku_name_cn':sku,'product_label':product,'product_name':product,'sku_gmv_cny':a['gmv_cny'],'allocated_net_sales_cny':a['net_sales_cny'],'order_sku_rows':len(rows),'unmapped_product_rows':0,'unmapped_sku_rows':0}
            item['sku_label_source']='sku_dimension'
            d['scope_month_sku'].append(item); d['module_06_sku_growth'].append(item)
        for (product,channel),rows in groups(current,['product','channel']):
            a=stats(rows); t=traffic.get((month,product,channel),{})
            item={**base,'product_label':product,'product_name':product,'product_id':product,'channel':channel,'attributed_gmv_cny':a['gmv_cny'],'attributed_items':a['net_items'],**{k:t.get(k) for k in FIELDS['traffic'][3:]}}
            d['module_07_channel_product_gmv'].append(item); d['module_08_channel_conversion'].append(item)
        # Traffic-only combinations are needed for zero-sales conversion periods.
        for (m,p,c),t in traffic.items():
            if m==month and not any(r['product']==p and r['channel']==c for r in current):
                d['module_08_channel_conversion'].append({**base,**t,'product_label':p,'attributed_gmv_cny':0,'attributed_items':0})
        customers={r['customer_id'] for r in current}; returning=len(customers & historical_customers)
        d['customer_month'].append({**base,**s,'customer_count':len(customers),'matched_net_sales_cny':s['net_sales_cny'],'item_return_rate':ratio(total(current,'returned_quantity'),s['gross_items']),'returning_customer_count':returning,'repeat_customer_rate':ratio(returning,len(customers)),'orders_per_customer':ratio(s['order_count'],len(customers)),'gmv_per_customer':ratio(s['gmv_cny'],len(customers)),'matched_net_sales_per_customer':ratio(s['net_sales_cny'],len(customers))})
        historical_customers |= customers
        end=datetime.strptime(month+'-'+str(calendar.monthrange(int(month[:4]),int(month[5:]))[1]),'%Y-%m-%d')
        profiles=[]
        for (customer,),rows in groups(hist,['customer_id']):
            a=stats(rows)
            profiles.append({**base,'customer_key':customer,'customer_label':customer,'recency_days':(end.date()-max(datetime.fromisoformat(r['order_date']).date() for r in rows)).days,'frequency_orders':a['order_count'],'active_months':len({r['order_date'][:7] for r in rows}),'gmv_cny':a['gmv_cny'],'matched_net_sales_cny':a['net_sales_cny'],'item_return_rate':ratio(total(rows,'returned_quantity'),a['gross_items']),'average_order_value_cny':ratio(a['gmv_cny'],a['order_count'])})
        for field,score,reverse in [('recency_days','recency_score',True),('frequency_orders','frequency_score',False),('matched_net_sales_cny','monetary_score',False)]:
            ranked=sorted(profiles,key=lambda r:((-r[field]) if reverse else r[field],r['customer_key']))
            # SQL NTILE(5): remainder rows go to the first buckets.
            q,rem=divmod(len(ranked),5); at=0
            for bucket in range(1,6):
                for p in ranked[at:at+q+(bucket<=rem)]: p[score]=bucket
                at+=q+(bucket<=rem)
        for p in profiles:
            r,f,m=p['recency_score'],p['frequency_score'],p['monetary_score']; p['rfm_score']=r+f+m
            p['rfm_segment']='高价值忠诚客户' if r>=4 and f>=4 and m>=4 else '忠诚客户' if r>=3 and f>=4 else '新近高潜客户' if r>=4 else '沉睡高价值客户' if r<=2 and m>=4 else '流失风险客户' if r<=2 else '一般客户'
        d['customer_top_profile'].extend(sorted(profiles,key=lambda r:(-r['matched_net_sales_cny'],r['customer_key']))[:200])
        for (segment,),rows in groups(profiles,['rfm_segment']): d['customer_rfm_segments'].append({**base,'rfm_segment':segment,'customer_count':len(rows),'matched_net_sales_cny':total(rows,'matched_net_sales_cny'),'average_rfm_score':total(rows,'rfm_score')/len(rows)})
        for hour in range(24):
            rows=[r for r in current if datetime.fromisoformat(r['order_date']).hour==hour]
            d['customer_hour'].append({**base,'order_hour':hour,'order_count':count(rows,'order_id'),'customer_count':count(rows,'customer_id'),'gmv_cny':total(rows,'gmv_cny')})
        bands=defaultdict(int)
        for _,rows in groups(current,['customer_id']):
            n=count(rows,'order_id'); bands[str(n)+' 次' if n<5 else '5 次及以上']+=1
        for band in ['1 次','2 次','3 次','4 次','5 次及以上']: d['customer_frequency'].append({**base,'purchase_frequency_band':band,'customer_count':bands[band]})
        d['mapping_quality_month'].append({**base,'order_sku_rows':len(current),'unmapped_product_rows':0,'unmapped_sku_rows':0,'product_name_mapping_rate':1,'sku_name_mapping_rate':1})
    d['customer_quality']=[dict(order_count=count(orders,'order_id'),missing_username_orders=0,conflicting_username_orders=0,observed_customer_count=count(orders,'customer_id'))]
    expected_traffic={(r['order_date'][:7],r['product'],r['channel']) for r in orders}
    covered=len(expected_traffic & set(traffic))
    d['coverage']=[
        dict(metric='order_sku_mapping',numerator=len(orders),denominator=len(orders),rate=1,note='导入时校验产品和 SKU 必填；不是外部业务系统匹配结果'),
        dict(metric='净收入字段完整',numerator=len(orders),denominator=len(orders),rate=1,note='订单明细提供净收入；不是结算账单匹配率'),
        dict(metric='渠道流量覆盖',numerator=covered,denominator=len(expected_traffic),rate=ratio(covered,len(expected_traffic)),note='有订单的月份 × 产品 × 渠道是否提供流量记录'),
    ]
    return dict(generatedAt=datetime.now(timezone.utc).isoformat(), datasets=d,
                currency={'code':'CNY','name':'人民币','unit':'元'},
                source={'artifact':'国内电商学习演示','warehouse':'local','notice':'模拟数据，非真实数据，仅供学习'})
