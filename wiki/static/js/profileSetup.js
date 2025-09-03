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
export async function retrieveAuthorEntries(AUTHOR_ID){
            const url = `${AUTHOR_ID}/entries`;
            console.log(`fetched URL: ${url}`);
            const response = await fetch(url);
            if (!response.ok){
              throw new Error(`Could Not fetch this author's entries`);
            }
            const entriesJson = await response.json();
            const entries = entriesJson['src'];
            console.log(`RESPONSE STATUS CODE FOR ENTRIES RETRIEVAL: ${response.status}`);
            console.log(entries);
            return entries;
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

export function setupAuthorEntries(entries){
  const entryList = document.querySelector("#entry_list");
    if(entries){
      console.log(`entries found`);
      for (const entry of entries){
          const entryLi = document.createElement("li");
          entryLi.className = "entryItem";
          entryLi.id = "entryItem";

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
          console.log(`Entry HTML: ${entryLi}`);
      }
}
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
                const description = document.querySelector("#description");
                description.textContent = truncateChars(fetchedAuthorProfile.description, 100) || "No Description";
                const github = document.querySelector("#github");
                github.textContent = truncateChars(fetchedAuthorProfile.github, 100) || "GitHUb Profile Not Found";
                }
     