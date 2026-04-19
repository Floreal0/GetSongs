import requests
import json

# 完善的请求头（模拟真实浏览器，避免反爬）
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Referer': 'https://music.163.com/',
    'Accept': 'application/json, text/plain, */*',
    'Accept-Encoding': 'gzip, deflate, br',
    'Accept-Language': 'zh-CN,zh;q=0.9',
    'Connection': 'keep-alive'
}

def search_song_id(search):
    # 1. 空输入校验
    if not search.strip():
        print("⚠️ 输入不能为空！")
        return None
    
    # ========== 核心功能：搜索歌曲并提取ID ==========
    print("\n📌 正在搜索歌曲并提取ID...")
    # 网易云最新搜索接口
    api_url = 'https://music.163.com/api/cloudsearch/pc'
    params = {
        's': search,
        'type': 1,         # 1=歌曲
        'offset': 0,
        'limit': 10,
        'total': 'true',
        'csrf_token': ''
    }

    try:
        response = requests.get(
            api_url,
            headers=HEADERS,
            params=params,
            timeout=10,
            allow_redirects=False
        )
        
        # 校验HTTP状态码
        if response.status_code != 200:
            print(f"❌ 接口请求失败，状态码：{response.status_code}")
            return None
        
        # 解析JSON
        try:
            result = json.loads(response.text)
        except json.JSONDecodeError as e:
            print(f"❌ JSON解析失败：{e}")
            return None
        
        # 校验业务码
        if result.get('code') != 200:
            print(f"❌ 接口返回错误：{result.get('msg', '未知错误')}")
            return None
        
        # 解析歌曲列表
        songs = result.get('result', {}).get('songs', [])
        if not songs:
            print("❌ 未搜索到相关歌曲！")
            return None
        
        # 展示歌曲信息
        print("\n===== 搜索结果（前10条） =====")
        song_list = []  # 存储歌曲信息，方便后续选择
        for idx, song in enumerate(songs, 1):
            song_id = song.get('id', '未知ID')
            song_name = song.get('name', '未知歌名')
            # 提取歌手（适配新接口ar字段）
            singer_list = song.get('ar', [])
            singers = '/'.join([a.get('name', '未知歌手') for a in singer_list]) if singer_list else '未知歌手'
            # 提取专辑
            album = song.get('al', {}).get('name', '未知专辑')
            
            song_info = {
                'index': idx,
                'id': song_id,
                'name': song_name,
                'singer': singers,
                'album': album
            }
            song_list.append(song_info)
            print(f"{idx}. 歌名：{song_name} | 歌手：{singers} | 专辑：{album} | ID：{song_id}")
        
        # 让用户选择歌曲，返回选中的ID
        while True:
            try:
                choice = input("\n请输入要下载的歌曲序号（1-10）：").strip()
                choice_idx = int(choice) - 1  # 转列表索引（从0开始）
                if 0 <= choice_idx < len(song_list):
                    selected_song = song_list[choice_idx]
                    selected_id = str(selected_song['id'])
                    print(f"\n✅ 已选中：{selected_song['name']} - {selected_song['singer']} | 歌曲ID：{selected_id}")
                    return selected_id
                else:
                    print(f"❌ 请输入1-{len(song_list)}之间的序号！")
            except ValueError:
                print("❌ 输入无效！请输入数字序号！")
    
    except requests.exceptions.Timeout:
        print("❌ 请求超时！请检查网络")
        return None
    except requests.exceptions.ConnectionError:
        print("❌ 网络连接失败！请检查网络")
        return None
    except Exception as e:
        print(f"❌ 提取ID失败：{str(e)}")
        return None

# 主逻辑
if __name__ == "__main__":
    user_input = input("请输入要搜索的歌曲名：")
    # 调用搜索函数，获取选中的歌曲ID
    selected_song_id = search_song_id(user_input)
    # 后续可直接把这个ID传给下载函数
    if selected_song_id:
        print(f"\n🎯 最终获取的歌曲ID：{selected_song_id}")
