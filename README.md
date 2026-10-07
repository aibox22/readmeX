# readmex

readmex 是一份 Cursor skill。它扫描目标仓库，再由 agent 写下 README、SVG Logo 或 MkDocs 文档站。

安装到当前用户、供所有仓库使用：

```bash
gh skill install aibox22/readmeX readmex --agent cursor --scope user
```

只装进当前仓库：

```bash
gh skill install aibox22/readmeX readmex --agent cursor --scope project
```

装好之后，在目标仓库里要求生成 README、Logo 或文档站即可。
