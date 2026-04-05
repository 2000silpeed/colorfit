import React from "react";
import { AbsoluteFill, Audio, Sequence, staticFile } from "remotion";
import { IntroScene } from "./components/IntroScene";
import { PersonaIntroScene } from "./components/PersonaIntroScene";
import { ScreenshotScene } from "./components/ScreenshotScene";
import { SubtitleOverlay } from "./components/SubtitleOverlay";
import { OutroScene } from "./components/OutroScene";

import stepsA from "../data/steps_a.json";
import stepsB from "../data/steps_b.json";
import stepsC from "../data/steps_c.json";
import narrationScript from "../data/narration-script.json";
import segmentsData from "../public/audio/segments.json";

const FPS = 30;
const sec = (s: number) => Math.round(s * FPS);

// sceneId → { start, end } 맵
const segMap: Record<string, { start: number; end: number }> = {};
for (const s of segmentsData.segments) {
  segMap[s.sceneId] = { start: s.start, end: s.end };
}

interface SceneTiming {
  id: string;
  startFrame: number;
  durationFrames: number;
  subtitle: string;
  screenshotFile?: string;
  sceneType: "intro" | "persona_intro" | "screenshot" | "outro";
  personaIndex?: number;
  personaName?: string;
  personaAge?: string;
  personaTone?: string;
  personaTpo?: string;
  accentColor?: string;
}

function buildTimeline(): SceneTiming[] {
  const scenes: SceneTiming[] = [];

  const push = (id: string, extra: Partial<SceneTiming>) => {
    const seg = segMap[id];
    if (!seg) return;
    scenes.push({
      id,
      startFrame: sec(seg.start),
      durationFrames: Math.max(sec(seg.end - seg.start), 1),
      subtitle: "",
      sceneType: "intro",
      ...extra,
    });
  };

  // INTRO
  push("intro", {
    sceneType: "intro",
    subtitle: narrationScript.intro.narration,
  });

  // PERSONA A
  push("persona_a_intro", {
    sceneType: "persona_intro",
    personaIndex: 0,
    personaName: "여성 20대",
    personaAge: "20대",
    personaTone: "여름쿨 소프트",
    personaTpo: "소개팅",
    accentColor: "#964F4C",
    subtitle: narrationScript.personaA.intro_narration,
  });

  narrationScript.personaA.steps.forEach((step, i) => {
    const ss = (stepsA[i] as { screenshot: string } | undefined)?.screenshot ?? "";
    push(`a_${step.id}`, {
      sceneType: "screenshot",
      screenshotFile: ss,
      subtitle: step.narration,
      accentColor: "#964F4C",
      personaName: (stepsA[i] as { title: string } | undefined)?.title ?? "",
    });
  });

  // PERSONA B
  push("persona_b_intro", {
    sceneType: "persona_intro",
    personaIndex: 1,
    personaName: "남성 30대",
    personaAge: "30대",
    personaTone: "가을웜 딥",
    personaTpo: "출근",
    accentColor: "#5C7A6E",
    subtitle: narrationScript.personaB.intro_narration,
  });

  narrationScript.personaB.steps.forEach((step, i) => {
    const ss = (stepsB[i] as { screenshot: string } | undefined)?.screenshot ?? "";
    push(`b_${step.id}`, {
      sceneType: "screenshot",
      screenshotFile: ss,
      subtitle: step.narration,
      accentColor: "#5C7A6E",
      personaName: (stepsB[i] as { title: string } | undefined)?.title ?? "",
    });
  });

  // PERSONA C
  push("persona_c_intro", {
    sceneType: "persona_intro",
    personaIndex: 2,
    personaName: "여성 40+",
    personaAge: "40대 이상",
    personaTone: "겨울쿨 딥",
    personaTpo: "하객/이벤트",
    accentColor: "#4A6B8A",
    subtitle: narrationScript.personaC.intro_narration,
  });

  narrationScript.personaC.steps.forEach((step, i) => {
    const ss = (stepsC[i] as { screenshot: string } | undefined)?.screenshot ?? "";
    push(`c_${step.id}`, {
      sceneType: "screenshot",
      screenshotFile: ss,
      subtitle: step.narration,
      accentColor: "#4A6B8A",
      personaName: (stepsC[i] as { title: string } | undefined)?.title ?? "",
    });
  });

  // OUTRO
  push("outro", {
    sceneType: "outro",
    subtitle: narrationScript.outro.narration,
  });

  return scenes;
}

const TIMELINE = buildTimeline();
export const TOTAL_FRAMES =
  TIMELINE[TIMELINE.length - 1].startFrame +
  TIMELINE[TIMELINE.length - 1].durationFrames;

export const ColorFitDemoComposition: React.FC = () => {
  return (
    <AbsoluteFill style={{ background: "#F8F6F3" }}>
      <Audio src={staticFile("audio/full.wav")} volume={1} />

      {TIMELINE.map((scene) => (
        <Sequence
          key={scene.id}
          from={scene.startFrame}
          durationInFrames={scene.durationFrames}
        >
          <AbsoluteFill>
            {scene.sceneType === "intro" && <IntroScene />}

            {scene.sceneType === "persona_intro" && (
              <PersonaIntroScene
                personaLabel={`Persona ${String.fromCharCode(65 + (scene.personaIndex ?? 0))}`}
                name={scene.personaName ?? ""}
                age={scene.personaAge ?? ""}
                tone={scene.personaTone ?? ""}
                tpo={scene.personaTpo ?? ""}
                accentColor={scene.accentColor ?? "#964F4C"}
                index={scene.personaIndex ?? 0}
              />
            )}

            {scene.sceneType === "screenshot" && scene.screenshotFile && (
              <ScreenshotScene
                screenshotPath={scene.screenshotFile}
                title={scene.personaName ?? ""}
                subtitle={scene.subtitle}
                accentColor={scene.accentColor}
              />
            )}

            {scene.sceneType === "outro" && <OutroScene />}

            {scene.sceneType !== "intro" &&
              scene.sceneType !== "outro" &&
              scene.subtitle && (
                <SubtitleOverlay
                  text={scene.subtitle}
                  accentColor={scene.accentColor}
                />
              )}
          </AbsoluteFill>
        </Sequence>
      ))}
    </AbsoluteFill>
  );
};
