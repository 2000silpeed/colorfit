import React from "react";
import { Composition } from "remotion";
import { ColorFitDemoComposition, TOTAL_FRAMES } from "./ColorFitDemo";

export const RemotionRoot: React.FC = () => {
  return (
    <Composition
      id="ColorFitDemo"
      component={ColorFitDemoComposition}
      durationInFrames={TOTAL_FRAMES}
      fps={30}
      width={1920}
      height={1080}
    />
  );
};
