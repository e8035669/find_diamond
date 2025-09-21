from typing import Optional
import json
from dataclasses import dataclass

from sssekai.crypto.APIManager import decrypt, SEKAI_APIMANAGER_KEYSETS
import msgpack


def decrypt_data(data: bytes):
    plain = decrypt(data, SEKAI_APIMANAGER_KEYSETS['jp'])
    msg = msgpack.unpackb(plain)
    return msg


RESOURCE_NAMES = {
    '1': '想いの木材',
    '2': 'おもたい木材',
    '3': 'かるい木材',
    '4': 'ベタベタの樹液',
    '5': '夕桐',
    '6': '想いの石ころ',
    '7': '銅',
    '8': '鉄',
    '9': '粘土',
    '10': 'きれいなガラス',
    '11': 'きらきクォーツ',
    '12': 'ダイヤモンド',
    '13': 'ねじ',
    '14': '釘',
    '15': 'プラスチック',
    '16': 'モーター',
    '17': '電池',
    '18': 'ライト',
    '19': '電子基板',
    '20': '四葉のクローバー',
    '21': 'さらさリネン',
    '22': 'ふわふわコットン',
    '23': '花びら',
    '24': 'まっさらな音色',
    '32': 'あおぞらシーグラス',
    '33': '月光石',
    '34': '流れ星のかけら',
    '35': 'スカイブルーメモリア',
    '36': 'パッシンイエローメモリア',
    '37': 'ポピーレッドメモリア',
    '38': 'イエローグリーンメモリア',
    '39': 'アプリコットメモリア',
    '40': 'ストリクトブルーメモリア',
    '41': 'ラブリーピンクメモリア',
    '42': 'オパールグリーンメモリア',
    '43': 'スリーズメモリア',
    '44': 'ターコイズブルーメモリア',
    '45': 'ジョリーコーラルメモリア',
    '46': 'ロイヤルブルーメモリア',
    '47': 'サンフラワーメモリア',
    '48': 'ポカポカピンクメモリア',
    '49': 'スプリンググリーンメモリア',
    '50': 'カンパヌラパープルメモリア',
    '51': 'ファリダメモリア',
    '52': 'ウィスタリアメモリア',
    '53': 'キャメルメモリア',
    '54': 'ッスルメモリア',
    '55': 'ブルーグリーンメモリア',
    '56': 'オレンジメモリア',
    '57': 'イエローメモリア',
    '58': 'ピンクメモリア',
    '59': 'レッドメモリア',
    '60': 'ブルーメモリア',
    '61': '雪の結',
    '62': '最高のオノの刃',
    '63': '最高のツルハシの先端',
    '64': '雷光石',
    '65': '彩虹のビードロ',
    '66': 'ふわもこわたぐも',
}

PLACE_NAME = {
    "1": "マイホーム",
    "2": "1F",
    "3": "2F",
    "4": "3F",
    "5": "さいしょの原っぱ",
    "6": "願いの砂浜",
    "7": "彩りの花畑",
    "8": "忘れ去られた場所",
}


def get_resource_name(rid: int):
    return RESOURCE_NAMES.get(str(rid), f'Resource {rid}')


def get_place_name(pid: int):
    return PLACE_NAME.get(str(pid), f'Place {pid}')


@dataclass
class DiamondPlace:
    site_id: int
    drop: dict


def find_diamond(decrypted_data: dict,
                 resource_id: int = 12) -> Optional[list[DiamondPlace]]:
    root = decrypted_data
    if 'updatedResources' in root:
        root = root['updatedResources']

    if 'userMysekaiHarvestMaps' in root:
        harvest_maps = root['userMysekaiHarvestMaps']
        ret = []
        for harvest_map in harvest_maps:
            site_id = harvest_map['mysekaiSiteId']
            resource_drops = harvest_map['userMysekaiSiteHarvestResourceDrops']
            find_drop = [
                drop for drop in resource_drops
                if drop['resourceId'] == resource_id
            ]
            for drop in find_drop:
                ret.append(DiamondPlace(site_id, drop))
        return ret
    return None


def get_remain_harvest_count(decrypted_data: dict):
    root = decrypted_data
    if 'updatedResources' in root:
        root = root['updatedResources']

    if 'userMysekaiHarvestMaps' in root:
        harvest_maps = root['userMysekaiHarvestMaps']
        ret = []
        for harvest_map in harvest_maps:
            site_id = harvest_map['mysekaiSiteId']
            resource_drops = harvest_map['userMysekaiSiteHarvestResourceDrops']
            info = {'site_id': site_id, 'drop_count': len(resource_drops)}
            ret.append(info)
        return ret
    return None


def test():
    with open('temp6.bin', 'rb') as f:
        data = f.read()
    decrypted_data = decrypt_data(data)
    ret = find_diamond(decrypted_data, 11)
    if ret:
        print('Find diamond')
        for d in ret:
            print(d)
    else:
        print('Diamond not found')


if __name__ == "__main__":
    test()
