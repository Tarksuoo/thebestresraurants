"""Build the restaurant data for all of Seoul.

Input : 소상공인시장진흥공단 상가(상권)정보 서울 CSV (data.go.kr)
Output: data/seoul.js        small index (districts, food types)
        data/gu/<slug>.json  restaurants of one district, loaded on demand

Usage : python3 tools/build_data.py path/to/상가(상권)정보_서울_YYYYMM.csv
"""
import json, os, re, sys
import pandas as pd

SRC = sys.argv[1]
OUT = os.path.join(os.path.dirname(__file__), '..', 'data')

# ---------- food types (Korean sub-category -> app category, English label) ----------
SUB = {
    '그 외 기타 간이 음식점': ('quick', 'Quick bites'),
    '김밥/만두/분식': ('quick', 'Gimbap & street food'),
    '버거': ('quick', 'Burgers'),
    '치킨': ('quick', 'Fried chicken'),
    '토스트/샌드위치/샐러드': ('quick', 'Toast, sandwiches & salad'),
    '피자': ('quick', 'Pizza'),
    '기타 동남아식 전문': ('asian', 'Southeast Asian'),
    '베트남식 전문': ('asian', 'Vietnamese'),
    '분류 안된 외국식 음식점': ('western', 'International'),
    '경양식': ('western', 'Western'),
    '기타 서양식 음식점': ('western', 'Western'),
    '파스타/스테이크': ('western', 'Pasta & steak'),
    '패밀리레스토랑': ('western', 'Family restaurant'),
    '기타 일식 음식점': ('japanese', 'Japanese'),
    '일식 면 요리': ('japanese', 'Ramen & udon'),
    '일식 카레/돈가스/덮밥': ('japanese', 'Curry, tonkatsu & rice bowls'),
    '일식 회/초밥': ('japanese', 'Sushi & sashimi'),
    '요리 주점': ('pub', 'Pub food (izakaya/pocha)'),
    '마라탕/훠궈': ('chinese', 'Malatang & hot pot'),
    '중국집': ('chinese', 'Korean-Chinese'),
    '곱창 전골/구이': ('bbq', 'Gopchang (tripe)'),
    '국/탕/찌개류': ('korean', 'Soups & stews'),
    '국수/칼국수': ('korean', 'Noodles'),
    '기타 한식 음식점': ('korean', 'Korean'),
    '냉면/밀면': ('korean', 'Cold noodles'),
    '닭/오리고기 구이/찜': ('bbq', 'Chicken & duck'),
    '돼지고기 구이/찜': ('bbq', 'Korean BBQ (pork)'),
    '백반/한정식': ('korean', 'Korean home-style'),
    '복 요리 전문': ('seafood', 'Pufferfish'),
    '소고기 구이/찜': ('bbq', 'Korean BBQ (beef)'),
    '전/부침개': ('korean', 'Korean pancakes'),
    '족발/보쌈': ('korean', 'Jokbal & bossam'),
    '해산물 구이/찜': ('seafood', 'Seafood'),
    '횟집': ('seafood', 'Raw fish'),
}
# left out on purpose: cafes, bakeries, ice cream, rice cakes, beer-only bars,
# nightlife bars, cafeterias & buffets

GU_EN = {
    '종로구': 'Jongno-gu', '중구': 'Jung-gu', '용산구': 'Yongsan-gu', '성동구': 'Seongdong-gu',
    '광진구': 'Gwangjin-gu', '동대문구': 'Dongdaemun-gu', '중랑구': 'Jungnang-gu', '성북구': 'Seongbuk-gu',
    '강북구': 'Gangbuk-gu', '도봉구': 'Dobong-gu', '노원구': 'Nowon-gu', '은평구': 'Eunpyeong-gu',
    '서대문구': 'Seodaemun-gu', '마포구': 'Mapo-gu', '양천구': 'Yangcheon-gu', '강서구': 'Gangseo-gu',
    '구로구': 'Guro-gu', '금천구': 'Geumcheon-gu', '영등포구': 'Yeongdeungpo-gu', '동작구': 'Dongjak-gu',
    '관악구': 'Gwanak-gu', '서초구': 'Seocho-gu', '강남구': 'Gangnam-gu', '송파구': 'Songpa-gu',
    '강동구': 'Gangdong-gu',
}

# ---------- Revised Romanization (enough for neighbourhood names) ----------
INI = ['g','kk','n','d','tt','r','m','b','pp','s','ss','','j','jj','ch','k','t','p','h']
MED = ['a','ae','ya','yae','eo','e','yeo','ye','o','wa','wae','oe','yo','u','wo','we','wi','yu','eu','ui','i']
# final consonant -> (sound class) ; romanised before a consonant / at end
FIN = ['', 'k','k','k','n','n','n','t','l','k','m','l','l','l','p','l','m','p','p','t','t','ng','t','t','k','t','p','t']
# final consonant romanised before a vowel (liaison)
FIN_V = ['', 'g','kk','ks','n','nj','nh','d','r','lg','lm','lb','ls','lt','lp','lh','m','b','ps','s','ss','ng','j','ch','k','t','p','h']

def syl(ch):
    c = ord(ch) - 0xAC00
    return c // 588, (c % 588) // 28, c % 28

def romanize(word):
    s = [syl(c) for c in word]
    out = []
    for i, (a, b, f) in enumerate(s):
        ini = INI[a]
        if i > 0:
            pf = s[i-1][2]; p = FIN[pf]
            if a == 11:                       # next starts with a vowel: carry the final over
                out[-1] = out[-1][:len(out[-1]) - len(FIN[pf])] if FIN[pf] and out[-1].endswith(FIN[pf]) else out[-1]
                ini = FIN_V[pf] if pf != 21 else ''
                if pf == 21: out[-1] += 'ng'
                if pf == 27: ini = ''
            elif a == 5:                      # ㄹ after a final
                if p == 'n': out[-1] = out[-1][:-1] + 'l'; ini = 'l'
                elif p == 'l': ini = 'l'
                elif p in ('k', 'p', 't', 'm', 'ng'):
                    ini = 'n'
                    if p in ('k', 'p', 't'): out[-1] = out[-1][:-1] + {'k': 'ng', 'p': 'm', 't': 'n'}[p]
            elif a == 2 or a == 6:            # nasal next: k/t/p become nasal
                if p in ('k', 'p', 't'): out[-1] = out[-1][:-1] + {'k': 'ng', 'p': 'm', 't': 'n'}[p]
                elif p == 'l' and a == 2: ini = 'l'
            elif a == 18 and p in ('k', 't', 'p'):  # aspiration
                out[-1] = out[-1][:-1]; ini = {'k': 'k', 't': 't', 'p': 'p'}[p]
        out.append(ini + MED[b] + FIN[f])
    r = ''.join(out)
    return r[:1].upper() + r[1:]

RO = {'남대문로': 'Namdaemun-ro', '신문로': 'Sinmun-ro', '충정로': 'Chungjeong-ro'}

def dong_en(name):
    m = re.fullmatch(r'(.+?)(동)?(\d+)가', name)            # 을지로3가, 회현동1가
    if m:
        base = RO.get(m.group(1)) or romanize(m.group(1)) + ('-dong' if m.group(2) else '')
        return f'{base} {m.group(3)}-ga'
    m = re.fullmatch(r'(.+?)(\d+)동', name)                 # 성수동1가 handled above; 상계1동 style
    if m:
        return f'{romanize(m.group(1))} {m.group(2)}-dong'
    for suf, en in (('동', '-dong'), ('로', '-ro'), ('가', '-ga')):
        if name.endswith(suf) and len(name) > 1:
            return romanize(name[:-1]) + en
    return romanize(name)

def slug(gu_en):
    return gu_en.lower().replace('-gu', '')

# ---------- load & filter ----------
cols = ['상가업소번호','상호명','지점명','상권업종대분류명','상권업종소분류명','시도명','시군구명',
        '법정동명','도로명주소','층정보','위도','경도']
df = pd.read_csv(SRC, dtype=str, usecols=cols, encoding_errors='replace').fillna('')
df = df[(df['상권업종대분류명'] == '음식') & (df['시도명'] == '서울특별시')]
df = df[df['상권업종소분류명'].isin(SUB)]
df = df[(df['상호명'].str.strip() != '') & (df['상호명'] != '업소명없음')]
df = df[df['시군구명'].isin(GU_EN)]
df['lat'] = pd.to_numeric(df['위도'], errors='coerce'); df['lon'] = pd.to_numeric(df['경도'], errors='coerce')
df = df[df['lat'].between(37.40, 37.72) & df['lon'].between(126.75, 127.20)]
df = df.drop_duplicates(['상호명', '도로명주소', '층정보'])
df = df.drop_duplicates('상가업소번호')

subs = list(dict.fromkeys(SUB[k] for k in SUB))          # unique (cat, label) pairs
sub_idx = {k: subs.index(v) for k, v in SUB.items()}

os.makedirs(os.path.join(OUT, 'gu'), exist_ok=True)
index = []
for gu, g in df.groupby('시군구명'):
    en = GU_EN[gu]; sl = slug(en)
    g = g.sort_values(['lat', 'lon'])
    dongs = sorted(g['법정동명'].unique())
    d_idx = {d: i for i, d in enumerate(dongs)}
    prefix = f'서울특별시 {gu} '
    rows = []
    for x in g.itertuples(index=False):
        addr = x.도로명주소[len(prefix):] if x.도로명주소.startswith(prefix) else x.도로명주소
        rows.append([x.상가업소번호, x.상호명.strip(), x.지점명.strip(), sub_idx[x.상권업종소분류명],
                     addr, x.층정보, round(x.lat, 6), round(x.lon, 6), d_idx[x.법정동명]])
    with open(os.path.join(OUT, 'gu', sl + '.json'), 'w', encoding='utf-8') as f:
        json.dump({'d': [dong_en(d) for d in dongs], 'r': rows}, f, ensure_ascii=False, separators=(',', ':'))
    index.append({'k': sl, 'en': en, 'ko': gu, 'n': len(rows),
                  'c': [round(g['lat'].median(), 5), round(g['lon'].median(), 5)],
                  'b': [round(g['lat'].min(), 5), round(g['lon'].min(), 5), round(g['lat'].max(), 5), round(g['lon'].max(), 5)]})

with open(os.path.join(OUT, 'seoul.js'), 'w', encoding='utf-8') as f:
    f.write('window.SEOUL=' + json.dumps({'v': '2026-09', 'subs': subs, 'gu': index}, ensure_ascii=False, separators=(',', ':')) + ';\n')

print(len(df), 'restaurants in', len(index), 'districts')
