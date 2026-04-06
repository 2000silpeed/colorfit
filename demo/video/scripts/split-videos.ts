/**
 * E2E 녹화 비디오를 씬별 MP4 클립으로 분할한다.
 * timestamp 기반으로 시작/종료 시간을 계산하고 ffmpeg로 잘라낸다.
 *
 * 실행: npx ts-node --project tsconfig.node.json scripts/split-videos.ts
 */

import * as fs from "fs";
import * as path from "path";
import { execSync } from "child_process";

const E2E_OUTPUT = path.resolve(__dirname, "../../e2e/output");
const VIDEO_PUBLIC = path.resolve(__dirname, "../public/video-clips");

interface StepEntry {
  id: string;
  timestamp: string;
}

interface ClipInfo {
  id: string;
  start: number;
  duration: number;
  file: string;
}

function loadSteps(persona: string): StepEntry[] {
  // E2E output의 steps_X.json (timestamp 포함)
  const file = path.join(E2E_OUTPUT, `steps_${persona}.json`);
  return JSON.parse(fs.readFileSync(file, "utf-8"));
}

function splitVideo(
  videoPath: string,
  steps: StepEntry[],
  prefix: string,
  extraPadEnd: number = 2
): ClipInfo[] {
  const clips: ClipInfo[] = [];
  const base = new Date(steps[0].timestamp).getTime();

  for (let i = 0; i < steps.length; i++) {
    const step = steps[i];
    const start = (new Date(step.timestamp).getTime() - base) / 1000;
    const nextStart = steps[i + 1]
      ? (new Date(steps[i + 1].timestamp).getTime() - base) / 1000
      : start + extraPadEnd;

    // 씬 전환을 보여주기 위해 다음 씬 시작 0.5초 후까지 포함
    const duration = Math.min(nextStart - start + 0.5, nextStart - start + extraPadEnd);

    const outFile = `${prefix}_${step.id}.mp4`;
    const outPath = path.join(VIDEO_PUBLIC, outFile);

    if (fs.existsSync(outPath)) {
      console.log(`  스킵 (이미 존재): ${outFile}`);
      clips.push({ id: step.id, start, duration, file: `video-clips/${outFile}` });
      continue;
    }

    console.log(`  분할: ${step.id} (${start.toFixed(1)}s, ${duration.toFixed(1)}s)`);

    execSync(
      `ffmpeg -y -ss ${start.toFixed(3)} -i "${videoPath}" -t ${duration.toFixed(3)} ` +
        `-vf "scale=390:844:force_original_aspect_ratio=decrease,pad=390:844:(ow-iw)/2:(oh-ih)/2:color=white" ` +
        `-c:v libx264 -preset fast -crf 23 -pix_fmt yuv420p -an "${outPath}"`,
      { stdio: "pipe" }
    );

    clips.push({ id: step.id, start, duration, file: `video-clips/${outFile}` });
  }

  return clips;
}

function main() {
  fs.mkdirSync(VIDEO_PUBLIC, { recursive: true });

  const personas = [
    { key: "A", prefix: "a", video: "video_A.webm" },
    { key: "B", prefix: "b", video: "video_B.webm" },
    { key: "C", prefix: "c", video: "video_C.webm" },
  ];

  const allClips: Record<string, ClipInfo[]> = {};

  for (const p of personas) {
    const videoPath = path.join(E2E_OUTPUT, p.video);
    if (!fs.existsSync(videoPath)) {
      console.log(`⚠️ ${p.video} 없음, 스킵`);
      continue;
    }

    console.log(`\n=== Persona ${p.key} ===`);
    const steps = loadSteps(p.key);
    const clips = splitVideo(videoPath, steps, p.prefix, 2);
    allClips[p.prefix] = clips;
  }

  // video-clips.json 저장
  const outputJson = path.join(VIDEO_PUBLIC, "clips.json");
  fs.writeFileSync(outputJson, JSON.stringify(allClips, null, 2));
  console.log(`\nclips.json 저장: ${outputJson}`);

  const totalClips = Object.values(allClips).reduce((s, c) => s + c.length, 0);
  console.log(`총 ${totalClips}개 클립 생성 완료`);
}

main();
