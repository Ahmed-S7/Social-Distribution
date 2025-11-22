import { truncateChars } from './util.js';
import { marked } from "https://unpkg.com/marked@latest/lib/marked.esm.js";
export async function retrieveAuthor(AUTHOR_ID, AUTHOR_HOST){
            const url= `${AUTHOR_HOST}${AUTHOR_ID}/profile/`
            console.log( `url fetched:${url}`);
            const response = await fetch(url);
            if (!response.ok) throw new Error(`HTTP ${response.status}`);
            const author = await response.json();
            console.log(author);
            console.log(`RESPONSE STATUS CODE: ${response.status}`);
            return author;
          }  
export async function retrieveAuthorEntries(AUTHOR_ID, page = 1, pageSize = 10){
            const url = `${AUTHOR_ID}/entries?page=${page}&size=${pageSize}`;
            console.log(`fetched URL: ${url}`);
            const response = await fetch(url);
            if (!response.ok){
              throw new Error(`Could Not fetch this author's entries`);
            }
            const entriesJson = await response.json();
            console.log(`RESPONSE STATUS CODE FOR ENTRIES RETRIEVAL: ${response.status}`);
            console.log(entriesJson);
            const pageNumber = parseInt(entriesJson['page_number']) || page;
            const size = parseInt(entriesJson['size']) || pageSize;
            const count = parseInt(entriesJson['count']) || 0;
            const totalPages = Math.ceil(count / size);
            return {
              entries: entriesJson['src'] || [],
              pagination: {
                page_number: pageNumber,
                size: size,
                count: count,
                has_previous: pageNumber > 1,
                has_next: pageNumber < totalPages && count > 0
              }
            };
          }

function getCSRFToken() {
  const tokenInput = document.querySelector('[name=csrfmiddlewaretoken]');
  return tokenInput ? tokenInput.value : '';
}

function getOriginFromUrl(url) {
  try {
    const parsedUrl = new URL(url);
    return parsedUrl.origin; // includes hostname + port
  } catch (error) {
    console.error("Invalid URL:", error);
    return null;
  }
}

export function setupAuthorEntries(entries, clearExisting = false, animate = true){
  const entryList = document.querySelector("#entry_list");
    if(clearExisting && entryList){
      entryList.innerHTML = '';
    }
    if(entries && entries.length > 0){
      console.log(`entries found: ${entries.length}`);
      entries.forEach((entry, index) => {
          const entryLi = document.createElement("li");
          entryLi.className = "entryItem profile-entry-item";
          entryLi.id = "entryItem";
          if(animate){
            entryLi.style.opacity = "0";
            entryLi.style.transform = "translateY(20px)";
          }

          // Post card container
          const postCard = document.createElement("div");
          postCard.className = "post-card";

          // Entry link - keeping your original structure
          const entryUrl = entry.web;
          const link = document.createElement("a");
          link.setAttribute("href", entryUrl);

          // Header
          const header = document.createElement("div");
          header.className = "post-header";

          const headerInner = document.createElement("div");
          const title = document.createElement("div");
          title.className = "post-title";
          title.textContent = entry.title;

          const small = document.createElement("small");
          console.log(entry.author);
          // Fixed date formatting to match HTML template
          const formattedDate = new Date(entry.published).toLocaleDateString('en-US', {
              month: 'short',
              day: '2-digit',
              year: 'numeric',
              hour: '2-digit',
              minute: '2-digit'
          });
          small.innerHTML = `Posted by <strong>${entry.author.displayName}</strong> on ${formattedDate}`;

          headerInner.appendChild(title);
          headerInner.appendChild(small);
          header.appendChild(headerInner);
          link.appendChild(header);

          // Content
          const contentDiv = document.createElement("div");
          contentDiv.className = "post-content";

          if (entry.contentType.includes("base64")) {
              const img = document.createElement("img");
              img.setAttribute("src", `data:${entry.contentType},${entry.content}`);
              img.setAttribute("alt", entry.title);
              contentDiv.classList.add("text-center");
              contentDiv.appendChild(img);
          } else if (entry.contentType === "text/markdown") {
              // Added markdown handling to match HTML
             const renderedMarkdown = marked.parse(entry.content);
             contentDiv.innerHTML = renderedMarkdown;
          } else {
              const p = document.createElement("p");
              p.textContent = entry.content;
              contentDiv.appendChild(p);
          }

          link.appendChild(contentDiv);
          postCard.appendChild(link);

          // Footer
          const footer = document.createElement("div");
          footer.className = "post-footer";

          // --- Like Form ---
          function getCSRFToken() {
          let cookieValue = null;
          if (document.cookie && document.cookie !== '') {
              const cookies = document.cookie.split(';');
              for (let i = 0; i < cookies.length; i++) {
                  const cookie = cookies[i].trim();
                  if (cookie.substring(0, 10) === 'csrftoken=') {
                      cookieValue = decodeURIComponent(cookie.substring(10));
                      break;
                  }
              }
          }
          return cookieValue;
        }


          const likeForm = document.createElement("form");
          likeForm.setAttribute("method", "post");
          likeForm.setAttribute("action", `/entries/${entry.id.split("/").at(-1)}/like/`);

          const csrfInputLike = document.createElement("input");
          csrfInputLike.setAttribute("type", "hidden");
          csrfInputLike.setAttribute("name", "csrfmiddlewaretoken");
          csrfInputLike.setAttribute("value", getCSRFToken());

          const likedFromProfile = document.createElement("input");
          likedFromProfile.setAttribute("type", "hidden");
          likedFromProfile.setAttribute("name", "liked_from_profile");
          likedFromProfile.setAttribute("value", "true");

          const likeBtn = document.createElement("button");
          likeBtn.setAttribute("type", "submit");
          likeBtn.className = "like-btn like-btn-custom border-0 bg-transparent";
          likeBtn.textContent = `❤️${entry.likes.count}`;

          likeForm.appendChild(csrfInputLike);
          likeForm.appendChild(likedFromProfile);
          likeForm.appendChild(likeBtn);
          footer.appendChild(likeForm);

          //-- Comment Form --
          const commentForm = document.createElement("form");
          commentForm.setAttribute("method", "post");
          commentForm.setAttribute("action", `/authors/${entry.author.id.split("/").at(-1)}/entries/${entry.id.split("/").at(-1)}/`);

          const csrfInputComment = document.createElement("input");
          csrfInputComment.setAttribute("type", "hidden");
          csrfInputComment.setAttribute("name", "csrfmiddlewaretoken");
          csrfInputComment.setAttribute("value", getCSRFToken());

          const commentBtn = document.createElement("button");
          commentBtn.setAttribute("type", "submit");
          commentBtn.className = "btn btn-outline-secondary btn-sm comment-btn-custom";
          commentBtn.textContent = `💬 Comment (${entry.comments.count})`;

          commentForm.appendChild(csrfInputComment);
          commentForm.appendChild(commentBtn);
          footer.appendChild(commentForm);

          // --- Share Button ---
          const shareBtn = document.createElement("button");
          shareBtn.className = "btn btn-outline-success btn-sm share-link-btn";
          shareBtn.setAttribute("type", "button");
          shareBtn.setAttribute("data-link", `/authors/${entry.author.id.split("/").at(-1)}/entries/${entry.id.split("/").at(-1)}/`); // 
          shareBtn.textContent = `🔗 Share Link`;
          footer.appendChild(shareBtn);

          // CRITICAL FIX: Append footer to postCard
          postCard.appendChild(footer);

          // Append postCard to entryLi, then add entryLi to entryList
          entryLi.appendChild(postCard);
          entryList.appendChild(entryLi);
          
          // Animate entry in with delay
          if(animate){
            setTimeout(() => {
              entryLi.style.transition = "opacity 0.5s ease-in, transform 0.5s ease-in";
              entryLi.style.opacity = "1";
              entryLi.style.transform = "translateY(0)";
            }, index * 100);
          }
          console.log(`Entry HTML: ${entryLi}`);
      });
    } else {
      if(entryList && !clearExisting){
        const noEntries = document.createElement("li");
        noEntries.className = "entryItem";
        noEntries.textContent = "No entries yet.";
        entryList.appendChild(noEntries);
      }
    }
}

export function setupPaginationControls(pagination, authorId, onPageChange){
  // Remove existing pagination if any
  const existingPagination = document.querySelector("#entries-pagination");
  if(existingPagination){
    existingPagination.remove();
  }
  
  if(!pagination || pagination.count <= pagination.size){
    return; // No pagination needed
  }
  
  const entryListSection = document.querySelector(".entry_list");
  if(!entryListSection){
    return;
  }
  
  const paginationContainer = document.createElement("div");
  paginationContainer.id = "entries-pagination";
  paginationContainer.className = "entries-pagination mt-4";
  
  const paginationNav = document.createElement("nav");
  paginationNav.setAttribute("aria-label", "Entries pagination");
  
  const paginationUl = document.createElement("ul");
  paginationUl.className = "pagination justify-content-center";
  
  // Previous button
  const prevLi = document.createElement("li");
  prevLi.className = pagination.has_previous ? "page-item" : "page-item disabled";
  const prevLink = document.createElement(pagination.has_previous ? "a" : "span");
  prevLink.className = "page-link";
  prevLink.setAttribute("aria-label", "Previous");
  prevLink.innerHTML = '<span aria-hidden="true">&laquo; Previous</span>';
  if(pagination.has_previous && onPageChange){
    prevLink.href = "#";
    prevLink.addEventListener('click', (e) => {
      e.preventDefault();
      onPageChange(pagination.page_number - 1);
    });
  }
  prevLi.appendChild(prevLink);
  paginationUl.appendChild(prevLi);
  
  // Page numbers (show current page and 2 pages on each side)
  const totalPages = Math.ceil(pagination.count / pagination.size);
  const startPage = Math.max(1, pagination.page_number - 2);
  const endPage = Math.min(totalPages, pagination.page_number + 2);
  
  if(startPage > 1){
    const firstLi = document.createElement("li");
    firstLi.className = "page-item";
    const firstLink = document.createElement("a");
    firstLink.className = "page-link";
    firstLink.textContent = "1";
    firstLink.href = "#";
    firstLink.addEventListener('click', (e) => {
      e.preventDefault();
      onPageChange(1);
    });
    firstLi.appendChild(firstLink);
    paginationUl.appendChild(firstLi);
    
    if(startPage > 2){
      const ellipsisLi = document.createElement("li");
      ellipsisLi.className = "page-item disabled";
      const ellipsisSpan = document.createElement("span");
      ellipsisSpan.className = "page-link";
      ellipsisSpan.textContent = "...";
      ellipsisLi.appendChild(ellipsisSpan);
      paginationUl.appendChild(ellipsisLi);
    }
  }
  
  for(let i = startPage; i <= endPage; i++){
    const pageLi = document.createElement("li");
    pageLi.className = i === pagination.page_number ? "page-item active" : "page-item";
    const pageLink = i === pagination.page_number ? document.createElement("span") : document.createElement("a");
    pageLink.className = "page-link";
    pageLink.textContent = i;
    if(i !== pagination.page_number && onPageChange){
      pageLink.href = "#";
      pageLink.addEventListener('click', (e) => {
        e.preventDefault();
        onPageChange(i);
      });
    }
    pageLi.appendChild(pageLink);
    paginationUl.appendChild(pageLi);
  }
  
  if(endPage < totalPages){
    if(endPage < totalPages - 1){
      const ellipsisLi = document.createElement("li");
      ellipsisLi.className = "page-item disabled";
      const ellipsisSpan = document.createElement("span");
      ellipsisSpan.className = "page-link";
      ellipsisSpan.textContent = "...";
      ellipsisLi.appendChild(ellipsisSpan);
      paginationUl.appendChild(ellipsisLi);
    }
    
    const lastLi = document.createElement("li");
    lastLi.className = "page-item";
    const lastLink = document.createElement("a");
    lastLink.className = "page-link";
    lastLink.textContent = totalPages;
    lastLink.href = "#";
    lastLink.addEventListener('click', (e) => {
      e.preventDefault();
      onPageChange(totalPages);
    });
    lastLi.appendChild(lastLink);
    paginationUl.appendChild(lastLi);
  }
  
  // Next button
  const nextLi = document.createElement("li");
  nextLi.className = pagination.has_next ? "page-item" : "page-item disabled";
  const nextLink = document.createElement(pagination.has_next ? "a" : "span");
  nextLink.className = "page-link";
  nextLink.setAttribute("aria-label", "Next");
  nextLink.innerHTML = '<span aria-hidden="true">Next &raquo;</span>';
  if(pagination.has_next && onPageChange){
    nextLink.href = "#";
    nextLink.addEventListener('click', (e) => {
      e.preventDefault();
      onPageChange(pagination.page_number + 1);
    });
  }
  nextLi.appendChild(nextLink);
  paginationUl.appendChild(nextLi);
  
  paginationNav.appendChild(paginationUl);
  paginationContainer.appendChild(paginationNav);
  
  // Add page info
  const pageInfo = document.createElement("div");
  pageInfo.className = "text-center mt-2";
  const infoText = document.createElement("small");
  infoText.className = "text-muted";
  infoText.textContent = `Showing page ${pagination.page_number} of ${totalPages} (${pagination.count} entries total)`;
  pageInfo.appendChild(infoText);
  paginationContainer.appendChild(pageInfo);
  
  // Insert after entry list
  entryListSection.parentNode.insertBefore(paginationContainer, entryListSection.nextSibling);
}

function setupPfpAndName(IS_AUTHENTICATED,EDIT_URL,DEFAULT_IMAGE_URL,fetchedAuthorProfile, profilePicAndName){
              //Profile Picture and Name Display
              //////////////////////////////////////////////////////////////////////////////////
              //Authenticated user check successful, then make the profile picture clickable
              if (IS_AUTHENTICATED){
                const link = document.createElement("a");
                  link.href = EDIT_URL;
                  link.className = "edit_profile_button";

                  //Make profile picture lead to pfp editing
                  const profileImg = document.querySelector("#profile_image_page");
                  profileImg.className = "profile_image_page";
                  profileImg.src = fetchedAuthorProfile.profileImage || DEFAULT_IMAGE_URL;
                  profileImg.alt = "Profile Picture";
                  link.appendChild(profileImg);
                  profilePicAndName.appendChild(link);

                //Authenticated user check fails, then make the profile picture non-clickable -->
                } else {
                  const profileImg = document.querySelector("#profile_image_page");
                  profileImg.className = "profile_image_page";
                  profileImg.src = fetchedAuthorProfile.profileImage || DEFAULT_IMAGE_URL;
                  profileImg.alt = "Profile Picture";
                  profilePicAndName.appendChild(profileImg);
                }

                const authorSerial = fetchedAuthorProfile.id.split("/").at(-1);

                console.log(`This author's serial is: ${authorSerial}`);
                const displayName = document.createElement("h3");
                displayName.className = "display_name";
                displayName.textContent = fetchedAuthorProfile.displayName;
                profilePicAndName.appendChild(displayName);
                /////////////////////////////////////////////////////////////////////////////////////////////
}      
export function setupProfile(IS_AUTHENTICATED,EDIT_URL,DEFAULT_IMAGE_URL,fetchedAuthorProfile, profilePicAndName){
                //Profile Picture and Name Display
                setupPfpAndName(IS_AUTHENTICATED,EDIT_URL,DEFAULT_IMAGE_URL,fetchedAuthorProfile, profilePicAndName);
                /////////////////////////////////////////////////////////////////////////////////////////////

                ////////////////////////////////////////////////////////////////////////////////////////////////
                //Setup the GitHub and Description from the fetched author
                setupDescGithub(fetchedAuthorProfile);
                /////////////////////////////////////////////////////////////////////////////////////////////////

                ////////////////////////////////////////////////////////////////////////////////////////////////
                //Setup the follow details
                const friendsCount = document.querySelector("#friends_count");
                const followerCount = document.querySelector("#follower_count");
                const followingsCount = document.querySelector("#followings_count");
                const entryCount = document.querySelector("#entry_count");

                friendsCount.textContent = fetchedAuthorProfile.friends_count;
                followerCount.textContent = fetchedAuthorProfile.followers_count;
                followingsCount.textContent = fetchedAuthorProfile.followings_count;
                entryCount.textContent = fetchedAuthorProfile.entries_count;
                }
function setupDescGithub(fetchedAuthorProfile){
                //Setup the GitHuB and Description from the fetched author
                const descriptionAndGitHub = document.querySelector('#description_content');
                const description = document.querySelector("#description");
                
                // Set description with proper class
                if (fetchedAuthorProfile.description && fetchedAuthorProfile.description.trim() !== '') {
                    description.textContent = truncateChars(fetchedAuthorProfile.description, 100);
                    description.className = "description";
                } else {
                    description.textContent = "No Description";
                    description.className = "description no-description";
                }
                
                // Only show GitHub logo if GitHub URL exists
                if (fetchedAuthorProfile.github && fetchedAuthorProfile.github.trim() !== '') {
                    // Try to get the static path from the script tag with constants
                    let gitLogoPath = '/static/images/gitLogo.png'; // default fallback
                    const constantsScript = document.querySelector('script[id="constants"]');
                    if (constantsScript) {
                        const scriptContent = constantsScript.textContent;
                        // Extract static path pattern and construct GitHub logo path
                        const defaultImageMatch = scriptContent.match(/DEFAULT_IMAGE_URL = "([^"]+)"/);
                        if (defaultImageMatch) {
                            gitLogoPath = defaultImageMatch[1].replace('/images/default_pfp.webp', '/images/gitLogo.png');
                        }
                    }
                    
                    const githubLogo = document.createElement("img");
                    githubLogo.id = "gitLogo";
                    githubLogo.src = gitLogoPath;
                    githubLogo.alt = "GitHub Logo";
                    
                    const link = document.createElement("a");
                    link.href = fetchedAuthorProfile.github;
                    link.target = "_blank";
                    link.rel = "noopener noreferrer";
                    link.className = "githubLink";
                    
                    link.appendChild(githubLogo);

                    const gitHubUserName = document.createElement("p");
                    gitHubUserName.textContent = "GitHub Profile";
                    gitHubUserName.className = "github";

                    link.appendChild(gitHubUserName);
                    descriptionAndGitHub.appendChild(link);
                } else {
                    const noGitHub = document.createElement("p");
                    noGitHub.textContent = "GitHub Profile Not Found";
                    noGitHub.className = "no-github";
                    descriptionAndGitHub.appendChild(noGitHub);
                }
                
                }
     