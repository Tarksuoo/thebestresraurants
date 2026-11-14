# Seoul Eats

Tourist food map for Seoul. Static site: `index.html` + `data/`, hosted on Netlify.

- Map: Naver Maps (falls back to OpenStreetMap)
- Reviews, accounts, photos: Supabase
- Restaurant data: data.go.kr, 소상공인시장진흥공단 상가(상권)정보 (2026-09), all 25 districts of Seoul

`data/seoul.js` is a small index of the districts. Each district's restaurants are in `data/gu/<name>.json`
and are only downloaded when the map shows that district.

To refresh the data with a newer file from data.go.kr:

    python3 tools/build_data.py path/to/소상공인시장진흥공단_상가(상권)정보_서울_YYYYMM.csv

`supabase/` holds the SQL that set up the database. `tools/` holds the data script. Neither is part of the website.
