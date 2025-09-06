import { marked } from "https://unpkg.com/marked@latest/lib/marked.esm.js";
export function truncateChars(text, limit) {
  if (!text) return '';
  return text.length > limit ? text.slice(0, limit) + '…' : text;
}
export function renderMarkdown(entries){
      const entryList = entries;
      const renderedEntries = [];
      entryList.forEach(entry => {
        const rendered = entry.contentType ==="text/markdown"
        ? marked.parse(entry.content)
        : entry.content;
        
      renderedEntries.push({entry, rendered});   
    });
    return renderedEntries;
    }
    
    
export function buildEditProfileUrl(username){
    return `/${username}/profile/edit/`;
}