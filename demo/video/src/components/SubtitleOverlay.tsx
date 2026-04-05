import React from "react";
import { useCurrentFrame, interpolate } from "remotion";

interface SubtitleOverlayProps {
  text: string;
  accentColor?: string;
}

export const SubtitleOverlay: React.FC<SubtitleOverlayProps> = ({
  text,
  accentColor = "#964F4C",
}) => {
  const frame = useCurrentFrame();

  const opacity = interpolate(frame, [0, 8], [0, 1], {
    extrapolateRight: "clamp",
  });
  const y = interpolate(frame, [0, 8], [10, 0], {
    extrapolateRight: "clamp",
  });

  return (
    <div
      style={{
        position: "absolute",
        bottom: 60,
        left: "50%",
        transform: `translateX(-50%) translateY(${y}px)`,
        opacity,
        maxWidth: 1400,
        width: "90%",
        background: "rgba(15, 12, 11, 0.82)",
        backdropFilter: "blur(12px)",
        borderRadius: 16,
        padding: "20px 40px",
        display: "flex",
        alignItems: "center",
        gap: 16,
        fontFamily: "'Pretendard Variable', 'Pretendard', sans-serif",
      }}
    >
      <div
        style={{
          width: 4,
          height: 32,
          borderRadius: 2,
          background: accentColor,
          flexShrink: 0,
        }}
      />
      <div
        style={{
          fontSize: 28,
          color: "rgba(255, 255, 255, 0.95)",
          fontWeight: 400,
          lineHeight: 1.5,
          letterSpacing: 0.3,
        }}
      >
        {text}
      </div>
    </div>
  );
};
