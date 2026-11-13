/**
 * 근무·급여 집계기용 — 구글 시트 Apps Script 에 "추가"하는 코드
 *
 * ⚠ 기존 onEdit(e) 함수와 다른 코드는 절대 지우지 마세요. 아래 두 함수를 "더하기만" 합니다.
 *
 * 1) 이미 doGet(e) 함수가 있으면: 새로 만들지 말고, 기존 doGet 맨 윗줄에 아래 3줄만 끼워 넣으세요.
 *      if (e && e.parameter && e.parameter.action === 'schedule') {
 *        return scheduleJson_(e.parameter);
 *      }
 * 2) doGet 이 없으면: 아래 doGet 을 그대로 붙여 넣으세요.
 * 3) scheduleJson_ 함수는 항상 새로 붙여 넣으세요.
 * 4) 배포 → 배포 관리 → 연필(수정) → 버전 "새 버전" → 배포. (웹앱 주소는 그대로 유지됩니다)
 *
 * 선택(권장): 프로젝트 설정 → 스크립트 속성에 SCHEDULE_KEY = (아무 긴 문자열) 을 추가하면,
 *             같은 값을 집계기 설정의 "접근 키"에 넣은 사람만 읽을 수 있습니다.
 */

// (기존 doGet 이 없을 때만 붙여 넣기)
function doGet(e) {
  if (e && e.parameter && e.parameter.action === 'schedule') {
    return scheduleJson_(e.parameter);
  }
  return ContentService.createTextOutput('ok');
}

// 스케줄표 탭 A열~L열을 화면에 보이는 그대로(getDisplayValues) 돌려줍니다. 시트 내용은 바꾸지 않습니다.
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
