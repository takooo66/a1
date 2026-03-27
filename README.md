# a1

## 目的
このリポジトリは、最小構成で実装・テスト・レビュー運用を確認するためのサンプルです。  
`src/` に実装、`tests/` に対応するテストを配置し、基本的な品質ゲート（Lint / Format / Test）を明示します。

## セットアップ手順
1. Python 3.10 以上を用意する。
2. （任意）仮想環境を作成して有効化する。
   ```bash
   python -m venv .venv
   source .venv/bin/activate
   ```
3. 必要に応じてツールをインストールする。
   ```bash
   pip install -U pytest ruff
   ```

## 想定実行方法
### サンプル実装の実行
```bash
python -c "from src.text_utils import normalize_whitespace; print(normalize_whitespace('  hello   world  '))"
```

### 品質チェック（レビュー観点）
- Lint
  ```bash
  ruff check .
  ```
- Format
  ```bash
  ruff format .
  ```
- Test
  ```bash
  python -m unittest discover -s tests -p 'test_*.py'
  ```
