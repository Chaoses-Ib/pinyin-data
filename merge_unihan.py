# -*- coding: utf-8 -*-
import collections
import re

def code_to_hanzi(code):
    hanzi = chr(int(code.replace('U+', '0x'), 16))
    return hanzi


def sort_pinyin_dict(pinyin_dict):
    dic = collections.OrderedDict(
        sorted(pinyin_dict.items(),
               key=lambda item: int(item[0].replace('U+', '0x'), 16))
    )
    for item in dic.items():  # pinyin_combinations 要求
        item[1][:] = sorted(item[1])
    return dic


def remove_dup_items(lst):
    new_lst = []
    for item in lst:
        if item not in new_lst:
            new_lst.append(item)
    return new_lst


def parse_pinyins(fp):
    pinyin_map = {}
    for line in fp:
        line = line.strip()
        if line.startswith('#') or not line:
            continue
        code, pinyin = line.split('#')[0].split(':')
        pinyin = ','.join([x.strip() for x in pinyin.split() if x.strip()])
        pinyin_map[code.strip()] = pinyin.split(',')
    return pinyin_map


def merge(raw_pinyin_map, adjust_pinyin_map, overwrite_pinyin_map):
    new_pinyin_map = {}
    for code, pinyins in raw_pinyin_map.items():
        if code in overwrite_pinyin_map:
            pinyins = overwrite_pinyin_map[code]
        elif code in adjust_pinyin_map:
            pinyins = adjust_pinyin_map[code] + pinyins
        new_pinyin_map[code] = remove_dup_items(pinyins)

    return new_pinyin_map


def save_data(pinyin_map, writer):
    for code, pinyins in pinyin_map.items():
        hanzi = code_to_hanzi(code)
        line = '{code}: {pinyin}  # {hanzi}\n'.format(
            code=code, pinyin=','.join(pinyins), hanzi=hanzi
        )
        writer.write(line)

def pinyin_to_ascii(pinyin):
    py = re.sub('[āáǎà]', 'a', pinyin)
    py = re.sub('[ēéěèếề]|ê̄|ê̌', 'e', py)  # ê̄=ê+̄ , ê̌=ê+̌ 
    py = re.sub('[īíǐì]', 'i', py)
    py = re.sub('[ōóǒò]', 'o', py)
    py = re.sub('[ūúǔù]', 'u', py)
    py = re.sub('[üǘǚǜ]', 'v', py)
    py = re.sub('[ńňǹ]', 'n', py)
    py = re.sub('[ḿ]', 'm', py)
    return py

def pinyin_to_ascii_num(pinyin):
    py = pinyin_to_ascii(pinyin)
    if re.search('[āēīōū]|ê̄', pinyin):  # ü
        return py + '1'
    if re.search('[áéếíóúǘḿń]', pinyin):
        return py + '2'
    if re.search('[ǎěǐǒǔǚň]|ê̌', pinyin):
        return py + '3'
    if re.search('[àèềìòùǜǹ]', pinyin):
        return py + '4'
    return py + '5'  # 0不好输入

# 小鹤双拼
def pinyin_to_double_pinyin_xiaohe(pinyin):
    ascii = pinyin_to_ascii(pinyin)
    if ascii == 'hng':  # 哼
        ascii = 'heng'

    if ascii[0] == 'z' or ascii[0] == 'c' or ascii[0] == 's':
        py = ascii[0]
        ascii = ascii[1:]
        if ascii[0] == 'h':
            sheng = { 'z': 'v', 'c': 'i', 's': 'u' }
            py = sheng[py]
            ascii = ascii[1:]
    else:
        py = ascii[0]
        ascii = ascii[1:]

    if len(ascii) == 0:
        py += py
    elif len(ascii) == 1:
        py += ascii
    else:
        if ascii == 'ng':  # ang, eng
            ascii = py + ascii
        yun = {
            'iu': 'q', 'ei': 'w', 'uan': 'r', 'ue': 't', 've': 't', 'un': 'y', 'uo': 'o', 'ie': 'p',
            'ong': 's', 'iong': 's', 'ai': 'd', 'en': 'f', 'eng': 'g', 'ang': 'h', 'an': 'j', 'uai': 'k', 'ing': 'k', 'uang': 'l', 'iang': 'l',
            'ou': 'z', 'ua': 'x', 'ia': 'x', 'ao': 'c', 'ui': 'v', 'in': 'b', 'iao': 'n', 'ian': 'm'
            }
        py += yun[ascii]

    return py

def save_data2(pinyin_map):
    all_pinyins = set()
    pinyin_combinations = set()
    for pinyins in pinyin_map.values():
        for pinyin in pinyins:
            all_pinyins.add(pinyin)
        pinyin_combinations.add(' '.join(pinyins))
    all_pinyins = sorted(all_pinyins, key=lambda x: (pinyin_to_ascii_num(x), x))
    pinyin_combinations = sorted(pinyin_combinations, key=lambda x: (x.count(' '), x))

    pinyin_multi_combination_map = {}
    for pinyins in pinyin_map.values():
        if len(pinyins) > 1:
            pinyin_multi_combination_map[' '.join(pinyins)] = sorted([ all_pinyins.index(pinyin) for pinyin in pinyins ])
    pinyin_multi_combinations = sorted(pinyin_multi_combination_map.values())
    for key, val in pinyin_multi_combination_map.items():
        pinyin_multi_combination_map[key] = pinyin_multi_combinations.index(val)

    # pinyin_compact.txt
    tables = {
        # 粗略匹配有拼音的汉字：
        # [〇-礼][𠀀-𰻞]
        # [〇㐀-鿭-礼][𠀀-𭀖灰𰻝𰻞]
        range(0x3400, 0x9FED+1): [],  # .{1017}\0
        range(0x20000, 0x2D016+1): [],
        range(0x3007, 0x3007+1): [],
        range(0xE815, 0xE864+1): [],  # .{18472}\0
        range(0xFA18, 0xFA18+1): [],  # .{4532}\0
        range(0x2F835, 0x2F835+1): [],  # .{10271}\0
        range(0x30EDD, 0x30EDE+1): []  # .{5800}\0
    }
    for rng, lst in tables.items():
        lst[:] = [0xFFFF] * (rng.stop - rng.start)
    for code, pinyins in pinyin_map.items():
        hanzi = int(code.replace('U+', '0x'), 16)
        for rng, lst in tables.items():
            if hanzi in rng:
                if len(pinyins) == 1:
                    lst[hanzi - rng.start] = all_pinyins.index(pinyins[0])
                else:
                    lst[hanzi - rng.start] = len(all_pinyins) + pinyin_multi_combination_map[' '.join(pinyins)]

    with open('pinyin_compact.txt', 'w', encoding='utf8') as f:
        f.write(f'''pinyins:
{ chr(10).join(','.join((pinyin, pinyin_to_ascii(pinyin), pinyin_to_ascii_num(pinyin), pinyin_to_double_pinyin_xiaohe(pinyin))) for pinyin in all_pinyins) }

pinyin_combinations:
{ chr(10).join(','.join(str(v) for v in combinations) for combinations in pinyin_multi_combinations) }

pinyin_tables:
{ chr(10).join(f'0x{ rng.start :X}, 0x{ rng.stop - 1 :X}:{ chr(10) }{ ",".join(str(v) for v in lst) }' for rng, lst in tables.items()) }''')


    # all_pinyin.md
    with open('all_pinyins.md', 'w', encoding='utf8') as f:
        f.write(f'''## All Pinyins
{ len(all_pinyins) }
```
{ ' '.join(sorted(all_pinyins)) }
```

## All Pinyin Combinations
{ len(pinyin_combinations) - len(pinyin_multi_combinations) } + { len(pinyin_multi_combinations) } = { len(pinyin_combinations) }
```
{ chr(10).join(pinyin_combinations) }
```''')


def extend_pinyins(old_map, new_map, only_no_exists=False):
    for code, pinyins in new_map.items():
        if only_no_exists:   # 只当 code 不存在时才更新
            if code not in old_map:
                old_map[code] = pinyins
        else:
            old_map.setdefault(code, []).extend(pinyins)


if __name__ == '__main__':
    raw_pinyin_map = {}
    '''
    with open('kHanyuPinyin.txt', encoding='utf8') as fp:
        khanyupinyin = parse_pinyins(fp)
        raw_pinyin_map.update(khanyupinyin)
    with open('kXHC1983.txt', encoding='utf8') as fp:
        kxhc1983 = parse_pinyins(fp)
        extend_pinyins(raw_pinyin_map, kxhc1983)
    '''
    with open('kXHC1983.txt', encoding='utf8') as fp:
        kxhc1983 = parse_pinyins(fp)
        raw_pinyin_map.update(kxhc1983)
    with open('nonCJKUI.txt', encoding='utf8') as fp:
        noncjkui = parse_pinyins(fp)
        extend_pinyins(raw_pinyin_map, noncjkui)
    with open('kMandarin_8105.txt', encoding='utf8') as fp:
        adjust_pinyin_map = parse_pinyins(fp)
        extend_pinyins(raw_pinyin_map, adjust_pinyin_map)
    with open('kMandarin_overwrite.txt', encoding='utf8') as fp:
        _map = parse_pinyins(fp)
        extend_pinyins(adjust_pinyin_map, _map)
        extend_pinyins(raw_pinyin_map, adjust_pinyin_map)
    with open('kMandarin.txt', encoding='utf8') as fp:
        _map = parse_pinyins(fp)
        extend_pinyins(adjust_pinyin_map, _map)
        extend_pinyins(raw_pinyin_map, adjust_pinyin_map)
    with open('kTGHZ2013.txt', encoding='utf8') as fp:
        _map = parse_pinyins(fp)
        extend_pinyins(adjust_pinyin_map, _map)
        extend_pinyins(raw_pinyin_map, adjust_pinyin_map)
    with open('kHanyuPinlu.txt', encoding='utf8') as fp:
        khanyupinyinlu = parse_pinyins(fp)
        extend_pinyins(adjust_pinyin_map, _map)
        extend_pinyins(raw_pinyin_map, adjust_pinyin_map)
    with open('GBK_PUA.txt', encoding='utf8') as fp:
        pua_pinyin_map = parse_pinyins(fp)
        extend_pinyins(raw_pinyin_map, pua_pinyin_map)
    with open('kanji.txt', encoding='utf8') as fp:
        _map = parse_pinyins(fp)
        extend_pinyins(raw_pinyin_map, _map, only_no_exists=True)

    with open('overwrite.txt', encoding='utf8') as fp:
        overwrite_pinyin_map = parse_pinyins(fp)
        extend_pinyins(raw_pinyin_map, overwrite_pinyin_map)

    new_pinyin_map = merge(raw_pinyin_map, adjust_pinyin_map,
                           overwrite_pinyin_map)
    new_pinyin_map = sort_pinyin_dict(new_pinyin_map)

    assert len(new_pinyin_map) == len(raw_pinyin_map)
    code_set = set(new_pinyin_map.keys())
    #assert set(khanyupinyin.keys()) - code_set == set()
    assert set(khanyupinyinlu.keys()) - code_set == set()
    assert set(kxhc1983.keys()) - code_set == set()
    assert set(adjust_pinyin_map.keys()) - code_set == set()
    assert set(overwrite_pinyin_map.keys()) - code_set == set()
    assert set(pua_pinyin_map.keys()) - code_set == set()
    with open('pinyin.txt', 'w', encoding='utf8') as fp:
        fp.write('# version: 0.11.0\n')
        fp.write('# source: https://github.com/mozillazg/pinyin-data\n')
        save_data(new_pinyin_map, fp)
    save_data2(new_pinyin_map)