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
function getCSRFToken() {
  const tokenInput = document.querySelector('[name=csrfmiddlewaretoken]');
  return tokenInput ? tokenInput.value : '';
}

export function setupAuthorEntries(entries){
          const entryList = document.querySelector("#entry_list");
           if(entries){
              for (const entry of entries){
                const entry = document.createElement("li");
                li.className = "entryItem";
                li.id = "entryItem";

                // Post card container
                const postCard = document.createElement("div");
                postCard.className = "post-card";

                // Entry link
                const entryUrl = entry.entry.web;
                const link = document.createElement("a");
                link.setAttribute("href", entryUrl);

                // Header
                const header = document.createElement("div");
                header.className = "post-header";

                const headerInner = document.createElement("div");
                const title = document.createElement("div");
                title.className = "post-title";
                title.textContent = entryData.title;

                const small = document.createElement("small");
                small.textContent = `Posted by <strong>${entry.entry.author.displayName}</strong> on ${entry.entry.published}`;

                headerInner.appendChild(title);
                headerInner.appendChild(small);
                header.appendChild(headerInner);
                link.appendChild(header);

                // Content
                const contentDiv = document.createElement("div");
                contentDiv.className = "post-content";

                if (entry.entry.contentType.includes("base64")) {
                  const img = document.createElement("img");
                  img.setAttribute("src", `data:${entry.entry.contentType},${entry.entry.content}`);
                  img.setAttribute("alt", entry.entry.title);
                  contentDiv.classList.add("text-center");
                  contentDiv.appendChild(img);
                } else {
                  const p = document.createElement("p");
                  p.textContent = entry.entry.content;
                  contentDiv.appendChild(p);
                }

                link.appendChild(contentDiv);
                postCard.appendChild(link);

                // Footer
                const footer = document.createElement("div");
                footer.className = "post-footer";

                // --- Like Form ---
                const form = document.createElement("form");
                form.setAttribute("method", "post");
                form.setAttribute("action", `/wiki/like-entry/${entry.serial}/`);

                const csrfInput = document.createElement("input");
                csrfInput.setAttribute("type", "hidden");
                csrfInput.setAttribute("name", "csrfmiddlewaretoken");
                csrfInput.setAttribute("value", getCSRFToken());

                const likedFromProfile = document.createElement("input");
                likedFromProfile.setAttribute("type", "hidden");
                likedFromProfile.setAttribute("name", "liked_from_profile");
                likedFromProfile.setAttribute("value", "true");

                const likeBtn = document.createElement("button");
                likeBtn.setAttribute("type", "submit");
                likeBtn.className = "like-btn like-btn-custom border-0 bg-transparent";
                likeBtn.textContent = `❤️${entry.likes.count}`;

                form.appendChild(csrfInput);
                form.appendChild(likedFromProfile);
                form.appendChild(likeBtn);
                footer.appendChild(form);

                // --- Comment Button ---
                const commentBtn = document.createElement("a");
                commentBtn.className = "btn btn-outline-secondary btn-sm comment-btn-custom";
                commentBtn.setAttribute("href", `authors/${entry.entry.author.split("/").at(-1)}/entries/${entry.entry.serial}/`); 
                commentBtn.textContent = `💬 Comment (${entry.comments.count})`;
                footer.appendChild(commentBtn);

                // --- Share Button ---
                const shareBtn = document.createElement("button");
                shareBtn.className = "btn btn-outline-success btn-sm share-link-btn";
                shareBtn.setAttribute("type", "button");
                shareBtn.setAttribute("data-link", `${window.location.origin}/wiki/${entry.author.serial}/${entry.serial}/`);
                shareBtn.textContent = "🔗 Share Link";
                footer.appendChild(shareBtn);
              }






           }
  /* <h3>Entries</h3>
            {% if entries %}
            <link rel="stylesheet" href="{% static 'wiki/entry_card.css' %}">
                <ul class="entry_list">
                    {% for entry, rendered in entries %}   
                     <li class="entryItem"> <div class="post-card">
                        <!--Now clicking an entry (entry header) should lead to entry details-->
                        <a href="{% url 'wiki:entry_detail' author.serial entry.serial %}">
                            <div class="post-header">

                                <div>
                                    <div class="post-title">{{ entry.title }}</div>
                                    <small>
                                        Posted by <strong>{{ entry.author.displayName }}</strong>
                                        on {{ entry.created_at|date:"M d, Y H:i" }}
                                    </small>
                                </div>
                            </div>
                            
                            {% if "base64" in entry.contentType %}
                               <div class="post-content text-center">
                                   <img src="data:{{ entry.contentType }},{{ entry.content }}" alt="{{ entry.title }}" />
                               </div>
                            {% elif entry.contentType == "text/markdown" %}
                               <div class="post-content markdown-content">
                                   {{ rendered|safe }}
                               </div>
                            {% else %}
                               <div class="post-content">
                                   {{ entry.content }}
                               </div>
                            {% endif %}


                            </a>
                                <div class="post-footer">
                                        <form method="post" action="{% url 'wiki:like-entry' entry.serial %}">
                                            {% csrf_token %}
                                            <input type="hidden" name="liked_from_profile" value="true">
                                            <button type="submit" class="like-btn like-btn-custom border-0 bg-transparent">❤️{{ entry.likes.count}} </button>
                                        </form>
                                        <!--<p>{{ entry.likes.count }} likes</p>-->

                                <a href="{% url 'wiki:entry_detail' author.serial entry.serial %}" class="btn btn-outline-secondary btn-sm comment-btn-custom">💬 Comment ({{ entry.comments.count }})</a>
                                <button type="button" class="btn btn-outline-success btn-sm share-link-btn" data-link="{{ request.scheme }}://{{ request.get_host }}{% url 'wiki:entry_detail' author.serial entry.serial %}">🔗 Share Link</button>
                                </div>
                            </div>
                    {% endfor %}
                        </li>
                </ul>
            {% endif %}*/
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
     