# 安装、使用与排错 / Installation and use

## 三种入口

1. **只看效果**：打开在线图谱，或解压发行包后打开 `docs/index.html`。无需运行环境。
2. **让 Agent 选图制作**：把完整技能文件夹放入工具支持的技能目录。
3. **运行现成生成器**：Python 助手处理六类通用图；Node.js 重建固定数据的54例图谱。

## Agent 安装

在你的项目根目录执行对应命令。需要 Git；命令可用于 PowerShell、macOS 和 Linux。

### Codex

```sh
git clone https://github.com/jigongxian900-dotcom/data-charts-master.git .agents/skills/data-charts-master
```

目录结果为 `.agents/skills/data-charts-master/SKILL.md`。在同一项目打开会话，输入 `$data-charts-master` 后描述任务。

### Claude Code

```sh
git clone https://github.com/jigongxian900-dotcom/data-charts-master.git .claude/skills/data-charts-master
```

目录结果为 `.claude/skills/data-charts-master/SKILL.md`。在同一项目打开会话，输入 `/data-charts-master` 后描述任务。

### 下载 ZIP / 其他 Agent

从 Releases 下载并解压。把**包含 `SKILL.md` 的完整文件夹**改名为 `data-charts-master`，放入工具的自定义技能目录。不要多嵌套一层，也不要只复制 `SKILL.md`。

工具没有技能发现功能时，可直接说：“读取 `安装路径/SKILL.md`，按其中方法完成这次图表任务。”此方式依赖 Agent 能读取本地文件。

**用户范围安装**：Codex 支持 `~/.agents/skills/data-charts-master/`；Claude Code 支持 `~/.claude/skills/data-charts-master/`。`~` 指当前用户主目录，PowerShell 中可用 `$env:USERPROFILE` 定位。项目范围和用户范围选其一，避免同名技能重复发现。

安装路径依据：[OpenAI 本地技能目录](https://learn.chatgpt.com/docs/build-skills?kbid=111697)、[Claude Code 技能目录](https://code.claude.com/docs/en/skills#choose-where-skills-load)。文件放置核验不等于所有客户端的自动发现都已实测。

## 第一次任务

```text
使用 data-charts-master。
业务问题：哪些区域没有达到目标？是规模差，还是改善不足？
受众：区域经营负责人。
数据：附上期间、区域、实际、目标、上期与单位；缺失保留为空。
输出：单文件离线 HTML、源数据表、手机布局、SVG 下载。
配色：石榴红。先按问题选图，差额采用共同基准。
```

通常交付 HTML 和源数据；文件名按任务确定。图型、解释与交互由问题决定，不会因为安装技能就运行自动后台服务。

## 运行 Python 样例

进入技能文件夹，以 Python 3.10+ 执行。使用标准库，不需要 `pip install`。

```sh
python scripts/chart_html.py validate examples/representative.json
python scripts/chart_html.py build examples/representative.json --out sample.html --theme ruby
```

Windows 可将 `python` 改为 `py`。成功后生成 `sample.html`、`sample.data.json`。用浏览器打开 HTML。

通用助手支持 `bar`、`line`、`stacked`、`waterfall`、`box`、`scatter`。自定义数据先看[输入格式](../references/html-delivery.md)，再运行 `validate`。54例图谱需要按案例修改，不能把任意 JSON 直接传给它。

## 开发与重建

需要 Node.js 20+，无需 npm 依赖：

```sh
node scripts/build_gallery.js
```

该命令重建 `examples/dashboard-atlas/atlas.html`、`source-data.json` 与54份 SVG，并同步 `docs/index.html`、`docs/source-data.json` 和 `docs/labs/`。因此本地样例与 GitHub Pages 不会因漏复制而分叉。

| 目录 | 内容 |
|---|---|
| `SKILL.md` / `references/` | 选图、数据、视觉和交付方法 |
| `assets/color-system.json` | 七套配色令牌 |
| `examples/dashboard-atlas/` | 固定数据54例、生成器与SVG |
| `examples/interaction-lab/` | 三个完整交互实例 |
| `examples/composed/` | 六图教学报告与可翻页演示，附同源输入 |
| `examples/operating-story/` | 一组八市场原始数据组成的连续经营案例 |
| `examples/representative.json` | 六类通用图的完整输入 |
| `docs/` | 公开图谱、预览和说明 |

验证：

```sh
python scripts/test_chart_html.py
python scripts/test_compose_html.py
python scripts/test_operating_story.py
python scripts/verify_release.py
```

## 更新与卸载

Git 安装的版本可执行：

```sh
git -C .agents/skills/data-charts-master pull --ff-only
```

Claude Code 将路径改为 `.claude/skills/data-charts-master`。有本地修改时先保存自己的修改；不要用强制覆盖处理更新失败。

卸载时删除**当初安装的那一个技能文件夹**。自己生成的图表另存项目输出目录，避免和安装目录一起移除。

## 常见问题

- **Agent 找不到技能**：确认当前项目、目录层级和 `SKILL.md` 名称。打开新会话；仍未出现时直接指定文件路径。
- **目标文件夹已存在**：先判断是旧安装还是其他文件。更新旧安装，或换一个空目录，不覆盖现有内容。
- **Python 命令不存在**：Windows 尝试 `py --version`；生成样例需要安装 Python，直接浏览图谱不需要。
- **手机图太复杂**：优先使用重排读数；查看原图细节时可在图形区域横向滚动。核心原值仍可查表。
- **想改所有配色**：修改 `assets/color-system.json` 后重建，并检查可读性、含义与打印。

## English quick route

From a project root, clone into `.agents/skills/data-charts-master` for Codex or `.claude/skills/data-charts-master` for Claude Code. Open an agent session and invoke the skill. Keep the complete folder. ZIP users should avoid an extra nested directory.

For a runnable sample, enter the skill folder and execute the Python commands above. The output is `sample.html` plus `sample.data.json`. The Node build command rebuilds and synchronizes all public gallery files. Git updates use `pull --ff-only`. To uninstall, remove only the installed skill folder.
