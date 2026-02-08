--
-- pandoc_crossref_filterと一緒に使用するLuaフィルター
--
-- Tableのキャプションに{.width="X,Y"}のように指定することで、
-- pandoc_crossref_filterでは、Table要素のclassesに`width="X,Y"`を追加します。
--
-- このLuaフィルターは、それを読み取って、実際のWordのテーブルの幅を指定します。
--

function Table(tbl)
	if not tbl.classes or #tbl.classes == 0 then
		return tbl
	end

	local width_class = nil

	-- width="..." を探す
	for _, cls in ipairs(tbl.classes) do
		local spec = cls:match('^width="([^"]+)"$')
		if spec then
			width_class = spec
			break
		end
	end

	-- 指定がなければ何もしない
	if not width_class then
		return tbl
	end

	-- 数値を分解
	local widths = {}
	for v in width_class:gmatch("[^,%s]+") do
		table.insert(widths, tonumber(v) / 100)
	end

	local col_count = #tbl.colspecs

	-- 列数チェック
	if #widths ~= col_count then
		error(string.format("[ERROR] table column count (%d) does not match width spec count (%d)", col_count, #widths))
	end

	-- 適用
	for i, w in ipairs(widths) do
		tbl.colspecs[i][2] = w
	end

	-- width クラスは不要なので削除
	local new_classes = {}
	for _, cls in ipairs(tbl.classes) do
		if not cls:match('^width="') then
			table.insert(new_classes, cls)
		end
	end
	tbl.classes = new_classes

	return tbl
end
