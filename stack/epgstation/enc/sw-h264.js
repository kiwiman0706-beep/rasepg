/**
 * ソフトウェアエンコード (x264) — 画質優先
 *   - Pi4 では実時間より遅い(録画後キュー処理向け)。Pi5 なら実用的。
 *   - CRF ベースで見た目の画質を安定させる。
 */
const spawn = require('child_process').spawn;

const input = process.env.INPUT;
const output = process.env.OUTPUT;
const ffmpeg = process.env.FFMPEG || 'ffmpeg';

const CRF = process.env.RASEPG_CRF || '23';
const PRESET = process.env.RASEPG_PRESET || 'veryfast';
const HEIGHT = process.env.RASEPG_HEIGHT || '720';
const AUDIO_BITRATE = process.env.RASEPG_ABITRATE || '128k';

const args = [
  '-y',
  '-fflags', '+discardcorrupt',
  '-analyzeduration', '10M', '-probesize', '32M',
  '-i', input,
  '-vf', `bwdif=mode=0,scale=-2:${HEIGHT}`,
  '-c:v', 'libx264',
  '-preset', PRESET,
  '-crf', CRF,
  '-pix_fmt', 'yuv420p',
  '-c:a', 'aac',
  '-b:a', AUDIO_BITRATE,
  '-ac', '2',
  '-movflags', '+faststart',
  '-f', 'mp4',
  output,
];

const child = spawn(ffmpeg, args);
child.stderr.on('data', (d) => process.stderr.write(d));
child.on('exit', (code) => process.exit(code));
process.on('SIGINT', () => child.kill('SIGINT'));
