import React from "react";
import {
  useCurrentFrame,
  interpolate,
  OffthreadVideo,
  staticFile,
} from "remotion";

interface VideoClipSceneProps {
  videoSrc: string;
  startFromSec: number;
  playbackRate?: number;
  title: string;
  subtitle?: string;
  accentColor?: string;
}

export const VideoClipScene: React.FC<VideoClipSceneProps> = ({
  videoSrc,
  startFromSec,
  playbackRate = 1,
  title,
  subtitle,
  accentColor = "#964F4C",
}) => {
  const frame = useCurrentFrame();

  const opacity = interpolate(frame, [0, 10], [0, 1], {
    extrapolateRight: "clamp",
  });

  const phoneY = interpolate(frame, [0, 20], [30, 0], {
    extrapolateRight: "clamp",
  });

  const labelOpacity = interpolate(frame, [12, 25], [0, 1], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });

  // startFrom은 컴포지션 fps 기준 (Remotion 스펙)
  const COMP_FPS = 30;
  const startFromFrame = Math.round(startFromSec * COMP_FPS);

  return (
    <div
      style={{
        width: "100%",
        height: "100%",
        background: "#F8F6F3",
        display: "flex",
        alignItems: "center",
        justifyContent: "center",
        opacity,
        fontFamily: "'Pretendard Variable', 'Pretendard', sans-serif",
      }}
    >
      {/* 왼쪽: 텍스트 영역 */}
      <div
        style={{
          flex: 1,
          display: "flex",
          flexDirection: "column",
          justifyContent: "center",
          padding: "80px 60px 80px 100px",
          gap: 16,
          opacity: labelOpacity,
        }}
      >
        <div
          style={{
            width: 48,
            height: 4,
            borderRadius: 2,
            background: accentColor,
            marginBottom: 8,
          }}
        />
        <div
          style={{
            fontSize: 38,
            fontWeight: 700,
            color: "#2C2422",
            letterSpacing: -1,
            lineHeight: 1.3,
          }}
        >
          {title}
        </div>
        {subtitle && (
          <div
            style={{
              fontSize: 22,
              color: "#8C7B77",
              fontWeight: 400,
              lineHeight: 1.6,
              maxWidth: 480,
            }}
          >
            {subtitle}
          </div>
        )}
      </div>

      {/* 오른쪽: 폰 목업 + 비디오 */}
      <div
        style={{
          flex: 1,
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
          paddingRight: 80,
          transform: `translateY(${phoneY}px)`,
        }}
      >
        <div
          style={{
            width: 360,
            height: 740,
            borderRadius: 48,
            background: "#1a1a1a",
            padding: 10,
            boxShadow:
              "0 40px 120px rgba(0,0,0,0.25), inset 0 0 0 1px rgba(255,255,255,0.1)",
            position: "relative",
          }}
        >
          {/* 폰 상단 노치 */}
          <div
            style={{
              position: "absolute",
              top: 14,
              left: "50%",
              transform: "translateX(-50%)",
              width: 120,
              height: 28,
              background: "#1a1a1a",
              borderRadius: 14,
              zIndex: 10,
            }}
          />
          {/* 스크린 — 비디오 재생 */}
          <div
            style={{
              width: "100%",
              height: "100%",
              borderRadius: 40,
              overflow: "hidden",
              background: "#ffffff",
            }}
          >
            <OffthreadVideo
              src={staticFile(videoSrc)}
              style={{
                width: "100%",
                height: "100%",
                objectFit: "cover",
                objectPosition: "top",
              }}
              startFrom={startFromFrame}
              playbackRate={playbackRate}
              volume={0}
            />
          </div>
        </div>
      </div>
    </div>
  );
};
