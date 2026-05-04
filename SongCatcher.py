#原名thin8.5_covOK.py，修改后加上vip歌曲识别，更新下载链接位置
import eyed3 
from requests import get as requests_get
from requests.exceptions import Timeout, ConnectionError, RequestException  # 新增
from bs4 import BeautifulSoup
from urllib.request import urlretrieve
import re
import os

headers = {
    'User-Agent':'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/63.0.3239.132 Safari/537.36 QIHU 360SE'
}

def clean_filename(filename):
    # 过滤Windows系统禁止的文件名非法字符
    illegal_chars = r'[\\/:*?"<>|]'
    return re.sub(illegal_chars, '', filename)

class SongCatcher():
    def __init__(self,songID):
        self.songID=songID
        self.song_page_soup = None  # 缓存歌曲页面的soup，避免重复请求
        self._init_song_page()      # 初始化时请求一次歌曲页面

    def _init_song_page(self):
        """初始化并缓存歌曲页面的soup，仅请求一次"""
        try:
            song_url = 'https://music.163.com/song?id=' + self.songID
            response = requests_get(song_url, headers=headers, timeout=10)
            response.raise_for_status()  # 校验状态码（404/500直接抛异常）
            self.song_page_soup = BeautifulSoup(response.text, 'lxml')
        except (Timeout, ConnectionError) as e:
            raise type(e)(f"请求歌曲页面失败: {str(e)}")
        except RequestException as e:
            raise RequestException(f"歌曲页面请求异常: {str(e)}")
        
    def is_vip_song(self):
        """判断当前歌曲是否为VIP/付费歌曲（优化版）"""

        # ========== 优化1：缩小VIP标识的查找范围（仅歌曲详情区） ==========
        song_detail_area = self.song_page_soup.find('div', class_='cnt')  # 歌曲详情核心区域
        if not song_detail_area:
            song_detail_area = self.song_page_soup  # 降级：找不到详情区再查整个页面
        
        # 匹配歌曲本身的VIP标识（排除无关文本）
        vip_text_pattern = re.compile(r'VIP歌曲|付费歌曲|黑胶专属|会员专享', re.IGNORECASE)
        vip_text = song_detail_area.find_all(text=vip_text_pattern)
        vip_class_pattern = re.compile(r'vip-song|pay-song|member-only', re.IGNORECASE)
        vip_elements = song_detail_area.find_all(class_=vip_class_pattern)

        # ========== 优化2：仅请求播放链接的响应头（不下载内容） ==========
        play_url = f'https://music.163.com/song/media/outer/url?id={self.songID}.mp3'
        try:
            # stream=True 不下载响应体，仅获取头；allow_redirects=True 跟踪真实地址
            play_response = requests_get(
                play_url, headers=headers, timeout=10, 
                allow_redirects=True, stream=True
            )
            play_response.raise_for_status()  # 校验播放链接状态码（403/404等抛异常）
            
            # 优化3：Content-Type 大小写兼容
            content_type = play_response.headers.get('Content-Type', '').lower()
            # 优化4：判定逻辑（需同时满足：播放链接非音频 + 页面有VIP标识）
            is_audio = content_type in ['audio/mpeg', 'audio/mp3', 'audio/x-mpeg']
            is_vip_mark = bool(vip_text or vip_elements)

            # 最终判定：播放链接不是音频，且页面有VIP标识 → 才是VIP歌曲
            vip_result = not is_audio and is_vip_mark

        # ========== 优化5：精准异常处理（区分播放链接的问题） ==========
        except (Timeout, ConnectionError) as e:
            raise type(e)(f"请求播放链接失败: {str(e)}")
        except RequestException as e:
            # 播放链接返回403/404（常见于VIP/下架歌曲），结合页面标识判断
            if '403' in str(e) or '404' in str(e):
                vip_result = bool(vip_text or vip_elements)  # 403/404 + 有VIP标识 → 判定为VIP
            else:
                raise RequestException(f"检测播放链接异常: {str(e)}")

        return vip_result

    def get_title(self):
        getName='https://music.163.com/song?id='+self.songID
        songHTML=requests_get(getName, headers=headers, timeout=10)

        soup = BeautifulSoup(songHTML.text, 'lxml')
        #when <head> is to long to save as a file name in Windows,there'll be an error,so get from body

        song=(str(soup.body.find(class_="f-ff2")).split(">")[1]).split("<")[0]     #get song-singer,

        singer=soup.body.find(class_="des s-fc4").get_text(strip=True)
        #修改待验证多个歌手显示最后一个的问题
        title=song +" - "+singer
        title=clean_filename(title)
        album_cover=soup.body.find(class_="u-cover u-cover-6 f-fl")     #type为bs4.element.Tag
        
        if not album_cover:
            raise ValueError("未找到专辑封面元素")
        # 直接获取img标签的src属性，和你截图里的结构完全对应
        img_tag = album_cover.find('img')
        if not img_tag or not img_tag.get('src'):
            raise ValueError("未找到封面图片链接")
        cover_url = img_tag.get('src')#cover_url=str(album_cover).split("\"")[5]#防止网页标签顺序更改
        #网易云修改了网页结构，之前的获取封面链接方法失效了，改为直接获取img标签的src属性

        return title,cover_url



    def create_mp3(self,title):#只能下免费的
        file_name=title+".mp3"
        getSong='https://music.163.com/song/media/outer/url?id='+self.songID+'.mp3'
        audio_content=requests_get(getSong, headers=headers, timeout=10).content
        print("正在写入"+file_name)
        with open(file_name,'wb') as f:     #create/rewrite
            f.write(audio_content)


    def change_cover(self,title,cover_url):
        
        file_name=title+".mp3"
        file_image=title+".jpg"
        urlretrieve(cover_url,file_image)       #download album cover
        print("changing album cover")
        audiofile = eyed3.load(file_name)
        if (audiofile.tag == None): 
            audiofile.initTag()
        audiofile.initTag()#bugs!!!!!
        with open(file_image, 'rb') as img_file:
            audiofile.tag.images.set(3, img_file.read(), 'image/jpeg')
        audiofile.tag.save(version=eyed3.id3.ID3_V2_3)

        cover_keep=input("Save album cover?(y/N)")
        if cover_keep == "y":
            pass
        else:
            os.remove(file_image)
#change 调用create，create调用get再return，以避免调用两次get的套圈写法?

def get_lyrics(lyric_id,title):
    lyric_url='http://music.163.com/api/song/lyric?' + 'id=' + lyric_id + '&lv=1&kv=1&tv=-1'
    lyrics_txt=requests_get(lyric_url, headers=headers, timeout=10)
    file_name=title+".lrc"
    with open(file_name,'wb') as f:
    	f.write(lyrics_txt.content)

if __name__ == "__main__":
    try:
        songID=input("请输入网易云音乐歌曲链接或歌曲ID：").split('=')[-1]
        #print(type(songID))
        catcher=SongCatcher(songID)
        title,cover_url=catcher.get_title()
        if catcher.is_vip_song():
            print("检测到该歌曲为VIP/付费歌曲，无法下载。")
        else:
            catcher.create_mp3(title)
            catcher.change_cover(title,cover_url)

            lyric_needs=input("need lyrics?(y/N)")
            if lyric_needs == "y":
                get_lyrics(songID,title)
    except Timeout:
        print("请求超时，请检查网络连接或稍后再试。")
    except ConnectionError:
        print("网络连接错误，请检查您的网络设置。")
    except RequestException as e:
        print(f"请求发生错误: {str(e)}")

#https://music.163.com/#/song?id=536622304 has bug,album cover can't assert into MP3

'''
 	class ClassName(object):
 		"""docstring for ClassName"""
 		def __init__(self, arg):
 			super(ClassName, self).__init__()
 			self.arg = arg
 			
'''
