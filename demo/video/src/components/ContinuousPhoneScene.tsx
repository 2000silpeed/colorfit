import React from "react";
import {
  useCurrentFrame,
  useVideoConfig,
  interpolate,
  Img,
  staticFile,
  OffthreadVideo,
} from "remotion";

interface StepTiming {
  startFrame: number;
  durationFrames: number;
  screenshotFile: string;
  videoStartSec: number;
  title: string;
  subtitle: string;
}

interface ContinuousPhoneSceneProps {
  steps: StepTiming[];
  accentColor: string;
  videoSrc?: string;
  mode: "screenshot" | "video";
}

export const ContinuousPhoneScene: React.FC<ContinuousPhoneSceneProps> = ({
  steps,
  accentColor,
  videoSrc,
  mode,
}) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  // 첫 씬 진입 애니메이션
  const enterOpacity = interpolate(frame, [0, 10], [0, 1], {
    extrapolateRight: "clamp",
  });
  const phoneY = interpolate(frame, [0, 20], [30, 0], {
    extrapolateRight: "clamp",
  });

  // 현재 프레임에 해당하는 스텝 찾기
  let currentIdx = 0;
  for (let i = steps.length - 1; i >= 0; i--) {
    if (frame >= steps[i].startFrame) {
      currentIdx = i;
      break;
    }
  }

  const current = steps[currentIdx];
  const CROSSFADE = 8; // 크로스페이드 프레임 수

  // 왼쪽 텍스트 페이드
  const textLocalFrame = frame - current.startFrame;
  const textOpacity = interpolate(textLocalFrame, [0, 12], [0, 1], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });

  return (
    <div
      style={{
        width: "100%",
        height: "100%",
        background: "#F8F6F3",
        display: "flex",
        alignItems: "center",
        justifyContent: "center",
        opacity: enterOpacity,
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
          key={`title-${currentIdx}`}
          style={{
            fontSize: 38,
            fontWeight: 700,
            color: "#2C2422",
            letterSpacing: -1,
            lineHeight: 1.3,
            opacity: textOpacity,
          }}
        >
          {current.title}
        </div>
        <div
          key={`sub-${currentIdx}`}
          style={{
            fontSize: 22,
            color: "#8C7B77",
            fontWeight: 400,
            lineHeight: 1.6,
            maxWidth: 480,
            opacity: textOpacity,
          }}
        >
          {current.subtitle}
        </div>
      </div>

      {/* 오른쪽: 폰 목업 (한 번만 렌더) */}
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
          <div
            style={{
              width: "100%",
              height: "100%",
              borderRadius: 40,
              overflow: "hidden",
              background: "#ffffff",
              position: "relative",
            }}
          >
            {mode === "video" && videoSrc ? (
              <OffthreadVideo
                src={staticFile(videoSrc)}
                startFrom={Math.round(current.videoStartSec * fps)}
                style={{
                  width: "100%",
                  height: "100%",
                  objectFit: "cover",
                  objectPosition: "top",
                }}
                volume={0}
              />
            ) : (
              <>
                {/* 크로스페이드: 현재 + 이전 스크린샷 겹침 */}
                {steps.map((step, i) => {
                  // 이 스텝이 보여야 하는지 판단
                  const isActive = i === currentIdx;
                  const isPrev = i === currentIdx - 1;

                  if (!isActive && !isPrev) return null;

                  let opacity = 1;
                  if (isActive) {
                    const localFrame = frame - step.startFrame;
                    opacity = interpolate(localFrame, [0, CROSSFADE], [0, 1], {
                      extrapolateLeft: "clamp",
                      extrapolateRight: "clamp",
                    });
                  }
                  if (isPrev) {
                    const nextStep = steps[currentIdx];
                    const localFrame = frame - nextStep.startFrame;
                    opacity = interpolate(localFrame, [0, CROSSFADE], [1, 0], {
                      extrapolateLeft: "clamp",
                      extrapolateRight: "clamp",
                    });
                  }

                  return (
                    <div
                      key={step.screenshotFile}
                      style={{
                        position: "absolute",
                        top: 0,
                        left: 0,
                        width: "100%",
                        height: "100%",
                        opacity,
                      }}
                    >
                      <Img
                        src={staticFile(step.screenshotFile)}
                        style={{
                          width: "100%",
                          height: "100%",
                          objectFit: "cover",
                          objectPosition: "top",
                        }}
                      />
                    </div>
                  );
                })}
              </>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};
