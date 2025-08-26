export function truncateChars(text, limit) {
  if (!text) return '';
  return text.length > limit ? text.slice(0, limit) + '…' : text;
}
         