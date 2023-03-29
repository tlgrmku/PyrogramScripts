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
userconfigpath = '/root/bot/'
saves = '/root/bot/save.json'
admins = []


def check_uid(uid, data):
    with open(saves, 'r') as rf:
        users = json.load(rf)
        if users.get(str(uid)):
            return False
        else:
            users[uid] = data
    with open(saves, 'w') as wf:
        json.dump(users, wf, indent=4)
    return True

def deluser(uid):
    with open(saves, 'r') as rf:
        users = json.load(rf)
        if users.get(uid):
            conf = userconfigpath + users.get(uid) + '.conf'
            if os.path.isfile(conf):
                subprocess.call(f'rm {conf}', shell=True)
            del users[uid]
    with open(saves, 'w') as wf:
        json.dump(users, wf, indent=4)

def readfile(pathfile) -> list:
    with open(pathfile, 'r') as f:
        data = f.readlines()
    return data

def writefile(pathfile, data):
    with open(pathfile, 'a') as f:
        f.write(data)

def check_client(client_name) -> bool:
    good = ascii_letters + digits
    if all(map(lambda c: c in good, client_name)):
        for i in readfile(wgfile):
            data = re.findall(r'### Client \D*', i)
            if data != []:
                if client_name == data[0].split()[-1]:
                    return False
        return True
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

def get_data_params(key_value) -> str:
    #SERVER_PUB_IP SERVER_PORT CLIENT_DNS_1 CLIENT_DNS_2 SERVER_PUB_KEY
    for i in readfile(paramsfile):
        data = re.split(r'=', i, maxsplit=1)
        if data[0] == key_value:
            return data[1].strip()

async def gen_config(msg):
    name = msg.text[:15]
    if check_client(name):
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
    else:
        await app.send_message(msg.from_user.id, 'Выберите другое имя. Можно использовать до 15 букв \
латинского алфавита[a-z A-Z] или цифр[0-9]. \
Скачайте vpn-клиент тут: https://www.wireguard.com/install/')


app = Client('Userbot')


@app.on_message(filters.user(admins) & filters.command(commands='del', prefixes='/') & filters.private)
async def delfunc(_, msg):
    deluser(msg.command[-1])


@app.on_message(filters.command(commands='vpn', prefixes='/') & filters.private)
async def vpn(_, msg):
    print(msg.from_user.id, msg.from_user.username, msg.from_user.first_name, msg.text)
    await app.send_message(msg.from_user.id, 'Напишите любое имя конфига. Можно использовать до 15 букв \
латинского алфавита[a-z A-Z] или цифр[0-9]. \
Скачайте vpn-клиент тут: https://www.wireguard.com/install/')


@app.on_message(filters.text & filters.private)
async def first_msg(_, msg):
    print(msg.from_user.id, msg.from_user.username, msg.from_user.first_name, msg.text)
    if check_uid(msg.from_user.id, msg.text):
        await gen_config(msg)
    else:
        await app.send_message(msg.from_user.id, f'{msg.from_user.first_name}. Кажется вы уже получали конфиг.')


app.run()

