import { truncateChars } from './util.js';
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
export function setupPfpName(IS_AUTHENTICATED,EDIT_URL,DEFAULT_IMAGE_URL,fetchedAuthorProfile, profilePicAndName){
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
                const displayName = document.createElement("h3");
                displayName.className = "display_name";
                displayName.textContent = fetchedAuthorProfile.displayName;
                profilePicAndName.appendChild(displayName);
                }
export function setupDescGithub(fetchedAuthorProfile){
                //Setup the GitHuB and Description from the fetched author
                const description = document.querySelector("#description");
                description.textContent = truncateChars(fetchedAuthorProfile.description, 100) || "No Description";
                const github = document.querySelector("#github");
                github.textContent = truncateChars(fetchedAuthorProfile.github, 100) || "GitHUb Profile Not Found";
                }
     