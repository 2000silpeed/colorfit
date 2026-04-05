export interface StepData {
  persona: string;
  id: string;
  title: string;
  desc: string;
  url: string;
  screenshot: string;
  timestamp?: string;
}

export interface NarrationSegment {
  sceneId: string;
  speechDuration: number;
  start: number;
  end: number;
}

export interface NarrationData {
  totalDuration: number;
  silenceGap: number;
  segments: NarrationSegment[];
}

export type PersonaId = "A" | "B" | "C";

export interface PersonaInfo {
  id: PersonaId;
  name: string;
  age: string;
  tone: string;
  tpo: string;
  accentColor: string;
  videoFile: string;
  steps: StepData[];
}
