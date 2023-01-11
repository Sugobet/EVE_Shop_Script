from os import system, path as Path
import time
import datetime
from PIL import Image
from cnocr import CnOcr
import threading
from random import randint
from ast import literal_eval
import pyfiglet


'''
收藏夹商品个数限制最多 16 个

两种模式：
    狙击手模式：针对单一一个商品进行监听
    正常模式：对收藏夹所有商品进行监听

购买商品：
    商品价格低于 设置的价格就购买，否则继续看下一个商品
    购买时按照当前余额购买，余额充足的情况下默认买断，余额不足以买断则能买多少就买多少
    如果余额比商品单价少则放弃购买，继续看下一个商品
    如果商品没有卖单，继续看下一个商品

'''


收藏夹商品个数 = 14
模式 = 1

path = 'C:/Users/sugob/Desktop/shop'
device = ["bot1", '192.168.1.250:5667']

one_index = [286, 78, 527, 112]
two_index = [292, 243, 530, 271]
商品列表 = {}

cnocr = CnOcr()

def LoadImage(tag, path) -> Image.Image:
    try:
        img = Image.open(f'{path}/{tag}.png')
    except Exception as e:
        添加日志(f'错误：{e}')
        time.sleep(3)
        return LoadImage(tag, path)
    return img


def 获取截图(device_address, device_name):
        system(f'adb -s {device_address} exec-out screencap -p > {device_name}.png')


def crop(x1, y1, x2, y2, img: Image.Image) -> Image.Image:
    try:
        newimg = img.crop((x1, y1, x2, y2))
    except Exception as e :
        添加日志(f'错误：{e}')
    return newimg


def 向上滑屏幕():
    start_pointX = randint(550, 700)
    start_pointY = randint(550, 600)
    system(f"adb -s {device[1]} shell input swipe {start_pointX} {start_pointY} {start_pointX} {start_pointY - 400}")


def 向下滑屏幕():
    start_pointX = randint(550, 700)
    start_pointY = randint(130, 155)
    system(f"adb -s {device[1]} shell input swipe {start_pointX} {start_pointY} {start_pointX} {start_pointY + 400}")



def 获取收藏夹商品():
    本地收藏夹商品个数 = 收藏夹商品个数
    本地商品索引  = one_index.copy()
    列数 = 收藏夹商品个数 / 4
    if int(列数) < 列数:
        列数 += 1

    获取截图(device[1], device[0])
    img = LoadImage(device[0], path)

    for col in range(int(列数)):
        if col >= 1:
                本地商品索引[1] += 190
                本地商品索引[3] += 190
                本地商品索引[0] -= 245 * 3
                本地商品索引[2] -= 245 * 3
        
        if col == 2:
            start_pointX = randint(550, 700)
            start_pointY = randint(550, 600)
            system(f"adb -s {device[1]} shell input swipe {start_pointX} {start_pointY} {start_pointX} {start_pointY - 400}")
            time.sleep(2)
            获取截图(device[1], device[0])
            time.sleep(1)
            img = LoadImage(device[0], path)
            本地商品索引 = two_index.copy()

        for cow in range(4):
            if 本地收藏夹商品个数 <= 0:
                break
            if cow >= 1:
                本地商品索引[0] += 245
                本地商品索引[2] += 245
            crop_img = crop(*本地商品索引, img)
            res = cnocr.ocr(crop_img)
            crop_img.close()

            商品列表[res[0]["text"]] = 本地商品索引.copy()
            本地收藏夹商品个数 -= 1
    img.close()

    return 商品列表


def 设置配置文件(data):
    config_file = f"{path}/shop.config"

    with open(config_file, 'w', encoding='utf-8') as f1:
        f1.write(str(data))


def 读取配置文件():
    config_file = f"{path}/shop.config"

    if not Path.exists(config_file): return False

    with open(config_file, 'r', encoding='utf-8') as f1:
        return f1.read()


def 添加日志(data):
    log_file = f"{path}/shop.log"

    with open(log_file, 'a', encoding='utf-8') as f1:
        f1.write(f'{datetime.datetime.now()} ------ {str(data)}\n')


def 购物():
    向下滑屏幕()
    time.sleep(2)
    商品位置列表 = 商品列表.copy()

    for 商品名字, 商品位置 in 商品位置列表.items():
        if list(商品位置列表.keys())[8] == 商品名字:
            向上滑屏幕()
            time.sleep(2)

        system(f"adb -s {device[1]} shell input tap {商品位置[2] - randint(10, 170)} {商品位置[3]}")
        time.sleep(2)
        获取截图(device[1], device[0])
        time.sleep(1)
        img = LoadImage(device[0], path)
        crop_img = crop(996, 312, 1157, 367, img)
        res = cnocr.ocr(crop_img)

        if res == [] or '购买' != res[0]["text"]:
            # 关闭
            print(商品名字, "：没有卖单")
            system(f"adb -s {device[1]} shell input tap {1134 + randint(2, 16)} {78 + randint(2, 18)}")
            continue

        crop_img = crop(755, 302, 982, 378, img)
        res = cnocr.ocr(crop_img)
        钱 = list(res[0]["text"])
        del 钱[-2:len(钱)]
        print(商品名字, ": ", (("".join(钱)).replace(",", "").replace('.', '') + ".0"))

        # 关闭
        system(f"adb -s {device[1]} shell input tap {1134 + randint(2, 16)} {78 + randint(2, 18)}")


if __name__ == "__main__":
    # 获取截图(device, device)
    # exit()

    print(pyfiglet.figlet_format("Sugobet\n"))

    _new_conf = {}

    # 商品列表与配置文件进行比对
    本地商品列表 = 获取收藏夹商品()
    # 如果配置文件不存在则创建
    配置文件内容 = 读取配置文件()
    if 配置文件内容 == False:
        for 本地商品 in 本地商品列表.keys():
            _new_conf[本地商品] = ['价格', 0]
        设置配置文件(_new_conf)
        print(f'请设置好配置文件再运行脚本\n配置文件所在路径: {path}/shop.config')
        exit()

    配置文件商品列表 = literal_eval(配置文件内容)
    # 如果本地商品列表没有，配置文件有，则为减
    state = False
    删除名单 = []
    for 配置文件商品 in 配置文件商品列表.keys():
        if 配置文件商品 not in 本地商品列表.keys():
            删除名单.append(配置文件商品)
            state = True
            添加日志(f"商品减少: {配置文件商品}")
    for val in 删除名单:
        if 删除名单 is not []: del 配置文件商品列表[val]

    if state:
        设置配置文件(配置文件商品列表)
        配置文件内容 = 读取配置文件()
        配置文件商品列表 = literal_eval(配置文件内容)

    # 如果本地商品列表有，配置文件没有，则为增
    state = False
    for 本地商品 in 本地商品列表.keys():
        if 本地商品 not in 配置文件商品列表.keys():
            配置文件商品列表[本地商品] = ['价格', 0]
            state = True
            添加日志(f"商品增加: {本地商品}")
    if state:
        设置配置文件(配置文件商品列表)
        print(f'检测到商品数量增加\n请设置好配置文件再运行脚本\n配置文件所在路径: {path}/shop.config')
        exit()

    购物()
