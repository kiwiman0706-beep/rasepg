/**
 * ハードウェアエンコード (Raspberry Pi 4 / V4L2 M2M h264_v4l2m2m)
 *   - 1080i を bwdif でソフトデインターレース → 720p へ縮小 → HW H.264
 *   - 宅外視聴向けの軽量 MP4 (約 2Mbps / AAC 128k)
 * EPGStation から INPUT/OUTPUT が環境変数で渡されます。
 */
const spawn = require('child_process').spawn;
const path = require('path');

const input = process.env.INPUT;
const output = process.env.OUTPUT;
const ffmpeg = process.env.FFMPEG || 'ffmpeg';

const VIDEO_BITRATE = process.env.RASEPG_VBITRATE || '2000k';
const AUDIO_BITRATE = process.env.RASEPG_ABITRATE || '128k';
const HEIGHT = process.env.RASEPG_HEIGHT || '720';

const args = [
  '-y',
  '-fflags', '+discardcorrupt',
  '-analyzeduration', '10M', '-probesize', '32M',
  '-i', input,
  // 1080i → デインターレース(bwdif) → 720p 縮小
  '-vf', `bwdif=mode=0,scale=-2:${HEIGHT}`,
  '-c:v', 'h264_v4l2m2m',
  '-b:v', VIDEO_BITRATE,
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
