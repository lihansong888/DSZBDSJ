import requests
import re
import os


# ========== 填写源的地址 ==========
URL_LIST = [
    "https://raw.githubusercontent.com/bang359/dsj/refs/heads/main/dsjcs1.txt",
    "https://raw.githubusercontent.com/qingtingjjjjjjj/Jsnzkpgtv/refs/heads/main/my1.txt"
    
]

# ========== 分组映射：左边是源里的分组名，右边是输出时改后的分组名 ==========
GROUP_MAP = {
    "📺央卫IPTV": "HS央卫IPTV",
    "📺央卫网络": "HS央卫IPTV",
    "📡地方频道": "地方频道",
    "📽爱奇艺": "HS爱奇艺频道",
    "🚀风云极速": "风云极速频道",
    "📺咪咕视频": "咪咕视频",
    # ========== 以下qingtingjjjjjjj ==========
    "黄渤电影": "HS电影直播频道",
    "贺岁电影": "HS电影直播频道",
    "谍战电影": "HS电影直播频道",
    "罪犯电影": "HS电影直播频道",
    "电影高分动作": "HS电影直播频道",
    "电影贺岁": "HS电影直播频道",
    "电影谍战片": "HS电影直播频道",
    "电影谍战": "HS电影直播频道",
    "电影犯罪片": "HS电影直播频道",
    "电影梁家辉": "HS电影直播频道",
    "电影搞笑喜剧": "HS电影直播频道",
    "电影战争片": "HS电影直播频道",
    "电影嫣然影厅": "HS电影直播频道",
    "电影喜剧专场": "HS电影直播频道",
    "电影周星星": "HS电影直播频道",
    "电影动作电影": "HS电影直播频道",
    "电影功夫片": "HS电影直播频道",
    "电影刘德华": "HS电影直播频道",
    "电影八点档": "HS电影直播频道",
    "电影丧尸片": "HS电影直播频道",
    "甄子丹电影": "HS电影直播频道",
    "王晶电影": "HS电影直播频道",
    "玄幻电影": "HS电影直播频道",
    "沈腾电影": "HS电影直播频道",
    "武侠电影": "HS电影直播频道",
    "枪战电影": "HS电影直播频道",
    "林正英电影": "HS电影直播频道",
    "李连杰电影": "HS电影直播频道",
    "战争电影": "HS电影直播频道",
    "成龙电影": "HS电影直播频道",
    "怪兽电影": "HS电影直播频道",
    "强森电影": "HS电影直播频道",
    "宇宙科幻合集": "HS电影直播频道",
    "周星驰电影": "HS电影直播频道",
    "古天乐电影": "HS电影直播频道",
    "功夫电影": "HS电影直播频道",
    "刘德华电影": "HS电影直播频道",
    
}

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
            sp = ln.split(',',1)
            name_part = sp[0].strip()
            url_part = sp[1].strip()
            if url_part == "#genre#":
                current_group = name_part
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
    # 用改后的分组名初始化空列表
    group_bucket = {v: [] for v in GROUP_MAP.values()}
    seen = set()
    for url in URL_LIST:
        try:
            resp = requests.get(url, timeout=15)
            resp.raise_for_status()
            channels = parse_any(resp.text)
            for extinf, play_url in channels:
                ch_name = get_channel_name(extinf)
                ch_group = get_group_title(extinf)
                # 只保留 GROUP_MAP 里有的分组，其他全屏蔽
                if ch_group not in GROUP_MAP:
                    continue
                # 关键：查映射表，把源分组名改成输出分组名
                output_group = GROUP_MAP[ch_group]
                item_key = (ch_name, play_url)
                if item_key not in seen:
                    seen.add(item_key)
                    group_bucket[output_group].append((ch_name, play_url))
        except Exception as e:
            print(f"⚠️ 拉取 {url} 失败：{e}")
    total_cnt = sum(len(v) for v in group_bucket.values())
    print(f"✅筛选结束，共提取 {total_cnt} 个频道")
    for gname, ch_list in group_bucket.items():
        print(f"  - {gname}: {len(ch_list)} 个频道")

    out_dir = os.path.dirname(os.path.abspath(__file__))
    output_m3u = ["#EXTM3U"]
    for gname, ch_list in group_bucket.items():
        for cname, curl in ch_list:
            # 输出时用改后的分组名
            fake_ext = f'#EXTINF:-1 group-title="{gname}",{cname}'
            output_m3u.append(fake_ext)
            output_m3u.append(curl)
    m3u8_path = os.path.join(out_dir, "live.m3u8")
    with open(m3u8_path, "w", encoding="utf-8") as f:
        f.write("\n".join(output_m3u))
    print(f"✅已输出 m3u8：{m3u8_path}")

if __name__ == "__main__":
    main()
