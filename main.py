# -*- coding: UTF-8 -*-

import requests
import re
import random
import socket
import struct
import time
import os
import urllib.parse

def login(account, password):
    PHONE_PATTERN = r"(^(1)\d{10}$)"
    if re.match(PHONE_PATTERN, account):
        account = f"+86{account}"
        third_name = "huami_phone"
    else:
        third_name = "huami"

    headers = {
        "content-type": "application/x-www-form-urlencoded; charset=UTF-8",
        "user-agent": "MiFit/6.12.0 (MCE16; Android 16; Density/1.5)",
        "app_name": "com.xiaomi.hm.health",
    }
    url1 = "https://api-user.huami.com/registrations/" + account + "/tokens"
    data1 = f"client_id=HuaMi&country_code=CN&json_response=true&name={account}&password={password}&redirect_uri=https://s3-us-west-2.amazonaws.com/hm-registration/successsignin.html&state=REDIRECTION&token=access"
    res1 = requests.post(url1, data=data1, headers=headers)

    if res1.status_code == 200:   # 检查状态码是否为200,是则请求成功
        r1sc = res1.status_code
        res1 = res1.json()
        if "access" in res1:   # 检查登录是否成功
            print(f"信息:登录成功,Access Code={r1sc}")
            code = res1["access"]
        else:
            print(f"错误:用户名或密码不正确,Access Code={r1sc}")
            return None, None
    elif res1.status_code == 429:   # 检查状态码是否为429,是则请求过于频繁
        print(f"错误:请求过于频繁,请稍后再试,Access Code={res1.status_code}")
        return None, None
    else:
        print(f"错误:登录失败,Access Code={res1.status_code}")
        return None, None

    url2 = "https://account.huami.com/v2/client/login"
    data2 = f"app_name=com.xiaomi.hm.health&country_code=CN&code={code}&device_id=00:00:00:00:00:00&device_model=android_phone&app_version=6.12.0&grant_type=access_token&allow_registration=false&source=com.xiaomi.hm.health&third_name={third_name}"
    res2 = requests.post(url2, data=data2, headers=headers)
   
    if res2.status_code == 200:   # 检查状态码是否为200,是则请求成功
        r2sc = res2.status_code
        res2 = res2.json()
        login_token = res2["token_info"]["login_token"]
        user_id = res2["token_info"]["user_id"]
        print(f"信息:登录成功,Login Code={r2sc},User ID={user_id}")
        return login_token, user_id
    else:
        print(f"错误:登录失败,Login Code={res2.status_code}")
        return None, None

def get_app_token(login_token):   # 获取 app_token
    headers = {
        "content-type": "application/x-www-form-urlencoded; charset=UTF-8",
        "user-agent": "MiFit/6.12.0 (MCE16; Android 16; Density/1.5)",
        "app_name": "com.xiaomi.hm.health",
    }
    url = f"https://account-cn.huami.com/v1/client/app_tokens?login_token={login_token}"
    res = requests.get(url, headers=headers)

    if res.status_code == 200:
        res_data = res.json()
        if "token_info" in res_data:
            print(f"信息:成功获取到 app_token ,Code={res.status_code}")
            return res_data["token_info"]["app_token"]
        else:
            print("错误:无法解析出有效的 app_token ,Code={res.status_code}")
            return None
    else:
        print(f"错误:无法获取到有效的 app_token ,Code={res.status_code}")
        return None

def change_steps(account, user_id, app_token, steps):
    # 修改步数
    sec_timestamp = get_sec_timestamp()
    if sec_timestamp is None:
        sec_timestamp = int(time.time())
        print(f"警告:NTP 时间获取失败,使用系统时间{sec_timestamp}")
    
    dateToday = time.strftime("%F")
    deviceID = "0000000000000000"
    
    dataJSON = "%5b%7b%22data_hr%22%3a%22" + "%5c%2fv7%2b"*480 + f"%22%2c%22date%22%3a%22{dateToday}%22%2c%22data%22%3a%5b%7b%22start%22%3a0%2c%22stop%22%3a1439%2c%22value%22%3a%22" + "A"*5760 + f"%22%2c%22tz%22%3a32%2c%22did%22%3a%22{deviceID}%22%2c%22src%22%3a24%7d%5d%2c%22summary%22%3a%22%7b%5c%22v%5c%22%3a6%2c%5c%22slp%5c%22%3a%7b%5c%22st%5c%22%3a0%2c%5c%22ed%5c%22%3a0%2c%5c%22dp%5c%22%3a0%2c%5c%22lt%5c%22%3a0%2c%5c%22wk%5c%22%3a0%2c%5c%22usrSt%5c%22%3a-1440%2c%5c%22usrEd%5c%22%3a-1440%2c%5c%22wc%5c%22%3a0%2c%5c%22is%5c%22%3a0%2c%5c%22lb%5c%22%3a0%2c%5c%22to%5c%22%3a0%2c%5c%22dt%5c%22%3a0%2c%5c%22rhr%5c%22%3a0%2c%5c%22ss%5c%22%3a0%7d%2c%5c%22stp%5c%22%3a%7b%5c%22ttl%5c%22%3a{steps}%2c%5c%22dis%5c%22%3a0%2c%5c%22cal%5c%22%3a0%2c%5c%22wk%5c%22%3a0%2c%5c%22rn%5c%22%3a0%2c%5c%22runDist%5c%22%3a0%2c%5c%22runCal%5c%22%3a0%2c%5c%22stage%5c%22%3a%5b%5d%7d%2c%5c%22goal%5c%22%3a0%2c%5c%22tz%5c%22%3a%5c%2228800%5c%22%7d%22%2c%22source%22%3a24%2c%22type%22%3a0%7d%5d"
    #dataJSON = URL_encode_dataJSON(dateToday, deviceID, steps)
    #print(f"信息:dataJSON={dataJSON}")
    
    headers0 = {
        "content-type": "application/x-www-form-urlencoded; charset=UTF-8",
        "user-agent": "MiFit/6.12.0 (MCE16; Android 16; Density/1.5)",
        "app_name": "com.xiaomi.hm.health",
        "apptoken": app_token,
    }
    url0 = f"https://api-mifit-cn.huami.com/v1/data/band_data.json?&t={sec_timestamp}"
    data0 = f"userid={user_id}&last_sync_data_time={sec_timestamp}&device_type=0&last_deviceid={deviceID}&data_json={dataJSON}"
    
    try:
        res0 = requests.post(url0, data=data0, headers=headers0)
        res0_data = res0.json()
        print(f"信息:账号:{account};步数={steps};返回结果={res0_data}")
        if res0_data.get('message') == 'success':
            return True
        else:
            return False
    except Exception as e:
        print(f"错误:提交步数失败:{e}")
        return False

def get_sec_timestamp():
    # 通过 NTP 服务器获取秒级时间戳
    try:
        NTP_SERVER = 'ntp.ntsc.ac.cn'
        PORT = 123
        NTP_FORMAT = '!12I'
        NTP_DELTA = 2208988800
        
        client = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        client.settimeout(5)
        
        data = bytearray(48)
        data[0] = 0x1B
        
        client.sendto(data, (NTP_SERVER, PORT))
        data, address = client.recvfrom(1024)
        
        if data:
            unpacked = struct.unpack(NTP_FORMAT, data[:48])
            timestamp = unpacked[10] - NTP_DELTA
            print(f"信息:成功通过 NTP 服务器获取到秒级时间戳,SecTimeStamp={timestamp}")
            return int(timestamp)
        
        return None
        
    except socket.timeout:
        print("错误:连接 NTP 服务器超时")
        return None
    except socket.gaierror:
        print("错误:无法解析 NTP 服务器地址")
        return None
    except Exception as e:
        print(f"错误:获取时间戳失败 - {e}")
        return None
    finally:
        try:
            client.close()
        except:
            pass


def URL_encode_dataJSON(dateToday, deviceID, steps):
    JSON_Frame = f'[{{"date":"{dateToday}","data":[{{"start":0,"stop":1439,"did":"{deviceID}","src":24}}],"summary":"{{\\"stp\\":{{\\"ttl\\":{steps}}}}}","source":24,"type":0}}]'   # 待编码 JSON 模板
    Encoded_dataJSON = urllib.parse.quote(JSON_Frame, safe='')   # 对 JSON 进行 URL 编码
    return Encoded_dataJSON


# 主程序
if __name__ == "__main__":
    # 从环境变量安全地获取 GitHub Secret 中的账号与密码
    ACCOUNT = os.environ.get("ACCOUNT", "")
    PASSWORD = os.environ.get("PASSWORD", "")
    
    # 用户账号组配置:每个账号可以设置固定步数或使用随机范围
    # 配置格式: [账号, 密码, 步数设置]
        # 步数值选定:
        # - 固定值: 如 30000
        # - 随机范围: [最小值, 最大值] 如 [25000, 55000]
        # - None: 使用默认随机范围
    AccountGroup = [
        [ACCOUNT, PASSWORD, 55555],   # 使用默认随机步数
        #['账号2', '密码2', [20000, 40000]],  # 使用随机范围20000-40000
        #['账号3', '密码3', [30000, 50000]],  # 使用随机范围30000-50000
        #['账号4', '密码4', 50000],  # 使用定值步数50000
    ]
    
    # 默认随机范围（用于步数设置为None的情况）
    DefaultRandomMin = 35000
    DefaultRandomMax = 65000
    
    for i in AccountGroup:   # 遍历用户账号组中的每个账号信息并对每个用户账号执行步数刷取操作
        account = i[0]
        password = i[1]
        step_config = i[2]
        
        # 根据步数配置类型确定最终步数
        if step_config is None:
            # 使用默认随机范围
            step = random.randint(DefaultRandomMin, DefaultRandomMax)
            print(f"信息:账号:{account},本次步数类型:默认范围随机,本次随机范围:[{DefaultRandomMin}-{DefaultRandomMax}],本次最终步数:{step}")
        elif isinstance(step_config, list) and len(step_config) == 2:
            # 使用自定义随机范围
            random_min, random_max = step_config
            step = random.randint(random_min, random_max)
            print(f"信息:账号:{account},本次步数类型:自定义范围随机,本次随机范围:[{random_min}-{random_max}],本次最终步数:{step}")
        else:
            # 使用固定步数
            step = step_config
            print(f"信息:账号:{account},本次步数类型:定值,本次最终步数:{step}")
        
        # 登录获取token
        login_token, userid = login(account, password)
        if not login_token:
            print(f'错误:账号:{account},登录失败')
            continue
        else:
            print(f'信息:账号:{account},登录成功')
        
        # 获取app_token
        app_token = get_app_token(login_token)
        if not app_token:
            print(f'错误:账号:{account},获取 app_token 失败')
            continue
        else:
            print(f'信息:账号:{account},获取 app_token 成功')
        
        # 修改步数
        result = change_steps(account, userid, app_token, str(step))
        if result:
            print(f'信息:账号:{account} 步数修改成功')
        else:
            print(f'错误:账号:{account} 步数修改失败')
        
        print("-" * 50)
