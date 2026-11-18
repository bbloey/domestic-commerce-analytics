"""Human-readable data guide, rendered from the same state as the dashboard."""
from html import escape
from src.model import FIELDS

FIELD_INFO = {
    'line_id':('明细行编号','文本','唯一键；每行唯一，不等于订单或客户'),
    'order_id':('订单编号','文本','COUNT DISTINCT；同一订单可以有多条商品行'),
    'order_date':('订单时间','北京时间，无时区字符串','按月/小时分组；不自动代表付款或确认收货'),
    'customer_id':('模拟统一客户编号','文本','COUNT DISTINCT；跨平台真实身份需要可靠映射'),
    'product':('产品中文名','文本','产品分组；必填'),
    'sku':('SKU名称','文本','SKU分组；一个SKU只属于一个产品'),
    'channel':('平台来源','枚举','douyin=抖系；taobao=淘系；jd=京系；单订单互斥'),
    'quantity':('购买件数','正整数，件','SUM；不能当订单数或人数'),
    'returned_quantity':('退货件数','非负整数，件','SUM；不得超过购买件数'),
    'gmv_cny':('商品成交金额','非负数，人民币元','SUM；明细行合计，不是单价'),
    'net_sales_cny':('净收入输入值','非负数，人民币元','SUM；不等于利润或已对账结算额'),
    'month':('统计月份','YYYY-MM','按月分组；月目标唯一'),
    'impressions':('曝光次数','非负整数，次','SUM；教学统一口径'),
    'page_views':('浏览次数','非负整数，次','SUM；不是点击次数'),
    'unique_page_views':('去重浏览数','非负整数，表内口径','只在月×产品×渠道内去重；跨组相加不是全店UV'),
    'unique_customers':('流量表客户数','非负整数，表内口径','只在月×产品×渠道内去重；跨组不是唯一人数'),
    'target_gmv_cny':('全店月度目标','非负数，人民币元','按月取单值；不能按商品重复累加'),
}
METRICS = [
    ('GMV','Σ gmv_cny','按订单月份与当前有效筛选；不推断付款/确认收货状态'),
    ('净收入','Σ net_sales_cny','输入字段合计；不含成本，不能推导利润'),
    ('购买件数 / 净销量','Σ quantity / (Σ quantity − Σ returned_quantity)','产品销量使用购买件数；总览和SKU使用净销量'),
    ('订单数 / 客户数','COUNT DISTINCT(order_id) / COUNT DISTINCT(customer_id)','分别去重；不能按商品或平台分组数直接相加'),
    ('在售产品 / 在售SKU','当前范围有正向GMV的产品数 / SKU数','以商品键去重；并非库存可售状态'),
    ('平均订单金额 / 单品平均售价','GMV ÷ 去重订单数 / GMV ÷ 净销量','单品平均售价沿用模板净销量分母；不是每行价格的简单平均'),
    ('全店目标达成率','当月GMV ÷ 当月全店目标','目标为0不可算；商品/渠道筛选后的主靶图改显示其占全店GMV的比例'),
    ('GMV / 销量环比','本月值 ÷ 紧邻上月值 − 1','无上月或上月为0不可算；不跳过空月找比较基准'),
    ('产品 / SKU占比','当前产品或SKU金额 ÷ 当前图表范围金额合计','分母随该图表支持的筛选变化'),
    ('渠道占比','渠道GMV ÷ 当前所选渠道GMV合计','单选某平台时图表内占比为100%；不等于全店份额'),
    ('CTR（浏览曝光比）','Σ page_views ÷ Σ impressions','缺少clicks字段，不能当严格点击率'),
    ('CVR代理','Σ unique_customers ÷ Σ unique_page_views','产品范围次数之比；不能当全平台唯一用户转化率'),
    ('件数退货率','Σ returned_quantity ÷ Σ quantity','不是退款金额率，也没有订单退款批次匹配'),
    ('回头客率（页面复购率）','当月客户中历史出现过的人数 ÷ 当月客户数','历史截至上月；不等于当月购买两次及以上比例'),
    ('人均消费 / 人均净收入 / 人均订单','当月GMV / 净收入 / 去重订单数，各自除以当月客户数','客户页仅受月份影响；不把明细行当人数'),
    ('月内购买频次','每客户当月去重订单数','分为1、2、3、4、5次及以上'),
    ('RFM / 客户Top200','R=月末距最近购买天数；F=历史去重订单；M=历史净收入','从最早订单月至所选月；Top200按M降序，Top15仅是图表展示截取'),
    ('映射 / 身份质量','已覆盖记录数 ÷ 对应记录数','当前输入校验要求字段必填和一致；100%不证明真实业务数据完美'),
    ('渠道流量覆盖','提供流量的有订单月×产品×渠道组合数 ÷ 全部有订单组合数','基于完整当前版本；不随商品/渠道筛选变化'),
]
CHAPTERS = [
    ('1 经营总览','规模和目标表现如何？','靶图、KPI、GMV与销量趋势、环比','月份；产品/SKU/渠道按界面允许的组合'),
    ('2 产品监控','哪些商品贡献销售与增长？','产品/SKU环图、增长矩阵、排行榜','月份、产品、SKU；忽略渠道'),
    ('3 渠道监控','平台贡献与流量表现怎样？','渠道占比、金额堆积图、增长表、流量代理趋势','月份、产品、渠道；忽略SKU'),
    ('4 客户监控','哪些模拟客户值得进一步观察？','Top200、RFM、回头客、频次、时段','仅月份；RFM使用截至所选月的累计历史'),
    ('5 数据质量','上述数字是否有足够数据支持？','覆盖率、名称映射、客户身份、币种、页尾声明','名称映射卡随月份；覆盖与身份统计取全版本；映射明细保留全部月份'),
    ('6 数据源','如何理解、替换和验证数据？','四项说明、文件/SQL预览、编辑、应用与撤销','当前数据版本；不受经营图表顶部筛选影响'),
]

def table(headers, rows):
    return '<div class="table-wrap guide-table"><table><thead><tr>'+''.join('<th>'+escape(x)+'</th>' for x in headers)+'</tr></thead><tbody>'+''.join('<tr>'+''.join('<td>'+escape(str(v))+'</td>' for v in row)+'</tr>' for row in rows)+'</tbody></table></div>'

def render_source_guide(state):
    tables=state['tables'];orders=tables['orders']
    dates=sorted(r['order_date'][:10] for r in orders)
    period=(dates[0]+' 至 '+dates[-1]) if dates else '无订单'
    simulated=sum('模拟' in str(state.get('sources',{}).get(k,'')) for k in FIELDS)
    mode='全部模拟数据' if simulated==len(FIELDS) else '混合来源（含模拟）' if simulated else '用户导入；真实性未验证'
    facts=[('订单日期范围',period),('订单商品行',f'{len(orders):,} 行'),('去重订单',f"{len({r['order_id'] for r in orders}):,} 单"),('去重模拟/导入客户',f"{len({r['customer_id'] for r in orders}):,} 个ID"),('流量 / 目标',f"{len(tables['traffic']):,} / {len(tables['targets']):,} 行"),('数据标记',mode)]
    fact_html=''.join('<div><span>'+escape(k)+'</span><strong>'+escape(v)+'</strong></div>' for k,v in facts)
    overview=table(['要说明什么','举例说明','不说明会怎样'],[
        ('① 数据契约','例如：一个订单买了两种商品，会有两条明细，但仍只算一个订单；金额单位是人民币元。','把订单明细行当人数，或把不同粒度的度量直接相加'),
        ('② 指标口径','例如：模拟月GMV为10万元、全店目标为20万元，目标达成率为50%；净收入不等于利润。','同名指标含义不同，KPI与表格对不上'),
        ('③ 章节骨架','例如：先看总览发现销售下降，再到产品和渠道页找下降贡献，最后核查数据质量。','只有图表，没有从问题到证据的分析过程'),
        ('④ 输出约束','例如：选择“京系”后渠道图只看京系；指标定义保持不变，不支持渠道筛选的模块要明确提示。','筛选看似变化却未重算，或固定结论随筛选失去依据'),
    ])
    grains=table(['数据表','一行代表什么 / 唯一键','当前样本量'],[
        ('orders','一条订单商品明细；line_id唯一，同一订单可多行',len(orders)),
        ('traffic','月份 × 产品 × 平台来源；组合唯一',len(tables['traffic'])),
        ('targets','一条全店月目标；month唯一',len(tables['targets'])),
    ])
    fields=''.join('<h4>'+escape(name)+'</h4>'+table(['中文字段','字段名','类型 / 单位','聚合与使用规则'],[(FIELD_INFO[f][0],f,FIELD_INFO[f][1],FIELD_INFO[f][2]) for f in names]) for name,names in FIELDS.items())
    metrics=table(['指标','计算公式 / 分母','范围、排除与边界'],METRICS)
    chapters=table(['章节顺序','回答的问题','表与图','有效筛选 / 统计范围'],CHAPTERS)
    spec=table(['说明主题','可复用的 spec 路径','本项目对应实现'],[
        ('数据契约','meta.grain / period / dataMode + datasets[].fields','model.FIELDS / validate；本页范围与样本量读取当前state'),
        ('指标口径','fields[].derived / agg + binding.filters / sort','model.aggregate；前端的分组、比率、排序与空值处理'),
        ('章节骨架','layout.regions + components[]','src/dashboard.html中的page-overview至page-quality；src/sources.html'),
        ('输出约束','binding.scope / recompute + interactions / exports','前端FILTER_SCOPE；server.py预览/应用；build.py公开构建'),
    ])
    return f'''<!-- SOURCE_GUIDE_START -->
<div class="source-guide" id="source-guide">
 <div class="guide-heading"><h3>先读懂数据，再更新看板</h3><p>这份说明回答四件事：数据是什么、指标怎么算、报告怎么读、更新后怎么验收。</p></div>
 {overview}
 <details class="card guide-block" open><summary><b>① 数据契约</b><span>一行代表什么，数据覆盖到哪里</span></summary>
  <div class="guide-body"><div class="guide-facts">{fact_html}</div>
   <p>样本量与日期范围来自当前完整数据版本，应用更新并刷新后重算；不跟随图表筛选。金额单位为人民币元（CNY），订单时间按北京时间解释。默认数据由固定随机种子生成；来源标签只说明导入方式，不证明数据真实性。</p>
   {grains}
   <details class="guide-inner"><summary>展开全部字段清单与单位（orders / traffic / targets）</summary>{fields}</details>
   <p class="guide-caution">不要把行数当订单数或客户数。模拟客户ID在本地统一；真实平台同名、同号不等于同一人。曝光和客户的去重边界必须在各平台核实后再比较。</p>
  </div>
 </details>
 <details class="card guide-block"><summary><b>② 指标口径</b><span>公式、分母、阈值和不能回答的问题</span></summary>
  <div class="guide-body">{metrics}
   <h4>RFM分档与分群</h4><p>历史截至所选月末，R由久到近、F/M由低到高分别按NTILE(5)规则分为1—5档；同值按客户ID打散，可能分属邻档。客户不足5人时不保证出现5分。</p>
   <p>按以下顺序互斥归类：R≥4且F≥4且M≥4→高价值忠诚；R≥3且F≥4→忠诚；R≥4→新近高潜；R≤2且M≥4→沉睡高价值；R≤2→流失风险；其余→一般客户。这里的R/F/M条件指分档得分，不是原始天数、订单数或金额。这是教学规则，不是预测概率。</p>
   <h4>排除与空值</h4><p>必填缺失、唯一键重复、计数非法、退货超过购买等情况拒绝整次更新，不静默删行。流量组合不完整时隐藏相应转化图并提示补充。分母为0或上月缺失时底层返回空值；现有部分图形仍可能将空值画为0，不能据此声称实际值为0。</p>
   <p>不含成本、投放和匹配退款批次，不能回答利润、ROI、真实退款率或增长原因；模拟平台对比不能用于判断真实平台优劣。</p>
  </div>
 </details>
 <details class="card guide-block"><summary><b>③ 章节骨架</b><span>规模 → 商品 → 渠道 → 客户 → 质量 → 数据更新</span></summary>
  <div class="guide-body">{chapters}<p>先确认规模变化，再拆解商品、渠道和客户构成，最后检查数据是否足以支持判断。图表说明与字段解释固定；带筛选条件的数字是当前范围的描述，不能自动升级为因果结论。</p></div>
 </details>
 <details class="card guide-block"><summary><b>④ 输出约束</b><span>哪里联动、如何重算、交付什么、怎样验收</span></summary>
  <div class="guide-body">
   <h4>固定层与联动层</h4><p>固定层：章节顺序、指标定义、阈值、业务边界、页尾学习声明。版本层：本页样本量与数据范围、完整版本的覆盖和客户质量统计。联动层：各图表仅按上表支持的筛选重算；界面显示忽略的筛选项。经营总览选择渠道时，缺少对应口径的订单数、净收入等显示空值；全店客户卡仍只随月份变化。</p>
   <h4>结构与数字</h4><p>按本项目已定义的六个模块一一对应组织，不在换数据时随意删减；不是对其他网站全部业务口径作1:1承诺。输入金额来自明细或月目标表，聚合数由计算产生，不能把KPI写死在页面。比例由汇总分子÷汇总分母重算，去重人数不能跨分组直接相加。</p>
   <h4>更新流程</h4><p>上传文件或SQL查询 → 选择表与字段映射 → 预览/编辑草稿 → 校验 → 版本检查 → 应用整张表 → 后端重算 → 页面刷新。查询和编辑草稿不会直接覆盖看板；新增月份先补目标。完整服务支持撤销上一次更新。</p>
   <h4>交付物</h4><p>本地完整网站、独立HTML报告、三表CSV/Excel样例、分析与服务源码、月度指标CSV、质量审计JSON、数据口径文档和GitHub源码包。GitHub Pages仅支持静态展示与已有数据筛选；上传、SQL和编辑需要Python服务。构建默认读取 data 中的CSV，不读取本机上传版本，因此公开报告不自动同步本机更新。</p>
   <h4>验收清单</h4><ul><li>同月同范围的总览、产品、SKU、渠道与小时GMV回汇总一致。</li><li>一单多行不增加订单数；客户频次分布人数之和等于当月客户数。</li><li>切换月份/渠道后，仅支持该筛选的模块重算；固定定义和范围提示保持明确。</li><li>Excel/CSV往返、字段校验、版本冲突、撤销、只读SQL正常。</li><li>公开HTML包含全部说明，图表正常显示；不包含本地运行状态或数据库凭据。</li></ul>
  </div>
 </details>
 <details class="guide-inner guide-spec"><summary>给复用者：如何对应到你的 spec 模板</summary><p>下列路径沿用你提供的描述方式，作为复用设计的映射；它们不是当前项目已经存在的JSON配置字段，也不会被通用spec引擎直接执行。</p>{spec}</details>
</div>
<!-- SOURCE_GUIDE_END -->'''

