# Airwallex Track 8 — Escrow-Bound Marketplace Settlement Agent

最小 demo：seller reserves（卖家储备金）+ net payouts（净额结算）+
risk-adjusted limits（风险调限额），落在 Airwallex 法币 payout 上。
定位：不追奖，打 Escrix 法币 escrow 的基础。交件 **周日 11/15 早上 10:29 PT**
（窗口 10:29 关，不是晚上）。

## 今晚 / 今天能做的事（不用等准入批复）

准入申请昨晚 21:07 PT 已发在 Slack `#platforms-kits-5-6-7-and-8`，
Account ID `acct_6nTcO1PLNw2O9S1QTrFzpQ`，
Client ID `OW4WNxLgQ3aX957n4IzkuA`（`hackathon2` key；旧 `hackathon` key
服务器端已坏，不再用）。
批复没到之前，这三件事都能做，默认 sandbox 本来就支持：

1. 登录 + 查余额（`GET /api/v1/account/wallet_info`）
2. 跑通 escrow 核心：锁钱 → 验证 → 净额放款 / 全额退款（`escrow.py`，已写好）
3. 模拟充值、跑 demo 账本、录视频的脚本（`demo.py --offline`）

等批复到了才做的事：`POST /api/v1/accounts/create`（connected accounts）、
`POST /api/v1/beneficiaries/create`、`POST /api/v1/transfers/create`。
`demo.py` 里有个 probe：批复到了它会报 ENABLED，没到会报 HTTP 400，
不用猜。

## 怎么跑

```bash
cd airwallex-track8-demo
python3 test_escrow.py        # 先跑这个，5 个测试全过
python3 demo.py --offline     # 离线账本：3 个 job，1 个失败退款分支
cp .env.example .env          # 把 API key 填进 .env（只放本机，绝不提交）
python3 demo.py               # 再跑一次：登录 + 余额 + 准入 probe
```

只用 Python 标准库，不用 pip。API key 跟密码一样，别发 Slack、别进 repo、
别截图发出来；Client ID 不是密钥，Slack 申请里已经贴过了。

## 五天计划（每天 2–3 小时）

- 周一 11/09：今天 — 跑通上面这套，确认登录 + 余额能通
- 周二 11/10：核心流接上 sandbox（锁钱 → 验证 → 放款/退款）
- 周三 11/11：风险调整 + demo 脚本
- 周四 11/12：端到端跑通 + 录视频（5 分钟以内）+ 写 setup 说明
- 周日 11/15 早上 10:29 前：交件（demo + 视频 + repo + setup 说明）

## 还没办的事

- Webinar：至少参加一场。11/06 那场已错过，下一场时间还没公布 —
  在 Slack `#help` 问一句（草稿昨晚已给）。
- 队名还是默认 "Haodong's Team"，有空在 HackerEarth 后台改成 Escrix，
  不影响评审。
- 批复：每天早上 digest 会盯 Slack 回复；`demo.py` 的 probe 也能自己查。

## 文件

- `escrow.py` — escrow 核心（纯逻辑，无网络）：reserve / verify /
  net payout / refund / risk-adjusted cap
- `airwallex_client.py` — sandbox 客户端：login、wallet_info、
  connected-accounts probe、create_transfer（批复后才调）
- `demo.py` — 一键演示：离线账本 + 在线 sandbox 检查
- `test_escrow.py` — 5 个测试
- `.env.example` / `.gitignore` — 密钥只放本机 `.env`
