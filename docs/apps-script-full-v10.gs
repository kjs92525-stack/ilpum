// ═══════════════════════════════════════════════════════════════════
//  일품집 예약 관리 + 직원 스케줄 — Google Apps Script 백엔드  v10
//
//  ▶ 변경 후: 배포 → 기존 배포 관리 → 새 버전으로 수정 (URL 유지)
//
//  ★ v8 → v9 변경점 (중요) ★
//   - onEdit 이 이제 "탭 이름"을 먼저 확인합니다.
//     · 9.1(화) 같은 예약 탭  → 기존 v8 동작 그대로
//     · 스케줄표 탭           → 근무 구분 자동 확장만 실행 (정렬 안 함)
//     · 그 외 탭(직원 등)     → 아무것도 하지 않음
//   - v8 은 "모든 탭"에서 C열 기준 자동정렬이 돌았습니다.
//     스케줄표가 같은 스프레드시트에 있으면 날짜 블록이 뒤섞입니다.
//     v9 에서 이 부분이 차단됩니다.
//
//  doGet API (v8 과 100% 동일 — 프론트엔드 수정 불필요)
//  ?action=tabs               → 탭 목록
//  ?action=read&date=...      → 예약 읽기
//  ?action=add&date=...&n=... → 예약 추가
//  ?action=delete&date=...    → 단건 삭제
//  ?action=clearDate&date=... → 전체 삭제
//  ?action=schedule[&key=...] → 스케줄표 탭 A~L 읽기 (v10 추가, 급여 집계기용)
// ═══════════════════════════════════════════════════════════════════


// ── 설정 ───────────────────────────────────────────────────────────
var RESV_TAB_RE  = /^\d{1,2}\.\d{1,2}/;   // "9.1(화)" 형태 = 예약 탭
var SCHEDULE_TAB = '스케줄표';             // 스케줄 탭 이름 (다르면 여기만 수정)

// 스케줄표 근무 구분 약어 → 전체 표기
var SHIFT_MAP = {
  '종': '종일',   '종일': '종일',
  '오': '오후',   '오후': '오후',
  '전': '오전',   '오전': '오전',
  '휴': '휴무',   '휴무': '휴무',
  '배': '배송',   '배송': '배송',
  '알': '당일알바', '알바': '당일알바',
  '달': '달서지원', '달서': '달서지원'
};


// ════════════════════════════════════════════════════════════════════
//  onEdit — 탭별로 분기 (v9 핵심)
// ════════════════════════════════════════════════════════════════════
function onEdit(e) {
  if (!e || !e.range) return;

  var name = e.range.getSheet().getName();

  if (RESV_TAB_RE.test(name)) {      // 예약 탭
    onEditReservation(e);
    return;
  }
  if (name === SCHEDULE_TAB) {       // 스케줄표 탭
    onEditSchedule(e);
    return;
  }
  // 직원 탭 등 나머지는 건드리지 않음
}


// ── 예약 탭 전용 (v8 원본 로직 그대로) ──────────────────────────────
function onEditReservation(e) {
  var range = e.range;
  var sheet = range.getSheet();
  var col   = range.getColumn();
  var row   = range.getRow();
  var value = e.value;
  var a1    = range.getA1Notation();

  if (!value || row <= 1) return;

  // 1. 시간 자동 변환 (C열 또는 H2 셀)
  if ((col == 3 && row >= 2) || (a1 == 'H2')) {
    if (!isNaN(value) && value.toString().length >= 1 && value.toString().length <= 4) {
      var strValue = value.toString();
      var hours, minutes;
      if (strValue.length <= 2) {
        hours = strValue; minutes = '00';
      } else {
        hours   = strValue.substring(0, strValue.length - 2);
        minutes = strValue.substring(strValue.length - 2);
      }
      range.setValue(hours + ':' + minutes);
    }
  }

  // 2. 연락처 하이픈 자동 삽입 (F열)
  if (col == 6) {
    var str = value.toString().replace(/-/g, '');
    if (str.length === 10 || str.length === 11) {
      if (str.indexOf('10') === 0) str = '0' + str;
      range.setValue(str.replace(/(\d{3})(\d{3,4})(\d{4})/, '$1-$2-$3'));
    }
  }

  // 3. 테이블번호 자동 확장 (B열)
  if (col == 2 && row >= 2) {
    var expanded = formatTableStr(value);
    if (expanded && expanded !== String(value)) {
      range.setValue(expanded);
    }
  }

  // 4. 자동 정렬 + 가운데 정렬  ← 이제 예약 탭에서만 실행됨
  if (a1 != 'H2') {
    var lastRow = sheet.getLastRow();
    var lastCol = sheet.getLastColumn();
    if (lastRow > 1) {
      var sortRange = sheet.getRange(2, 1, lastRow - 1, lastCol);
      sortRange.sort({ column: 3, ascending: true });
      sortRange.setHorizontalAlignment('center');
      sortRange.setVerticalAlignment('middle');
    }
  }
}


// ── 스케줄표 탭 전용 ────────────────────────────────────────────────
//  C~J열(근무자 슬롯)에서 "이름/약어" 입력 시 자동 확장
//   예)  여재동/종  →  여재동(종일)
//        지수/오    →  지수(오후)
//        상옥/전    →  상옥(오전)
//        박은정/알  →  박은정(당일알바)
//  ※ 정렬·행삭제는 절대 하지 않습니다 (블록 구조 보존)
function onEditSchedule(e) {
  var range = e.range;
  var col   = range.getColumn();
  var row   = range.getRow();
  var value = e.value;

  if (!value || row < 2) return;
  if (col < 3 || col > 10) return;   // C~J 슬롯만 대상

  var expanded = expandShift(value);
  if (expanded && expanded !== String(value)) {
    range.setValue(expanded);
  }
  range.setHorizontalAlignment('center').setVerticalAlignment('middle');
}


// ── 유틸: 근무 약어 확장 ────────────────────────────────────────────
function expandShift(val) {
  var str = String(val).trim();
  var m = str.match(/^(.+?)\s*\/\s*(\S+)$/);
  if (!m) return str;

  var name = m[1].trim();
  var full = SHIFT_MAP[m[2].trim()];
  if (!full) return str;

  return name + '(' + full + ')';
}


// ── 유틸: 시간 값 → "H:MM" 변환 ────────────────────────────────────
function normalizeTime(val) {
  if (val === null || val === undefined || val === '') return '';
  if (val instanceof Date) {
    try { return Utilities.formatDate(val, 'Asia/Seoul', 'H:mm'); } catch(e) {}
    var kstMs = val.getTime() + 9 * 60 * 60 * 1000;
    var kd    = new Date(kstMs);
    return kd.getUTCHours() + ':' + String(kd.getUTCMinutes()).padStart(2, '0');
  }
  var str = String(val).trim();
  if (/^\d{1,2}:\d{2}/.test(str)) return str.split(':').slice(0, 2).join(':');
  var num = parseFloat(str);
  if (!isNaN(num) && num >= 0 && num < 1) {
    var tm = Math.round(num * 1440);
    return Math.floor(tm / 60) + ':' + String(tm % 60).padStart(2, '0');
  }
  return str;
}


// ── 유틸: 테이블번호 — R1~R4 자동 확장 및 숫자면 T 접미사 ────────────────
function formatTableStr(tableStr) {
  if (!tableStr) return '';
  var ROOM_FULL = {
    'R1': ['R1-1', 'R1-2'],
    'R2': ['R2-1', 'R2-2'],
    'R3': ['R3-1', 'R3-2'],
    'R4': ['R4-1', 'R4-2', 'R4-3', 'R4-4']
  };

  var tokens = String(tableStr).split(/[,，]/).map(function(s) {
    return s.trim().replace(/T$/i, '').trim();
  }).filter(Boolean);

  var res = [];
  for (var i = 0; i < tokens.length; i++) {
    var tok = tokens[i];

    if (/^[1-4]$/.test(tok) && res.length > 0 && /^R4-[1-4]$/.test(res[res.length - 1])) {
      res.push('R4-' + tok);
      continue;
    }

    var up = tok.toUpperCase();

    if (ROOM_FULL[up]) {
      res = res.concat(ROOM_FULL[up]);
      continue;
    }

    var m = up.match(/^R4[-]?([1-4](?:[,\-]?[1-4])*)$/);
    if (m) {
      var digits = m[1].match(/[1-4]/g);
      if (digits) {
        for (var k = 0; k < digits.length; k++) {
          res.push('R4-' + digits[k]);
        }
        continue;
      }
    }

    if (/^\d+$/.test(tok)) {
      res.push(tok + 'T');
      continue;
    }

    res.push(up);
  }

  var finalRes = [];
  for (var idx = 0; idx < res.length; idx++) {
    if (finalRes.indexOf(res[idx]) === -1) {
      finalRes.push(res[idx]);
    }
  }

  return finalRes.join(', ');
}


// ── 유틸: 연락처 하이픈 포맷 ────────────────────────────────────────
function formatPhone(raw) {
  var str = String(raw || '').replace(/-/g, '').trim();
  if (str.length === 10 || str.length === 11) {
    return str.replace(/(\d{3})(\d{3,4})(\d{4})/, '$1-$2-$3');
  }
  return str;
}


// ── 유틸: 날짜 → 탭 검색 ───────────────────────────────────────────
//  ★ v9.1 수정: 기존에는 indexOf(prefix)===0 으로 앞글자만 비교해서
//    "10.1" 이 "10.10", "10.11" 에도 걸렸습니다. (탭 순서가 바뀌면 오탐)
//    이제 숫자 뒤에 "(" 가 오는지까지 확인해 정확히 한 탭만 찾습니다.
function findSheetByDate(ss, dateStr) {
  if (!dateStr) return null;
  var parts = dateStr.split('-');
  if (parts.length < 3) return null;

  var m = parseInt(parts[1], 10);
  var d = parseInt(parts[2], 10);
  if (isNaN(m) || isNaN(d)) return null;

  var sheets = ss.getSheets();
  for (var i = 0; i < sheets.length; i++) {
    var nm = sheets[i].getName();
    var mt = nm.match(/^(\d{1,2})\.(\d{1,2})(?!\d)/);   // 숫자 뒤에 숫자가 더 오면 불일치
    if (!mt) continue;
    if (parseInt(mt[1], 10) === m && parseInt(mt[2], 10) === d) return sheets[i];
  }
  return null;
}


// ── 유틸: 탭 목록 ──────────────────────────────────────────────────
function getAvailableSheets(ss) {
  var sheets = ss.getSheets();
  var result = [];
  var year   = new Date().getFullYear();
  for (var i = 0; i < sheets.length; i++) {
    var name  = sheets[i].getName();
    var match = name.match(/^(\d{1,2})\.(\d{1,2})/);
    if (match) {
      var m = parseInt(match[1]), d = parseInt(match[2]);
      result.push({
        date:    year + '-' + String(m).padStart(2,'0') + '-' + String(d).padStart(2,'0'),
        tabName: name
      });
    }
  }
  result.sort(function(a, b){ return a.date.localeCompare(b.date); });
  return result;
}


// ── 유틸: 빈 행 제거 + 시간순 정렬 (예약 탭 전용) ─────────────────────
function cleanSheet(sheet) {
  var lastRow = sheet.getLastRow();
  if (lastRow <= 1) return;
  for (var i = lastRow; i >= 2; i--) {
    if (!sheet.getRange(i, 1).getValue()) sheet.deleteRow(i);
  }
  var newLast = sheet.getLastRow();
  if (newLast > 1) {
    sheet.getRange(2, 1, newLast - 1, sheet.getLastColumn())
         .sort({ column: 3, ascending: true });
  }
}


// ════════════════════════════════════════════════════════════════════
//  doGet — 모든 요청 처리 (v8 과 동일, 수정 없음)
// ════════════════════════════════════════════════════════════════════
function doGet(e) {
  try {
    var ss     = SpreadsheetApp.getActiveSpreadsheet();
    var action = e.parameter.action || '';
    var date   = e.parameter.date   || '';

    if (action === 'schedule') {          // v10 추가: 근무·급여 집계기용 스케줄표 읽기
      return scheduleJson_(e.parameter);
    }

    if (action === 'tabs') {
      return ok({ tabs: getAvailableSheets(ss) });
    }

    if (action === 'read' || (!action && date)) {
      if (!date) return err('date 없음');
      var sheet = findSheetByDate(ss, date);
      if (!sheet) return ok({ data: [], tabName: null });

      var data   = sheet.getDataRange().getValues();
      var result = [];
      for (var i = 1; i < data.length; i++) {
        var row = data[i];
        if (!row[0] || String(row[0]).trim() === '') continue;
        result.push({
          rowNum: i + 1,
          n:      String(row[0]).trim(),
          t:      String(row[1] || '').trim().split(',')
                    .map(function(s){ return s.trim(); }).filter(Boolean),
          time:   normalizeTime(row[2]),
          g:      String(row[3] || '').trim(),
          note:   String(row[4] || '').trim(),
          phone:  String(row[5] || '').trim(),
        });
      }
      return ok({ data: result, tabName: sheet.getName() });
    }

    if (action === 'add') {
      if (!date) return err('date 없음');
      var addSheet = findSheetByDate(ss, date);
      if (!addSheet) return err('탭 없음: ' + date + ' — 시트에 탭을 먼저 만들어주세요');

      var n      = e.parameter.n     || '';
      var tables = e.parameter.t     || '';
      var time   = e.parameter.time  || '';
      var g      = e.parameter.g     || '';
      var note   = e.parameter.note  || '';
      var phone  = e.parameter.phone || '';

      if (!n || !tables || !time) return err('필수 항목 누락');

      addSheet.appendRow([
        n,
        formatTableStr(tables),
        time,
        g,
        note,
        formatPhone(phone),
      ]);
      cleanSheet(addSheet);
      return ok({ action: 'added' });
    }

    if (action === 'delete') {
      if (!date) return err('date 없음');
      var delSheet = findSheetByDate(ss, date);
      if (!delSheet) return err('탭 없음');
      var rowNum = parseInt(e.parameter.rowNum || '0');
      if (rowNum >= 2) delSheet.deleteRow(rowNum);
      cleanSheet(delSheet);
      return ok({ action: 'deleted' });
    }

    if (action === 'clearDate') {
      if (!date) return err('date 없음');
      var clrSheet = findSheetByDate(ss, date);
      if (!clrSheet) return ok({ action: 'cleared' });
      for (var j = clrSheet.getLastRow(); j >= 2; j--) clrSheet.deleteRow(j);
      return ok({ action: 'cleared' });
    }

    return err('알 수 없는 action: ' + action);

  } catch(ex) {
    return err(ex.message);
  }
}


// ── doPost 미사용 ───────────────────────────────────────────────────
function doPost(e) {
  return err('doPost 미사용');
}


// ── 응답 헬퍼 ───────────────────────────────────────────────────────
function ok(data) {
  return ContentService
    .createTextOutput(JSON.stringify(Object.assign({ ok: true }, data)))
    .setMimeType(ContentService.MimeType.JSON);
}
function err(msg) {
  return ContentService
    .createTextOutput(JSON.stringify({ ok: false, error: msg }))
    .setMimeType(ContentService.MimeType.JSON);
}


// ════════════════════════════════════════════════════════════════════
//  v10 추가 — 스케줄표 읽기 (시트 내용은 바꾸지 않음)
//  선택: 프로젝트 설정 → 스크립트 속성에 SCHEDULE_KEY 를 정하면 같은 키를 넣은 사람만 읽음
// ════════════════════════════════════════════════════════════════════
// 스케줄표 탭 A열~L열을 화면에 보이는 그대로 돌려줍니다. 시트 내용은 바꾸지 않습니다.
function scheduleJson_(p) {
  var out = function (o) {
    return ContentService.createTextOutput(JSON.stringify(o)).setMimeType(ContentService.MimeType.JSON);
  };
  var need = PropertiesService.getScriptProperties().getProperty('SCHEDULE_KEY');
  if (need && (p.key || '') !== need) return out({ ok: false, error: '접근 키가 달라요' });
  var ss = SpreadsheetApp.getActiveSpreadsheet();
  var sh = ss.getSheetByName('스케줄표');
  if (!sh) {
    var all = ss.getSheets();
    for (var i = 0; i < all.length; i++) {
      if (all[i].getName().replace(/\s/g, '').indexOf('스케줄표') === 0) { sh = all[i]; break; }
    }
  }
  if (!sh) return out({ ok: false, error: '"스케줄표" 탭을 찾지 못했어요' });
  var rows = sh.getLastRow();
  if (rows < 1) return out({ ok: true, values: [] });
  var values = sh.getRange(1, 1, rows, 12).getDisplayValues();   // A~L
  return out({ ok: true, values: values });
}
