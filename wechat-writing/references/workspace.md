# 工作区与恢复

只在用户要求保存、继续、多轮打磨、学习长期风格，或任务明显需要跨轮恢复时读取。目标是可靠保存用户写作状态，同时避免把私人材料写入 Skill 安装目录或错误文章。

## 确定写作工作区

按以下顺序解析，命中后停止：

1. 用户本次明确指定的写作目录；
2. 当前项目中已经存在且包含 `articles/`、`author-profile.md` 或 `style-lessons.md` 的 `workspace/`；
3. 当前项目中已经存在、且从对话可确认属于本写作任务的其他目录；
4. 确实需要持久化但没有候选目录时，使用当前项目的 `workspace/`。若当前工作区不是一个可写项目，询问一次保存位置，不自行改用 Skill 安装目录或用户主目录。

解析完成后记录本次任务使用的绝对路径。所有文章、指针和作者资料都必须位于该目录内；规范化路径后若目标越出工作区，停止写入并请用户重新指定。

不要根据 `SKILL.md` 所在位置推断用户工作区。Skill 被全局安装后，安装目录只保存通用方法和模板。

## 隐私与 Git

作者档案、写作样本和未发布文章默认视为私人内容。目标目录位于 Git 仓库时：

- 已被 `.gitignore`、`.git/info/exclude` 或其他项目规则排除：可以按用户请求保存；
- 尚未被排除：在写入私人资料前说明风险，并询问是加入忽略规则还是改用其他目录；不要静默提交或暂存这些文件；
- 用户明确要求版本控制某篇文章时，只对该文章执行，不自动扩大到作者档案和全部样本。

普通单轮写作不因存在工作区规则而强制落盘。

## 初始化文件

模板位于 Skill 包内：

- `assets/author-profile.template.md` → `<工作区>/author-profile.md`
- `assets/style-lessons.template.md` → `<工作区>/style-lessons.md`
- `assets/article-brief.template.md` → `<工作区>/articles/<文章目录>/brief.md`

只在真正需要相应文件时复制。复制后写入目标文件，永远不修改模板。已有目标文件先读取并局部更新，不覆盖。

## 文章目录和活动指针

持久化文章使用：

```text
workspace/
├── active-article.md
└── articles/
    └── YYYYMMDD-short-title/
        ├── brief.md
        ├── sources.md
        ├── draft.md
        ├── review.md
        ├── final.md
        └── versions/
```

`active-article.md` 只保存工作区内的相对路径和更新时间：

```yaml
article: articles/YYYYMMDD-short-title
current: draft.md
updated: YYYY-MM-DD
```

`current` 只能是文章根目录中的 `draft.md` 或 `final.md`。创建新的跨轮文章目录、切换文章、写入新草稿或完成终稿后更新指针。路径必须解析到当前工作区的 `articles/` 内；指针或当前文件无效时忽略相应字段，不跟随到外部目录。

`brief.md` 中记录 `status: active | paused | complete`。开始跨轮任务时为 `active`，等待用户材料时可标为 `paused`，文字终稿完成时标为 `complete`。旧文章没有状态字段时仍可恢复，不强制迁移。

## “继续上次文章”的恢复顺序

1. 当前对话已经明确文章目录或标题：使用它，并校验目录仍在工作区内；
2. 否则读取有效的 `active-article.md`；
3. 指针缺失或失效时扫描 `articles/`：先看 `active` 或 `paused` 文章；只有一个未完成候选则使用，多个未完成候选时列出最近更新的至多 3 个标题和日期，只问一次让用户选择；没有未完成文章时再对 `complete` 或无状态的旧文章使用同样规则，不按目录顺序或模糊相似度静默猜测；
4. 没有候选时说明尚无可恢复文章，并继续处理用户当前提供的材料。

恢复文章时：

- 读取 `brief.md`；
- 指针含有效 `current` 时读取该文件；旧指针没有 `current` 时，优先读取存在的 `final.md`，只有 `draft.md` 明确更新或 `review.md` 表明终稿之后仍在修改时才回到 `draft.md`；
- `review.md` 存在时读取其中仍未解决的阻断项；
- `versions/` 只作为历史，不参与“最新稿”自动选择；
- `sources.md` 仅在当前工作需要事实或来源时读取。

恢复后只加载当前步骤需要的上下文，不把全部历史版本灌入对话。若 `review.md` 标明“需要作者输入”，先提出那个会实质改变结果的问题，再继续。

## 保存与覆盖规则

- 用户提供的原稿不覆盖；修改稿写入文章目录。
- 写入前读取目标文件，保留未知的用户内容。
- 普通语言修订不制造新版本；实质重写且用户希望比较时才写入 `versions/`。
- `sources.md`、`review.md` 和 `versions/` 都按需创建，不创建空文件。
- 写入 `draft.md` 后把活动指针的 `current` 设为 `draft.md`；最终文字写入 `final.md` 后改为 `final.md`，并将 `brief.md` 状态更新为 `complete`。活动指针可以保留，方便后续修订，创建下一篇文章时再切换。
