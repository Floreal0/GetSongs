import webbrowser

def open_page(search):
    # 1. 空输入校验：避免输入空值时报错
    if not search.strip():
        print("⚠️ 输入不能为空！")
        return
    
    words=search.split(" ")
    url="https://music.163.com/#/search/m/?s="
    # 用%20连接所有关键词，避免末尾多一个%20
    search_str = "%20".join(words)
    final_url = base_url + search_str
    
    # 3. 打开浏览器 + 提示信息
    print(f"🔍 正在打开网易云搜索页：{final_url}")
    webbrowser.open(final_url)
open_page(input())
