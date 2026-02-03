---
output:
  custom_document:
    path: README.md
    pandoc_args: ['--to=gfm', '--filter=pandoc_crossref_filter', '--wrap=preserve']
pandoc_crossref_filter:
  section:
    auto_section: true
    start_header_level: 2
  table:
    table_number_count_level: 1
---

# Pandoc crossref filter

## 特徴

- Markdownの中で、セクション番号、図番号、表番号の相互参照を実現します。
- Pandocのカスタムフィルターとして動作します。
- VSCodeのプラグインである、Markdown Preview Enhancedとの連携が可能です。
- PlantUML/Mermaidの図の中にも引用を挿入することができます。
- 表の中で改行することができます。Pandocを使ってMarkdownをWordファイルに変換したときにも、改行が維持されます。
- 参照元にジャンプできるリンクを自動で付与します。ただし、現在はPandocの出力フォーマットが以下の場合のみ対応しています。
  - Word(docx)
  - HTML
  - GitHub Flavored Markdown(GFM)

<br>

既存の類似OSSである[pandoc-crossref](https://github.com/lierdakil/pandoc-crossref)を使わずに、本OSSを開発した理由は以下です。

- 章番号の自動カウントを開始するヘッダーのレベルを変更できます。
  例：開始レベルを2に変更すると、`## ヘッダー2` => `## 1. ヘッダー2`、`### ヘッダー3` => `### 1.1 ヘッダー3`のようになります。
- 図番号、表番号を、1からの連番ではなく、章番号や節番号に合わせた番号で付与することができます。
  例：[図1-1]、[表3-4-2]
- PlantUMLやMermaidの図の中にも引用を挿入することができます。またMarkdown Preview Enhancedを利用したプレビューやフォーマット変換に対応しています。

<br>

## インストール方法

### 事前に必要なもの

- Pandoc==3.6.2: [https://github.com/jgm/pandoc/releases](https://github.com/jgm/pandoc/releases)  
  ※異なるバージョンのPandocだと、動作が異なる場合があります。
- Python≧3.10: [https://www.python.org/downloads/](https://www.python.org/downloads/)

### インストール

まず、本プロジェクトをcloneしてください。

```shell-session
$ git clone https://github.com/Akira106/pandoc_crossref_filter.git
$ cd pandoc_crossref_filter
```

続いて、PlantUMLを使用する場合、PlantUMLサーバーのURLを設定します。

```shell-session
$ vi src/pandoc_crossref_filter/config.py
```

- 例：公開サーバーを使用する場合

```
PLANTUML_SERVER_URL = "https://www.plantuml.com/plantuml"
```

- 例：自前でサーバーを立てる場合

例えば以下のようなdocker-composeファイルで、サーバーを立てます。

```yaml
version: '3'
services:
  plantuml-server:
    image: plantuml/plantuml-server
    container_name: plantuml-local-server
    ports:
      - "8080:8080"
```

```shell-session
$ docker-compose up -d
```

`config.py`には、以下のように記述します。

```
PLANTUML_SERVER_URL = "http://127.0.0.1:8080"
```

最後に、pipでインストールします。

- Mermaidを使用しない場合

```shell-session
$ pip3 install .
```

- Mermaidを使用する場合

```shell-session
$ pip3 install .[all]
$ playwright install chromium
```

※ 上記の実行時に`XXXXX which is not on PATH.`のようなWarningメッセージが出た場合、環境変数`PATH`に、インストール先のパスを追加してください。

### Markdown Preview Enhancedのプレビュー画面との連携の設定

**※本設定を行うと、プレビュー画面の動作が重くなります。プレビュー画面を常に表示しながら同時に編集したい場合は、本設定を実施しないでください。**

Markdown Preview Enhancedのプレビュー画面で、本フィルターの機能をプレビューしたい場合は、以下の設定が必要です。

|VSCodeの設定項目|設定値|
|:---|:---|
|Markdown-preview-enhanced: Pandoc Arguments|["--filter=pandoc_crossref_filter"]|
|Markdown-preview-enhanced: Use Pandoc Parser|チェックをつける|
: Markdown Preview Enhancedのプレビュー機能との連携の設定{#tbl:tbl_mpe_preview}

<br>

### Markdown Preview EnhancedのPlantUMLの設定

また、Markdown Preview EnhancedでPlantUMLを使用する場合は、以下の**いずれか**の設定が必要です。

|VSCodeの設定項目|設定値|
|:---|:---|
|Markdown-preview-enhanced: Plantuml Jar Path|PlantUMLの.jarファイルをダウンロードして、そのパスを設定する。|
|Markdown-preview-enhanced: Plantuml Server|`PlantUMLサーバーのURL`/svg|
: Markdown Preview EnhancedのPlantUMLの設定{#tbl:tbl_mpe_plantuml}

## 使い方

### 参照の挿入方法 {#sec:sec_insert}

#### セクション番号の挿入

ヘッダーの末尾に`{#sec:XXX}`を追加します。

`例`

```
## ヘッダー2{#sec:test_sec}
```

#### 図番号の挿入

以下のように記載します。

```
![キャプション](図のパス){#fig:XXX}
```
`例`

```
![テストの画像](assets/test.svg){#fig:test_fig}
```

#### 表番号の挿入

表の下に、以下のようなキャプションを表の下に直接追加します。

```
: キャプション{#tbl:XXX}
```

`例`

```
| C1 | C2 |
|:---|:---|
| v1 | v2 |
| v3 | v4 |
: テストの表{#tbl:test_tbl}
```

<br>

##### 参考{.un}
Markdown Previce Enhancedを使用する場合、import機能で外部CSVファイルを表として使用するこができます。

`例`

```
@import "test.csv"
: importされた表{#tbl:import_tbl}
```

#### PlantUMLへの図番号の挿入 {#sec:sec_puml_insert}

1. \`\`\`{.plantuml}\`\`\`というコードブロックを使用します。**※1**
2. PlantUMLのコードブロックの中に以下のコメントを記載することで、図番号の挿入、キャプション、出力画像ファイル名の設定を行います。
  - 図番号の挿入：`'#fig:XXX`
  - キャプション：`'caption=YYY`
  - 出力画像のファイル名：`'filename=ZZZ`


**※1**
\`\`\`plantuml\`\`\`という表記でもPandoc単体なら動作しますが、PlantUMLの中で[@sec:sec_cite]に示す引用を使用した場合、Markdown Preview Enhancedとの連携が正しく動作しなくなります。

`例`

    ```{.plantuml}
    'filename="test.svg"
    '#fig:fig_puml
    'caption=PlantUMLの画像です

    Bob -> Alice : hello
    ```

#### Mermaidへの図番号の挿入 {#sec:sec_mermaid_insert}

1. \`\`\`{.mermaid}\`\`\`というコードブロックを使用します。**※1**
2. Mermaidのコードブロックの中に以下のコメントを記載することで、図番号の挿入、キャプション、出力画像ファイル名の設定を行います。
  - 図番号の挿入：`%%#fig:XXX`
  - キャプション：`%%caption=YYY`
  - 出力画像のファイル名：`%%filename=ZZZ`


**※1**
\`\`\`mermaid\`\`\`という表記でもPandoc単体なら動作しますが、Mermaidの中で[@sec:sec_cite]に示す引用を使用した場合、Markdown Preview Enhancedとの連携が正しく動作しなくなります。

`例`

    ```{.mermaid}
    %%filename="test.svg"
    %%#fig:fig_puml
    %%caption=Mermaidの画像です
    sequenceDiagram
      Bob ->> Alice : hello
    ```


### 参照の引用 {#sec:sec_cite}

セクション番号、図番号、表番号を、それぞれ

- `[@sec:XXX]`
- `[@fig:XXX]`
- `[@tbl:XXX]`

で引用することができます。
(`XXX`は、[@sec:sec_insert]で挿入したものに対応します)

引用は、本文、箇条書き、表、ヘッダー([@sec:sec_cite_in_header]) 、コードブロックの中(PlantUML/Mermaidの図の中、[@sec:sec_cite_in_puml])で使用することができます。

<br>

また、末尾に`+title`を追加することで、タイトルも一緒に引用することができます。

`例`

- `[@sec:XXX+title]`
- `[@fig:XXX+title]`
- `[@tbl:XXX+title]`

### 設定値

Markdownファイルの先頭に`---`で囲ったブロックを記述します。その中で、以下のように`pandoc_crossref_filter`から始まるYAML形式で、設定を記載することができます。

```
---
pandoc_crossref_filter:
  section:
    ...(設定値)
  figure:
    ...(設定値)
  table:
    ...(設定値)
  code_block:
    ...(設定値)
---
```

- `section`の設定値

|設置値|型|デフォルト値|内容|
|:---|:---|:---|:---|
|auto_section|boolean|false|ヘッダーの先頭に、自動でセクション番号を追加します。|
|start_header_level|integer|1|セクション番号のカウントを開始するヘッダーのレベルを設定します。例えば2を設定した場合、ヘッダー1はセクション番号のカウントに含まれなくなります。|
|section_title_template|array[string]|["%s."]|ヘッダーの先頭に挿入されるセクション番号の文字列のテンプレートです。`%s`の中に実際のセクション番号が挿入されます。配列で複数指定することで、ヘッダーのレベルに応じてテンプレートを変更することができます。|
|delimiter|string|"."|セクション番号の数字の区切り文字です。|
|section_ref_template|array[string]|["第%s章", "%s節", "%s項", "%s目"]|参照を引用したときの、セクション番号の文字列のテンプレートです。`%s`の中に実際のセクション番号が挿入されます。配列で複数指定することで、ヘッダーのレベルに応じてテンプレートを変更することができます。|
: セクション番号の設定項目{#tbl:tbl_config_section}

- `figure`の設定値

|設置値|型|デフォルト値|内容|
|:---|:---|:---|:---|
|figure_number_count_level|integer|0|図番号の連番をカウントするヘッダーのレベルです。<br>例：<br>・0を設定：`図X`のように、ドキュメント全体で連番を使用します。<br>・1を設定：`図1-X`のように、章番号ごとに連番をカウントします。<br>・負の値を設定：個別のヘッダーごとに連番をカウントします。|
|figure_title_template|string|"[図%s]"|図番号の文字列のテンプレートです。`%s`の中に実際の図番号が挿入されます。|
|delimiter|string|"-"|図番号の区切り文字です。|
: 図番号の設定項目{#tbl:tbl_config_figure}

- `table`の設定値

|設置値|型|デフォルト値|内容|
|:---|:---|:---|:---|
|table_number_count_level|integer|0|表番号の連番をカウントするヘッダーのレベルです。<br>例：<br>・0を設定：`表X`のように、ドキュメント全体で連番を使用します。<br>・1を設定：`表1-X`のように、章番号ごとに連番をカウントします。<br>・負の値を設定：個別のヘッダーごとに連番をカウントします。|
|table_title_template|string|"[表%s]"|表番号の文字列のテンプレートです。`%s`の中に実際の表番号が挿入されます。|
|delimiter|string|"-"|表番号の区切り文字です。|
: 表番号の設定項目{#tbl:tbl_config_table}

- `code_block`の設定値

|設置値|型|デフォルト値|内容|
|:---|:---|:---|:---|
|save_dir|string|"assets"|PlantUML/Mermaidを画像出力したときの、出力先のディレクトリのパスです。|
: コードブロックの設定項目{#tbl:tbl_config_code_block}

### その他の機能

#### セクション番号のカウントの除外

ヘッダーの後ろに`{.un}`または`{.unnumbered}`を記載することで、そのヘッダーはセクション番号をカウントから除外します。

`例`

```
# このヘッダーはセクション番号のカウントから除外される{.un}
```

#### ヘッダー内のセクション番号の引用{#sec:sec_cite_in_header}

ヘッダー内で、他のセクション番号を引用することができます。
例えば、セクション番号のカウントを、途中から数字からアルファベットに変更したい場合など、細かい動作を指定するのに有効です。

#### PlantUML/Mermaid内の相互参照{#sec:sec_cite_in_puml}

PlantUML/Mermaidのコードブロック内で、[@sec:sec_cite]の引用を使用することが可能です。
ただし、Markdown Preview Enhancedとの連携を行う場合は、[@sec:sec_puml_insert]に記載したように、コードブロックの先頭を`{.plantuml}`/`{.mermaid}`で開始する必要があります。

##### 補足{.un}

コードブロックの先頭を`plantuml`/`mermaid`で開始した場合、Markdown Preview Enhancedの機能でエクスポートを行ったときに、
本フィルターが相互参照を解決するよりも先に、Markdown Preview EnhancedによってPlantUML/Mermaidの画像出力が実行されてしまい、相互参照を解決できなくなります。

#### 表の中の改行

表の中で、`<br>`を使うことで、改行ができます。Pandocの機能でWordファイルに変換した場合にも、本フィルターを使用することで、Wordファイル内で改行が維持されます。

#### SoftBreakの改行変換

Markdownで改行する場合は、末尾にスペースを2つ付ける必要があります。
しかし本フィルターを使用することで、Markdown中のただの改行(SoftBreak)を、改行に変換することができます。

### エクスポート

PandocまたはMarkdown Preview Enhancedの機能を使って、相互参照を解決したファイルをエクスポートすることができます。

#### GitHub Flavored Markdown(GFM)への変換 {#sec:sec_gfm_export}

Markdownファイルの先頭に`---`で囲ったブロックを記述します。その中で、以下のようにMarkdown Preview Enhancedのエクスポート設定を記載することで、エクスポートが可能になります。

`例`

以下の設定例では、対象のMarkdownを`test_export.md`というファイル名でエクスポートします。

```
---
output:
  custom_document:
    path: test_export.md
    pandoc_args: ['--to=gfm', '--filter=pandoc_crossref_filter', '--wrap=preserve']
---
```

上記を設定したら、VSCodeで以下のような操作を行うことで、エクスポートが可能です。

- 対象のMarkdownファイルに対して右クリック
- → 「Markdown Preview Enhanced: Open Preview to the Side」をクリック
- → プレビュー画面で右クリック
- → 「Export」→「Pandoc」

#### Wordファイルへの変換

[@sec:sec_gfm_export]と同様に、`pandoc_args`の設定に本フィルターを追加することで、エクスポートが可能になります。
※エクスポート設定の詳細は、Markdown Preview Enhancedのマニュアルをご参照ください。

`例`

```
---
output:
  word_document:
    path: output_docx/test_export.docx
    toc: true
    pandoc_args: ['--filter=pandoc_crossref_filter', '--wrap=preserve']
---
```

### サンプル

[sample](sample/)にサンプルを記載しています。
