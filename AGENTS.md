<!-- @zone user -->
# AGENTS.md — Kit-Build-Plus
Kit-Build教师角色计算机化，流程须符合相关论文
AI从原文抽目标图/裁kit → 学生重建 → 比对学生图与目标图 → 评分报告。
GUI，
<其余技术栈待定>。

## 权限
### 禁止读（仅用户授权可读）
README.md
（已有对于*.md时）*.md.tpl

### 写
<!-- @zone {group} -->
<!-- /@zone {group} -->
group：
all       # 总是允许写
user      # 禁止写，可请求用户授权
code      # 当用户指示编程时可写
research  # 其他情况 

## Commands
.venv/bin/python -V
.venv/bin/python -m pip install -r requirements.txt
.venv/bin/python -m uvicorn src.main:app --host 127.0.0.1 --port 8848
curl -s -o /dev/null -w '%{http_code}\n' http://127.0.0.1:8848/
<测试代码待定>

## 约定
每功能一个文件夹{feature}/，每个文件在{feature}/INDEX.md备注，不在{feature}/外创建相关文件
测试放入{feature}/test/test_*.py
{feature}/*之间禁止import彼此
跨功能交互只经share/契约，不直接import对方内部实现
契约：一个契约域一个文件，字段注释含含义/单位/可空/枚举
行为契约同样在share/：Protocol或纯函数签名
顺序：契约→契约测试→实现→实现测试；消费方只用契约类型
出边界的转换由提供方做，share/只做契约→契约，调用点不包converter
契约被第二个feature消费即冻结；改动先给旧→新、影响范围、迁移方式，经用户确认

单函数<30行否则拆分
所有文件<200行否则拆分
拆分后外部行为须不变，须过测试

用户指定测试场景清单，你负责写测试
禁止按实现自证测试
每个测试须全通过一次，故意不通过一次（确认测试有效）
测试失败后先尝试修复，连续失败两次则停止
重构/拆分测试：先跑现有测试保证原来可通过，拆分后再次测试观察功能是否正常

创建文档参考该文档.md.tpl的结构与写作风格

## 文档结构
.env
{name}.md.tpl # {name}.md模板
AGENTS.md
README.md # 仅面向用户
TODO.md # 任务版，仅保留两轮对话任务，每轮刷新
docs/PROGRESS.md # 项目进度，一行一个已完成/待完成任务
docs/research/ # 相关文献
tmp/
{feature}/ # 功能实现。包括share/
{feature}/{WHY,DESIGN,TASKS}.md # 功能文档。分别为“为什么引入这个功能”，“用户体验与页面设计”，“实现该feature的步骤”

## Code Style
界面、报告、文档用中文
UTF-8
新增或修改文档时保留@zone标记

## Git Workflow
提交时机：改动前提交；用户满意改动后提交
提交门槛：通过完成定义
一次提交只覆盖一个{feature}/

### Git Commit 要求
例：git add -A && git commit -m "feat: 新增重建页拖拽对齐（prompt: 图形可拖拽拼合）"
提交信息格式：<类型>: <简述>（来源: <prompt 简述>）
类型：feat/fix/refactor/docs/test/chore
实验任务：开exp/<名字>分支
.gitignore 必含 .env、.venv/、__pycache__/；密钥、目标图缓存不入库
提交须包括测试

## Boundaries
先问用户：装新依赖、改端口、删改docs/中文件、改本文件

不做：
测量值进文档：测试项数、模块数、路由数
用户授权前勾选或取消勾选里程碑复选框。
用户授权前新建文档
KB-Mixed

## 完成定义
当且仅当：
新增的每条命令、路径、版本都跑过且有输出；
{测试代码待定} 退出码 0；
涉及 `src/` 时服务能起，`GET /` 返 200；

<!-- /@zone user -->
