<!-- @zone code -->

# TODO — kit-build-plus
任务版，只留两轮。每轮整体重写。复选框可由 agent 勾选。

## 交接

已验证：.venv/bin/python -m pytest 退出 0；flake8 退出 0；npm test 退出 0；
uvicorn 起在 127.0.0.1:8848，GET / 与 /api/health 均 200。
阶段 0 至 6 后端大体落地，人工裁定批首次用到即进库。
测验与量表已按用户意思整条删除：因变量由问卷星等外部平台收集，
本项目不出题、不收答。
前端有首页、教材准备、建图、差异图、历史、导出六页；
教材准备页可看批次、切批、重抽。
当前分支 fix/audit-20261028，改动未提交。

踩过的坑：
1 契约冻结，改前给旧→新、影响范围、迁移方式，等用户确认
2 新契约文件不得与 feature 子包同名
3 deps 的连接锁与写锁必须分开，合并会自锁超时
4 导出表按列名取值测试，别用数字下标
5 flake8 上限 100 列，配置在 .flake8
6 base_url 填到根，代码自己拼 /v1/chat/completions
7 密钥只走环境变量，不进文件、日志、响应、commit
8 测完服务用 fuser -k 端口/tcp；pkill -f uvicorn 会连承载 shell 一起杀掉
9 pydantic 字段名不能叫 construct，会与 BaseModel 自带方法撞名
10 变异验证后必须删 __pycache__：改回同长度的源码若落在同一秒，
   pyc 被认为有效，跑的还是旧代码
11 前端只认 client.ts 一个出口；新接口要先补 types/api.ts，
   否则类型断言会盖住后端字段变更
12 写锁不可重入：会把库写进去的调用必须整段落在锁内，且只进一层
13 下载类接口要看 Content-Disposition，文件名由后端给，前端不自己拼
14 批次一换，概念 id 就换了一套，恢复草稿要先比对 map_version
15 一份教材同时只有一批在用：切批时先清这份教材的全部标记，再置新的那批
16 版本号是教材内唯一，判「这一版被用过没」必须带 material_id，
   否则别的教材用过 v1 就把新教材的 v1 判成锁定
17 split 会剪掉没被命题用到的零件，所以改图那一份 kit 不能从命题反推，
   要直接读库里存的概念与连接词
18 后端改了接口先重启再点界面：旧进程还在跑旧代码时，前端拿不到新字段，
   异常又被事件回调吞掉，表现是「点了没反应」
19 headless 里改输入框用原型上的 value setter 再派发 input，改完要等一拍
   再改下一个 select，否则读到过期闭包

## 本轮

- [x] 版本锁按教材限定：SubmissionUsage 带 material_id，别的教材用过 v1
      不再锁死新教材的 v1；GET /api/lock 增必填 material_id
- [x] 手机拖概念整页跟着动：零件栏的 draggable 只在细指针设备上开，
      另加触屏搬运手势——按住在零件栏、拖到画布松手即放下
- [x] 手机上传教材后立刻退回选择教材处：进画布直接按新教材开，
      不再回落列表第一项；配套 web/tests/flowStart.test.ts 与 carry.test.ts
- [x] 给 fx 补外部冻结入口（?fx=freeze、?veil=static 一类）：
      aurora、globe、loadglobe 复用既有静帧与 stop，不另开渲染路径，
      正常浏览与 prefers-reduced-motion 分支不变
- [x] 新增 web/tools/shot.mjs：只用 node 内置 fetch 与 WebSocket 驱动 CDP，
      Chrome 进独立进程组，正常结束、中断、异常与硬超时都整组 SIGKILL
- [x] 归档临时测量架引发的资源泄漏：.scratch/fx-measure/BUG.md 记现象、
      根因、复现、修复清单与验收，并写明不杀 gpu 子进程、不靠
      visibilitychange、不用 --single-process
- [x] 设置里加开发者模式：密码 1234321，服务端再验一次；开关记忆在浏览器，
      关掉即清
- [x] 开发者模式可改目标图任意命题的三元组，也可加删命题、改名增删概念与连接词
- [x] 开发者改动落库而非只存浏览器：新增 dev_overlay 表，读图时盖在冻结图上，
      冻结图的指纹、版本号与投用标记不动，撤销即删该行；草稿与提交按改后的图校验
- [ ] 手机连不上开发服：ufw 开启且默认 DROP，5173 未放行；要用户执行
      sudo ufw allow 5173/tcp（vite 已绑 0.0.0.0:5173，放行后即可用局域网 IP 访问）
- [ ] 手机上上传教材后回主页：已按「新教材直接进画布」改过一处，
      只剩真机确认是不是整页重载引起

## 上一轮

- [x] 重抽批次界面接通：新增 GET /api/kit/entry（复用 KitOut，
      靠 kit_service.version_kit 取某一批零件集），BatchList 列版本号、
      来源、命题数、时间，可切批可重抽，样式单独放 batch.css
- [x] App 拆出 hooks/useKit.ts 与 hooks/useAttempts.ts，从 253 行回到 190 行
- [x] 恢复远程草稿前先核对 map_version，切批后旧草稿不再串到新图上
- [x] 后端补 tests/api/test_kit_versions.py 两条用例并做变异验证
- [x] 导出页补预览表：GET /api/export/preview 回表头、前几行与总行数
      （默认 8 行，1 到 50），单元格先拼 CSV 再读回来，与下载逐字一致；
      前端 Preview 组件横向滚动展示，空单元格显示破折号
- [x] 抽 ui-share/atoms/Notice.tsx：错误与状态的角色配对收进一处
- [x] 按用户意思删掉超时自动提交：那是实验设计的内容，项目不做计时
- [x] 首页三个入口改纵向一行一个：entries 单列、最宽 560
- [x] 按设备自动选版式：web/src/data/device.ts 看 UA 写 html[data-device]，
      ui-share/styles/device.css 管触控目标、动作条竖排、画布单列
- [x] 修「切换批次后两个都显示在用」：mark_in_use 只置新批、不清旧批，
      改成先清这份教材的全部标记再置新批
- [x] 手机极光细条纹：按输出空间抖动，幅度按放大倍数预加重；
      真机复测后决定不再追，抖动留在树里

## 未解决

### 阶段 7 前端

- [ ] 按钮仍有 18 处各 view 手写 button 加 .btn 类：视觉已由 base.css 统一，
      是否再抽 atoms/Btn（只省 class 拼装）待定，抽之前不迁移
- [ ] useStudyFlow.ts 超出单文件行数约定，是否单开一轮拆待用户定

### 阶段 8 文档（用户已说先不动，等叫）

- [ ] 各 feature 的 DESIGN.md 与多份 INDEX、WHY 仍是旧风格：
      有表格、粗体、引用块、代码围栏
- [ ] kbp/contracts 只有 INDEX.md，缺 WHY 与 TASKS；kbp/api 没有 DESIGN.md，
      是否补要用户定
- [ ] web 与 ui-share 没有索引文档，导出页、批次组件与两份钩子未在文档里露面
- [ ] 每份随所属 feature 的提交一起改，不单开纯文档提交

<!-- /@zone code -->
