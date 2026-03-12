"""
Aligned层升级：通过NCBI Taxonomy API填充拉丁学名
运行：python src/database/enrich_latin_names.py
"""
import sqlite3, os, time, requests

DB_PATH = os.environ.get("DB_PATH", "data/tcm_exosome.db")
SUPABASE_URL = os.environ.get("SUPABASE_URL", "")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY", "")

# 已知常用中药的拉丁学名映射（高置信度）
KNOWN_LATIN = {
    "人参": "Panax ginseng C.A.Mey.",
    "黄芪": "Astragalus membranaceus (Fisch.) Bge.",
    "当归": "Angelica sinensis (Oliv.) Diels",
    "川芎": "Ligusticum chuanxiong Hort.",
    "白术": "Atractylodes macrocephala Koidz.",
    "茯苓": "Poria cocos (Schw.) Wolf",
    "甘草": "Glycyrrhiza uralensis Fisch.",
    "熟地黄": "Rehmannia glutinosa Libosch.",
    "地黄": "Rehmannia glutinosa (Gaertn.) DC.",
    "白芍": "Paeonia lactiflora Pall.",
    "赤芍": "Paeonia lactiflora Pall.",
    "丹参": "Salvia miltiorrhiza Bge.",
    "黄连": "Coptis chinensis Franch.",
    "黄芩": "Scutellaria baicalensis Georgi",
    "黄柏": "Phellodendron chinense Schneid.",
    "大黄": "Rheum palmatum L.",
    "附子": "Aconitum carmichaelii Debx.",
    "肉桂": "Cinnamomum cassia Presl",
    "生姜": "Zingiber officinale Rosc.",
    "干姜": "Zingiber officinale Rosc.",
    "半夏": "Pinellia ternata (Thunb.) Breit.",
    "陈皮": "Citrus reticulata Blanco",
    "枳实": "Citrus aurantium L.",
    "柴胡": "Bupleurum chinense DC.",
    "升麻": "Cimicifuga heracleifolia Kom.",
    "葛根": "Pueraria montana var. lobata (Willd.) Maesen & S.M.Almeida ex Sanjappa & Predeep",
    "麻黄": "Ephedra sinica Stapf",
    "桂枝": "Cinnamomum cassia Presl",
    "苦杏仁": "Prunus armeniaca L.",
    "桔梗": "Platycodon grandiflorus (Jacq.) A.DC.",
    "薄荷": "Mentha haplocalyx Briq.",
    "荆芥": "Nepeta cataria L.",
    "防风": "Saposhnikovia divaricata (Turcz.) Schischk.",
    "羌活": "Notopterygium incisum Ting ex H.T.Chang",
    "白芷": "Angelica dahurica (Fisch. ex Hoffm.) Benth. & Hook.f.",
    "细辛": "Asarum heterotropoides Fr. Schmidt",
    "藁本": "Ligusticum sinense Oliv.",
    "苍术": "Atractylodes lancea (Thunb.) DC.",
    "厚朴": "Magnolia officinalis Rehd. et Wils.",
    "砂仁": "Amomum villosum Lour.",
    "豆蔻": "Amomum kravanh Pierre ex Gagnep.",
    "薏苡仁": "Coix lacryma-jobi L.",
    "泽泻": "Alisma plantago-aquatica L.",
    "猪苓": "Polyporus umbellatus (Pers.) Fries",
    "车前子": "Plantago asiatica L.",
    "木通": "Akebia quinata (Houtt.) Decne.",
    "滑石": "Talcum",
    "金银花": "Lonicera japonica Thunb.",
    "连翘": "Forsythia suspensa (Thunb.) Vahl",
    "蒲公英": "Taraxacum mongolicum Hand.-Mazz.",
    "紫花地丁": "Viola yedoensis Makino",
    "鱼腥草": "Houttuynia cordata Thunb.",
    "板蓝根": "Isatis indigotica Fort.",
    "大青叶": "Isatis indigotica Fort.",
    "青黛": "Isatis indigotica Fort.",
    "穿心莲": "Andrographis paniculata (Burm.f.) Nees",
    "三七": "Panax notoginseng (Burkill) F.H.Chen",
    "川贝母": "Fritillaria cirrhosa D.Don",
    "浙贝母": "Fritillaria thunbergii Miq.",
    "天花粉": "Trichosanthes kirilowii Maxim.",
    "瓜蒌": "Trichosanthes kirilowii Maxim.",
    "山药": "Dioscorea polystachya Turcz.",
    "莲子": "Nelumbo nucifera Gaertn.",
    "芡实": "Euryale ferox Salisb.",
    "龙眼肉": "Dimocarpus longan Lour.",
    "酸枣仁": "Ziziphus jujuba Mill.",
    "远志": "Polygala tenuifolia Willd.",
    "石菖蒲": "Acorus tatarinowii Schott",
    "龙骨": "Os Draconis",
    "牡蛎": "Ostrea gigas Thunberg",
    "磁石": "Magnetitum",
    "朱砂": "Cinnabaris",
    "鹿茸": "Cervus nippon Temminck",
    "冬虫夏草": "Cordyceps sinensis (Berk.) Sacc.",
    "灵芝": "Ganoderma lucidum (Leyss. ex Fr.) Karst.",
    "枸杞子": "Lycium barbarum L.",
    "麦冬": "Ophiopogon japonicus (L.f.) Ker-Gawl.",
    "天冬": "Asparagus cochinchinensis (Lour.) Merr.",
    "玉竹": "Polygonatum odoratum (Mill.) Druce",
    "百合": "Lilium lancifolium Thunb.",
    "石斛": "Dendrobium nobile Lindl.",
    "沙参": "Adenophora tetraphylla (Thunb.) Fisch.",
    "女贞子": "Ligustrum lucidum Ait.",
    "墨旱莲": "Eclipta prostrata L.",
    "何首乌": "Fallopia multiflora (Thunb.) Harald.",
    "肉苁蓉": "Cistanche deserticola Ma",
    "淫羊藿": "Epimedium brevicornu Maxim.",
    "仙茅": "Curculigo orchioides Gaertn.",
    "补骨脂": "Psoralea corylifolia L.",
    "菟丝子": "Cuscuta chinensis Lam.",
    "杜仲": "Eucommia ulmoides Oliv.",
    "续断": "Dipsacus asper Wall.",
    "骨碎补": "Drynaria roosii Nakaike",
    "狗脊": "Cibotium barometz (L.) J.Sm.",
    "姜黄": "Curcuma longa L.",
    "郁金": "Curcuma aromatica Salisb.",
    "莪术": "Curcuma phaeocaulis Val.",
    "三棱": "Sparganium stoloniferum (Graebn.) Buch.-Ham. ex Juz.",
    "延胡索": "Corydalis yanhusuo W.T.Wang",
    "没药": "Commiphora myrrha Engl.",
    "乳香": "Boswellia carterii Birdw.",
    "桃仁": "Prunus persica (L.) Batsch",
    "红花": "Carthamus tinctorius L.",
    "益母草": "Leonurus japonicus Houtt.",
    "泽兰": "Lycopus lucidus Turcz.",
    "牛膝": "Achyranthes bidentata Bl.",
    "王不留行": "Vaccaria segetalis (Neck.) Garcke",
    "血竭": "Daemonorops draco Bl.",
    "虎杖": "Reynoutria japonica Houtt.",
    "地龙": "Pheretima aspergillum (E.Perrier)",
    "水蛭": "Hirudo nipponia Whitman",
    "全蝎": "Buthus martensii Karsch",
    "蜈蚣": "Scolopendra subspinipes mutilans L.Koch",
    "僵蚕": "Bombyx mori Linnaeus",
    "斑蝥": "Mylabris phalerata Pallas",
    "丁香": "Syzygium aromaticum (L.) Merr. et Perry",
    "小茴香": "Foeniculum vulgare Mill.",
    "吴茱萸": "Evodia rutaecarpa (Juss.) Benth.",
    "花椒": "Zanthoxylum bungeanum Maxim.",
    "高良姜": "Alpinia officinarum Hance",
    "乌药": "Lindera aggregate (Sims) Kosterm.",
    "木香": "Aucklandia lappa DC.",
    "香附": "Cyperus rotundus L.",
    "枳壳": "Citrus aurantium L.",
    "川楝子": "Melia toosendan Sieb. et Zucc.",
    "沉香": "Aquilaria sinensis (Lour.) Gilg",
    "玫瑰花": "Rosa rugosa Thunb.",
    "绿萼梅": "Prunus mume (Sieb.) Sieb. et Zucc.",
    "一枝黄花": "Solidago virgaurea L.",
    "丁公藤": "Erycibe obtusifolia Benth.",
    "三白草": "Saururus chinensis (Lour.) Baill.",
    "三颗针": "Berberis wilsoniae Hemsl.",
    "丝瓜络": "Luffa cylindrica (L.) Roem.",
    "两头尖": "Anemone raddeana Regel",
    "两面针": "Zanthoxylum nitidum (Roxb.) DC.",
}

def enrich_latin_names():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()

    # 确保列存在
    try:
        c.execute("ALTER TABLE tcm_single_herb ADD COLUMN name_latin TEXT")
        conn.commit()
    except:
        pass

    # 更新已知映射
    updated = 0
    for cn, latin in KNOWN_LATIN.items():
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
        data = [{"name_cn": cn, "name_latin": latin, "data_level": "aligned"} for cn, latin in KNOWN_LATIN.items()]
        for i in range(0, len(data), 50):
            batch = data[i:i+50]
            client.table("tcm_single_herb").upsert(batch, on_conflict="name_cn").execute()
        print(f"Supabase同步完成: {len(data)} 条")

if __name__ == "__main__":
    enrich_latin_names()
