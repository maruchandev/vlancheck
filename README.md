# VLAN 検査サーバー

ラズパイを固定IP `10.0.0.1` で設置し、教室ごとの VLAN 疎通検査を curl だけで記録・進捗管理するツール。

## セットアップ(ラズパイで一度だけ)

```bash
# 1. 固定IP (10.0.0.1/8)
sudo nmtui   # Wired connection → IPv4 Manual → 10.0.0.1/8, GW, DNS

# 2. 配置
sudo mkdir -p /opt/vlancheck
sudo cp server.py /opt/vlancheck/
sudo cp vlancheck.service /etc/systemd/system/

# 3. 常駐起動
sudo systemctl daemon-reload
sudo systemctl enable --now vlancheck

# 4. 確認
curl 10.0.0.1/h
```

## 使い方(全コマンド curl だけ)

```bash
curl 10.0.0.1/p/N101     # 検査(現場で打つやつ)
curl 10.0.0.1/a/N500     # リストにない部屋を追加
curl 10.0.0.1/d/N101     # 誤検査の取り消し
curl 10.0.0.1/r          # 一覧(検査済み/未検査・担当者)
curl 10.0.0.1/g          # 進捗(件数・%)
curl 10.0.0.1/h          # ヘルプ
```

## 事前定義の変更

`server.py` 冒頭の2箇所のみ編集する。

- `ROOMS`: 検査対象の部屋リスト
- `PEOPLE`: 担当者PCの固定IP → 名前(検査時に自動記録される)

## 記録

検査結果は `checklist.json`(部屋ごとに done / time / who)に保存され、再起動後も残る。
