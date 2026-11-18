# Domestic Commerce Analytics
国内电商经营分析与可视化学习项目。以订单商品明细、渠道流量、月度目标为输入，分析经营规模、产品与SKU贡献、平台渠道表现、客户价值和数据质量。

**模拟数据，非真实数据，仅供学习。** 渠道为抖系、淘系、京系，金额为人民币元（CNY）。

[打开HTML报告](https://bbloey.github.io/domestic-commerce-analytics/index.html) · [构建流程](docs/BUILD.md) · [数据口径](docs/DATA_CONTRACT.md) · [数据说明](data/README.md)

## 1. 数据处理代码
[src/model.py](src/model.py)包含三表校验、月度聚合、去重订单与客户、RFM分群及模拟数据生成。
[build.py](build.py)读取CSV、执行校验与16项跨模块金额对账，生成独立网页和分析结果。
[src/source_guide.py](src/source_guide.py)提供数据契约、指标口径、章节骨架、输出约束四部分解释。

默认数据包含2026年1—4月的3,450条订单商品行、72条流量记录、4条月目标；四个月模拟GMV为¥1,444,944.91。结果仅用于演示计算流程。

## 2. 网站构建流程
在项目根目录运行：
```bash
python build.py
```
打开生成的[docs/index.html](docs/index.html)。页面保留模块切换、月份/商品/渠道筛选和图表提示。
修改data中的CSV后再次运行构建。若要明确重置成初始模拟样例，运行`python build.py --reset-demo`；该选项会覆盖三张输入CSV。

具体构建与部署步骤见[BUILD.md](docs/BUILD.md)。

## 3. 数据
- [orders.csv](data/orders.csv)：订单商品明细。
- [traffic.csv](data/traffic.csv)：月份×产品×渠道流量。
- [targets.csv](data/targets.csv)：全店月目标。

样本量和日期范围来自实际读取的数据，不在页面写死。每条订单只归属一个平台来源；跨平台客户编号仅在模拟环境中统一。

## 4. 数据口径
[DATA_CONTRACT.md](docs/DATA_CONTRACT.md)包含字段、单位、公式、分母、RFM阈值、质量规则及解释边界。
销售额不等于利润；浏览曝光比不是真实点击率；回头客率不等于月内复购率；流量去重数跨产品相加不等于全店唯一人数。

## 5. HTML与项目结构
```text
domestic-commerce-analytics/
├── README.md
├── server.py / start.py / start.cmd   完整网站与数据源服务
├── build.py
├── src/                       数据处理、页面、样式与说明代码
├── data/                      三张模拟CSV和数据说明
├── docs/
│   ├── index.html             可直接打开的HTML报告
│   ├── DATA_CONTRACT.md       数据口径
│   └── BUILD.md               构建与GitHub Pages发布
└── output/                    月度指标与质量审计
```

## 完整数据源：上传、SQL、修改和撤销

完整功能已保留在 `server.py` 及 `src/` 中。安装 Python 3.10+ 后，在项目根目录运行：

```bash
python -m pip install -r requirements.txt
python start.py
```

公网网站地址为：[国内电商经营分析看板](https://bbloey.github.io/domestic-commerce-analytics/index.html)。

公网版提供报告浏览、图表筛选和数据源模块展示。上传、SQL 和保存修改需运行上述 Python 服务；Windows 也可双击 `start.cmd`，在自动打开的本地完整网站中操作。

操作顺序：选择 Excel / CSV 或 SQL → 预览与校验 → 在线修改 → 应用更新 → 图表重算；可撤销上次已应用的更新。国内版还提供字段映射、增删行和 Excel 模板。

SQLite 无需额外驱动。PostgreSQL 可选安装 `psycopg[binary]`，MySQL 可选安装 `pymysql`；使用只读账户与 TLS。SQL 凭据不保存。

`docs/index.html` 是可直接打开和发布到 GitHub Pages 的静态快照，保留数据源模块布局及完整网站入口。静态托管不运行 Python，需在完整网站中进行上传、SQL 和持久化修改。首次启动 UCI 项目需处理完整工作簿，请等待初始化完成。

运行中导入与修改的数据只保存在 `local-data/`，不会覆盖 `data/` 中的输入文件，也不打入发布压缩包。`python build.py` 始终从 `data/` 重建快照；运行中修改不会自动发布。需要更新静态报告时，先导出当前数据并审核，再替换构建输入；UCI 默认构建会校验官方文件，因此自定义数据应另行记录来源并调整构建校验。

新增项目文件：`server.py`（上传/SQL/编辑/版本接口）、`start.py` / `start.cmd`（完整网站启动）、`requirements.txt`（运行依赖）。原有数据处理、图表、数据口径和构建文件继续保留。
