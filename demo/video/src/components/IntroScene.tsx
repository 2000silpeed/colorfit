import React from "react";
import {
  useCurrentFrame,
  interpolate,
  spring,
  useVideoConfig,
} from "remotion";

export const IntroScene: React.FC = () => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  const logoScale = spring({ frame, fps, config: { damping: 14, stiffness: 80 } });
  const logoOpacity = interpolate(frame, [0, 20], [0, 1], {
    extrapolateRight: "clamp",
  });

  const subtitleOpacity = interpolate(frame, [25, 50], [0, 1], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });
  const subtitleY = interpolate(frame, [25, 50], [20, 0], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });

  const taglineOpacity = interpolate(frame, [50, 75], [0, 1], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });

  return (
    <div
      style={{
        width: "100%",
        height: "100%",
        background: "linear-gradient(135deg, #F8F6F3 0%, #EDE9E4 100%)",
        display: "flex",
        flexDirection: "column",
        alignItems: "center",
        justifyContent: "center",
        fontFamily: "'Pretendard Variable', 'Pretendard', sans-serif",
      }}
    >
      {/* 배경 장식 */}
      <div
        style={{
          position: "absolute",
          top: "10%",
          right: "8%",
          width: 300,
          height: 300,
          borderRadius: "50%",
          background: "rgba(150, 79, 76, 0.06)",
        }}
      />
      <div
        style={{
          position: "absolute",
          bottom: "15%",
          left: "6%",
          width: 200,
          height: 200,
          borderRadius: "50%",
          background: "rgba(150, 79, 76, 0.04)",
        }}
      />

      {/* 로고 */}
      <div
        style={{
          transform: `scale(${logoScale})`,
          opacity: logoOpacity,
          display: "flex",
          flexDirection: "column",
          alignItems: "center",
          gap: 16,
        }}
      >
        <div
          style={{
            width: 100,
            height: 100,
            borderRadius: 28,
            background: "#964F4C",
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
            boxShadow: "0 20px 60px rgba(150, 79, 76, 0.3)",
          }}
        >
          <span style={{ fontSize: 52, color: "#F8F6F3", fontWeight: 700, letterSpacing: -2 }}>C</span>
        </div>
        <div
          style={{
            fontFamily: "'Nanum Myeongjo', Georgia, serif",
            fontSize: 80,
            fontWeight: 700,
            color: "#2C2422",
            letterSpacing: -3,
          }}
        >
          ColorFit
        </div>
      </div>

      {/* 서브타이틀 */}
      <div
        style={{
          opacity: subtitleOpacity,
          transform: `translateY(${subtitleY}px)`,
          marginTop: 32,
          fontSize: 32,
          color: "#964F4C",
          fontWeight: 500,
          letterSpacing: 1,
        }}
      >
        AI 퍼스널컬러 기반 패션 추천 엔진
      </div>

      {/* 태그라인 */}
      <div
        style={{
          opacity: taglineOpacity,
          marginTop: 20,
          fontSize: 22,
          color: "#8C7B77",
          fontWeight: 400,
          letterSpacing: 0.5,
        }}
      >
        진단받은 퍼스널컬러를 실제 쇼핑에 연결합니다
      </div>
    </div>
  );
};
