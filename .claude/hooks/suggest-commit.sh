#!/bin/bash
# suggest-commit.sh - Claude 작업 완료 후 커밋 제안 hook
# Stop 이벤트에서 실행되어 변경사항이 있으면 커밋을 제안합니다.

PROJECT_DIR="${CLAUDE_PROJECT_DIR:-$(pwd)}"

# Git 저장소인지 확인
if ! git -C "$PROJECT_DIR" rev-parse --git-dir > /dev/null 2>&1; then
    exit 0
fi

# 변경사항 확인 (staged + unstaged)
STAGED=$(git -C "$PROJECT_DIR" diff --cached --name-only 2>/dev/null)
UNSTAGED=$(git -C "$PROJECT_DIR" diff --name-only 2>/dev/null)
UNTRACKED=$(git -C "$PROJECT_DIR" ls-files --others --exclude-standard 2>/dev/null)

# 모든 변경사항 결합
ALL_CHANGES=""
if [ -n "$STAGED" ]; then
    ALL_CHANGES="$STAGED"
fi
if [ -n "$UNSTAGED" ]; then
    if [ -n "$ALL_CHANGES" ]; then
        ALL_CHANGES="$ALL_CHANGES"$'\n'"$UNSTAGED"
    else
        ALL_CHANGES="$UNSTAGED"
    fi
fi
if [ -n "$UNTRACKED" ]; then
    if [ -n "$ALL_CHANGES" ]; then
        ALL_CHANGES="$ALL_CHANGES"$'\n'"$UNTRACKED"
    else
        ALL_CHANGES="$UNTRACKED"
    fi
fi

# 중복 제거 및 정렬
ALL_CHANGES=$(echo "$ALL_CHANGES" | sort -u | grep -v '^$')

# 변경사항이 없으면 종료
if [ -z "$ALL_CHANGES" ]; then
    exit 0
fi

# 변경 파일 개수
FILE_COUNT=$(echo "$ALL_CHANGES" | wc -l)

# 변경사항 요약 출력 (Claude에게 전달)
cat << EOF

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📝 Git 변경사항 감지됨 (${FILE_COUNT}개 파일)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

변경된 파일:
$ALL_CHANGES

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
💡 커밋하시려면 다음을 확인해주세요:
   - 위 변경사항을 커밋하시겠습니까? (y/n)
   - 또는 /commit 명령으로 conventional commit 생성
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
EOF

# JSON 출력: Claude가 계속 대화할 수 있도록 block 결정
# 이렇게 하면 Claude가 사용자에게 커밋 여부를 물어볼 수 있음
echo '{"decision":"block","reason":"변경사항이 있습니다. 커밋 여부를 확인해주세요."}'

exit 0
