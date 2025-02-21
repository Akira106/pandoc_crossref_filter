---
output:
  custom_document:
    path: sample.md
    pandoc_args: [
        "--to=gfm",
        "--filter=pandoc_crossref_filter",
        "--wrap=preserve"
    ]
  word_document:
    path: sample.docx
    toc: true
    pandoc_args: [
        "--filter=pandoc_crossref_filter"
    ]
pandoc_crossref_filter:
    section:
      auto_section: true
      start_header_level: 2
    figure:
      figure_number_count_level: 1
    table:
      table_number_count_level: 2
    code_block:
      save_dir: "assets"
---
# pandoc_crossref_filterによる相互参照のサンプル

## 自動でセクション番号が付与されます {#sec:sec1}
### 自動でセクション番号が付与されます {#sec:sec2}
#### 自動でセクション番号が付与されます {#sec:sec3}
##### 自動でセクション番号が付与されます {#sec:sec4}

## .unを付与すると、章番号を付与しません {.un}

セクション番号の参照ができます。

- [@sec:sec1]
- [@sec:sec2]
- [@sec:sec3]
- [@sec:sec4]

## [@sec:sec2]-A) ヘッダーの中でもセクション番号を参照できます {.unnumbered}

## 図番号の参照

[@fig:fig1]を参照します。

![図番号の参照のサンプルです](http://mirrors.creativecommons.org/presskit/logos/cc.logo.large.png){#fig:fig1}

## 表番号の参照

[@tbl:tbl1]を参照します。

|列A|列B|
|:---|:---|
|テスト|です|
|`<br>`を使うと、表の中も改行できます(Word変換にも対応。)|・改行<br>・される<br>|
|表の中でも参照が使えます|[@sec:sec1], [@fig:fig1]|

: 表番号の参照のサンプルです{#tbl:tbl1}

## PlantUMLの相互参照

特殊な記法ですが、plantumlで作成した図も相互参照できます。

```{.plantuml}
'filename=test1.svg
'#fig:puml1
'caption=処理Xのシーケンス図

mainframe シーケンス1
participant 機能A as A
participant 機能B as B

A -> B: リクエスト
ref over B: [@fig:puml2]参照
B --> A: 応答
```

<br>

```{.plantuml}
'filename=test2.svg
'#fig:puml2
'caption=処理Xの詳細

mainframe シーケンス2
participant 機能B as B
participant 機能C as C

B -> C: リクエスト
C -> C: [@sec:sec1]を参照
C --> B: 応答
```