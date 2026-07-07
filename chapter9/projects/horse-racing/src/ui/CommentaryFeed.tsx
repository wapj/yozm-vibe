export interface CommentaryMessage {
  id: string;
  text: string;
}

export interface CommentaryFeedProps {
  messages: CommentaryMessage[];
}

/** 최근 몇 줄만 유지하는 중계 피드의 상한(PRD 4.6: 2~3줄). */
export const COMMENTARY_FEED_MAX_LINES = 3;

/** PRD 4.6: 전달된 중계 메시지 중 최신 항목만 상한 개수까지 노출한다. */
export function CommentaryFeed({ messages }: CommentaryFeedProps) {
  const visible = messages.slice(-COMMENTARY_FEED_MAX_LINES);

  return (
    <ul className="commentary-feed" aria-label="실황 중계">
      {visible.map((message) => (
        <li key={message.id}>{message.text}</li>
      ))}
    </ul>
  );
}
