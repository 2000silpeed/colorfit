import React from "react";
import { AbsoluteFill, Audio, Sequence, staticFile } from "remotion";
import { IntroScene } from "./components/IntroScene";
import { PersonaIntroScene } from "./components/PersonaIntroScene";
import { ContinuousPhoneScene } from "./components/ContinuousPhoneScene";
import { SubtitleOverlay } from "./components/SubtitleOverlay";
import { OutroScene } from "./components/OutroScene";

import stepsA from "../data/steps_a.json";
import stepsB from "../data/steps_b.json";
import stepsC from "../data/steps_c.json";
import narrationScript from "../data/narration-script.json";
import segmentsData from "../public/audio/segments.json";

const FPS = 30;
const sec = (s: number) => Math.round(s * FPS);

// sceneId → { start, end }
const segMap: Record<string, { start: number; end: number }> = {};
for (const s of segmentsData.segments) {
  segMap[s.sceneId] = { start: s.start, end: s.end };
}

interface StepTiming {
  startFrame: number;
  durationFrames: number;
  screenshotFile: string;
  videoStartSec: number;
  title: string;
  subtitle: string;
}

interface PersonaBlock {
  introId: string;
  introProps: {
    personaLabel: string;
    name: string;
    age: string;
    tone: string;
    tpo: string;
    accentColor: string;
    index: number;
    subtitle: string;
  };
  steps: StepTiming[];
  accentColor: string;
  blockStartFrame: number;
  blockDurationFrames: number;
}

function buildPersonaBlock(
  prefix: string,
  introId: string,
  introNarration: string,
  narrationSteps: { id: string; narration: string }[],
  stepsData: { screenshot: string; title: string }[],
  introProps: Omit<PersonaBlock["introProps"], "subtitle">,
  accentColor: string,
): PersonaBlock {
  const introSeg = segMap[introId];
  const steps: StepTiming[] = [];

  const firstStepId = `${prefix}_${narrationSteps[0].id}`;
  const lastStepId = `${prefix}_${narrationSteps[narrationSteps.length - 1].id}`;
  const blockStart = introSeg ? introSeg.start : 0;

  narrationSteps.forEach((ns, i) => {
    const sceneId = `${prefix}_${ns.id}`;
    const seg = segMap[sceneId];
    if (!seg) return;

    const ss = stepsData[i]?.screenshot ?? "";
    steps.push({
      // 블록 내부 기준 프레임 (블록 시작 = 0)
      startFrame: sec(seg.start - blockStart) - (introSeg ? sec(introSeg.end - introSeg.start) : 0),
      durationFrames: Math.max(sec(seg.end - seg.start), 1),
      screenshotFile: ss,
      videoStartSec: 0,
      title: stepsData[i]?.title ?? "",
      subtitle: ns.narration,
    });
  });

  // 블록: persona_intro 끝 ~ 마지막 스텝 끝
  const introEnd = introSeg ? sec(introSeg.end) : 0;
  const lastSeg = segMap[lastStepId];
  const blockEnd = lastSeg ? sec(lastSeg.end) : introEnd;

  return {
    introId,
    introProps: { ...introProps, subtitle: introNarration },
    steps,
    accentColor,
    blockStartFrame: introEnd,
    blockDurationFrames: blockEnd - introEnd,
  };
}

// 빌드
const personaA = buildPersonaBlock(
  "a", "persona_a_intro",
  narrationScript.personaA.intro_narration,
  narrationScript.personaA.steps,
  stepsA as { screenshot: string; title: string }[],
  { personaLabel: "Persona A", name: "여성 20대", age: "20대", tone: "여름쿨 소프트", tpo: "소개팅", accentColor: "#964F4C", index: 0 },
  "#964F4C",
);

const personaB = buildPersonaBlock(
  "b", "persona_b_intro",
  narrationScript.personaB.intro_narration,
  narrationScript.personaB.steps,
  stepsB as { screenshot: string; title: string }[],
  { personaLabel: "Persona B", name: "남성 30대", age: "30대", tone: "가을웜 딥", tpo: "출근", accentColor: "#5C7A6E", index: 1 },
  "#5C7A6E",
);

const personaC = buildPersonaBlock(
  "c", "persona_c_intro",
  narrationScript.personaC.intro_narration,
  narrationScript.personaC.steps,
  stepsC as { screenshot: string; title: string }[],
  { personaLabel: "Persona C", name: "여성 40+", age: "40대 이상", tone: "겨울쿨 딥", tpo: "옷장→코디 완성", accentColor: "#4A6B8A", index: 2 },
  "#4A6B8A",
);

const personas = [personaA, personaB, personaC];

// intro / outro
const introSeg = segMap["intro"];
const outroSeg = segMap["outro"];

// 전체 프레임 계산
const allSegs = segmentsData.segments;
const lastSeg = allSegs[allSegs.length - 1];
export const TOTAL_FRAMES = sec(lastSeg.start + (lastSeg.end - lastSeg.start));

export const ColorFitDemoComposition: React.FC = () => {
  return (
    <AbsoluteFill style={{ background: "#F8F6F3" }}>
      <Audio src={staticFile("audio/full.wav")} volume={1} />

      {/* INTRO */}
      {introSeg && (
        <Sequence from={sec(introSeg.start)} durationInFrames={sec(introSeg.end - introSeg.start)}>
          <IntroScene />
          <SubtitleOverlay text={narrationScript.intro.narration} />
        </Sequence>
      )}

      {/* PERSONAS */}
      {personas.map((p) => {
        const introSegData = segMap[p.introId];
        if (!introSegData) return null;

        return (
          <React.Fragment key={p.introId}>
            {/* Persona Intro */}
            <Sequence
              from={sec(introSegData.start)}
              durationInFrames={sec(introSegData.end - introSegData.start)}
            >
              <PersonaIntroScene
                personaLabel={p.introProps.personaLabel}
                name={p.introProps.name}
                age={p.introProps.age}
                tone={p.introProps.tone}
                tpo={p.introProps.tpo}
                accentColor={p.introProps.accentColor}
                index={p.introProps.index}
              />
              <SubtitleOverlay
                text={p.introProps.subtitle}
                accentColor={p.accentColor}
              />
            </Sequence>

            {/* 스텝들: 하나의 연속 Sequence */}
            <Sequence
              from={p.blockStartFrame}
              durationInFrames={p.blockDurationFrames}
            >
              <ContinuousPhoneScene
                steps={p.steps}
                accentColor={p.accentColor}
                mode="screenshot"
              />
              {/* 자막 오버레이 — 씬별로 변경 */}
              {p.steps.map((step, i) => (
                <Sequence
                  key={`sub-${i}`}
                  from={step.startFrame}
                  durationInFrames={step.durationFrames}
                >
                  <SubtitleOverlay
                    text={step.subtitle}
                    accentColor={p.accentColor}
                  />
                </Sequence>
              ))}
            </Sequence>
          </React.Fragment>
        );
      })}

      {/* OUTRO */}
      {outroSeg && (
        <Sequence from={sec(outroSeg.start)} durationInFrames={sec(outroSeg.end - outroSeg.start)}>
          <OutroScene />
          <SubtitleOverlay text={narrationScript.outro.narration} />
        </Sequence>
      )}
    </AbsoluteFill>
  );
};
