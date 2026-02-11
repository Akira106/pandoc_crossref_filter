--
-- pandoc_crossref_filterと一緒に使用するLuaフィルター
--
-- Tableのキャプションに{colwidth="X,Y"}のように指定することで、
-- pandoc_crossref_filterでは、Table要素のattributesに`width="X,Y"`を追加します。
--
-- このLuaフィルターは、それを読み取って、実際のWordのテーブルの幅を指定します。
--

function Table(tbl)
	if not tbl.attributes then
		return tbl
	end

	local spec = tbl.attributes["colwidth"]

	-- 指定がなければ何もしない
	if not spec or spec == "" then
		return tbl
	end

	-- 数値を分解
	local widths = {}
	for v in tostring(spec):gmatch("[^,%s]+") do
		local n = tonumber(v)
		if not n then
			error(string.format("[ERROR] invalid colwidth value: %s", v))
		end
		table.insert(widths, n / 100)
	end

	local col_count = #tbl.colspecs

	-- 列数チェック
	if #widths ~= col_count then
		error(string.format("[ERROR] table column count (%d) does not match colwidth spec count (%d)", col_count, #widths))
	end

	-- 適用
	for i, w in ipairs(widths) do
		tbl.colspecs[i][2] = w
	end

	return tbl
end
