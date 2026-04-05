import React from "react";
import {
  useCurrentFrame,
  interpolate,
  spring,
  useVideoConfig,
} from "remotion";

interface PersonaIntroSceneProps {
  personaLabel: string;
  name: string;
  age: string;
  tone: string;
  tpo: string;
  accentColor: string;
  index: number;
}

export const PersonaIntroScene: React.FC<PersonaIntroSceneProps> = ({
  personaLabel,
  name,
  age,
  tone,
  tpo,
  accentColor,
  index,
}) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  const cardScale = spring({
    frame,
    fps,
    config: { damping: 16, stiffness: 100 },
  });
  const cardOpacity = interpolate(frame, [0, 15], [0, 1], {
    extrapolateRight: "clamp",
  });

  const tag1Opacity = interpolate(frame, [20, 35], [0, 1], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });
  const tag1X = interpolate(frame, [20, 35], [-30, 0], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });

  const tag2Opacity = interpolate(frame, [30, 45], [0, 1], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });
  const tag2X = interpolate(frame, [30, 45], [-30, 0], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });

  const tag3Opacity = interpolate(frame, [40, 55], [0, 1], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });
  const tag3X = interpolate(frame, [40, 55], [-30, 0], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });

  const indexBgColors = ["#964F4C", "#5C7A6E", "#4A6B8A"];
  const bgColor = indexBgColors[index] || "#964F4C";

  const tags = [
    { label: "연령", value: age },
    { label: "퍼스널컬러", value: tone },
    { label: "TPO", value: tpo },
  ];

  const tagAnimations = [
    { opacity: tag1Opacity, x: tag1X },
    { opacity: tag2Opacity, x: tag2X },
    { opacity: tag3Opacity, x: tag3X },
  ];

  return (
    <div
      style={{
        width: "100%",
        height: "100%",
        background: "#F8F6F3",
        display: "flex",
        alignItems: "center",
        justifyContent: "center",
        fontFamily: "'Pretendard Variable', 'Pretendard', sans-serif",
      }}
    >
      <div
        style={{
          transform: `scale(${cardScale})`,
          opacity: cardOpacity,
          background: "white",
          borderRadius: 32,
          padding: "60px 80px",
          boxShadow: "0 24px 80px rgba(44, 36, 34, 0.10)",
          minWidth: 700,
          display: "flex",
          flexDirection: "column",
          gap: 32,
        }}
      >
        {/* 상단: 번호 + 페르소나 라벨 */}
        <div style={{ display: "flex", alignItems: "center", gap: 20 }}>
          <div
            style={{
              width: 60,
              height: 60,
              borderRadius: 18,
              background: bgColor,
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
              fontSize: 28,
              fontWeight: 700,
              color: "white",
              flexShrink: 0,
            }}
          >
            {String.fromCharCode(65 + index)}
          </div>
          <div>
            <div
              style={{
                fontSize: 15,
                color: "#8C7B77",
                fontWeight: 500,
                letterSpacing: 2,
                textTransform: "uppercase",
                marginBottom: 4,
              }}
            >
              Persona {String.fromCharCode(65 + index)}
            </div>
            <div
              style={{
                fontSize: 34,
                fontWeight: 700,
                color: "#2C2422",
                letterSpacing: -1,
              }}
            >
              {name}
            </div>
          </div>
        </div>

        {/* 구분선 */}
        <div
          style={{
            height: 1,
            background: "linear-gradient(to right, #EDE9E4, transparent)",
          }}
        />

        {/* 태그 목록 */}
        <div style={{ display: "flex", flexDirection: "column", gap: 16 }}>
          {tags.map((tag, i) => (
            <div
              key={tag.label}
              style={{
                display: "flex",
                alignItems: "center",
                gap: 16,
                opacity: tagAnimations[i].opacity,
                transform: `translateX(${tagAnimations[i].x}px)`,
              }}
            >
              <div
                style={{
                  fontSize: 13,
                  color: "#8C7B77",
                  fontWeight: 500,
                  letterSpacing: 1,
                  width: 90,
                  flexShrink: 0,
                }}
              >
                {tag.label}
              </div>
              <div
                style={{
                  background: "#F8F6F3",
                  borderRadius: 10,
                  padding: "8px 20px",
                  fontSize: 22,
                  fontWeight: 600,
                  color: "#2C2422",
                }}
              >
                {tag.value}
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};
