from pyrogram import Client, filters
import re
import subprocess
from string import ascii_letters, digits
import json
import os.path

#Example save.json
#{
#    "id": "name_config"
#}

wgfile = '/etc/wireguard/wg0.conf'
paramsfile = '/etc/wireguard/params'
userconfigpath = '/root/vpnbot/'
saves = '/root/vpnbot/save.json'
admins = [] #id админа бота



def addjson(uid: str, name: str):
    with open(saves, 'r') as rf:
        users = json.load(rf)
        users[uid] = name
    with open(saves, 'w') as wf:
        json.dump(users, wf, indent=4)

def deluser(uid: str):
    wg_nic = get_data_params('SERVER_WG_NIC')
    with open(saves, 'r') as rf:
        users = json.load(rf)
        if users.get(uid):
            lines = readfile(wgfile)
            for i, line in enumerate(lines):
                if users.get(uid) in line:
                    del lines[i:i + 6]
            with open(wgfile, 'w') as wgf:
                wgf.writelines(lines)
            conf = userconfigpath + users.get(uid) + '.conf'
            if os.path.isfile(conf):
                subprocess.call(f'rm {conf}', shell=True)
            del users[uid]
    with open(saves, 'w') as wf:
        json.dump(users, wf, indent=4)
    subprocess.run(f"bash -c 'wg syncconf {wg_nic} <(wg-quick strip {wg_nic})'", shell=True)

def readfile(pathfile: str) -> list:
    with open(pathfile, 'r') as f:
        data = f.readlines()
    return data

def writefile(pathfile: str, data: str):
    with open(pathfile, 'a') as f:
        f.write(data)

def check_client(client_name: str) -> bool:
    good = ascii_letters + digits
    if all(map(lambda c: c in good, client_name)):
        for i in readfile(wgfile):
            data = re.findall(r'### Client \D*', i)
            if data != []:
                if client_name == data[0].split()[-1]:
                    return False
        return True
    return False

def check_uid(uid: int) -> bool:
    with open(saves, 'r') as rf:
        users = json.load(rf)
        if users.get(str(uid)):
            return True
        else:
            return False

def get_local_ip() -> str:
    maxnum = 0
    for i in readfile(wgfile):
        data = re.search(r'10.66.66.\d{1,3}', i)
        if data != None:
            num = int(data.group()[9:])
            if num < 250:
                if maxnum < num:
                    maxnum = num
            else:
                print('Превышено количество ip адрессов')
    return str(maxnum + 1)

def genkeys() -> tuple:
    privatkey = subprocess.run('wg genkey', shell=True, capture_output=True).stdout.decode().strip('\n')
    pubkey = subprocess.run(f'echo {privatkey} | wg pubkey', shell=True, capture_output=True).stdout.decode().strip('\n')
    presharedkey = subprocess.run('wg genpsk', shell=True, capture_output=True).stdout.decode().strip('\n')
    return privatkey, pubkey, presharedkey

def get_data_params(key_value: str) -> str:
    #SERVER_PUB_IP SERVER_PORT CLIENT_DNS_1 CLIENT_DNS_2 SERVER_PUB_KEY
    for i in readfile(paramsfile):
        data = re.split(r'=', i, maxsplit=1)
        if data[0] == key_value:
            return data[1].strip()

async def gen_config(msg):
    name = msg.text[:15]
    addjson(msg.from_user.id, name)
    path_config = userconfigpath + name + '.conf'
    privatkey, pubkey, presharedkey = genkeys()
    num_ip = get_local_ip()
    server_pubkey = get_data_params('SERVER_PUB_KEY')
    server_ip = get_data_params('SERVER_PUB_IP')
    server_port = get_data_params('SERVER_PORT')
    dns1 = get_data_params('CLIENT_DNS_1')
    dns2 = get_data_params('CLIENT_DNS_2')
    wg_nic = get_data_params('SERVER_WG_NIC')
    text = f'[Interface]\n\
PrivateKey = {privatkey}\n\
Address = 10.66.66.{num_ip}/32, fd42:42:42::{num_ip}/128\n\
DNS = {dns1}, {dns2}\n\n[Peer]\n\
PublicKey = {server_pubkey}\n\
PresharedKey = {presharedkey}\n\
AllowedIPs = 0.0.0.0/0, ::/0\n\
Endpoint = {server_ip}:{server_port}\n'
    text_wg = f'\n### Client {name}\n[Peer]\n\
PublicKey = {pubkey}\n\
PresharedKey = {presharedkey}\n\
AllowedIPs = 10.66.66.{num_ip}/32,fd42:42:42::{num_ip}/128\n'
    writefile(path_config, text)
    writefile(wgfile, text_wg)
    res = subprocess.run(f"bash -c 'wg syncconf {wg_nic} <(wg-quick strip {wg_nic})'", shell=True)
    print(res)
    await app.send_document(msg.from_user.id,
        document=path_config,
        caption=f'{msg.from_user.first_name}. Ваш конфиг готов. Сохраните его. В wireguard \
нажмите на + и выберите сохранённый файл конфигурации.')


api_id = 12345
api_hash = "0123456789abcdef0123456789abcdef"
bot_token = "123456:ABC-DEF1234ghIkl-zyx57W2v1u123ew11"

app = Client('client', api_id=api_id, api_hash=api_hash, bot_token=bot_token)
#app = Client('client')


@app.on_message(filters.command(commands='id', prefixes='/') & filters.private)
async def uidfunc(_, msg):
    print(msg.from_user.id, msg.from_user.username, msg.from_user.first_name, msg.text)
    await app.send_message(msg.from_user.id, f'Ваш id в Telegram: {msg.from_user.id}')


@app.on_message(filters.user(admins) & filters.command(commands='help', prefixes='/') & filters.private)
async def helpfunc(_, msg):
    print(msg.from_user.id, msg.from_user.username, msg.from_user.first_name, msg.text)
    await app.send_message(msg.from_user.id, '/vpn - создание конфига. /id - мой id. /del id - удаление юзера.')


@app.on_message(filters.user(admins) & filters.command(commands='del', prefixes='/') & filters.private)
async def delfunc(_, msg):
    print(msg.from_user.id, msg.from_user.username, msg.from_user.first_name, msg.text)
    if msg.command[-1] == 'del':
        await app.send_message(msg.from_user.id, 'Подсказка: /del id - удалить юзера.')
    else:
        deluser(msg.command[-1])
        await app.send_message(msg.from_user.id, 'Конфиг удалён.')


@app.on_message(filters.command(commands=['vpn', 'start'], prefixes='/') & filters.private)
async def vpn(_, msg):
    print(msg.from_user.id, msg.from_user.username, msg.from_user.first_name, msg.text)
    await app.send_message(msg.from_user.id, 'Напишите любое имя конфига. Можно использовать до 15 букв \
латинского алфавита[a-z A-Z] или цифр[0-9]. \
Скачайте vpn-клиент тут: https://www.wireguard.com/install/')


@app.on_message(filters.text & filters.private)
async def first_msg(_, msg):
    print(msg.from_user.id, msg.from_user.username, msg.from_user.first_name, msg.text)
    if check_uid(msg.from_user.id):
        await app.send_message(msg.from_user.id, f'{msg.from_user.first_name}. Кажется вы уже получали конфиг.')
    else:
        if check_client(msg.text[:15]):
            await gen_config(msg)
        else:
            await app.send_message(msg.from_user.id, 'Выберите другое имя. Можно использовать до 15 букв \
латинского алфавита[a-z A-Z] или цифр[0-9]. \
Скачайте vpn-клиент тут: https://www.wireguard.com/install/')

app.run()
