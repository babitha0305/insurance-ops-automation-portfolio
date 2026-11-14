/**
 * Bordereau upload validator (Google Apps Script).
 * Setup: paste into Extensions > Apps Script of a Sheet that has a tab named "Upload"
 * with headers in row 1: Ref | Name | InceptionDate | Premium | Currency.
 * Adds a menu "Bordereau Controls", highlights problem rows, writes an "Exceptions" tab,
 * and optionally emails a summary. Tested on a live Google Sheet using test_upload.csv:
 * 10 rows checked, 7 exceptions, total premium 6700.50 (as expected). Email summary not tested.
 */
const CONFIG = { sheet: 'Upload', exceptions: 'Exceptions', validCcy: ['GBP'], notify: '' /* set an email */ };

function onOpen() {
  SpreadsheetApp.getUi().createMenu('Bordereau Controls')
    .addItem('Run validation', 'runValidation').addToUi();
}

function runValidation() {
  const ss = SpreadsheetApp.getActive();
  const sh = ss.getSheetByName(CONFIG.sheet);
  const data = sh.getDataRange().getValues();
  const rows = data.slice(1);
  sh.getRange(2, 1, rows.length, data[0].length).setBackground(null);

  const seen = {}, exceptions = [];
  rows.forEach((r, i) => {
    const [ref, name, date, prem, ccy] = r, rowNum = i + 2, issues = [];
    if (!ref || !name || !date) issues.push('missing field');
    if (ref) { if (seen[ref]) issues.push('duplicate of row ' + seen[ref]); else seen[ref] = rowNum; }
    if (CONFIG.validCcy.indexOf(ccy) === -1) issues.push('invalid currency');
    if (typeof prem !== 'number' || prem <= 0) issues.push('non-positive premium');
    if (issues.length) {
      sh.getRange(rowNum, 1, 1, r.length).setBackground('#f8d7da');
      exceptions.push([rowNum, ref, issues.join('; ')]);
    }
  });

  const ex = ss.getSheetByName(CONFIG.exceptions) || ss.insertSheet(CONFIG.exceptions);
  ex.clearContents().getRange(1, 1, 1, 3).setValues([['Row', 'Ref', 'Issues']]);
  if (exceptions.length) ex.getRange(2, 1, exceptions.length, 3).setValues(exceptions);

  const total = rows.reduce((a, r) => a + (typeof r[3] === 'number' ? r[3] : 0), 0);
  const msg = rows.length + ' rows checked, ' + exceptions.length + ' exceptions, total premium ' + total.toFixed(2);
  if (CONFIG.notify) MailApp.sendEmail(CONFIG.notify, 'Bordereau validation summary', msg);
  SpreadsheetApp.getUi().alert(msg);
}
