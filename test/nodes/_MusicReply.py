import random
from typing import Any

from sekaibot import Node
from sekaibot.adapter.cqhttp.event import MessageEvent
from sekaibot.adapter.cqhttp.message import CQHTTPMessageSegment
from sekaibot.permission import SuperUser
from sekaibot.rule import Keywords


def get_music_dict():
    return {
        "コぇちっちゃ＜てゴ×ンネ": 2634888175,
        "Angel (feat. 可不)": 1993088172,
        "Aye, aye, sir!": 2638525890,
        "Boi": 2008261020,
        "CH4NGE": 1950028990,
        "CH4NGE (feat. 可不)": 1950028990,
        "Dull!! (feat.  可不)": 2014256984,
        "Dull!! (feat. 可不)": 2014256984,
        "Fallen": 28935215,
        "GURU (ボカロ盤バージョン)": 1972350196,
        "Nosy": 2138232626,
        "Rabbit!?。": 1991045644,
        "あなたの愛した世界が見たくて": 2638034902,
        "あのね (feat. 可不)": 1969551854,
        "いっせーのーで": 1879331969,
        "いまいち (feat. 可不)": 2017145307,
        "ぅゅゅ(´；ω；｀)": 2103430407,
        "うらやみ しい (feat. Kai,初音ミク,可不)": 2129136868,
        "うらやみしい (feat. Kai,初音ミク,可不)": 2129136868,
        "きゅうくらりん": 1875436617,
        "くうになる (feat. 可不&初音ミク)": 1912598037,
        "このままの心で怖かった": 2151646203,
        "これが最後に夏 だから": 2638037327,
        "しあわせのはこ": 2101412302,
        "それだけ": 2620017424,
        "ただ病名が欲しかった": 2084397982,
        "だきしめるまで。 (feat. 可不)": 1917999677,
        "ちょっかい問題": 2067572658,
        "ちょっとあざとい": 1871751442,
        "ねこふんじゃった。": 2074417425,
        "ねむれないよる (feat. 可不)": 2625456240,
        "はぐ (feat. 初音ミク & 可不)": 2097828677,
        "ひみつのユーフォー": 1870563237,
        "ふわり (feat. MIMI,可不,初音ミク)": 2034848078,
        "またおいで": 2635812056,
        "みんな嫌いだ、消えて。": 2637054771,
        "もっとかわいい": 1957290730,
        " ようやく君が死んだんだ。": 1968613039,
        "アイソトープ": 2141345581,
        "アイロニカルユー トピア": 1935648709,
        "アンチ活動中": 2639749210,
        "エリート": 2139362850,
        "オマジナイ": 2084311527,
        "カルト (feat. 可不)": 2636997854,
        "キッカイケッタイ": 1979045976,
        "ギフト": 2149523329,
        "サヨナラは言わないでさ (feat. 可不)": 2057648979,
        "ジェラシス": 1867931739,
        "ジブラ": 1982784816,
        "タクシィ": 2122655412,
        "ツキミチシルベ (feat. 初音ミク & 可不) [vocaloid ver.]": 2148168729,
        "ドリームイーター": 2003904108,
        "ナイトルール": 1914692622,
        "ハナビラ": 2144758550,
        "ババースデイ": 2097515349,
        "パイルクレイ (可不 ver.)": 2629500638,
        "ヒミツ (feat. 可不)": 1961784984,
        "プロポーズ": 2071866065,
        "マニアカル": 2639634944,
        "メモリー    ー": 2095851244,
        "下剋上": 2091876015,
        "不埒な喝采": 1867928484,
        "今はいいんだよ。 (feat. 可不)": 2008735702,
        "今日、世界が終わるのでした。 (feat. 可不)": 2637791865,
        "凡人": 1465290469,
        "化孵化": 2058263033,
        "可不ちゃんのカレーうどん狂騒曲": 2099352526,
        "天使の翼。": 2006511504,
        "妄想哀歌 (feat. 初音ミク & 可 不)": 2054974200,
        "心を刺す言葉だけ (feat. 初音ミク & 可不)": 2091770490,
        "息をするだけ (feat. 可不)": 2066426135,
        "悲しみの雨": 533455758,
        "愛するように": 2127734560,
        "損益分 岐点 (feat. 可不)": 2636669090,
        "撫でんな": 1941555670,
        "明るい夜": 2624045024,
        "明日が来るのが怖くてさ (feat. 可不)": 2135100197,
        "昏い夜 (feat. 吐息,v flower,可不)": 2052146908,
        "星界ちゃんと可不ちゃんのおつかい合騒曲": 2091673318,
        "死にたいわけじゃなくて (feat. 可不)": 2069326520,
        "流線形メーデー": 1963685523,
        "無理に笑わなくて良いよ": 1922287635,
        "生きる (feat. 可不)": 1862516716,
        "私のドッペルゲンガー": 2042620663,
        "絶対敵対メチャキライヤー": 1941347910,
        "縛": 1989151258,
        "脆弱性": 2059789820,
        "脳裏のマキナ (feat. 可不)": 1904183194,
        "花となれ": 1867931740,
        "花火 が落ちる前に": 2620449634,
        "薄明の雫": 2638086615,
        "食虫植物": 1867921493,
        "飴色の微熱": 1959409924,
        "これが最後に夏だから": 2638037327,
        "ようやく君が死んだんだ。": 1968613039,
        "キャットラビング": 2042620725,
        "キュートなカノジョ": 2617560634,
        "クィホーティ": 1959715041,
        "シニカルディ ストピア": 1922810292,
        "チーズ": 2139361218,
        "ハナタバ": 1999253939,
        "フィオーレ (feat. 初音ミク & 可不)": 2077050077,
        "マーシャル・マキシマイザー": 1900171627,
        "メモリー": 2095851244,
        "妄想哀歌 (feat. 初音ミク & 可不)": 2054974200,
        "愛し愛 (feat. 初音ミク           & 可不)": 2117567658,
        "愛撫誘発性攻撃行動 (feat. 可不)": 1998983149,
        "感傷トワイライト": 512376195,
        "朝日": 1867928486,
        "死んでしまったんだ": 1944863562,
        "私は、私達は": 2026535564,
        "裏世界 (feat. 可不)": 2154502893,
        "酸素ソング": 2634843775,
        "ストッ ク ホ ルムオフィス": 2080019955,
        "フォニイ": 1900172235,
        "ローライト": 2633908595,
        "妄想哀歌 (feat. 初音ミ   ク & 可不)": 2054974200,
        "空を満たして (feat. 可不)": 1956553544,
        "電脳眠眠猫 (feat. 可不)": 2146644042,
        "九段下パンデミック。": 2637083552,
        "シニカルデ ィストピア": 1922810292,
        "ストックホルムオフィス": 2080019955,
        "愛し愛 (feat. 初音ミク & 可不)": 2117567658,
        "ギ フト": 2149523329,
        "シニカルディストピア": 1922810292,
    }


@SuperUser()
@Keywords("随机歌曲", "随机音乐")
class MusicComm(Node[MessageEvent, dict, Any]):
    priority: int = 1
    block: bool = True

    async def handle(self) -> None:
        music = get_music_dict()
        song_id = music[random.choice(list(music.keys()))]
        response = CQHTTPMessageSegment.music(type_="163", id_=song_id)
        await self.reply(response)
