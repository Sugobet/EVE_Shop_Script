from os import system, path as Path
import datetime
from PIL import Image
from cnocr import CnOcr
import threading
import time
from random import randint
from ast import literal_eval
import pyfiglet
from concurrent.futures import ThreadPoolExecutor
import asyncio

from nonebot import on_command
from nonebot.rule import to_me
from nonebot.matcher import Matcher
from nonebot.adapters.onebot.v11 import Bot, Message
from nonebot.params import Arg, CommandArg, ArgPlainText, Command
from nonebot.adapters.onebot.v11 import MessageSegment, Event
from nonebot.typing import T_State


loop = asyncio.get_event_loop()

_脚本运行状态 = 0


商品 = on_command("商品", priority=5)
脚本 = on_command("脚本", priority=5)

是否购买 = None
等待是否购买 = 0

@商品.handle()
async def _(bot: Bot, event: Event, state: T_State, matcher: Matcher):
    global 是否购买, 等待是否购买, 配置文件商品列表, 收藏夹商品个数

    raw_msg = event.message.extract_plain_text()
    msg_list = raw_msg.split(' ')
    if len(msg_list) == 1:
        await matcher.send("商品-命令菜单 --- 开发中")
        return

    if len(msg_list) == 2:
        if msg_list[1] == '不购买':
            if 等待是否购买:
                是否购买 = False
                await matcher.send('已放弃购买')
                return
            await matcher.send('当前没有商品需要确认是否购买')
            return
        
        if msg_list[1] == '购买':
            if 等待是否购买:
                是否购买 = True
                await matcher.send('已尝试购买')
                return
            await matcher.send('当前没有商品需要确认是否购买')
            return

    if len(msg_list) == 3:
        if msg_list[1] == '设置收藏夹商品个数':
            收藏夹商品个数 = int(msg_list[2])
            await matcher.send('设置成功')
            return

    # /商品 设置购买价格 魔女级 9999999
    if len(msg_list) == 4:
        if msg_list[1] == '设置购买价格':
            本地配置文件列表 = literal_eval(读取配置文件())
            if msg_list[2] not in 本地配置文件列表.keys():
                await matcher.send(f'设置失败；{msg_list[2]} 未在收藏夹内')
                return
            本地配置文件列表[msg_list[2]][0] = msg_list[3]
            设置配置文件(本地配置文件列表)
            配置文件商品列表[msg_list[2]][0] = 本地配置文件列表[msg_list[2]][0]
            await matcher.send(f'商品：{msg_list[2]}\n更新价格：{msg_list[3]}\n更改价格成功 （更改立即生效，无需重启脚本）')
            return

        if msg_list[1] == '设置提醒':
            本地配置文件列表 = literal_eval(读取配置文件())
            if msg_list[2] not in 本地配置文件列表.keys():
                await matcher.send(f'设置失败；{msg_list[2]} 未在收藏夹内')
                return
            if msg_list[3] == "提醒":
                本地配置文件列表[msg_list[2]][1] = True
            elif msg_list[3] == "不提醒":
                本地配置文件列表[msg_list[2]][1] = False
            设置配置文件(本地配置文件列表)
            配置文件商品列表[msg_list[2]][1] = 本地配置文件列表[msg_list[2]][1]
            await matcher.send(f'商品：{msg_list[2]}\n是否提醒：{msg_list[3]}\n设置成功 （更改立即生效，无需重启脚本）')
            return

        if msg_list[1] == '设置购买数量':
            本地配置文件列表 = literal_eval(读取配置文件())
            if msg_list[2] not in 本地配置文件列表.keys():
                await matcher.send(f'设置失败；{msg_list[2]} 未在收藏夹内')
                return
            本地配置文件列表[msg_list[2]][2] = msg_list[3]
            设置配置文件(本地配置文件列表)
            配置文件商品列表[msg_list[2]][2] = 本地配置文件列表[msg_list[2]][2]
            await matcher.send(f'商品：{msg_list[2]}\n更改购买数量：{msg_list[3]}\n设置成功 （更改立即生效，无需重启脚本）')
            return


@脚本.handle()
async def _(bot: Bot, event: Event, state: T_State, matcher: Matcher):
    global _脚本运行状态, 配置文件商品列表
    raw_msg = event.message.extract_plain_text()
    msg_list = raw_msg.split(' ')
    if len(msg_list) == 1:
        await matcher.send("脚本-命令菜单 --- 开发中")
        return
    if len(msg_list) == 2:
        if msg_list[1] == "启动":
            if _脚本运行状态:
                await matcher.send(f"脚本已经启动过了，请勿重复启动")
                return

            def run():
                global _脚本运行状态
                tasks = []
                tasks.append(启动(bot))
                loop.run_until_complete(asyncio.wait(tasks))
                _脚本运行状态 = 0

            t = threading.Thread(target=run)
            t.start()
            await matcher.send('脚本已成功启动！')
            return

        if msg_list[1] == "停止":
            if _脚本运行状态:
                _脚本运行状态 = 0
                await matcher.send(f"脚本已停止运行")
                return
            await matcher.send(f"停止失败，脚本并未启动")
            return

        if msg_list[1] == "查看日志":
            await matcher.send(读取日志())
            return

        if msg_list[1] == "清空日志":
            清空日志()
            await matcher.send("日志已清空")
            return

        if msg_list[1] == "查看配置":
            str1 = ""
            for 商品名字, 值 in 配置文件商品列表.items():
                str1 += f'商品名字：{商品名字}\n购买价格：{值[0]}\n购买数量：{值[2]}\n是否提醒：{"提醒" if 值[1] else "不提醒"}\n----------------'
            await matcher.send(str1)
            return

        if msg_list[1] == '脚本状态':
            if _脚本运行状态:
                await matcher.send('脚本运行状态: 正在运行')
                return
            await matcher.send('脚本运行状态: 已停止')
            return


收藏夹商品个数 = 6
模式 = 1

path = 'C:/Users/sugob/Desktop/shop'
device = ["bot1", '192.168.1.250:5667']

one_index = [286, 78, 527, 112]
two_index = [292, 243, 530, 271]
商品列表 = {}
配置文件商品列表 = None

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
        system(f'adb -s {device_address} exec-out screencap -p > {path}/{device_name}.png')


def crop(x1, y1, x2, y2, img: Image.Image) -> Image.Image:
    newimg = None
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
    global 商品列表
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

            new_str = ''
            if len(res) > 1:
                for s in range(len(res)):
                    new_str += res[s]["text"]
            else:
                new_str = res[0]["text"]
            商品列表[new_str] = 本地商品索引.copy()
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


def 清空日志():
    log_file = f"{path}/shop.log"

    with open(log_file, 'w', encoding='utf-8') as f1:
        f1.write('')


def 读取日志():
    log_file = f"{path}/shop.log"

    if not Path.exists(log_file): return False

    with open(log_file, 'r', encoding='utf-8') as f1:
        return f1.read()


def 购买数量(num):
    point = { # stepX 150  stepY 90
        "1": [827 + randint(10, 110), 326 + randint(10, 50)],
        "2": [977 + randint(10, 110), 326 + randint(10, 50)],
        "3": [1127 + randint(10, 110), 326 + randint(10, 50)],
        "4": [827 + randint(10, 110), 416 + randint(10, 50)],
        "5": [977 + randint(10, 110), 416 + randint(10, 50)],
        "6": [1127 + randint(10, 110), 416 + randint(10, 50)],
        "7": [827 + randint(10, 110), 506 + randint(10, 50)],
        "8": [977 + randint(10, 110), 506 + randint(10, 50)],
        "9": [1127 + randint(10, 110), 506 + randint(10, 50)],
        "0": [977 + randint(10, 110), 596 + randint(10, 50)]
    }

    num_list = list(str(num))
    ret = []
    for num in num_list:
        ret.append(point[num])

    return ret


async def 购物(bot: Bot):
    global 是否购买, 等待是否购买, _脚本运行状态

    向下滑屏幕()
    await asyncio.sleep(2)
    商品位置列表 = 商品列表.copy()
    global 配置文件商品列表
    本地配置文件商品列表 = 配置文件商品列表

    for 商品名字, 商品位置 in 商品位置列表.items():
        if not _脚本运行状态:
            return
        if len(商品位置列表) >= 9:
            if list(商品位置列表.keys())[8] == 商品名字:
                向上滑屏幕()
                await asyncio.sleep(2)

        system(f"adb -s {device[1]} shell input tap {商品位置[2] - randint(10, 170)} {商品位置[3]}")
        await asyncio.sleep(2)
        获取截图(device[1], device[0])
        await asyncio.sleep(1)
        img = LoadImage(device[0], path)
        crop_img = crop(996, 312, 1157, 367, img)
        res = cnocr.ocr(crop_img)

        if res == [] or '购买' != res[0]["text"]:
            # 关闭
            img.close()
            crop_img.close()
            system(f"adb -s {device[1]} shell input tap {1134 + randint(2, 16)} {78 + randint(2, 18)}")
            continue

        crop_img = crop(755, 302, 982, 378, img)
        res = cnocr.ocr(crop_img)
        钱 = list(res[0]["text"])
        del 钱[-2:len(钱)]

        价格 = int((("".join(钱)).replace(",", "").replace('.', '').replace('O', '0').replace('o', '0').replace('U', '0').replace('L', '0')))

        # 价格比对
        # 现获得的价格与配置文件的价格比对，前者小于等于后者则购买，
        # 如果设置了提醒，则通过QQ机器人提醒
        # 如果提醒之后，需要购买，通过输入命令更改配置文件，然后重载全局 配置文件商品列表 变量
        配置文件价格 = int(本地配置文件商品列表[商品名字][0])
        if 价格 > 配置文件价格:
            # 关闭
            img.close()
            crop_img.close()
            system(f"adb -s {device[1]} shell input tap {1134 + randint(2, 10)} {78 + randint(2, 10)}")
            continue

        配置文件购买数量 = int(本地配置文件商品列表[商品名字][2]) # 1-99999999999999区间

        if 本地配置文件商品列表[商品名字][1]:
            # QQ提醒 购买数量、自动买断、不买
            等待是否购买 = 1
            await bot.send_group_msg(group_id=341046164, message=f"低价格商品提醒：\n商品：{商品名字}\n单价：{价格}\n购买数量：{配置文件购买数量}\n如果要购买请回复：/商品 购买\n否则回复：/商品 不购买\n若三分钟内没有回复则自动放弃购买")
            count = 0
            while 等待是否购买:
                if 是否购买 != None:
                    if 是否购买:
                        等待是否购买 = 0
                        是否购买 = None
                        continue
                    else:
                        等待是否购买 = 0
                        continue
                if count >= 180:
                    等待是否购买 = 0
                    continue
                count += 1
                await asyncio.sleep(1)
            if 是否购买 == False:
                是否购买 = None
                img.close()
                crop_img.close()
                system(f"adb -s {device[1]} shell input tap {1134 + randint(2, 10)} {78 + randint(2, 10)}")
                continue

            if count >= 180:
                img.close()
                crop_img.close()
                system(f"adb -s {device[1]} shell input tap {1134 + randint(2, 10)} {78 + randint(2, 10)}")
                continue

        # 不提醒
        # 点击购买
        system(f"adb -s {device[1]} shell input tap {996 + randint(10, 160)} {312 + randint(10, 55)}")
        # 打开输入框
        system(f"adb -s {device[1]} shell input tap {415 + randint(10, 140)} {601 + randint(10, 30)}")
        # 获取余额
        await asyncio.sleep(2)
        获取截图(device[1], device[0])
        await asyncio.sleep(1)
        img = LoadImage(device[0], path)
        crop_img = crop(71, 642, 324, 698, img)
        res = cnocr.ocr(crop_img)
        余额_r = res[0]["text"]
        余额 = int((("".join(余额_r)).replace(",", "").replace('.', '').replace('O', '0').replace('o', '0').replace('U', '0').replace('L', '0')))
        if (配置文件购买数量 * 价格) > 余额:
            添加日志(f"购买 [{商品名字}]---数量:{配置文件购买数量}  失败：isk不足；当前余额{余额}；所需isk: {配置文件购买数量 * 价格}")

            img.close()
            crop_img.close()            
            system(f"adb -s {device[1]} shell input tap {200 + randint(2, 10)} {150 + randint(2, 10)}")
            await asyncio.sleep(1)
            system(f"adb -s {device[1]} shell input tap {200 + randint(2, 10)} {150 + randint(2, 10)}")
            await asyncio.sleep(1)
            system(f"adb -s {device[1]} shell input tap {1134 + randint(2, 10)} {78 + randint(2, 10)}")
            continue

        point_list = 购买数量(配置文件购买数量)
        for point in point_list:
            system(f"adb -s {device[1]} shell input tap {point[0]} {point[1]}")
            await asyncio.sleep(0.5)

        # 确认购买：
        system(f"adb -s {device[1]} shell input tap {1127 + randint(10, 110)} {596 + randint(10, 50)}")
        await asyncio.sleep(1)
        system(f"adb -s {device[1]} shell input tap {693 + randint(10, 140)} {597 + randint(10, 30)}")
        await asyncio.sleep(1)
        添加日志(f"购买 [{商品名字}]---数量:{配置文件购买数量}  成功；剩余余额{余额 - (配置文件购买数量 * 价格)}")

        # 关闭
        img.close()
        crop_img.close()
        system(f"adb -s {device[1]} shell input tap {1134 + randint(2, 10)} {78 + randint(2, 10)}")


async def 启动(bot: Bot):
    global _脚本运行状态, 配置文件商品列表
    if _脚本运行状态:
        return
    _脚本运行状态 = 1

    # await matcher.send(pyfiglet.figlet_format("Sugobet\n"))

    _new_conf = {}

    向下滑屏幕()
    await asyncio.sleep(2)

    # 商品列表与配置文件进行比对
    本地商品列表 = 获取收藏夹商品()
    # 如果配置文件不存在则创建
    配置文件内容 = 读取配置文件()
    if 配置文件内容 == False:
        await bot.send_group_msg(group_id=341046164, message=f'检测到配置文件不存在......')
        await bot.send_group_msg(group_id=341046164, message=f'正在创建配置文件......')
        for 本地商品 in 本地商品列表.keys():
            _new_conf[本地商品] = ['价格', False, '购买数量']
        设置配置文件(_new_conf)
        配置文件商品列表 = _new_conf
        await bot.send_group_msg(group_id=341046164, message=f'配置文件创建完成......')
        await bot.send_group_msg(group_id=341046164, message=f'请配置好配置文件再启动脚本\n请使用命令配置商品参数\n命令：/商品 设置购买价格 商品名字 价格\n命令：/商品 设置提醒 提醒/不提醒\n命令：/商品 设置购买数量 商品名字 购买数量')
        _脚本运行状态 = 0
        return

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
            配置文件商品列表[本地商品] = ['价格', False, '购买数量']
            state = True
            添加日志(f"商品增加: {本地商品}")
    if state:
        设置配置文件(配置文件商品列表)
        await bot.send_group_msg(group_id=341046164, message=f'检测到商品数量增加\n请使用命令配置商品参数\n命令：/商品 设置购买价格 商品名字 价格\n命令：/商品 设置提醒 提醒/不提醒\n命令：/商品 设置购买数量 商品名字 购买数量')
        _脚本运行状态 = 0
        return
    await bot.send_group_msg(group_id=341046164, message='脚本启动完成')

    while _脚本运行状态:
        await 购物(bot)
