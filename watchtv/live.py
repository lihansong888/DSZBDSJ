import requests
import re
import os

# ========== 源地址（加速链接） ==========
URL_LIST = [
    "https://cdn.jsdelivr.net/gh/bang359/dsj@main/dsjcs1.txt",
    "https://cdn.jsdelivr.net/gh/qingtingjjjjjjj/Jsnzkpgtv@main/my1.txt"
]

# ========== 第一块：分组映射（左边：源内分组名，右边输出分组名） ==========
GROUP_MAP = {
    "📺央卫IPTV": "HS央卫IPTV",
    "📺央卫网络": "HS央卫IPTV",
    "📡地方频道": "地方频道",
    "📽爱奇艺": "HS爱奇艺频道",
    "🚀风云极速": "风云极速频道",
    "📺咪咕视频": "咪咕视频",
}

# ========== 第二块：频道白名单（这些是频道名，不是分组！命中全部归入 HS电影直播频道） ==========
MOVIE_CHANNEL_NAMES = {
    "黄渤电影",
    "贺岁电影",
    "谍战电影",
    "罪犯电影",
    "电影高分动作",
    "电影贺岁",
    "电影谍战片",
    "电影谍战",
    "电影犯罪片",
    "电影梁家辉",
    "电影搞笑喜剧",
    "电影战争片",
    "电影嫣然影厅",
    "电影喜剧专场",
    "电影周星星",
    "电影动作电影",
    "电影功夫片",
    "电影刘德华",
    "电影八点档",
    "电影丧尸片",
    "甄子丹电影",
    "王晶电影",
    "玄幻电影",
    "沈腾电影",
    "武侠电影",
    "枪战电影",
    "林正英电影",
    "李连杰电影",
    "战争电影",
    "成龙电影",
    "怪兽电影",
    "强森电影",
    "宇宙科幻合集",
    "周星驰电影",
    "古天乐电影",
    "功夫电影",
    "刘德华电影",
}

unknown_group = set()
unknown_name = set()

def parse_any(text: str):
    res = []
    extinf_line = None
    current_group = None
    for raw_line in text.splitlines():
        ln = raw_line.strip()
        if not ln:
            continue
        if ln.startswith("#EXTINF:"):
            extinf_line = ln
            continue
        if extinf_line is not None and not ln.startswith("#"):
            res.append((extinf_line, ln))
            extinf_line = None
            continue
        if ',' in ln and not ln.startswith("#"):
            sp = ln.split(',', 1)
            name_part = sp[0].strip()
            url_part = sp[1].strip()
            if url_part == "#genre#":
                current_group = name_part.strip()
                continue
            if current_group:
                fake_ext = f'#EXTINF:-1 group-title="{current_group}",{name_part}'
            else:
                fake_ext = f'#EXTINF:-1,{name_part}'
            res.append((fake_ext, url_part))
    return res

def get_channel_name(extinf):
    if "," in extinf:
        return extinf.split(",")[-1].strip()
    return ""

def get_group_title(extinf):
    m = re.search(r'group-title="([^"]+)"', extinf)
    if m:
        return m.group(1).strip()
    return ""

def main():
    # 初始化输出分组桶
    group_bucket = {}
    for g in GROUP_MAP.values():
        group_bucket[g] = []
    group_bucket["HS电影直播频道"] = []

    seen = set()
    for url in URL_LIST:
        print(f"\n===== 正在拉取源：{url} =====")
        try:
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
            }
            resp = requests.get(url, timeout=20, headers=headers)
            resp.raise_for_status()
            print(f"✅源成功下载，前300字符预览：{resp.text[:300]}")
            channels = parse_any(resp.text)
            print(f"📦解析出来总条目：{len(channels)}")

            for extinf, play_url in channels:
                ch_name = get_channel_name(extinf)
                ch_group = get_group_title(extinf)

                out_group = None
                # 规则1：先判断分组是否在分组映射表里
                if ch_group in GROUP_MAP:
                    out_group = GROUP_MAP[ch_group]
                # 规则2：分组不匹配，再判断频道名是不是电影频道白名单
                elif ch_name in MOVIE_CHANNEL_NAMES:
                    out_group = "HS电影直播频道"
                else:
                    # 都不满足，记录并跳过
                    if ch_group:
                        unknown_group.add(ch_group)
                    unknown_name.add(ch_name)
                    continue

                item_key = (ch_name, play_url)
                if item_key not in seen:
                    seen.add(item_key)
                    group_bucket[out_group].append((ch_name, play_url))
        except Exception as e:
            print(f"❌拉取失败：{e}")

    print("\n===== 调试信息 =====")
    print(f"遇到的未知分组：")
    for g in sorted(unknown_group):
        print(f"   > {repr(g)}")
    print(f"未匹配的频道名：")
    for n in sorted(unknown_name):
        print(f"   > {repr(n)}")

    total_cnt = sum(len(v) for v in group_bucket.values())
    print(f"\n✅最终有效频道总数：{total_cnt}")
    for gname, ch_list in group_bucket.items():
        print(f"   {gname} : {len(ch_list)}")

    out_dir = os.path.dirname(os.path.abspath(__file__))
    output_m3u = ["#EXTM3U"]
    for gname, ch_list in group_bucket.items():
        for cname, curl in ch_list:
            fake_ext = f'#EXTINF:-1 group-title="{gname}",{cname}'
            output_m3u.append(fake_ext)
            output_m3u.append(curl)

    m3u8_path = os.path.join(out_dir, "live.m3u8")
    with open(m3u8_path, "w", encoding="utf-8") as f:
        f.write("\n".join(output_m3u))
    print(f"\n✅文件输出到：{m3u8_path}")

if __name__ == "__main__":
    main()

