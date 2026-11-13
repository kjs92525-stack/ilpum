"""일용직 원장 변환. 실행 결과에는 개인정보가 있으므로 저장소에 추가하지 마세요.

python tools/convert_daily_workbook.py 원본.xlsx /tmp/daily-workbook.json
원본에 쓰인 범위만 변환하며 중간 빈 행·추가 열·셀 색·줄바꿈을 보존합니다.
"""
import datetime
import json
import re
import sys

import openpyxl
from openpyxl.styles.colors import COLOR_INDEX


def color(c):
    if c is None:
        return None
    if c.type == 'rgb' and isinstance(c.rgb, str):
        return '#' + c.rgb[-6:]
    if c.type == 'indexed' and c.indexed < len(COLOR_INDEX):
        return '#' + COLOR_INDEX[c.indexed][-6:]
    return None


def display(c):
    v = c.value
    if v is None:
        return ''
    if isinstance(v, (datetime.datetime, datetime.date)):
        if c.number_format == 'm/d':
            return f'{v.month}/{v.day}'
        return v.isoformat(sep=' ') if isinstance(v, datetime.datetime) else v.isoformat()
    if isinstance(v, (float, int)) and not isinstance(v, bool):
        if c.number_format == '#,##0':
            return f'{v:,.0f}'
        if c.number_format == '#,##0.00':
            return f'{v:,.2f}'
        if c.number_format == '###,####,####':
            s = str(int(v))
            return ','.join(filter(None, [s[:-8], s[-8:-4], s[-4:]]))
        return str(int(v)) if int(v) == v else str(v)
    return str(v)


def convert(path):
    book = openpyxl.load_workbook(path)
    result = {}
    for sheet in book:
        used = [c for row in sheet for c in row if c.value is not None]
        if not used:
            continue
        nr, nc = max(c.row for c in used), max(c.column for c in used)
        rows, styles = [], {}
        for r in range(nr):
            row = []
            for c in range(nc):
                cell = sheet.cell(r + 1, c + 1)
                row.append(display(cell))
                style = {}
                bg = color(cell.fill.fgColor) if cell.fill.patternType == 'solid' else None
                fg = color(cell.font.color)
                if bg and bg != '#FFFFFF':
                    style['bg'] = bg
                if fg and fg != '#000000':
                    style['fg'] = fg
                if cell.font.bold:
                    style['bold'] = True
                if cell.alignment.horizontal in ('left', 'center', 'right'):
                    style['align'] = cell.alignment.horizontal
                if style:
                    styles[f'{r},{c}'] = style
            rows.append(row)
        widths = [max(84, min(360, round((sheet.column_dimensions[openpyxl.utils.get_column_letter(c + 1)].width or 13) * 7 + 5))) for c in range(nc)]
        month = int(re.search(r'\d+', sheet.title).group())
        result[f'daily:2026-{month:02d}'] = {'name': sheet.title, 'rows': rows, 'styles': styles, 'widths': widths}
    return result


if __name__ == '__main__':
    with open(sys.argv[2], 'w', encoding='utf-8') as out:
        json.dump(convert(sys.argv[1]), out, ensure_ascii=False, separators=(',', ':'))
