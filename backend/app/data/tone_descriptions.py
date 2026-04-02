"""13-tone 퍼스널컬러 설명 + worst_colors 정적 데이터."""

from __future__ import annotations

TONE_DESCRIPTIONS: dict[str, dict] = {
    "spring_warm_light": {
        "description": "밝고 따뜻한 파스텔 톤이 가장 잘 어울려요. 복숭아빛, 크림색처럼 부드럽고 화사한 색감이 피부를 환하게 만들어줍니다.",
        "worst_colors": [
            {"hex": "#000000", "name_ko": "블랙"},
            {"hex": "#1C1C1C", "name_ko": "차콜 블랙"},
            {"hex": "#800020", "name_ko": "버건디"},
            {"hex": "#4B0082", "name_ko": "인디고"},
            {"hex": "#808080", "name_ko": "그레이"},
        ],
    },
    "spring_warm_bright": {
        "description": "선명하고 생기 있는 따뜻한 색이 잘 어울려요. 코럴, 오렌지, 밝은 골드처럼 화사하면서도 에너지 넘치는 색감이 얼굴에 생기를 더해줍니다.",
        "worst_colors": [
            {"hex": "#000000", "name_ko": "블랙"},
            {"hex": "#808080", "name_ko": "그레이"},
            {"hex": "#C9B1D0", "name_ko": "뮤트 라벤더"},
            {"hex": "#B0A6C6", "name_ko": "소프트 퍼플"},
            {"hex": "#2F4F4F", "name_ko": "다크 슬레이트"},
        ],
    },
    "spring_warm_vivid": {
        "description": "원색에 가까운 강렬하고 따뜻한 색이 가장 잘 어울려요. 비비드 레드, 선명한 옐로, 오렌지처럼 채도가 높은 색감이 에너지를 극대화합니다.",
        "worst_colors": [
            {"hex": "#B0A6C6", "name_ko": "소프트 퍼플"},
            {"hex": "#C9B1D0", "name_ko": "뮤트 라벤더"},
            {"hex": "#D3D3D3", "name_ko": "라이트 그레이"},
            {"hex": "#808080", "name_ko": "그레이"},
            {"hex": "#FADADD", "name_ko": "베이비 핑크"},
        ],
    },
    "summer_cool_light": {
        "description": "차가우면서 밝은 파스텔 톤이 잘 어울려요. 라벤더, 베이비 블루, 소프트 로즈처럼 시원하고 투명한 색감이 피부의 맑은 느낌을 살려줍니다.",
        "worst_colors": [
            {"hex": "#FF6600", "name_ko": "비비드 오렌지"},
            {"hex": "#FF0000", "name_ko": "비비드 레드"},
            {"hex": "#8B4513", "name_ko": "새들 브라운"},
            {"hex": "#FFD700", "name_ko": "골드"},
            {"hex": "#000000", "name_ko": "블랙"},
        ],
    },
    "summer_cool_soft": {
        "description": "차분하고 부드러운 쿨톤이 가장 잘 어울려요. 회색이 살짝 섞인 소프트한 색감이 우아하고 세련된 분위기를 만들어줍니다.",
        "worst_colors": [
            {"hex": "#FF0000", "name_ko": "비비드 레드"},
            {"hex": "#FF6600", "name_ko": "비비드 오렌지"},
            {"hex": "#FFD700", "name_ko": "골드"},
            {"hex": "#000000", "name_ko": "블랙"},
            {"hex": "#8B4513", "name_ko": "새들 브라운"},
        ],
    },
    "summer_cool_bright": {
        "description": "선명하면서도 차가운 톤이 잘 어울려요. 로열 블루, 핫 핑크, 밝은 퍼플처럼 시원한 색감 속에서 선명도가 높은 색이 세련된 인상을 줍니다.",
        "worst_colors": [
            {"hex": "#8B4513", "name_ko": "새들 브라운"},
            {"hex": "#CC7722", "name_ko": "옥토버 오렌지"},
            {"hex": "#C4A882", "name_ko": "뮤트 베이지"},
            {"hex": "#556B2F", "name_ko": "다크 올리브"},
            {"hex": "#6F4E37", "name_ko": "에스프레소"},
        ],
    },
    "summer_cool_mute": {
        "description": "탁하고 차분한 쿨톤이 가장 잘 어울려요. 먼지가 살짝 낀 듯한 뮤트 컬러가 은은하고 고급스러운 분위기를 연출해줍니다.",
        "worst_colors": [
            {"hex": "#FF0000", "name_ko": "비비드 레드"},
            {"hex": "#FFFF00", "name_ko": "비비드 옐로"},
            {"hex": "#FF6600", "name_ko": "비비드 오렌지"},
            {"hex": "#00FF00", "name_ko": "비비드 그린"},
            {"hex": "#FFD700", "name_ko": "골드"},
        ],
    },
    "autumn_warm_deep": {
        "description": "깊고 진한 따뜻한 색이 잘 어울려요. 버건디, 다크 브라운, 올리브처럼 깊이감 있는 색이 얼굴에 고급스러운 분위기를 더해줍니다.",
        "worst_colors": [
            {"hex": "#FADADD", "name_ko": "베이비 핑크"},
            {"hex": "#E6E6FA", "name_ko": "라이트 라벤더"},
            {"hex": "#87CEEB", "name_ko": "스카이 블루"},
            {"hex": "#FFB6C1", "name_ko": "라이트 핑크"},
            {"hex": "#F0FFF0", "name_ko": "허니듀"},
        ],
    },
    "autumn_warm_mute": {
        "description": "차분하고 따뜻한 뮤트 톤이 가장 잘 어울려요. 카키, 베이지, 더스티 로즈처럼 자연스럽고 편안한 색감이 부드러운 인상을 만들어줍니다.",
        "worst_colors": [
            {"hex": "#FF0000", "name_ko": "비비드 레드"},
            {"hex": "#0000FF", "name_ko": "비비드 블루"},
            {"hex": "#FFFF00", "name_ko": "비비드 옐로"},
            {"hex": "#FF00FF", "name_ko": "비비드 핑크"},
            {"hex": "#000000", "name_ko": "블랙"},
        ],
    },
    "autumn_warm_strong": {
        "description": "강렬하고 깊이 있는 따뜻한 색이 잘 어울려요. 번트 오렌지, 테라코타, 머스터드처럼 풍성하고 힘 있는 색감이 존재감을 살려줍니다.",
        "worst_colors": [
            {"hex": "#E6E6FA", "name_ko": "라이트 라벤더"},
            {"hex": "#FADADD", "name_ko": "베이비 핑크"},
            {"hex": "#87CEEB", "name_ko": "스카이 블루"},
            {"hex": "#D3D3D3", "name_ko": "라이트 그레이"},
            {"hex": "#C0C0C0", "name_ko": "실버"},
        ],
    },
    "winter_cool_deep": {
        "description": "어둡고 깊은 쿨톤이 가장 잘 어울려요. 블랙, 네이비, 딥 와인처럼 무게감 있는 색이 강렬하고 시크한 분위기를 극대화합니다.",
        "worst_colors": [
            {"hex": "#FFE4C4", "name_ko": "비스크"},
            {"hex": "#FADADD", "name_ko": "베이비 핑크"},
            {"hex": "#F5E6CC", "name_ko": "바닐라"},
            {"hex": "#C4A882", "name_ko": "뮤트 베이지"},
            {"hex": "#FFB347", "name_ko": "파스텔 오렌지"},
        ],
    },
    "winter_cool_strong": {
        "description": "선명하고 강한 쿨톤이 잘 어울려요. 트루 레드, 로열 블루, 에메랄드처럼 채도가 높은 차가운 색이 시크하면서도 세련된 인상을 줍니다.",
        "worst_colors": [
            {"hex": "#C4A882", "name_ko": "뮤트 베이지"},
            {"hex": "#D2B48C", "name_ko": "탠"},
            {"hex": "#8B4513", "name_ko": "새들 브라운"},
            {"hex": "#F5E6CC", "name_ko": "바닐라"},
            {"hex": "#CC7722", "name_ko": "옥토버 오렌지"},
        ],
    },
    "winter_cool_vivid": {
        "description": "가장 선명하고 강렬한 쿨톤이 잘 어울려요. 퓨어 레드, 일렉트릭 블루, 마젠타처럼 원색에 가까운 색이 극적인 대비를 만들어 화려한 존재감을 줍니다.",
        "worst_colors": [
            {"hex": "#C4A882", "name_ko": "뮤트 베이지"},
            {"hex": "#B0A6C6", "name_ko": "소프트 퍼플"},
            {"hex": "#D2B48C", "name_ko": "탠"},
            {"hex": "#C9B1D0", "name_ko": "뮤트 라벤더"},
            {"hex": "#808080", "name_ko": "그레이"},
        ],
    },
}
