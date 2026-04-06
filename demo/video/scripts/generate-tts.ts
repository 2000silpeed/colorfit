/**
 * ColorFit 데모 영상 TTS 생성 스크립트
 * Gemini TTS API로 나레이션 음성 파일을 생성한다.
 *
 * 실행: npx ts-node --project tsconfig.node.json scripts/generate-tts.ts
 */

import * as fs from "fs";
import * as path from "path";
import * as https from "https";
import { execSync } from "child_process";

const SPEED_FACTOR = 1.4;

const GEMINI_API_KEY = process.env.GEMINI_API_KEY;
if (!GEMINI_API_KEY) {
  console.error("GEMINI_API_KEY 환경변수가 없습니다.");
  process.exit(1);
}

const OUTPUT_DIR = path.resolve(__dirname, "../public/audio");
const SCRIPT_FILE = path.resolve(__dirname, "../data/narration-script.json");

interface TTSSegment {
  id: string;
  narration: string;
}

interface AudioSegmentResult {
  id: string;
  file: string;
  duration: number;
  start: number;
  end: number;
}

// PCM 24kHz 16bit mono -> WAV 변환
function pcmToWav(pcmBuffer: Buffer): Buffer {
  const sampleRate = 24000;
  const numChannels = 1;
  const bitsPerSample = 16;
  const byteRate = (sampleRate * numChannels * bitsPerSample) / 8;
  const blockAlign = (numChannels * bitsPerSample) / 8;
  const dataSize = pcmBuffer.length;
  const headerSize = 44;
  const wavBuffer = Buffer.alloc(headerSize + dataSize);

  // RIFF chunk
  wavBuffer.write("RIFF", 0);
  wavBuffer.writeUInt32LE(36 + dataSize, 4);
  wavBuffer.write("WAVE", 8);
  // fmt chunk
  wavBuffer.write("fmt ", 12);
  wavBuffer.writeUInt32LE(16, 16);
  wavBuffer.writeUInt16LE(1, 20); // PCM
  wavBuffer.writeUInt16LE(numChannels, 22);
  wavBuffer.writeUInt32LE(sampleRate, 24);
  wavBuffer.writeUInt32LE(byteRate, 28);
  wavBuffer.writeUInt16LE(blockAlign, 32);
  wavBuffer.writeUInt16LE(bitsPerSample, 34);
  // data chunk
  wavBuffer.write("data", 36);
  wavBuffer.writeUInt32LE(dataSize, 40);
  pcmBuffer.copy(wavBuffer, 44);

  return wavBuffer;
}

// WAV 파일의 재생 시간(초) 계산 — "data" 청크를 탐색
function getWavDuration(wavBuffer: Buffer): number {
  const sampleRate = wavBuffer.readUInt32LE(24);
  const numChannels = wavBuffer.readUInt16LE(22);
  const bitsPerSample = wavBuffer.readUInt16LE(34);

  // "data" 서브청크 위치를 탐색 (ffmpeg 출력은 44바이트 고정이 아닐 수 있음)
  let dataSize = 0;
  for (let i = 12; i < wavBuffer.length - 8; i++) {
    if (
      wavBuffer[i] === 0x64 && // 'd'
      wavBuffer[i + 1] === 0x61 && // 'a'
      wavBuffer[i + 2] === 0x74 && // 't'
      wavBuffer[i + 3] === 0x61 // 'a'
    ) {
      dataSize = wavBuffer.readUInt32LE(i + 4);
      break;
    }
  }

  return dataSize / ((sampleRate * numChannels * bitsPerSample) / 8);
}

// Gemini TTS API 호출
async function callGeminiTTS(text: string, voice: string = "Leda"): Promise<Buffer> {
  return new Promise((resolve, reject) => {
    const body = JSON.stringify({
      contents: [{ role: "user", parts: [{ text }] }],
      generationConfig: {
        responseModalities: ["AUDIO"],
        speechConfig: {
          voiceConfig: {
            prebuiltVoiceConfig: { voiceName: voice },
          },
        },
      },
    });

    const options = {
      hostname: "generativelanguage.googleapis.com",
      path: `/v1beta/models/gemini-2.5-flash-preview-tts:generateContent?key=${GEMINI_API_KEY}`,
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "Content-Length": Buffer.byteLength(body),
      },
    };

    const req = https.request(options, (res) => {
      const chunks: Buffer[] = [];
      res.on("data", (chunk) => chunks.push(chunk));
      res.on("end", () => {
        try {
          const responseText = Buffer.concat(chunks).toString();
          const json = JSON.parse(responseText);

          if (json.error) {
            reject(new Error(`Gemini API 오류: ${json.error.message}`));
            return;
          }

          const audioData =
            json?.candidates?.[0]?.content?.parts?.[0]?.inlineData?.data;
          if (!audioData) {
            reject(new Error("TTS 응답에 오디오 데이터가 없습니다."));
            return;
          }

          resolve(Buffer.from(audioData, "base64"));
        } catch (e) {
          reject(e);
        }
      });
    });

    req.on("error", reject);
    req.write(body);
    req.end();
  });
}

// ffmpeg atempo로 속도 변경 (피치 유지)
function applySpeedChange(inputPath: string, outputPath: string, speed: number): void {
  execSync(
    `ffmpeg -y -i "${inputPath}" -filter:a "atempo=${speed}" "${outputPath}"`,
    { stdio: "pipe" }
  );
}

// 단일 세그먼트 TTS 생성
async function generateSegmentTTS(
  segment: TTSSegment,
  outputPath: string,
  retries = 3
): Promise<number> {
  for (let attempt = 1; attempt <= retries; attempt++) {
    try {
      console.log(`  생성 중: ${segment.id} (시도 ${attempt}/${retries})`);
      const pcmBuffer = await callGeminiTTS(segment.narration, "Leda");
      const wavBuffer = pcmToWav(pcmBuffer);

      // 원본을 임시 파일에 저장 후 atempo 적용
      const tmpPath = outputPath.replace(".wav", "_raw.wav");
      fs.writeFileSync(tmpPath, wavBuffer);
      applySpeedChange(tmpPath, outputPath, SPEED_FACTOR);
      fs.unlinkSync(tmpPath);

      const finalBuf = fs.readFileSync(outputPath);
      const duration = getWavDuration(finalBuf);
      console.log(`  완료: ${segment.id} (${duration.toFixed(1)}초, ${SPEED_FACTOR}x)`);
      return duration;
    } catch (e) {
      console.error(`  실패 (${attempt}/${retries}): ${e}`);
      if (attempt === retries) throw e;
      const waitMs = attempt * 30000;
      console.log(`  ${waitMs / 1000}초 대기 후 재시도...`);
      await new Promise((r) => setTimeout(r, waitMs));
    }
  }
  throw new Error("최대 재시도 초과");
}

// 0.5초 무음 WAV 생성
function generateSilenceWav(durationSecs: number): Buffer {
  const sampleRate = 24000;
  const numSamples = Math.floor(sampleRate * durationSecs);
  const pcmBuffer = Buffer.alloc(numSamples * 2, 0); // 16bit = 2bytes per sample
  return pcmToWav(pcmBuffer);
}

// ffmpeg로 WAV 파일들을 concat (샘플레이트 자동 감지)
function concatWavFiles(wavPaths: string[], outputPath: string): number {
  const listFile = outputPath.replace(".wav", "_list.txt");
  const listContent = wavPaths.map((p) => `file '${p}'`).join("\n");
  fs.writeFileSync(listFile, listContent);

  execSync(
    `ffmpeg -y -f concat -safe 0 -i "${listFile}" -c copy "${outputPath}"`,
    { stdio: "pipe" }
  );
  fs.unlinkSync(listFile);

  const buf = fs.readFileSync(outputPath);
  return getWavDuration(buf);
}

async function main() {
  const script = JSON.parse(fs.readFileSync(SCRIPT_FILE, "utf-8"));

  // 모든 세그먼트를 순서대로 평탄화
  const segments: TTSSegment[] = [];

  // intro
  segments.push({ id: "intro", narration: script.intro.narration });

  // persona A
  segments.push({
    id: "persona_a_intro",
    narration: script.personaA.intro_narration,
  });
  for (const step of script.personaA.steps) {
    segments.push({ id: `a_${step.id}`, narration: step.narration });
  }

  // persona B
  segments.push({
    id: "persona_b_intro",
    narration: script.personaB.intro_narration,
  });
  for (const step of script.personaB.steps) {
    segments.push({ id: `b_${step.id}`, narration: step.narration });
  }

  // persona C
  segments.push({
    id: "persona_c_intro",
    narration: script.personaC.intro_narration,
  });
  for (const step of script.personaC.steps) {
    segments.push({ id: `c_${step.id}`, narration: step.narration });
  }

  // outro
  segments.push({ id: "outro", narration: script.outro.narration });

  console.log(`총 ${segments.length}개 세그먼트 TTS 생성 시작`);

  const segmentDir = path.join(OUTPUT_DIR, "segments");
  fs.mkdirSync(segmentDir, { recursive: true });

  const silenceFile = path.join(segmentDir, "_silence.wav");
  fs.writeFileSync(silenceFile, generateSilenceWav(0.4));

  const results: AudioSegmentResult[] = [];
  let cursor = 0;
  const SILENCE_DURATION = 0.4;

  for (let i = 0; i < segments.length; i++) {
    const seg = segments[i];
    const segFile = path.join(segmentDir, `${seg.id}.wav`);

    let duration: number;
    if (fs.existsSync(segFile)) {
      const buf = fs.readFileSync(segFile);
      duration = getWavDuration(buf);
      console.log(`  스킵 (이미 존재): ${seg.id} (${duration.toFixed(1)}초)`);
    } else {
      duration = await generateSegmentTTS(seg, segFile);
      // rate limit 방지: API 호출 간 7초 대기
      if (i < segments.length - 1) {
        await new Promise((r) => setTimeout(r, 7000));
      }
    }

    const start = cursor;
    const end = cursor + duration;
    results.push({ id: seg.id, file: segFile, duration, start, end });

    cursor = end + (i < segments.length - 1 ? SILENCE_DURATION : 0);
  }

  // 전체 오디오 합치기
  console.log("\n전체 오디오 합치는 중...");
  const wavPaths: string[] = [];
  for (let i = 0; i < results.length; i++) {
    wavPaths.push(results[i].file);
    if (i < results.length - 1) {
      wavPaths.push(silenceFile);
    }
  }

  const fullWavPath = path.join(OUTPUT_DIR, "full.wav");
  const totalDuration = concatWavFiles(wavPaths, fullWavPath);
  console.log(`전체 오디오 완성: ${fullWavPath} (${totalDuration.toFixed(1)}초)`);

  // segments.json 저장
  const segmentsJson = {
    totalDuration,
    silenceGap: SILENCE_DURATION,
    segments: results.map((r) => ({
      sceneId: r.id,
      speechDuration: r.duration,
      start: r.start,
      end: r.end,
    })),
  };

  const segmentsFile = path.join(OUTPUT_DIR, "segments.json");
  fs.writeFileSync(segmentsFile, JSON.stringify(segmentsJson, null, 2));
  console.log(`segments.json 저장: ${segmentsFile}`);

  // timeline.json 저장 (Remotion 컴포지션용)
  const FPS = 30;
  const totalFrames = Math.ceil(totalDuration * FPS);

  const timelineScenes = results.map((r, i) => {
    const nextStart =
      i < results.length - 1 ? results[i + 1].start : totalDuration;
    const endTime = nextStart;
    const durationFrames = Math.round((endTime - r.start) * FPS);

    return {
      id: r.id,
      anchor_time: r.start,
      end_time: endTime,
      duration_frames: durationFrames,
      start_frame: Math.round(r.start * FPS),
    };
  });

  const timelineJson = {
    totalDuration,
    totalFrames,
    fps: FPS,
    scenes: timelineScenes,
  };

  const timelineFile = path.join(OUTPUT_DIR, "timeline.json");
  fs.writeFileSync(timelineFile, JSON.stringify(timelineJson, null, 2));
  console.log(`timeline.json 저장: ${timelineFile}`);

  console.log("\nTTS 생성 완료!");
  console.log(`총 재생 시간: ${(totalDuration / 60).toFixed(1)}분`);
}

main().catch((e) => {
  console.error(e);
  process.exit(1);
});
