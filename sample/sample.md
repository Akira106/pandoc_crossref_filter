# pandoc_crossref_filterによる相互参照のサンプル

## 1. 自動でセクション番号が付与されます

### 1.1. 自動でセクション番号が付与されます

#### 1.1.1. 自動でセクション番号が付与されます

##### 1.1.1.1. 自動でセクション番号が付与されます

## .unを付与すると、章番号を付与しません

セクション番号の参照ができます。

- 第1章
- 1.1節
- 1.1.1項
- 1.1.1.1目

末尾に`+title`を追加することで、タイトルの参照も可能です。

- 第2章 図番号の参照

## 1.1-A) ヘッダーの中でもセクション番号を参照できます

## 2. 図番号の参照

\[図2-1\]を参照します。

![図番号の参照のサンプルです](http://mirrors.creativecommons.org/presskit/logos/cc.logo.large.png)  
\[図2-1\] 図番号の参照のサンプルです

## 3. 表番号の参照

\[表3-1\]を参照します。

<table>
<caption>[表3-1] 表番号の参照のサンプルです</caption>
<colgroup>
<col style="width: 80%" />
<col style="width: 20%" />
</colgroup>
<thead>
<tr>
<th style="text-align: left;">列A</th>
<th style="text-align: left;">列B</th>
</tr>
</thead>
<tbody>
<tr>
<td style="text-align: left;">テスト</td>
<td style="text-align: left;">です</td>
</tr>
<tr>
<td style="text-align: left;"><code>&lt;br&gt;</code>を使うと、表の中も改行できます(Word変換にも対応。)</td>
<td style="text-align: left;">・改行<br />
・される<br />
</td>
</tr>
<tr>
<td style="text-align: left;">表の中でも参照が使えます</td>
<td style="text-align: left;">第1章, [図2-1]</td>
</tr>
</tbody>
</table>

  

追加の機能で、テーブル内のセルを結合することができます。  
セルの中に、以下の文字列を記述することで、Pandocで変換するときに、セルが結合されます。

- 左のセルと結合：`->`
- 上のセルと結合：`〃`

例：

<table>
<caption>[表3-2] セルの結合の例</caption>
<colgroup>
<col style="width: 5%" />
<col style="width: 15%" />
<col style="width: 30%" />
<col style="width: 50%" />
</colgroup>
<thead>
<tr>
<th colspan="2" style="text-align: left;">項目
<div>
&#10;</div></th>
<th style="text-align: left;">型</th>
<th style="text-align: left;">説明</th>
</tr>
</thead>
<tbody>
<tr>
<td colspan="2" style="text-align: left;">TEST
<div>
&#10;</div></td>
<td style="text-align: left;">object</td>
<td style="text-align: left;">object型の項目です。</td>
</tr>
<tr>
<td rowspan="2" style="text-align: left;"><div>
&#10;</div></td>
<td style="text-align: left;">key1</td>
<td style="text-align: left;">string</td>
<td style="text-align: left;">key1の設定値です。</td>
</tr>
<tr>
<td style="text-align: left;">key2</td>
<td style="text-align: left;">integer</td>
<td style="text-align: left;">key2の設定値です。</td>
</tr>
</tbody>
</table>

  

## 4. PlantUMLの相互参照

特殊な記法ですが、plantumlで作成した図も相互参照できます。

![処理Xのシーケンス図](assets/test1.png)  
\[図4-1\] 処理Xのシーケンス図

  

<img src="assets/test2.png" style="width:30.0%" alt="処理Xの詳細" />  
\[図4-2\] 処理Xの詳細

  

\[図4-3\]は、Mermaidで作成しています。

<img src="assets/test_mermaid.png" style="width:30.0%" alt="Mermaidのテスト" />  
\[図4-3\] Mermaidのテスト
