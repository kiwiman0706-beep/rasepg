/**
 * リマックス (TS → MP4, 再エンコード無し) — 既定・推奨
 *   - 映像/音声をそのままコピー。CPU 負荷ほぼゼロで一瞬で完了。
 *   - 原画質を維持したまま MP4 コンテナ化(faststart 付き)して NAS に保存。
 *   - Pi4 を焼かずに全番組を残す用途に最適。持ち出し用の軽量化は HW/SW profile を別途指定。
 * 注: 地デジ TS は MPEG-2 映像 + AAC 音声。MP4 に copy で格納する(VLC / DS Video で再生可)。
 */
const spawn = require('child_process').spawn;

const input = process.env.INPUT;
const output = process.env.OUTPUT;
const ffmpeg = process.env.FFMPEG || 'ffmpeg';

const args = [
  '-y',
  '-fflags', '+discardcorrupt',
  '-analyzeduration', '10M', '-probesize', '32M',
  '-i', input,
  '-map', '0:v:0',      // 映像1本
  '-map', '0:a',        // 音声全て
  '-c:v', 'copy',
  '-c:a', 'copy',
  '-bsf:a', 'aac_adtstoasc',   // ADTS(TS) → ASC(MP4) へ音声ヘッダ変換
  '-sn',                // 字幕/データストリームは除外(MP4非対応のため)
  '-movflags', '+faststart',
  '-f', 'mp4',
  output,
];

const child = spawn(ffmpeg, args);
child.stderr.on('data', (d) => process.stderr.write(d));
child.on('exit', (code) => process.exit(code));
process.on('SIGINT', () => child.kill('SIGINT'));
