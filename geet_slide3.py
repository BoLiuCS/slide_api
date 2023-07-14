import json
import re
import time
import execjs, requests
from pathlib import Path
from PIL import Image
from loguru import logger
import io, ddddocr, random, rsa, hashlib


class Geetest(object):
    def __init__(self):
        self.headers = {
            "Accept": "*/*",
            "Accept-Language": "zh-CN,zh;q=0.9",
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "Pragma": "no-cache",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/108.0.0.0 Safari/537.36",
        }
        self.context = execjs.compile(open('encrypt.js', 'r', encoding='utf-8').read())

    # 地图还原
    def parse_bg_captcha(self, img, save_path=None):
        """
        滑块乱序背景图还原
        :param img: 图片路径str/图片路径Path对象/图片二进制
            eg: 'assets/bg.webp'
                Path('assets/bg.webp')
        :param save_path: 保存路径, <type 'str'>/<type 'Path'>; default: None
        :return: 还原后背景图 RGB图片格式
        """
        if isinstance(img, (str, Path)):
            _img = Image.open(img)
        elif isinstance(img, bytes):
            _img = Image.open(io.BytesIO(img))
        else:
            raise ValueError(f'输入图片类型错误, 必须是<type str>/<type Path>/<type bytes>: {type(img)}')
        # 图片还原顺序, 定值
        _Ge = [39, 38, 48, 49, 41, 40, 46, 47, 35, 34, 50, 51, 33, 32, 28, 29, 27, 26, 36, 37, 31, 30, 44, 45, 43,
               42, 12, 13, 23, 22, 14, 15, 21, 20, 8, 9, 25, 24, 6, 7, 3, 2, 0, 1, 11, 10, 4, 5, 19, 18, 16, 17]
        w_sep, h_sep = 10, 80

        # 还原后的背景图
        new_img = Image.new('RGB', (260, 160))

        for idx in range(len(_Ge)):
            x = _Ge[idx] % 26 * 12 + 1
            y = h_sep if _Ge[idx] > 25 else 0
            # 从背景图中裁剪出对应位置的小块
            img_cut = _img.crop((x, y, x + w_sep, y + h_sep))
            # 将小块拼接到新图中
            new_x = idx % 26 * 10
            new_y = h_sep if idx > 25 else 0
            new_img.paste(img_cut, (new_x, new_y))

        if save_path is not None:
            save_path = Path(save_path).resolve().__str__()
            new_img.save(save_path)
        return new_img

    # 注册滑块
    def register_slide(self):

        url = "https://www.geetest.com/demo/gt/register-slide"
        params = {
            "t": int(time.time() * 1000),
        }
        response = requests.get(url, headers=self.headers, params=params)
        challenge = response.json()["challenge"]
        gt = response.json()["gt"]
        # print('第一次请求：========>','challenge:',challenge,'gt:',gt)
        logger.info(f'gt:{gt},challenge:{challenge}')
        return gt, challenge

    def get_php(self, gt, challenge):
        url = "https://apiv6.geetest.com/get.php"

        params = {
            "gt": gt,
            "challenge": challenge,
            "lang": "zh-cn",
            "pt": "0",
            "client_type": "web",
            # "w": "5muM2kn7Svi7zzGDxxypVT6XzuttqbrJWA4z4i1bMDYasNZnNQA(1vWHEjH)sh0Hsj2EXxDIDFxZxv2jFh1y(SfgWZw3JJymYtUOK3wl7NKV4icZZR1FtiGfYwn64Zhh0h6IVnHARVbsZmzYVmCZ6SAzMdvXspxPNKP0voSPr9qUTd8WSIQzOBIacy0mqAtaCRiwws5f3FIPhD1JpQvLZaBlYEOfmy(8buQ7I(NjffOZ7PKtjGpW9xqTX4DxAjxtWgd5dXHVexs5d7OQHySL8H4RuyUucsWnoU9BwBrAqaNDsrs5ZYPSmfUo2C(R1J3Ku1jwQKo26Z7(81Uahw5Hpi1w4DREFkJI50US0iW7j3ZEBhpOpdwNu7oQcIzx(WvjgzclXXfabdIWf6A0pgTpv6of9g(Kk77TqtlTt5oMMUi4PcYjrjk4oojAdrLasONqifhXMDNJ)I7ucYuiu)J8cx1nSMY0J4Dy200LSf710oCpfur9F)6cbHRcigNGeO2eK1LOdV9BzQtbcqEE(Bm2niqpPYrapqtxW13DdLDfjLl6FKrg24TSoWix0mwtc3wBf62hYmONpztTo8SrMwKAMbR3cQVZVw32rHpaAqdXSS3NSOcrs)Jkwc1DUiu(AR68LCXEmRPbSM4Rh1g1VuXLieL4jccfzegluBHRGyl6u(oVPKynpvibAskHYJwapp9Jc2FMQXlQuPS6e)oP8vOEIqj(EfeBFF)YWOtiLVZLttLO1h3iXsuyU4Sbb)(938L)5hjZkL4cRAEObKaYlkEy04jTFOWmb17IbvcYg)Ga3heAGTyc1(eosFL5W1H5np)jN09xRm28JYVxOaPAq5R7QXOLK8KmGlQZoWHraYQSMJCcA8(UlujsePkaJRtJHmLeAXbk82JSOwrS0ObVuAPQi)iLS7AF5M2G66Vhjhs6oPsazHmc850siVZLvppvNXB6nQdVYO4aLqtvOHeX3XgBz)2zhEHZh6E8214GcD25SYKtFhVS5i6D3NZGjo7B9rmmtG)TdgSQFAiqfPBmXkL4fLi7d2XzCUplb)KhquezjuK(pJwuas5xdZoCxCGQDsL2etzx5FuvjO6nFGsXzPOfEujC8IQxD3yDJMzA0HEpM76NmgLScs5bckLjgYjcfAClqLXF8Hqub8W8YQHynFx1Tp7pP1HslfI8W)l2ok8KAvuFkvUqJPFpfzFZpP4OyjsfKHo)7S5Lihj7V9I6xHOA8SLsUcLfAFUDLhyIpM9i8397DYzNRe)25ucxK2pzcF4qbdQ49sX6RAbQgp68FhTb4dbG(yh3ONgqQFQOS4RmfMo5OrVX1J1QCiTZ7FqJH9aLiiucWjeXBz1XkaWudjWGR5s18ly1VMmJ1gv02aI)4htdBJuXs7rLf9B)lHvtJzyQypvJg8jsi8)jXOYIkt1(EGsV3A7iVMtO)tIu5sU5MHugkj5drWVyatC0HKGCpuRRNjyAlsP)HWHgDOe4UsQdXDp84vbf2AUzeSOPSXa6fnjuK8nnQsPZqcf8cJFtox2QFVL2JAut(9SPCuYE9RTKcqLJeY(dalbbZlToRXvrc6ImJc8iVTKCJ6Fk9GxgGAwT1EZOU4QpnpnI01ednFLQSjGWglhnxuaOn9rg2oSYcCFhWgrYwqPf(njEwZqms0YnqYsAe(LN)bcCkBmmBiUljrsguw5ZXjiBcreQxUp4VHmlTFxjHlJwZi9qFJaIU5Bi9v2PDVIDNn6hgt)soxYa52aKDkeGod5w5Ya3AfmTeXQM2QxMwkXuukAFGcqnGXEUlJfGkTPBPYrIqV1hE5F36hQVNjHuhnnTAzmkSueqUCSBCIcFCe4J4)K9)pRqUIuhtVeflXmG1qgudRofpm(VAgG5RsdMxEhpQnMg9sHaHDyUEaZIy0(BruLLbUhNkLHQ0kQ1Cy9mzQO3w4YR2MkRLtUuB8MT(xLRB(bVkVw9FXWP0LlJ5JLTQz8CvBnAG7iv6JuOWDNYW58NJnYHERMIPPCNIfo0bUEMflzlLFSUiaiDCxGpwi6X9lmzljrfyl0BRCti1zv4ewRW(Q6bgzZ4FWD9Q9ePkgD)AQhK0f6HRGvsyoqlQ7UaEHbG1U1sAzJbQTs5s9efEl4tMzrZklM0GEaGuoL7QV5JmBvt8S6Ph8XxiCg6lIbNafnMfdOELyRcSBcUInNAiiNHuDn5bHRtW)1AK)9paViMlzP4oymvrED6XnGH7Ep9932mSyTTh3BiE4zhLt0(rEM(0XXhmmIG8)MwtSv38FQ3Y67dwT5FcUBCpC80zO1e9NF2wcQWjegHHWhbdaiAAsFATvqDh4z)1JQa((4WlejcrV)SvfcNLDRFVngdy6z0GNpyEcOmLKwRn7SNiaK)rHS0ymVRfgJUzDRtqskDJBZdhvL7ZnhxvQI.333fb38885e00d146b510c454db2cedb23eb32726cf1d6408e59cd1d730c91885d24164cf4eb785165a1a38fd9df94c98756486393528c131908fc9ac532c48c0f310e57be79f8522fe91334903fdeadbdcf00a63f986b242649c8707a14a0ad4909c91e53faaaf12ff71d57ecaad2ffeabeb801265f037db748b24d1474fd4c",
            "callback": "geetest_" + str(int(time.time() * 1000))
        }
        response = requests.get(url, headers=self.headers, params=params)

        res = re.findall(r'geetest_\d*[(](.*)[)]', response.text)[0]
        c = json.loads(res)['data']['c']
        s = json.loads(res)['data']['s']

        # print('\n第二次请求========>', 'c的值:',c,'s的值：',s)

        return c, s

    def ajax_php(self, gt, challenge):
        url = "https://api.geetest.com/ajax.php"
        params = {
            "gt": gt,
            "challenge": challenge,
            "lang": "zh-cn",
            "pt": "0",
            "client_type": "web",
            # "w": "",
            "callback": "geetest_" + str(int(time.time() * 1000))
        }
        # print(params)
        response = requests.get(url, headers=self.headers, params=params)

        # print('\n第三次请求========>', '请求滑块类型:',response.text)

    def get_slide(self, gt, challenge):

        url = "https://api.geetest.com/get.php"
        params = {
            "is_next": "true",
            "type": "slide3",
            "gt": gt,
            "challenge": challenge,
            "lang": "zh-cn",
            "https": "true",
            "protocol": "https://",
            "offline": "false",
            "product": "embed",
            "api_server": "api.geetest.com",
            "isPC": "true",
            "autoReset": "true",
            "width": "100%",
            "callback": "geetest_" + str(int(time.time() * 1000))
        }

        response = requests.get(url, headers=self.headers, params=params)
        try:
            # print(response.text)
            res = re.findall(r'geetest_\d*[(](.*)[)]', response.text)[0]
            challenge = json.loads(res)['challenge']

        except:
            logger.error('请求失败,gt和challenge值已失效')
            return None, None, None, None
        # # https://www.geetest.com/pictures/gt/d401d55fc/bg/bdc103dc9.jpg
        bg = 'https://static.geetest.com/' + json.loads(res)['bg']
        full = 'https://static.geetest.com/' + json.loads(res)['fullbg']
        s = json.loads(res)['s']
        c = json.loads(res)['c']

        # 请求图片并保存
        image1 = requests.get(bg, headers=self.headers)
        bg_path = '未还原bg.jpg'
        with open(bg_path, 'wb') as f:
            f.write(image1.content)

        image2 = requests.get(full, headers=self.headers)
        full_path = '未还原full.jpg'
        with open(full_path, 'wb') as f:
            f.write(image2.content)

        # 还原图片
        self.parse_bg_captcha(bg_path, './bg.jpg')
        # print('bg.jpg还原成功:', './bg.jpg')
        self.parse_bg_captcha(full_path, './full.jpg')
        # print('full.jpg还原成功:', './full.jpg')

        # 返回滑块x坐标
        x = self.get_x()
        x = x - 5

        logger.info(f'\n第四次请求========>New_challenge的值:{challenge} c的值{c} New_s的值{s}  识别滑块的x坐标-5:{x}')
        return challenge, c, s, x

    def get_x(self):
        slide = ddddocr.DdddOcr(det=False, ocr=False)
        with open('bg.jpg', 'rb') as f:
            target_bytes = f.read()
        with open('full.jpg', 'rb') as f:
            background_bytes = f.read()
        res = slide.slide_comparison(target_bytes, background_bytes)

        return res.get('target')[0]

    def __ease_out_expo(self, sep):
        """
        缓动函数 easeOutExpo
        参考：https://easings.net/zh-cn#easeOutExpo
        """
        if sep == 1:
            return 1
        else:
            return 1 - pow(2, -10 * sep)

    def get_slide_track(self, distance):
        """
        根据滑动距离生成滑动轨迹
        :param distance: 需要滑动的距离
        :return: 滑动轨迹<type 'list'>: [[x,y,t], ...]
            x: 已滑动的横向距离
            y: 已滑动的纵向距离, 除起点外, 均为0
            t: 滑动过程消耗的时间, 单位: 毫秒
        """

        if not isinstance(distance, int) or distance < 0:
            raise ValueError(f"distance类型必须是大于等于0的整数: distance: {distance}, type: {type(distance)}")
        # 初始化轨迹列表
        slide_track = [
            [random.randint(-50, -10), random.randint(-50, -10), 0],
            [0, 0, 0],
        ]
        # 共记录count次滑块位置信息
        count = 30 + int(distance / 2)
        # 初始化滑动时间
        t = random.randint(50, 100)
        # 记录上一次滑动的距离
        _x = 0
        _y = 0
        for i in range(count):
            # 已滑动的横向距离
            x = round(self.__ease_out_expo(i / count) * distance)
            # 滑动过程消耗的时间
            t += random.randint(10, 20)
            if x == _x:
                continue
            slide_track.append([x, _y, t])
            _x = x
        slide_track.append(slide_track[-1])
        return slide_track

    # 验证滑块信息
    def get_validate(self, gt, challenge, c, s, x):
        url = "https://api.geetest.com/ajax.php"

        # RSA加密
        random = 'e06879c44e208a8e'
        u = self.rsa_encrypt(random)
        # print('RSA加密后的u：', u)
        # 通过x生成轨迹
        track = self.get_slide_track(x)

        # print('生成的滑动轨迹：', track)
        h = self.get_h(gt, challenge, c, s, track, random)
        # print('h的值：', h)
        w = h + u

        params = {
            "gt": gt,
            "challenge": challenge,
            "lang": "zh-cn",
            "$_BCX": "0",
            "client_type": "web",
            "w": w,
            "callback": "geetest_" + str(int(time.time() * 1000))
        }

        # response = requests.get(url, headers=self.headers, params=params)
        response = requests.get(url, headers=self.headers, params=params)
        logger.success(f'验证滑块信息: {response.text}')
        return response.text

    def rsa_encrypt(self, random):
        """
        rsa加密
        :param random: 随机数
        :return: 加密后的随机数
        """
        # 公钥模数
        n = '00C1E3934D1614465B33053E7F48EE4EC87B14B95EF88947713D25EECBFF7E74C7977D02DC1D9451F79DD5D1C10C29ACB6A9B4D6FB7D0A0279B6719E1772565F09AF627715919221AEF91899CAE08C0D686D748B20A3603BE2318CA6BC2B59706592A9219D0BF05C9F65023A21D2330807252AE0066D59CEEFA5F2748EA80BAB81'
        # 公钥指数
        e = '10001'
        # 构造公钥
        key = rsa.PublicKey(e=int(e, 16), n=int(n, 16))
        # print('key:',key)
        # 加密
        message = rsa.encrypt(random.encode('utf-8'), key)
        # 转换成16进制
        encrypt_data = message.hex()
        return encrypt_data

    def get_userresponse(self, x, challenge):

        userresponse = self.context.call("HHH", x, challenge)

        return userresponse

    def get_aa(self, track, c, s):
        aa = self.context.call("get_aa", track, c, s)
        return aa

    def get_h(self, gt, challenge, c, s, track, random):

        userresponse, passtime, rp, aa, ep = '', '', '', '', ''

        passtime = track[-1][-1]  # 滑动时间
        x = track[-1][0]  # 滑动距离x
        userresponse = self.get_userresponse(x, challenge)
        # window._W['$_BBEI'](window._W['$_FDL'](xy), c, s)
        aa = self.get_aa(track, c, s)  # 滑动轨迹加密
        ep = {
            "v": "7.9.0",
            "$_BIo": False,
            "me": True,
            "tm": {
                "a": 1681368670117,
                "b": 1681368670842,
                "c": 1681368670842,
                "d": 0,
                "e": 0,
                "f": 1681368670121,
                "g": 1681368670124,
                "h": 1681368670151,
                "i": 1681368670151,
                "j": 1681368670269,
                "k": 1681368670165,
                "l": 1681368670269,
                "m": 1681368670823,
                "n": 1681368670832,
                "o": 1681368670843,
                "p": 1681368671007,
                "q": 1681368671007,
                "r": 1681368671008,
                "s": 1681368671008,
                "t": 1681368671008,
                "u": 1681368671008
            },
            "td": -1
        }
        md5_data = (str(gt) + challenge[0:32] + str(passtime))
        rp = hashlib.md5(md5_data.encode('utf-8')).hexdigest()

        o = {
            "lang": "zh-cn",
            "userresponse": userresponse,  # 后端返回的challenge
            # {x: 59.260998539588186, y: -1.6461456075309115}   t就是x轴取整 滑块的移动距离
            "passtime": passtime,
            "imgload": 243,
            "aa": aa,
            "ep": ep,
            "h9s9": "1816378497",
            "rp": rp  # gt + 32 位 challenge + passtime，再经过 MD5 加密
        }
        # print('o:',o)
        h = self.context.call("get_h", o, random)
        # print('h:',h)
        return h

    def run(self, challenge):
        # gt, challenge = self.register_slide()
        gt = '3378262dc41a29fef92707dc5709d53d'
        # c,s = self.get_php(gt,challenge)
        self.ajax_php(gt, challenge)

        # 返回新的challenge和s参数  滑块x轴坐标
        challenge1, c, s, x = self.get_slide(gt, challenge)
        if challenge1 == None:
            return None

        # 验证滑块信息
        self.get_validate(gt, challenge1, c, s, x)


if __name__ == '__main__':
    GEET_slide = Geetest()
    GEET_slide.run('97b7b423db002567c8e0cc4cb536c34e')
