from chan_stats import ChanStats

tinyboard_selector = ".intro > a:nth-of-type(2)"
mitsuba_selector = ".quotePost"
meguca_selector = ".quote"
kusaba_selector = ".reflink > a:nth-of-type(2)"

chans = [
    ChanStats('kara', 'karachan.org')
    .users_online_settings("http://karachan.org/online.php", "createTextNode('", "'), a.nextSibling")
    .last_post_settings(('id', '4', 'b', 'z', '$', 'c', 'co', 'a', 'edu', 'f', 'fa', 'h', 'wat', 'ku', 'l', 'med', 'mil', 'mu', 'oc', 'p', 'sp', 'tech', 'thc', 'trv', 'v8', 'vg', 'x', 'og', 'r', 'kara', 'g', 's'),
                        mitsuba_selector),

    ChanStats('vi', 'pl.vichan.net')
    .users_online_settings("https://pl.vichan.net/online.php", "innerHTML+='", "| Aktywne")
    .last_post_settings(('b', 'cp', 'id', 'int', 'r+oc', 'veto', 'waifu', 'btc', 'c', 'c++', 'fso', 'h', 'ku', 'lsd', 'psl', 'sci', 'trv', 'vg', 'a', 'hk', 'lit', 'mu', 'tv', 'x', 'med', 'pr', 'pro', 'psy', 'sex', 'soc', 'sr', 'swag', 'chan', 'meta'),
                        tinyboard_selector),

    ChanStats("wilno", "wilchan.org")
    .users_online_settings("https://wilchan.org/licznik.php")
    .last_post_settings(('b', 'a', 'art', 'mf', 'vg', 'porn', 'lsd', 'h', 'o', 'pol', 'text', 'int'),
                        tinyboard_selector),

    ChanStats("heretyk", "heretyk.org")
    .last_post_settings(('b', 't', 'meta'), ".reflink > a:nth-of-type(2)"),

    ChanStats("kiwi", "kiwiszon.org/kusaba.php", cookie={"accept": "1"})
    .users_online_settings("https://kiwiszon.org/online.php?action=update")
    .last_post_settings(('b', 'wc'), kusaba_selector, "https://kiwiszon.org/boards"),

    ChanStats("sis", "sischan.pw")
    .users_online_settings("https://sischan.pw/online.php", "TextNode('", "'), a.next")
    .last_post_settings(('a', 'sis', 's', 'meta'),
                        mitsuba_selector),

    ChanStats("lenachan", "lenachan.eu.org")
    .last_post_settings(('b', 'int'), tinyboard_selector)
    .users_online_settings("https://lenachan.eu.org/online.php", eStart="document.write(", eStop=")"),

    ChanStats("gówno", "gowno.club")
    .users_online_settings("https://gowno.club/json/ip-count")
    .last_post_settings(('b',), meguca_selector),  # nie dodawać innych desek bo id postów jest liczone globalnie

    ChanStats("auchan", "http://auchan.pw")
    .users_online_settings("http://blogutils.net/olct/online.php?site=auchan.pw/", eStart="</iframe>\');\n$$.write(\"", eStop="\");\n\n$_")
    .last_post_settings(('b', 'kuc', 'hebe'), kusaba_selector),

    ChanStats("korniszon", "kornichan.xyz")
    .users_online_settings("https://kornichan.xyz/online.php", "innerHTML+='", "';var")
    .last_post_settings(('b', '$', 'a', 'c', 'ku', 'r4', 'sp', 'thc', 'trv', 'vg', 'f', 'fa', 'lit', 'mu', 'dt', 'hp', 'kib', 'mil', 'pol', 'x', 'med', 's', 'waifu', 'z', 'fz', 'meta'), tinyboard_selector),

    ChanStats("terchan", "terchan.xyz")
    .users_online_settings("https://terchan.xyz/online.php", eStart="createTextNode('", eStop="'), a.nextSibling)")
    .last_post_settings(('',), kusaba_selector)
    .set_notes("https://terchan.xyz"),

    ChanStats("chanarchive", "szonarchive.pw")

    # .last_post_settings(("b","$","a","c","ku","r4","sp","thc","trv","vg","f","fa","lit","mu","dt","hp","kib","mil","pol","x","med","s","waifu","z","fz","meta"),
    #     tinyboard_selector),
    # ChanStats("rybik", "rybik.ga"),
    # ChanStats("chanarchive", "chanarchive.pw")
]
