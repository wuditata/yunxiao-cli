# 项目级配置：.yunxiao.json

在使用本 skill 的项目根目录放置 `.yunxiao.json`，agent 启动前读取此文件获取上下文。

## 字段说明

```json
{
  "token": "<登录 token>",
  "profile": "pm-dev",
  "project": "<project_id>",
  "assignee": "张三"
}
```

| 字段 | 说明 |
|------|------|
| `token` | 云效登录 token，用于 `yunxiao_cli login token <token>` |
| `profile` | CLI profile 名，作为所有命令的 `--profile` 参数 |
| `project` | 当前代码仓对应的云效项目 ID |
| `assignee` | 当前用户身份标识，用于过滤"我的工作项"等场景 |

## 安全注意

`.yunxiao.json` 含明文 token，必须加入 `.gitignore`：

```
.yunxiao.json
```

## 初始化流程

首次配置后执行：

```bash
yunxiao_cli login token <token> --account <account_name>
yunxiao_cli profile add <profile> --account <account_name> --org <org_id> --project <project_id>
yunxiao_cli profile use <profile>
```
