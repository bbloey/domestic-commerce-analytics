# 网站构建流程
1. 安装Python 3.10+，在项目根目录打开终端。
2. 查看data/README.md及DATA_CONTRACT.md，确认三张CSV的字段与单位。
3. 运行python build.py。它只读取此项目的data目录，执行validate → aggregate → 回汇总对账。
4. 检查output/quality_audit.json所有quality_checks是否通过。
5. 用浏览器打开docs/index.html，检查图表、筛选、数据质量页尾声明，以及数据源与构建页的四项说明。
6. 修改输入CSV后重复第3—5步，再上传生成结果。

所有输入字段必须完整；每表最多20,000行，订单跨度不超过60个月，新增月份先补targets。上期缺失或分母为0不可解释为真实0值。
--reset-demo是显式覆盖输入数据的选项，普通build不会更改CSV。

生成HTML内嵌计算结果、图表与样式，无需本机后台或外部CDN。data目录与src目录仍需提交，以便复现。

## GitHub Pages 发布
把项目文件夹里面的内容上传至仓库根目录；先解压源码包，不要只把ZIP作为网页上传。
在仓库 Settings → Pages 中选择 Deploy from a branch、实际分支及 /docs 目录。
部署完成后的HTML网址以GitHub给出的链接为准。当前交付不包含已部署的公网地址。

## 文件对应关系
- 数据处理：src/model.py。
- 网站构建：build.py与src中的页面、样式和图表代码。
- 数据：data目录。
- 数据口径：docs/DATA_CONTRACT.md。
- 网页：docs/index.html；已内嵌图表脚本和数据，可直接用浏览器打开。
- 聚合结果与核验：output目录。

只发布上述项目内容；不要把本机原工作目录、凭据或上传缓存加入仓库。此副本不会读取原来的8767/8769项目目录。

## 完整数据源：上传、SQL、修改和撤销

完整功能已保留在 `server.py` 及 `src/` 中。安装 Python 3.10+ 后，在项目根目录运行：

```bash
python -m pip install -r requirements.txt
python start.py
```

Windows 也可双击 `start.cmd`。完整网站地址为 http://127.0.0.1:8867/#sources 。

操作顺序：选择 Excel / CSV 或 SQL → 预览与校验 → 在线修改 → 应用更新 → 图表重算；可撤销上次已应用的更新。国内版还提供字段映射、增删行和 Excel 模板。

SQLite 无需额外驱动。PostgreSQL 可选安装 `psycopg[binary]`，MySQL 可选安装 `pymysql`；使用只读账户与 TLS。SQL 凭据不保存。

`docs/index.html` 是可直接打开和发布到 GitHub Pages 的静态快照，保留数据源模块布局及完整网站入口。静态托管不运行 Python，需在完整网站中进行上传、SQL 和持久化修改。首次启动 UCI 项目需处理完整工作簿，请等待初始化完成。

运行中导入与修改的数据只保存在 `local-data/`，不会覆盖 `data/` 中的输入文件，也不打入发布压缩包。`python build.py` 始终从 `data/` 重建快照；运行中修改不会自动发布。需要更新静态报告时，先导出当前数据并审核，再替换构建输入；UCI 默认构建会校验官方文件，因此自定义数据应另行记录来源并调整构建校验。

新增项目文件：`server.py`（上传/SQL/编辑/版本接口）、`start.py` / `start.cmd`（完整网站启动）、`requirements.txt`（运行依赖）。原有数据处理、图表、数据口径和构建文件继续保留。
