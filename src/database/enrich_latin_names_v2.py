"""
大规模拉丁学名补充 - 覆盖《中国药典》主要品种
运行：python src/database/enrich_latin_names_v2.py
"""
import sqlite3, os

DB_PATH = os.environ.get("DB_PATH", "data/tcm_exosome.db")
SUPABASE_URL = os.environ.get("SUPABASE_URL", "")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY", "")

LATIN_MAP = {
    # A
    "矮地茶": "Ardisia japonica (Thunb.) Blume",
    "艾叶": "Artemisia argyi H.Lév. & Vaniot",
    "安息香": "Styrax benzoin Dryand.",
    # B
    "八角茴香": "Illicium verum Hook.f.",
    "巴豆": "Croton tiglium L.",
    "巴豆霜": "Croton tiglium L.",
    "菝葜": "Smilax china L.",
    "白扁豆": "Dolichos lablab L.",
    "白矾": "Alumen",
    "白附子": "Typhonium giganteum Engl.",
    "白花蛇舌草": "Hedyotis diffusa Willd.",
    "白及": "Bletilla striata (Thunb.) Rchb.f.",
    "白茅根": "Imperata cylindrica (L.) Beauv.",
    "白前": "Cynanchum stauntonii (Decne.) Schltr.",
    "白屈菜": "Chelidonium majus L.",
    "白术": "Atractylodes macrocephala Koidz.",
    "白薇": "Cynanchum atratum Bge.",
    "白鲜皮": "Dictamnus dasycarpus Turcz.",
    "白芷": "Angelica dahurica (Fisch. ex Hoffm.) Benth. & Hook.f.",
    "百部": "Stemona japonica (Bl.) Miq.",
    "百合": "Lilium lancifolium Thunb.",
    "败酱草": "Patrinia scabiosifolia Fisch.",
    "板蓝根": "Isatis indigotica Fort.",
    "半边莲": "Lobelia chinensis Lour.",
    "半枝莲": "Scutellaria barbata D.Don",
    "北沙参": "Glehnia littoralis F.Schmidt ex Miq.",
    "北豆根": "Menispermum dauricum DC.",
    "荜茇": "Piper longum L.",
    "荜澄茄": "Litsea cubeba (Lour.) Pers.",
    "萆薢": "Dioscorea septemloba Thunb.",
    "槟榔": "Areca catechu L.",
    "冰片": "Borneolum Syntheticum",
    "薄荷": "Mentha haplocalyx Briq.",
    "补骨脂": "Psoralea corylifolia L.",
    # C
    "苍耳子": "Xanthium sibiricum Patr.",
    "苍术": "Atractylodes lancea (Thunb.) DC.",
    "草豆蔻": "Alpinia katsumadai Hayata",
    "草果": "Amomum tsao-ko Crevost et Lemaire",
    "草乌": "Aconitum kusnezoffii Reichb.",
    "侧柏叶": "Platycladus orientalis (L.) Franco",
    "柴胡": "Bupleurum chinense DC.",
    "蝉蜕": "Cryptotympana pustulata Fabricius",
    "车前草": "Plantago asiatica L.",
    "车前子": "Plantago asiatica L.",
    "沉香": "Aquilaria sinensis (Lour.) Gilg",
    "陈皮": "Citrus reticulata Blanco",
    "赤芍": "Paeonia lactiflora Pall.",
    "赤小豆": "Vigna umbellata (Thunb.) Ohwi et Ohashi",
    "川贝母": "Fritillaria cirrhosa D.Don",
    "川楝子": "Melia toosendan Sieb. et Zucc.",
    "川木通": "Clematis armandii Franch.",
    "川牛膝": "Cyathula officinalis Kuan",
    "川乌": "Aconitum carmichaelii Debx.",
    "川芎": "Ligusticum chuanxiong Hort.",
    "穿山甲": "Manis pentadactyla Linnaeus",
    "穿心莲": "Andrographis paniculata (Burm.f.) Nees",
    "垂盆草": "Sedum sarmentosum Bunge",
    "磁石": "Magnetitum",
    "刺五加": "Acanthopanax senticosus (Rupr. Maxim.) Harms",
    # D
    "大蒜": "Allium sativum L.",
    "大枣": "Ziziphus jujuba Mill.",
    "大蓟": "Cirsium japonicum Fisch. ex DC.",
    "大腹皮": "Areca catechu L.",
    "大皂角": "Gleditsia sinensis Lam.",
    "党参": "Codonopsis pilosula (Franch.) Nannf.",
    "地骨皮": "Lycium chinense Mill.",
    "地肤子": "Kochia scoparia (L.) Schrad.",
    "地锦草": "Euphorbia humifusa Willd.",
    "地榆": "Sanguisorba officinalis L.",
    "丁香": "Syzygium aromaticum (L.) Merr. et Perry",
    "冬虫夏草": "Cordyceps sinensis (Berk.) Sacc.",
    "冬瓜皮": "Benincasa hispida (Thunb.) Cogn.",
    "冬凌草": "Isodon rubescens (Hemsl.) Hara",
    "豆蔻": "Amomum kravanh Pierre ex Gagnep.",
    "独活": "Angelica pubescens Maxim.",
    "杜仲": "Eucommia ulmoides Oliv.",
    # E
    "莪术": "Curcuma phaeocaulis Val.",
    "儿茶": "Acacia catechu (L.f.) Willd.",
    # F
    "番泻叶": "Cassia angustifolia Vahl",
    "防风": "Saposhnikovia divaricata (Turcz.) Schischk.",
    "防己": "Stephania tetrandra S.Moore",
    "飞扬草": "Euphorbia hirta L.",
    "佛手": "Citrus sarcodactylis Swingle",
    "茯神": "Poria cocos (Schw.) Wolf",
    "附子": "Aconitum carmichaelii Debx.",
    # G
    "甘草": "Glycyrrhiza uralensis Fisch.",
    "甘遂": "Euphorbia kansui T.N.Liou ex T.P.Wang",
    "干姜": "Zingiber officinale Rosc.",
    "藁本": "Ligusticum sinense Oliv.",
    "葛根": "Pueraria montana var. lobata (Willd.) Maesen",
    "功劳木": "Mahonia bealei (Fort.) Carr.",
    "钩藤": "Uncaria rhynchophylla (Miq.) Miq. ex Havil.",
    "狗脊": "Cibotium barometz (L.) J.Sm.",
    "枸杞子": "Lycium barbarum L.",
    "骨碎补": "Drynaria roosii Nakaike",
    "瓜蒌": "Trichosanthes kirilowii Maxim.",
    "广藿香": "Pogostemon cablin (Blanco) Benth.",
    "龟甲": "Chinemys reevesii (Gray)",
    # H
    "海风藤": "Piper kadsura (Choisy) Ohwi",
    "海金沙": "Lygodium japonicum (Thunb.) Sw.",
    "海螵蛸": "Sepiella maindroni de Rochebrune",
    "合欢花": "Albizia julibrissin Durazz.",
    "合欢皮": "Albizia julibrissin Durazz.",
    "何首乌": "Fallopia multiflora (Thunb.) Harald.",
    "荷叶": "Nelumbo nucifera Gaertn.",
    "红花": "Carthamus tinctorius L.",
    "红景天": "Rhodiola rosea L.",
    "厚朴": "Magnolia officinalis Rehd. et Wils.",
    "厚朴花": "Magnolia officinalis Rehd. et Wils.",
    "虎杖": "Reynoutria japonica Houtt.",
    "化橘红": "Citrus grandis (L.) Osbeck",
    "槐花": "Sophora japonica L.",
    "槐角": "Sophora japonica L.",
    "黄柏": "Phellodendron chinense Schneid.",
    "黄精": "Polygonatum kingianum Coll. et Hemsl.",
    "黄连": "Coptis chinensis Franch.",
    "黄芪": "Astragalus membranaceus (Fisch.) Bge.",
    "黄芩": "Scutellaria baicalensis Georgi",
    # J
    "鸡冠花": "Celosia cristata L.",
    "鸡内金": "Gallus gallus domesticus Brisson",
    "急性子": "Impatiens balsamina L.",
    "姜黄": "Curcuma longa L.",
    "僵蚕": "Bombyx mori Linnaeus",
    "降香": "Dalbergia odorifera T.Chen",
    "金钱草": "Lysimachia christiniae Hance",
    "金荞麦": "Fagopyrum dibotrys (D.Don) Hara",
    "金银花": "Lonicera japonica Thunb.",
    "金樱子": "Rosa laevigata Michx.",
    "荆芥": "Nepeta cataria L.",
    "桔梗": "Platycodon grandiflorus (Jacq.) A.DC.",
    "菊花": "Chrysanthemum morifolium Ramat.",
    "决明子": "Senna obtusifolia (L.) H.S.Irwin & Barneby",
    "卷柏": "Selaginella tamariscina (Beauv.) Spring",
    # K
    "苦参": "Sophora flavescens Ait.",
    "苦杏仁": "Prunus armeniaca L.",
    "款冬花": "Tussilago farfara L.",
    # L
    "莱菔子": "Raphanus sativus L.",
    "雷公藤": "Tripterygium wilfordii Hook.f.",
    "连翘": "Forsythia suspensa (Thunb.) Vahl",
    "莲子": "Nelumbo nucifera Gaertn.",
    "莲子心": "Nelumbo nucifera Gaertn.",
    "凌霄花": "Campsis grandiflora (Thunb.) K.Schum.",
    "灵芝": "Ganoderma lucidum (Leyss. ex Fr.) Karst.",
    "龙胆": "Gentiana scabra Bge.",
    "龙葵": "Solanum nigrum L.",
    "漏芦": "Rhaponticum uniflorum (L.) DC.",
    "芦根": "Phragmites communis Trin.",
    "鹿茸": "Cervus nippon Temminck",
    "路路通": "Liquidambar formosana Hance",
    "罗汉果": "Siraitia grosvenorii (Swingle) C.Jeffrey",
    # M
    "麻黄": "Ephedra sinica Stapf",
    "马齿苋": "Portulaca oleracea L.",
    "马钱子": "Strychnos nux-vomica L.",
    "麦冬": "Ophiopogon japonicus (L.f.) Ker-Gawl.",
    "蔓荆子": "Vitex trifolia L.",
    "毛诃子": "Terminalia chebula Retz.",
    "没药": "Commiphora myrrha Engl.",
    "墨旱莲": "Eclipta prostrata L.",
    "木瓜": "Chaenomeles speciosa (Sweet) Nakai",
    "木通": "Akebia quinata (Houtt.) Decne.",
    "木香": "Aucklandia lappa DC.",
    "牡丹皮": "Paeonia suffruticosa Andr.",
    "牡蛎": "Ostrea gigas Thunberg",
    # N
    "南沙参": "Adenophora tetraphylla (Thunb.) Fisch.",
    "南五味子": "Schisandra sphenanthera Rehd. et Wils.",
    "牛蒡子": "Arctium lappa L.",
    "牛膝": "Achyranthes bidentata Bl.",
    "女贞子": "Ligustrum lucidum Ait.",
    # P
    "佩兰": "Eupatorium fortunei Turcz.",
    "枇杷叶": "Eriobotrya japonica (Thunb.) Lindl.",
    "蒲公英": "Taraxacum mongolicum Hand.-Mazz.",
    "蒲黄": "Typha angustifolia L.",
    # Q
    "羌活": "Notopterygium incisum Ting ex H.T.Chang",
    "秦艽": "Gentiana macrophylla Pall.",
    "秦皮": "Fraxinus rhynchophylla Hance",
    "青蒿": "Artemisia annua L.",
    "青皮": "Citrus reticulata Blanco",
    "全蝎": "Buthus martensii Karsch",
    # R
    "忍冬藤": "Lonicera japonica Thunb.",
    "肉豆蔻": "Myristica fragrans Houtt.",
    "肉桂": "Cinnamomum cassia Presl",
    "肉苁蓉": "Cistanche deserticola Ma",
    "乳香": "Boswellia carterii Birdw.",
    # S
    "三棱": "Sparganium stoloniferum (Graebn.) Buch.-Ham. ex Juz.",
    "三七": "Panax notoginseng (Burkill) F.H.Chen",
    "沙棘": "Hippophae rhamnoides L.",
    "砂仁": "Amomum villosum Lour.",
    "山慈菇": "Pleione bulbocodioides (Franch.) Rolfe",
    "山豆根": "Sophora tonkinensis Gagnep.",
    "山茱萸": "Cornus officinalis Sieb. et Zucc.",
    "山药": "Dioscorea polystachya Turcz.",
    "山楂": "Crataegus pinnatifida Bge.",
    "商陆": "Phytolacca acinosa Roxb.",
    "射干": "Belamcanda chinensis (L.) DC.",
    "伸筋草": "Lycopodium japonicum Thunb.",
    "升麻": "Cimicifuga heracleifolia Kom.",
    "生姜": "Zingiber officinale Rosc.",
    "石菖蒲": "Acorus tatarinowii Schott",
    "石斛": "Dendrobium nobile Lindl.",
    "使君子": "Quisqualis indica L.",
    "熟地黄": "Rehmannia glutinosa Libosch.",
    "水蛭": "Hirudo nipponia Whitman",
    "丝瓜络": "Luffa cylindrica (L.) Roem.",
    "四季青": "Ilex chinensis Sims",
    "苏木": "Caesalpinia sappan L.",
    "酸枣仁": "Ziziphus jujuba Mill.",
    # T
    "太子参": "Pseudostellaria heterophylla (Miq.) Pax",
    "桃仁": "Prunus persica (L.) Batsch",
    "天冬": "Asparagus cochinchinensis (Lour.) Merr.",
    "天花粉": "Trichosanthes kirilowii Maxim.",
    "天麻": "Gastrodia elata Bl.",
    "天南星": "Arisaema erubescens (Wall.) Schott",
    "土茯苓": "Smilax glabra Roxb.",
    "土木香": "Inula helenium L.",
    "土贝母": "Bolbostemma paniculatum (Maxim.) Franquet",
    "土鳖虫": "Eupolyphaga sinensis Walker",
    # W
    "王不留行": "Vaccaria segetalis (Neck.) Garcke",
    "威灵仙": "Clematis chinensis Osbeck",
    "乌梅": "Prunus mume (Sieb.) Sieb. et Zucc.",
    "乌梢蛇": "Zaocys dhumnades (Cantor)",
    "吴茱萸": "Evodia rutaecarpa (Juss.) Benth.",
    "五倍子": "Rhus chinensis Mill.",
    "五加皮": "Acanthopanax gracilistylus W.W.Smith",
    "五味子": "Schisandra chinensis (Turcz.) Baill.",
    # X
    "西红花": "Crocus sativus L.",
    "西洋参": "Panax quinquefolium L.",
    "细辛": "Asarum heterotropoides Fr. Schmidt",
    "仙鹤草": "Agrimonia pilosa Ledeb.",
    "仙茅": "Curculigo orchioides Gaertn.",
    "香附": "Cyperus rotundus L.",
    "小茴香": "Foeniculum vulgare Mill.",
    "小蓟": "Cirsium setosum (Willd.) MB.",
    "辛夷": "Magnolia biondii Pamp.",
    "续断": "Dipsacus asper Wall.",
    "玄参": "Scrophularia ningpoensis Hemsl.",
    "旋覆花": "Inula japonica Thunb.",
    # Y
    "鸦胆子": "Brucea javanica (L.) Merr.",
    "延胡索": "Corydalis yanhusuo W.T.Wang",
    "野菊花": "Chrysanthemum indicum L.",
    "益母草": "Leonurus japonicus Houtt.",
    "益智": "Alpinia oxyphylla Miq.",
    "茵陈": "Artemisia scoparia Waldst. et Kit.",
    "淫羊藿": "Epimedium brevicornu Maxim.",
    "余甘子": "Phyllanthus emblica L.",
    "郁金": "Curcuma aromatica Salisb.",
    "郁李仁": "Prunus japonica Thunb.",
    "预知子": "Akebia quinata (Houtt.) Decne.",
    "远志": "Polygala tenuifolia Willd.",
    # Z
    "泽兰": "Lycopus lucidus Turcz.",
    "泽泻": "Alisma plantago-aquatica L.",
    "知母": "Anemarrhena asphodeloides Bge.",
    "栀子": "Gardenia jasminoides Ellis",
    "枳壳": "Citrus aurantium L.",
    "枳实": "Citrus aurantium L.",
    "制何首乌": "Fallopia multiflora (Thunb.) Harald.",
    "猪苓": "Polyporus umbellatus (Pers.) Fries",
    "紫草": "Lithospermum erythrorhizon Sieb. et Zucc.",
    "紫花地丁": "Viola yedoensis Makino",
    "紫苏叶": "Perilla frutescens (L.) Britt.",
    "紫苏子": "Perilla frutescens (L.) Britt.",
    "自然铜": "Pyritum",
    # 其他常用
    "九里香": "Murraya exotica L.",
    "云芝": "Coriolus versicolor (L.) Quel.",
    "亚麻子": "Linum usitatissimum L.",
    "京大戟": "Euphorbia pekinensis Rupr.",
    "伊贝母": "Fritillaria pallidiflora Schrenk",
    "佩兰": "Eupatorium fortunei Turcz.",
    "关黄柏": "Phellodendron amurense Rupr.",
    "冬葵果": "Malva verticillata L.",
    "夏天无": "Corydalis decumbens (Thunb.) Pers.",
    "夏枯草": "Prunella vulgaris L.",
    "大叶紫珠": "Callicarpa macrophylla Vahl",
    "北刘寄奴": "Artemisia eriopoda Bge.",
    "千年健": "Homalomena occulta (Lour.) Schott",
    "千里光": "Senecio scandens Buch.-Ham.",
    "千金子": "Euphorbia lathyris L.",
    "南板蓝根": "Baphicacanthus cusia (Nees) Bremek.",
    "南鹤虱": "Daucus carota L.",
    "哈蟆油": "Rana chensinensis David",
    "土荆皮": "Pseudolarix amabilis (Nelson) Rehd.",
    "地枫皮": "Illicium difengpi K.I.B. et K.I.M.",
    "华山参": "Physochlaina infundibularis Kuang",
    "九香虫": "Aspongopus chinensis Dallas",
    "体外培育牛黄": "Bos taurus domesticus Gmelin",
    "人工牛黄": "Bos taurus domesticus Gmelin",
    "人参叶": "Panax ginseng C.A.Mey.",
    "制天南星": "Arisaema erubescens (Wall.) Schott",
    "制草乌": "Aconitum kusnezoffii Reichb.",
    "制川乌": "Aconitum carmichaelii Debx.",
    "前胡": "Peucedanum praeruptorum Dunn",
    "半边莲": "Lobelia chinensis Lour.",
    "北沙参": "Glehnia littoralis F.Schmidt ex Miq.",
    "刀豆": "Canavalia gladiata (Jacq.) DC.",
}

def enrich_v2():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()

    # 确保列存在
    try:
        c.execute("ALTER TABLE tcm_single_herb ADD COLUMN name_latin TEXT")
        conn.commit()
    except:
        pass

    updated = 0
    for cn, latin in LATIN_MAP.items():
        result = c.execute(
            "UPDATE tcm_single_herb SET name_latin=?, data_level='aligned' WHERE name_cn=? AND (name_latin IS NULL OR name_latin='')",
            (latin, cn)
        )
        if result.rowcount > 0:
            updated += result.rowcount

    conn.commit()

    total = c.execute("SELECT COUNT(*) FROM tcm_single_herb").fetchone()[0]
    aligned = c.execute("SELECT COUNT(*) FROM tcm_single_herb WHERE name_latin IS NOT NULL AND name_latin != ''").fetchone()[0]
    print(f"总药材: {total}")
    print(f"已填充拉丁名: {aligned} ({aligned*100//total}%)")
    print(f"本次更新: {updated} 条")
    conn.close()

    # 同步到Supabase
    if SUPABASE_URL and SUPABASE_KEY:
        from supabase import create_client
        client = create_client(SUPABASE_URL, SUPABASE_KEY)
        data = [{"name_cn": cn, "name_latin": latin, "data_level": "aligned"}
                for cn, latin in LATIN_MAP.items()]
        for i in range(0, len(data), 50):
            client.table("tcm_single_herb").upsert(
                data[i:i+50], on_conflict="name_cn").execute()
        print(f"Supabase同步完成: {len(data)} 条")

if __name__ == "__main__":
    enrich_v2()
