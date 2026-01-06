---
name: finalize
description: |
  교정된 자막의 업로드 준비물을 완성하는 스킬.
  영어 번역 + 자막 번인을 병렬 실행.
  /finalize 또는 "업로드 준비", "번역하고 번인해줘" 등으로 호출.
arguments:
  - name: srt
    description: 교정된 SRT 파일 경로 (미지정 시 corrected/ 목록에서 선택)
    required: false
---

# Finalize - 업로드 준비물 완성

교정된 한국어 자막으로 업로드 준비물(영어 자막 + 번인 영상)을 생성하는 스킬.

## 사용법

```bash
# SRT 파일 직접 지정
/finalize --srt 2-echo-delta/videos/subtitles/corrected/meetup_02_서진님_corrected.srt

# SRT 미지정 시 corrected/ 목록에서 선택
/finalize
```

## 워크플로우

```
┌─────────────────────────────────────────────────────┐
│                    입력 확인                         │
│  --srt 있음 → 해당 파일 사용                        │
│  --srt 없음 → corrected/ 목록 보여주고 선택 요청    │
└────────┬────────────────────────────────────────────┘
         ▼
┌─────────────────────────────────────────────────────┐
│                  영상 파일 추론                      │
│  corrected/meetup_02_서진님_corrected.srt           │
│      → 1순위: cropped/meetup_02_서진님_cropped.mov  │
│      → 2순위: raw/meetup_02_서진님.mov              │
│  (매칭 실패 시 사용자에게 질문)                     │
└────────┬────────────────────────────────────────────┘
         ▼
┌─────────────────────────────────────────────────────┐
│               실행 전 확인 (사용자에게)              │
│  - SRT: {srt_path}                                  │
│  - 영상: {video_path}                               │
│  - 진행할까요?                                      │
└────────┬────────────────────────────────────────────┘
         ▼
    ┌────┴────┐
    ▼         ▼
┌────────┐ ┌────────┐
│subtitle│ │subtitle│  (병렬 실행)
│-trans- │ │-burnin │
│lator   │ │        │
└───┬────┘ └───┬────┘
    ▼         ▼
en/{name}    burnin_output/
_en.srt      {name}_burnin.mp4
    └────┬────┘
         ▼
┌─────────────────────────────────────────────────────┐
│                    결과 보고                         │
│  - 영어 자막: en/...                                │
│  - 번인 영상: burnin_output/...                     │
│  → 업로드 준비 완료!                                │
└─────────────────────────────────────────────────────┘
```

## 실행 단계

### Step 1: 입력 확인 및 SRT 선택

`--srt` 옵션이 없으면 사용자에게 선택 요청:

```
Task: AskUserQuestion
질문: 어떤 자막 파일을 사용할까요?
옵션:
  - meetup_02_건호님_corrected.srt
  - meetup_02_동훈님_corrected.srt
  - meetup_02_동운님_corrected.srt
  - meetup_02_서진님_corrected.srt
```

corrected/ 디렉토리에서 `*_corrected.srt` 파일 목록을 가져와 보여줌.

### Step 2: 영상 파일 추론

SRT 파일명에서 영상 파일 경로 추론 (cropped 우선, raw fallback):

```python
# 매칭 로직
srt_name = "meetup_02_서진님_corrected.srt"
base_name = srt_name.replace("_corrected", "")  # meetup_02_서진님.srt
video_stem = base_name.replace(".srt", "")      # meetup_02_서진님

# 1순위: cropped 영상
cropped_path = f"cropped/{video_stem}_cropped.mov"
# 2순위: raw 영상
raw_path = f"raw/{video_stem}.mov"

# 존재 여부 확인 (ls 또는 Glob)
if exists(cropped_path):
    video_path = cropped_path
elif exists(raw_path):
    video_path = raw_path
else:
    # 매칭 실패 → 사용자에게 질문
```

매칭 실패 시 (파일 미존재):
```
Task: AskUserQuestion
질문: 영상 파일을 찾을 수 없습니다. 경로를 입력해주세요.
```

### Step 3: 실행 전 확인

사용자에게 확인 질문:

```
Task: AskUserQuestion
질문: 다음 설정으로 진행할까요?
내용:
  - SRT: subtitles/corrected/meetup_02_서진님_corrected.srt
  - 영상: cropped/meetup_02_서진님_cropped.mov (또는 raw/...)
  - 출력:
    - 영어 자막: subtitles/en/meetup_02_서진님_corrected_en.srt
    - 번인 영상: burnin_output/meetup_02_서진님_burnin.mp4
    - ASS 파일: subtitles/ass/meetup_02_서진님_corrected.ass
옵션:
  - 진행
  - 취소
```

### Step 4: 병렬 실행

두 에이전트를 **동시에** 실행:

```
Task A: video-subtitle:subtitle-translator
Prompt: |
  다음 한국어 자막을 영어로 번역해주세요.
  - srt_path: {srt_path}

Task B: video-subtitle:subtitle-burnin
Prompt: |
  다음 자막을 영상에 번인해주세요.
  - video_path: {video_path}
  - srt_path: {srt_path}
  - output_path: burnin_output/{video_stem}_burnin.mp4
  - ass_output_dir: subtitles/ass/
```

**중요**: 두 Task를 같은 메시지에서 병렬로 호출.

### Step 5: 결과 보고

두 작업 완료 후 결과 요약:

```markdown
## 업로드 준비 완료!

### 생성된 파일
| 유형 | 파일 경로 |
|------|----------|
| 영어 자막 | subtitles/en/meetup_02_서진님_corrected_en.srt |
| 번인 영상 | burnin_output/meetup_02_서진님_burnin.mp4 |

### Translator 결과
- 번역 세그먼트: {count}개
- 원어 유지 용어: RAG, MCP, LangChain 등

### Burnin 결과
- 해상도: {width}x{height}
- 자막 개수: {count}개
- 스타일: BizCafe (Noto Sans CJK KR)

### 업로드 체크리스트
- [ ] 영어 자막 검토
- [ ] 번인 영상 재생 확인
- [ ] YouTube/플랫폼 업로드
```

## 출력 경로

| 출력 | 경로 |
|------|------|
| 영어 자막 | `subtitles/en/{basename}_en.srt` |
| 번인 영상 | `burnin_output/{basename}_burnin.mp4` |
| ASS 파일 | `subtitles/ass/{basename}.ass` |

## 예시

### 예시 1: SRT 직접 지정
```
/finalize --srt 2-echo-delta/videos/subtitles/corrected/meetup_02_서진님_corrected.srt
```

### 예시 2: 대화형 선택
```
> /finalize
Claude: 어떤 자막 파일을 사용할까요?
  1. meetup_02_건호님_corrected.srt
  2. meetup_02_동훈님_corrected.srt
  3. meetup_02_동운님_corrected.srt
  4. meetup_02_서진님_corrected.srt
User: 4
Claude: 다음 설정으로 진행할까요?
  - SRT: .../meetup_02_서진님_corrected.srt
  - 영상: cropped/meetup_02_서진님_cropped.mov
User: 진행
(translator + burnin 병렬 실행)
Claude: 업로드 준비 완료!
```

## 주의사항

1. **사전 조건**: `/video-subtitle`로 교정된 SRT 파일이 있어야 함
2. **영상 파일**: raw/ 디렉토리에 원본 영상이 있어야 burnin 가능
3. **폰트**: `Noto Sans CJK KR` 폰트 설치 필요 (burnin용)
4. **처리 시간**: 영상 길이에 따라 burnin 시간 소요
