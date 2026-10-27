<!-- @zone code -->

# ui-share — 索引
职责：**组件**。知道怎么画，不知道对错。无业务逻辑、不引用 kbp/contracts 的业务类型。

**本目录不对应 Python 包**，留在仓库根目录；被 `web/` 里的多个页面复用
（`rebuild` 的画布与 `score` 的差异图都要画概念图，各写一份迟早分叉）。

## 判定规则（来自 SPEC）

放"知道怎么画、但不知道对错"的东西。
一旦组件要知道"这条命题对不对"，它就不属于 ui-share，而属于对应 feature。

| 属于 ui-share | 不属于（属于 feature） |
|---|---|
| 概念块、连线、箭头等图元 | 判断"这条连线是否在目标图中" |
| 画布上的选中态与拖动 | 计算"分数是多少" |
| 按钮、输入框、弹层、布局骨架 | 决定"该不该允许提交" |
| 颜色/字号/间距等样式令牌 | 读取或写入数据库 |

## 文件

| 文件 | 职责 |
|---|---|
| `styles/*.css` | 视觉契约，原样取自用户原型（tokens/base/home/report/diagram/subpage/canvas/load） |
| `canvas/geometry.ts` | 概念块尺寸、连线出入点、同对多线的弯曲与连接词位置 |
| `canvas/RebuildCanvas.tsx` | 重建画布：概念块、连线、点选与拖动、待定虚线 |
| `canvas/useNodeDrag.ts` | 节点拖动：位移小于 4px 算点击 |
| `canvas/NodeChip.tsx` | 节点：圆角底 + 标签，选中反色 |
| `canvas/EdgeLine.tsx` | 连线：路径 + 加宽命中区 + 连接词底板 |
| `canvas/MarkerDefs.tsx` | 重建图的箭头 |
| `canvas/diffTypes.ts` | 一条判定与差异图筛选的形状 |
| `canvas/DiffMap.tsx` | 差异图组装：箭头、边、节点 |
| `canvas/DiffEdge.tsx` | 差异图的边与五类笔迹 |
| `canvas/DiffNodes.tsx` | 差异图的节点，只画被判定用到的概念 |
| `canvas/DiffMarkerDefs.tsx` | 差异图五种笔迹各自的箭头 |
| `atoms/Mark.tsx` | 五类判定的形状标记（不靠颜色） |
| `layout/Panel.tsx` | 入场面板，按下标错峰 |
| `layout/SubBar.tsx` | 返回条与页头 |
| `layout/RailGroup.tsx` | 零件栏分组容器 |

画布用直接 SVG 而非 ReactFlow：原型是固定 960×540 的空间，没有平移缩放，
ReactFlow 的视口与 handle 交互反而与设计冲突。

## 无障碍（全组件通用）

- 不用红/绿区分状态：一律"形状差异 + 文字标签"
- 命中区不小于 24px（触摸屏点-点连线要求）
- 不依赖悬停才能看懂的说明，关键说明常驻可见

<!-- /@zone code -->
