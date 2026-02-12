# Pandoc crossref filter

## 1. 特徴

- Markdownの中で、セクション番号、図番号、表番号の相互参照を実現します。
- Pandocのカスタムフィルターとして動作します。
- VSCodeのプラグインである、Markdown Preview Enhancedとの連携が可能です。
- PlantUML/Mermaidの図の中にも引用を挿入することができます。
- 表の中で改行することができます。Pandocを使ってMarkdownをWordファイルに変換したときにも、改行が維持されます。
- 参照元にジャンプできるリンクを自動で付与します。ただし、現在はPandocの出力フォーマットが以下の場合のみ対応しています。
  - Word(docx)
  - HTML
  - GitHub Flavored Markdown(GFM)

  

既存の類似OSSである[pandoc-crossref](https://github.com/lierdakil/pandoc-crossref)を使わずに、本OSSを開発した理由は以下です。

- 章番号の自動カウントを開始するヘッダーのレベルを変更できます。  
  例：開始レベルを2に変更すると、`## ヘッダー2` =\> `## 1. ヘッダー2`、`### ヘッダー3` =\> `### 1.1 ヘッダー3`のようになります。
- 図番号、表番号を、1からの連番ではなく、章番号や節番号に合わせた番号で付与することができます。  
  例：\[図1-1\]、\[表3-4-2\]
- PlantUMLやMermaidの図の中にも引用を挿入することができます。またMarkdown Preview Enhancedを利用したプレビューやフォーマット変換に対応しています。

  

## 2. インストール方法

### 2.1. 事前に必要なもの

- Pandoc==3.6.2: <https://github.com/jgm/pandoc/releases>  
  ※異なるバージョンのPandocだと、動作が異なる場合があります。
- Python≧3.10: <https://www.python.org/downloads/>

### 2.2. インストール

まず、本プロジェクトをcloneしてください。

``` shell-session
$ git clone https://github.com/Akira106/pandoc_crossref_filter.git
$ cd pandoc_crossref_filter
```

続いて、PlantUMLを使用する場合、PlantUMLサーバーのURLを設定します。

``` shell-session
$ vi src/pandoc_crossref_filter/config.py
```

- 例：公開サーバーを使用する場合

<!-- -->

    PLANTUML_SERVER_URL = "https://www.plantuml.com/plantuml"

- 例：自前でサーバーを立てる場合

例えば以下のようなdocker-composeファイルで、サーバーを立てます。

``` yaml
version: '3'
services:
  plantuml-server:
    image: plantuml/plantuml-server
    container_name: plantuml-local-server
    ports:
      - "8080:8080"
```

``` shell-session
$ docker-compose up -d
```

`config.py`には、以下のように記述します。

    PLANTUML_SERVER_URL = "http://127.0.0.1:8080"

最後に、pipでインストールします。

- Mermaidを使用しない場合

``` shell-session
$ pip3 install .
```

- Mermaidを使用する場合

``` shell-session
$ pip3 install .[all]
$ playwright install chromium
```

※ 上記の実行時に`XXXXX which is not on PATH.`のようなWarningメッセージが出た場合、環境変数`PATH`に、インストール先のパスを追加してください。

### 2.3. Markdown Preview Enhancedのプレビュー画面との連携の設定

**※本設定を行うと、プレビュー画面の動作が重くなります。プレビュー画面を常に表示しながら同時に編集したい場合は、本設定を実施しないでください。**

Markdown Preview Enhancedのプレビュー画面で、本フィルターの機能をプレビューしたい場合は、以下の設定が必要です。

| VSCodeの設定項目 | 設定値 |
|:---|:---|
| Markdown-preview-enhanced: Pandoc Arguments | \[“–filter=pandoc_crossref_filter”\] |
| Markdown-preview-enhanced: Use Pandoc Parser | チェックをつける |

\[表2-1\] Markdown Preview Enhancedのプレビュー機能との連携の設定

  

### 2.4. Markdown Preview EnhancedのPlantUMLの設定

また、Markdown Preview EnhancedでPlantUMLを使用する場合は、以下の**いずれか**の設定が必要です。

| VSCodeの設定項目 | 設定値 |
|:---|:---|
| Markdown-preview-enhanced: Plantuml Jar Path | PlantUMLの.jarファイルをダウンロードして、そのパスを設定する。 |
| Markdown-preview-enhanced: Plantuml Server | `PlantUMLサーバーのURL`/svg |

\[表2-2\] Markdown Preview EnhancedのPlantUMLの設定

## 3. 使い方

### 3.1. 参照の挿入方法

#### 3.1.1. セクション番号の挿入

ヘッダーの末尾に`{#sec:XXX}`を追加します。

`例`

    ## ヘッダー2{#sec:test_sec}

#### 3.1.2. 図番号の挿入

以下のように記載します。

    ![キャプション](図のパス){#fig:XXX}

`例`

    ![テストの画像](assets/test.svg){#fig:test_fig}

#### 3.1.3. 表番号の挿入

表の下に、以下のようなキャプションを表の下に直接追加します。

    : キャプション{#tbl:XXX}

`例`

    | C1 | C2 |
    |:---|:---|
    | v1 | v2 |
    | v3 | v4 |
    : テストの表{#tbl:test_tbl}

  

##### カラムの幅の設定

追加の機能で、カラムの幅を設定できます。

以下のように、`colwidth="X,Y,Z"`の形式で、カラムの幅をパーセンテージで指定してください。  
ただし、合計は100以下になるように設定してください。

    : キャプション{#tbl:XXX colwidth="30,70"}

  

##### 参考

Markdown Preview Enhancedを使用する場合、import機能で外部CSVファイルを表として使用するこができます。

`例`

    @import "test.csv"
    : importされた表{#tbl:import_tbl}

  

#### 3.1.4. PlantUMLへの図番号の挿入

1.  \`\`\`{.plantuml}\`\`\`というコードブロックを使用します。**※1**
2.  PlantUMLのコードブロックの中に以下のコメントを記載することで、図番号の挿入、キャプション、出力画像ファイル名、画像幅の設定を行います。

- 図番号の挿入(オプション)：`'#fig:XXX`
- キャプション：`'caption=YYY`
- 出力画像のファイル名：`'filename=ZZZ`
- 画像幅(オプション)：`'width=WWW`

**※1**  
\`\`\`plantuml\`\`\`という表記でもPandoc単体なら動作しますが、PlantUMLの中で3.2節に示す引用を使用した場合、Markdown Preview Enhancedとの連携が正しく動作しなくなります。

`例`

    ```{.plantuml}
    'filename="test.svg"
    '#fig:fig_puml
    'caption=PlantUMLの画像です
    'width=30%

    Bob -> Alice : hello
    ```

#### 3.1.5. Mermaidへの図番号の挿入

1.  \`\`\`{.mermaid}\`\`\`というコードブロックを使用します。**※1**
2.  Mermaidのコードブロックの中に以下のコメントを記載することで、図番号の挿入、キャプション、出力画像ファイル名、画像幅の設定を行います。

- 図番号の挿入(オプション)：`%%#fig:XXX`
- キャプション：`%%caption=YYY`
- 出力画像のファイル名：`%%filename=ZZZ`
- 画像幅(オプション)：`%%width=WWW`

**※1**  
\`\`\`mermaid\`\`\`という表記でもPandoc単体なら動作しますが、Mermaidの中で3.2節に示す引用を使用した場合、Markdown Preview Enhancedとの連携が正しく動作しなくなります。

`例`

    ```{.mermaid}
    %%filename="test.svg"
    %%#fig:fig_puml
    %%caption=Mermaidの画像です
    %%width=30%

    sequenceDiagram
      Bob ->> Alice : hello
    ```

### 3.2. 参照の引用

セクション番号、図番号、表番号を、それぞれ

- `[@sec:XXX]`
- `[@fig:XXX]`
- `[@tbl:XXX]`

で引用することができます。  
(`XXX`は、3.1節で挿入したものに対応します)

引用は、本文、箇条書き、表、ヘッダー(3.4.2項) 、コードブロックの中(PlantUML/Mermaidの図の中、3.4.3項)で使用することができます。

  

また、末尾に`+title`を追加することで、タイトルも一緒に引用することができます。

`例`

- `[@sec:XXX+title]`
- `[@fig:XXX+title]`
- `[@tbl:XXX+title]`

### 3.3. 設定値

Markdownファイルの先頭に`---`で囲ったブロックを記述します。その中で、以下のように`pandoc_crossref_filter`から始まるYAML形式で、設定を記載することができます。

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

- `section`の設定値

| 設置値 | 型 | デフォルト値 | 内容 |
|:---|:---|:---|:---|
| auto_section | boolean | false | ヘッダーの先頭に、自動でセクション番号を追加します。 |
| start_header_level | integer | 1 | セクション番号のカウントを開始するヘッダーのレベルを設定します。例えば2を設定した場合、ヘッダー1はセクション番号のカウントに含まれなくなります。 |
| section_title_template | array\[string\] | \[“%s.”\] | ヘッダーの先頭に挿入されるセクション番号の文字列のテンプレートです。`%s`の中に実際のセクション番号が挿入されます。配列で複数指定することで、ヘッダーのレベルに応じてテンプレートを変更することができます。 |
| delimiter | string | “.” | セクション番号の数字の区切り文字です。 |
| section_ref_template | array\[string\] | \[“第%s章”, “%s節”, “%s項”, “%s目”\] | 参照を引用したときの、セクション番号の文字列のテンプレートです。`%s`の中に実際のセクション番号が挿入されます。配列で複数指定することで、ヘッダーのレベルに応じてテンプレートを変更することができます。 |

\[表3-1\] セクション番号の設定項目

- `figure`の設定値

<table>
<caption>[表3-2] 図番号の設定項目</caption>
<colgroup>
<col style="width: 25%" />
<col style="width: 25%" />
<col style="width: 25%" />
<col style="width: 25%" />
</colgroup>
<thead>
<tr>
<th style="text-align: left;">設置値</th>
<th style="text-align: left;">型</th>
<th style="text-align: left;">デフォルト値</th>
<th style="text-align: left;">内容</th>
</tr>
</thead>
<tbody>
<tr>
<td style="text-align: left;">figure_number_count_level</td>
<td style="text-align: left;">integer</td>
<td style="text-align: left;">0</td>
<td style="text-align: left;">図番号の連番をカウントするヘッダーのレベルです。<br />
例：<br />
・0を設定：<code>図X</code>のように、ドキュメント全体で連番を使用します。<br />
・1を設定：<code>図1-X</code>のように、章番号ごとに連番をカウントします。<br />
・負の値を設定：個別のヘッダーごとに連番をカウントします。</td>
</tr>
<tr>
<td style="text-align: left;">figure_title_template</td>
<td style="text-align: left;">string</td>
<td style="text-align: left;">“[図%s]”</td>
<td style="text-align: left;">図番号の文字列のテンプレートです。<code>%s</code>の中に実際の図番号が挿入されます。</td>
</tr>
<tr>
<td style="text-align: left;">delimiter</td>
<td style="text-align: left;">string</td>
<td style="text-align: left;">“-”</td>
<td style="text-align: left;">図番号の区切り文字です。</td>
</tr>
</tbody>
</table>

- `table`の設定値

<table>
<caption>[表3-3] 表番号の設定項目</caption>
<colgroup>
<col style="width: 25%" />
<col style="width: 25%" />
<col style="width: 25%" />
<col style="width: 25%" />
</colgroup>
<thead>
<tr>
<th style="text-align: left;">設置値</th>
<th style="text-align: left;">型</th>
<th style="text-align: left;">デフォルト値</th>
<th style="text-align: left;">内容</th>
</tr>
</thead>
<tbody>
<tr>
<td style="text-align: left;">table_number_count_level</td>
<td style="text-align: left;">integer</td>
<td style="text-align: left;">0</td>
<td style="text-align: left;">表番号の連番をカウントするヘッダーのレベルです。<br />
例：<br />
・0を設定：<code>表X</code>のように、ドキュメント全体で連番を使用します。<br />
・1を設定：<code>表1-X</code>のように、章番号ごとに連番をカウントします。<br />
・負の値を設定：個別のヘッダーごとに連番をカウントします。</td>
</tr>
<tr>
<td style="text-align: left;">table_title_template</td>
<td style="text-align: left;">string</td>
<td style="text-align: left;">“[表%s]”</td>
<td style="text-align: left;">表番号の文字列のテンプレートです。<code>%s</code>の中に実際の表番号が挿入されます。</td>
</tr>
<tr>
<td style="text-align: left;">delimiter</td>
<td style="text-align: left;">string</td>
<td style="text-align: left;">“-”</td>
<td style="text-align: left;">表番号の区切り文字です。</td>
</tr>
</tbody>
</table>

- `code_block`の設定値

| 設置値 | 型 | デフォルト値 | 内容 |
|:---|:---|:---|:---|
| save_dir | string | “assets” | PlantUML/Mermaidを画像出力したときの、出力先のディレクトリのパスです。 |

\[表3-4\] コードブロックの設定項目

### 3.4. その他の機能

#### 3.4.1. セクション番号のカウントの除外

ヘッダーの後ろに`{.un}`または`{.unnumbered}`を記載することで、そのヘッダーはセクション番号をカウントから除外します。

`例`

    # このヘッダーはセクション番号のカウントから除外される{.un}

#### 3.4.2. ヘッダー内のセクション番号の引用

ヘッダー内で、他のセクション番号を引用することができます。  
例えば、セクション番号のカウントを、途中から数字からアルファベットに変更したい場合など、細かい動作を指定するのに有効です。

#### 3.4.3. PlantUML/Mermaid内の相互参照

PlantUML/Mermaidのコードブロック内で、3.2節の引用を使用することが可能です。  
ただし、Markdown Preview Enhancedとの連携を行う場合は、3.1.4項に記載したように、コードブロックの先頭を`{.plantuml}`/`{.mermaid}`で開始する必要があります。

##### 補足

コードブロックの先頭を`plantuml`/`mermaid`で開始した場合、Markdown Preview Enhancedの機能でエクスポートを行ったときに、  
本フィルターが相互参照を解決するよりも先に、Markdown Preview EnhancedによってPlantUML/Mermaidの画像出力が実行されてしまい、相互参照を解決できなくなります。

#### 3.4.4. 表の中の改行

表の中で、`<br>`を使うことで、改行ができます。Pandocの機能でWordファイルに変換した場合にも、本フィルターを使用することで、Wordファイル内で改行が維持されます。

#### 3.4.5. SoftBreakの改行変換

Markdownで改行する場合は、末尾にスペースを2つ付ける必要があります。  
しかし本フィルターを使用することで、Markdown中のただの改行(SoftBreak)を、改行に変換することができます。

### 3.5. エクスポート

PandocまたはMarkdown Preview Enhancedの機能を使って、相互参照を解決したファイルをエクスポートすることができます。

#### 3.5.1. GitHub Flavored Markdown(GFM)への変換

Markdownファイルの先頭に`---`で囲ったブロックを記述します。その中で、以下のようにMarkdown Preview Enhancedのエクスポート設定を記載することで、エクスポートが可能になります。

`例`

以下の設定例では、対象のMarkdownを`test_export.md`というファイル名でエクスポートします。  
※エクスポート設定の詳細は、Markdown Preview Enhancedのマニュアルをご参照ください。

    ---
    output:
      custom_document:
        path: test_export.md
        pandoc_args: [
          '--to=gfm',
          '--filter=pandoc_crossref_filter',
          '--wrap=preserve'
        ]
    ---

上記を設定したら、VSCodeで以下のような操作を行うことで、エクスポートが可能です。

- 対象のMarkdownファイルに対して右クリック
- → 「Markdown Preview Enhanced: Open Preview to the Side」をクリック
- → プレビュー画面で右クリック
- → 「Export」→「Pandoc」

#### 3.5.2. Wordファイルへの変換

3.5.1項と同様に、`pandoc_args`の設定に本フィルターを追加することで、エクスポートが可能になります。  
※エクスポート設定の詳細は、Markdown Preview Enhancedのマニュアルをご参照ください。

`例`

    ---
    output:
      word_document:
        path: output_docx/test_export.docx
        toc: true
        pandoc_args: [
          '--filter=pandoc_crossref_filter',
          '--wrap=preserve'
        ]
    ---

### 3.6. サンプル

[sample](sample/)にサンプルを記載しています。
