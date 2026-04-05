import React from "react";
import {
  useCurrentFrame,
  interpolate,
  spring,
  useVideoConfig,
} from "remotion";

export const OutroScene: React.FC = () => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  const titleOpacity = interpolate(frame, [0, 25], [0, 1], {
    extrapolateRight: "clamp",
  });
  const titleScale = spring({ frame, fps, config: { damping: 14 } });

  const stat1Opacity = interpolate(frame, [30, 50], [0, 1], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });
  const stat2Opacity = interpolate(frame, [45, 65], [0, 1], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });
  const stat3Opacity = interpolate(frame, [60, 80], [0, 1], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });

  const taglineOpacity = interpolate(frame, [85, 110], [0, 1], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });

  const stats = [
    { value: "5,031", unit: "코디", label: "큐레이션된 착장" },
    { value: "167K", unit: "상품", label: "연결된 쇼핑 아이템" },
    { value: "13", unit: "톤", label: "퍼스널컬러 세부 분류" },
  ];

  const statOpacities = [stat1Opacity, stat2Opacity, stat3Opacity];

  return (
    <div
      style={{
        width: "100%",
        height: "100%",
        background: "linear-gradient(160deg, #2C2422 0%, #1a1210 100%)",
        display: "flex",
        flexDirection: "column",
        alignItems: "center",
        justifyContent: "center",
        fontFamily: "'Pretendard Variable', 'Pretendard', sans-serif",
        gap: 0,
      }}
    >
      {/* 배경 장식 */}
      <div
        style={{
          position: "absolute",
          top: "20%",
          left: "50%",
          transform: "translateX(-50%)",
          width: 600,
          height: 600,
          borderRadius: "50%",
          background: "radial-gradient(circle, rgba(150,79,76,0.12) 0%, transparent 70%)",
          pointerEvents: "none",
        }}
      />

      {/* 로고 타이틀 */}
      <div
        style={{
          opacity: titleOpacity,
          transform: `scale(${titleScale})`,
          display: "flex",
          flexDirection: "column",
          alignItems: "center",
          gap: 12,
          marginBottom: 60,
        }}
      >
        <div
          style={{
            fontFamily: "'Nanum Myeongjo', Georgia, serif",
            fontSize: 72,
            fontWeight: 700,
            color: "#F8F6F3",
            letterSpacing: -2,
          }}
        >
          ColorFit
        </div>
        <div
          style={{
            width: 60,
            height: 3,
            background: "#964F4C",
            borderRadius: 2,
          }}
        />
      </div>

      {/* 수치 통계 */}
      <div
        style={{
          display: "flex",
          gap: 60,
          marginBottom: 70,
        }}
      >
        {stats.map((stat, i) => (
          <div
            key={stat.label}
            style={{
              opacity: statOpacities[i],
              display: "flex",
              flexDirection: "column",
              alignItems: "center",
              gap: 8,
              minWidth: 200,
            }}
          >
            <div
              style={{
                display: "flex",
                alignItems: "baseline",
                gap: 6,
              }}
            >
              <span
                style={{
                  fontSize: 60,
                  fontWeight: 700,
                  color: "#964F4C",
                  letterSpacing: -2,
                  lineHeight: 1,
                }}
              >
                {stat.value}
              </span>
              <span
                style={{
                  fontSize: 26,
                  fontWeight: 600,
                  color: "#F8F6F3",
                  opacity: 0.8,
                }}
              >
                {stat.unit}
              </span>
            </div>
            <div
              style={{
                fontSize: 16,
                color: "rgba(248, 246, 243, 0.5)",
                fontWeight: 400,
                letterSpacing: 0.5,
              }}
            >
              {stat.label}
            </div>
          </div>
        ))}
      </div>

      {/* 슬로건 */}
      <div
        style={{
          opacity: taglineOpacity,
          fontSize: 30,
          color: "rgba(248, 246, 243, 0.7)",
          fontWeight: 300,
          letterSpacing: 2,
          textAlign: "center",
        }}
      >
        당신의 색을 찾아드립니다
      </div>
    </div>
  );
};
