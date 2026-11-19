# 耿妍佳 · 数据分析作品集

个人作品集网站，汇总四个项目：电商用户价值分析、国内电商经营分析看板、消费者需求研究 Agent、LendingClub 信贷风控分析。

网站地址：https://bbloey.github.io/domestic-commerce-analytics/portfolio/

## 网站内容

- 个人简介、教育背景与实习经历：整理自本人提供的简历。
- 精选项目：按分析方向筛选，提供摘要弹窗、方法边界、项目代码和报告入口。
- 技能工具与邮箱联系入口。

## 本地运行

无需构建和安装依赖，在项目目录运行 `python -m http.server 8890`，打开 `http://127.0.0.1:8890/`。

## 维护与发布

`index.html` 管理主体内容；`style.css` 管理响应式样式；`script.js` 管理项目详情和筛选。`favicon.svg` 为站点图标。

当前发布位置为 bbloey/domestic-commerce-analytics 仓库的 docs/portfolio/，GitHub Pages 从 main 分支 docs 目录发布。将这六个页面文件同步到该子目录后提交推送即可。未来迁移到 bbloey.github.io 主页仓库时，可将它们放在仓库根目录并配置 Pages。修改项目指标前，请核对来源仓库中的数据口径。项目图形预览中的示意图均已标明，不是完整统计图。

原始简历 PDF、研究中间文件和项目运行缓存不包含在公开仓库内。联系入口使用简历提供的求职邮箱。

## 内容依据与边界

- https://github.com/bbloey/-Retail- ：摘要依据 output/metrics.json；正式 HTML 为空，demo_report.html 为合成样例，不混用样例结论。
- https://github.com/bbloey/domestic-commerce-analytics ：模拟数据看板；公网报告不提供 Python 后端编辑服务。
- https://github.com/bbloey/Social-Media-Comment-Analysis ：依据主 README，公开仓库仅使用合成示例。
- https://github.com/bbloey/LendingClub_da ：依据 report_inline.html，保留成熟度、近似 Vintage、成本与因果解释边界。

页面结构参考用户指定的 https://wongjy76-hub.github.io/ ，本项目独立编写页面、样式和交互，未复制其图片或个人经历。
